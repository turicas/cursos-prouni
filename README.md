# Cursos PROUNI

Script que baixa todos os dados relativos aos cursos que possuem bolsas
integrais e parciais no PROUNI - o script automatiza a [busca disponível no
site do PROUNI](http://prounialuno.mec.gov.br/consulta/publica/) e gera uma
planilha.


## Dados

**[Acesse diretamente os dados
extraídos](https://drive.google.com/open?id=1ojj0Gmfa7Nf4JPMfWEk37fKQdQeqFSI0)**
caso você não queira/possa rodar o script.


## Rodando

Esse script depende de Python 3.6 e de algumas bibliotecas. Instale-as
executando:

```bash
pip install -r requirements.txt
```

Daí, basta executar:

```bash
sh run.sh
```

Os arquivos `cursos-prouni.csv` e `enderecos-campi.csv` serão criados (além de
versões deles em `xls` e `sqlite`). Divirta-se! :)
