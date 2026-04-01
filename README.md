# BWGI Python Challenge

Solução para os três desafios de programação enviados pela BWGI, usando apenas a biblioteca padrão do Python.

## Requisitos

- Python 3.9+
- Nenhuma dependência externa

## Como rodar

```bash
python -m unittest discover -s tests -v
```

## Estrutura

- `reconcile_accounts.py`: conciliação 1:1 entre transações, com suporte a duplicatas e tolerância de +/- 1 dia.
- `last_lines.py`: iterator que devolve as linhas de um arquivo em ordem inversa, lendo por blocos.
- `computed_property.py`: decorator no estilo `property`, com cache invalidado quando as dependências mudam.

## Notas de implementação

- `reconcile_accounts` faz o matching por grupo `(departamento, valor, beneficiário)` e prioriza a data mais cedo no arquivo oposto.
- `last_lines` lê o arquivo em modo binário, respeita o tamanho máximo de bloco e só decodifica trechos completos em UTF-8.
- `computed_property` preserva `setter`, `deleter` e docstring, e trata atributos ausentes como um estado estável enquanto continuarem ausentes.

