import decimal
import io
import json
import re

import rows
from scrapy import FormRequest, Spider


class ProuniSpider(Spider):
    name = 'prouni'
    start_urls = ['http://prounialuno.mec.gov.br/consulta/publica/opcao/1/tipo/3']

    def parse(self, response):
        'Extrai os nomes dos cursos disponíveis'

        html = response.body_as_unicode()
        codigo_cursos = [line for line in html.splitlines()
                         if 'var listaProcurar' in line][0]
        json_cursos = codigo_cursos.replace('var listaProcurar =', '').strip()[:-1]
        for curso_busca in json.loads(json_cursos):
            curso_busca = curso_busca['id']
            yield FormRequest(
                callback=self.parse_cidades,
                formdata={'opcao': '1', 'tipo': '3', 'valor': curso_busca},
                meta={'curso_busca': curso_busca},
                method='POST',
                url='http://prounialuno.mec.gov.br/consulta/resultado-procurar/',
            )

    def parse_cidades(self, response):
        'Para cada nome de curso devolvido, extrai as cidades que o possui'

        meta = {
            'curso_busca': response.request.meta['curso_busca'],
        }

        uf = None
        for child in response.xpath('//div[@id="conteudo_esquerda"]/*'):
            if child.re('<div class="uf_lista"'):
                uf = child.xpath('./text()').extract()[0]

            else:
                cidade = child.xpath('./li/a')
                cidade_meta = meta.copy()
                cidade_meta['cidade_busca'] = cidade.xpath('./text()').extract()[0]
                cidade_meta['cidade_filtro'] = \
                        cidade.xpath('./@onclick').extract()[0]\
                        .replace("mostrarResultadoFinal('", '')\
                        .replace("')", '')
                cidade_meta['uf_busca'] = uf

                yield FormRequest(
                        callback=self.parse_cursos,
                        formdata={
                            'opcao': '',
                            'tipo': '3',
                            'valor': meta['curso_busca'],
                            'filtro': cidade_meta['cidade_filtro'],
                        },
                        meta=cidade_meta,
                        method='POST',
                        url='http://prounialuno.mec.gov.br/consulta/resultado-final-procurar/',
                )

    def parse_cursos(self, response):
        'Para cada cidade, extrai as universidades, campi e cursos'

        header = '''
            <table>
                <tr>
                    <td>Curso</td>
                    <td>Grau</td>
                    <td>Turno</td>
                    <td>Mensalidade</td>
                    <td>Bolsa Integral Cotas</td>
                    <td>Bolsa Integral Ampla</td>
                    <td>Bolsa Parcial Cotas</td>
                    <td>Bolsa Parcial Ampla</td>
                </tr>
        '''
        footer = '''
            </table>
        '''
        meta = response.request.meta
        curso_busca = meta['curso_busca']
        cidade_busca = meta['cidade_busca']
        uf_busca = meta['uf_busca']
        cidade_filtro = meta['cidade_filtro']

        universidades = response.xpath('//div[@class="local_ies"]')
        for universidade in universidades:
            nome_universidade = universidade.xpath('./h2/text()').extract()[0]
            campi = universidade.xpath('./table[@class="tabela_bordas campus"]')
            for campus in campi:
                campus_nome = ' '.join(campus.xpath('./thead/tr/th/text()').extract()).strip()
                campus_endereco_id = int(campus.xpath('./thead/tr/th/a/@onclick').extract()[0].replace("visualizarEndereco('", '').replace("')", ''))
                cursos = campus.xpath('./tbody/tr[not(contains(@class, "hide"))]')[2:]
                table_html = header + '\n'.join([curso.extract() for curso in cursos]) + footer
                table_cursos = rows.import_from_html(
                    io.BytesIO(table_html.encode('utf8')),
                    encoding='utf8'
                )
                regexp_curso = re.compile(r'(.*) \(([0-9]+)\)')
                cursos_extraidos = []
                for curso in table_cursos:
                    curso = dict(curso._asdict())
                    curso['curso_busca'] = curso_busca
                    curso['cidade_busca'] = cidade_busca
                    curso['uf_busca'] = uf_busca
                    curso['cidade_filtro'] = cidade_filtro

                    curso['universidade_nome'] = nome_universidade
                    curso['campus_nome'] = campus_nome
                    curso['campus_endereco_id'] = campus_endereco_id

                    curso['nome'], curso['id_curso'] = \
                            regexp_curso.findall(curso['curso'])[0]
                    del curso['curso']
                    curso['mensalidade'] = decimal.Decimal(curso['mensalidade'].replace('R$', '').replace('.', '').replace(',', '.').strip())

                    for campo in ('bolsa_integral_cotas',
                                  'bolsa_integral_ampla',
                                  'bolsa_parcial_cotas',
                                  'bolsa_parcial_ampla'):
                        if curso[campo] == '---':
                            curso[campo] = None

                    cursos_extraidos.append(curso)
                yield FormRequest(
                    callback=self.parse_campus_endereco,
                    meta={'cursos_extraidos': cursos_extraidos},
                    method='POST',
                    url=f'http://prounialuno.mec.gov.br/consulta/mostrar-endereco/id/{campus_endereco_id}',
                )

    def parse_campus_endereco(self, response):
        'Pega detalhes do endereço do campus e devolve os cursos disponíveis'

        campos = ('campus_uf campus_municipio campus_logradouro '
                  'campus_complemento campus_bairro campus_telefone').split()
        valores = response.xpath('//span[@class="txt_form"]/text()').extract()
        dados_campus = dict(zip(campos, [valor.strip() for valor in valores]))

        cursos_extraidos = response.request.meta['cursos_extraidos']
        for curso in cursos_extraidos:
            curso.update(dados_campus)
            yield curso
