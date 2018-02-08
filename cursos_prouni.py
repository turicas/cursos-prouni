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
        regexp_curso = re.compile(r'(.*) \(([0-9]+)\)')
        regexp_notas = re.compile('bolsa\(s\) ([^ ]+) para (.+?) Nota de corte: ([0-9,]+)')
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
                campus_id = int(campus.xpath('./thead/tr/th/a/@onclick').extract()[0].replace("visualizarEndereco('", '').replace("')", ''))
                cursos = campus.xpath('./tbody/tr[not(contains(@class, "hide"))]')[2:]
                for curso in cursos:
                    html = header + curso.extract() + footer
                    table = rows.import_from_html(
                        io.BytesIO(html.encode('utf8')),
                        encoding='utf8'
                    )
                    data = dict(table[0]._asdict())
                    data['curso_id'] = curso.xpath('@onclick').extract()[0]\
                        .replace("visualizarEscolhaCurso('", '')\
                        .replace("')", '')
                    data['curso_busca'] = curso_busca
                    data['cidade_busca'] = cidade_busca
                    data['uf_busca'] = uf_busca
                    data['cidade_filtro'] = cidade_filtro

                    data['universidade_nome'] = nome_universidade
                    data['campus_nome'] = campus_nome
                    data['campus_id'] = campus_id

                    data['nome'], _ = regexp_curso.findall(data['curso'])[0]
                    del data['curso']
                    data['mensalidade'] = decimal.Decimal(
                        data['mensalidade'].replace('R$', '')
                                           .replace('.', '')
                                           .replace(',', '.').strip()
                    )

                    for campo in ('bolsa_integral_cotas',
                                  'bolsa_integral_ampla',
                                  'bolsa_parcial_cotas',
                                  'bolsa_parcial_ampla'):
                        if data[campo] == '---':
                            data[campo] = None

                    busca_notas = response.xpath(f'//div[contains(@id, "_{data["curso_id"]}")]/descendant::*/text()')
                    notas_texto = ' '.join([texto.strip()
                                            for texto in busca_notas.extract()
                                            if texto.strip()])
                    notas = set(regexp_notas.findall(notas_texto))
                    notas = {f'nota_{nota[0].replace("is", "l")}_{nota[1].split()[0]}': nota[2].replace(',', '.')
                             for nota in notas}
                    for key in ('nota_integral_ampla', 'nota_integral_cotas',
                                'nota_parcial_ampla', 'nota_parcial_cotas'):
                        data[key] = notas.get(key, None)
                    yield data
