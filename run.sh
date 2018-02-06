#!/bin/bash

OUTPUT_CSV="cursos-prouni.csv"
OUTPUT_XLS="cursos-prouni.xls"
OUTPUT_SQLITE="cursos-prouni.sqlite"
QUERY="SELECT
		*
	FROM
		table1
	ORDER BY
		mensalidade DESC,
		uf_busca ASC,
		cidade_busca ASC,
		universidade_nome ASC"

rm -rf $OUTPUT_CSV $OUTPUT_XLS $OUTPUT_SQLITE
scrapy runspider cursos_prouni.py \
	-s HTTPCACHE_ENABLED=True \
	-o $OUTPUT_CSV

echo "Extração ok. Convertendo arquivos..."
rows convert $OUTPUT_CSV $OUTPUT_SQLITE
rows query "$QUERY" $OUTPUT_SQLITE --output=$OUTPUT_CSV
rows convert $OUTPUT_CSV $OUTPUT_XLS
