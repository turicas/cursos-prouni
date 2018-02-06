import csv

from scrapy import FormRequest, Spider


class EnderecosCampiSpider(Spider):
    name = 'enderecos-campi'

    def start_requests(self):
        campi = set()
        with open('cursos-prouni.csv', encoding='utf8') as fobj:
            for row in csv.DictReader(fobj):
                campus_id = row["campus_id"]
                if campus_id not in campi:
                    yield FormRequest(
                        method='POST',
                        meta=row,
                        url=f'http://prounialuno.mec.gov.br/consulta/mostrar-endereco/id/{campus_id}'
                    )
                    campi.add(campus_id)

    def parse(self, response):
        'Pega detalhes do endereço do campus e devolve os cursos disponíveis'

        campos = 'uf municipio logradouro complemento bairro telefone'.split()
        valores = response.xpath('//span[@class="txt_form"]/text()').extract()
        dados_campus = dict(zip(campos, [valor.strip() for valor in valores]))
        dados_campus['id'] = response.request.meta['campus_id']

        yield dados_campus
