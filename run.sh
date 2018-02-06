#!/bin/bash

OUTPUT1_CSV="cursos-prouni.csv"
OUTPUT1_XLS="cursos-prouni.xls"
OUTPUT2_CSV="enderecos-campi.csv"
OUTPUT2_XLS="enderecos-campi.xls"
OUTPUT_SQLITE="prouni.sqlite"
QUERY="SELECT
		*
	FROM
		table1
	ORDER BY
		mensalidade DESC,
		uf_busca ASC,
		cidade_busca ASC,
		universidade_nome ASC"

rm -rf $OUTPUT1_CSV $OUTPUT2_CSV $OUTPUT1_XLS $OUTPUT2_XLS $OUTPUT_SQLITE
scrapy runspider cursos_prouni.py \
	-s HTTPCACHE_ENABLED=False \
	-o $OUTPUT1_CSV
scrapy runspider enderecos_campi.py \
	-s HTTPCACHE_ENABLED=False \
	-o $OUTPUT2_CSV

echo "Extração ok. Convertendo arquivos..."
rows convert $OUTPUT1_CSV $OUTPUT_SQLITE
rows convert $OUTPUT2_CSV $OUTPUT_SQLITE
rows query "$QUERY" $OUTPUT_SQLITE --output=$OUTPUT1_CSV
rows convert $OUTPUT1_CSV $OUTPUT1_XLS
rows convert $OUTPUT2_CSV $OUTPUT2_XLS
