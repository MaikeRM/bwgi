# BWGI Python Challenge

Solução dos três desafios proposta no enunciado, implementada em Python usando apenas a biblioteca padrão.

Resumo da entrega:

- 3 desafios concluídos;
- compatível com Python 3.9+;
- suíte automatizada cobrindo cenários do enunciado e casos de borda;
- sem dependências externas.

## Como executar

Rodar a suíte completa:

```bash
python3 -m unittest discover -s tests -v
```

## Desafio `reconcile_accounts`

Implementação em `reconcile_accounts.py`.

### Objetivo

Conciliar duas listas de transações e devolver cópias das entradas com uma nova coluna de status, marcando cada linha como `FOUND` ou `MISSING`.

### Abordagem

- Indexação de `transactions2` com `defaultdict(deque)`, agrupando por `(departamento, valor, beneficiário, data)`.
- Para cada linha de `transactions1`, busca por candidatos com mesma chave de negócio e data em `-1`, `0` ou `+1` dia.
- O critério de desempate segue o enunciado: a correspondência escolhe a data mais cedo disponível.
- Duplicatas são tratadas em relação `1 para 1`: uma linha só pode consumir uma contraparte ainda não utilizada.
- As entradas originais não são modificadas.

### Complexidade

- Tempo: `O(n + m)`, considerando indexação de uma lista e varredura da outra com busca em número constante de buckets.
- Memória auxiliar: `O(m)`, para armazenar o índice de `transactions2`.

### Casos cobertos

- exemplo do enunciado;
- duplicidades com correspondência `1 para 1`;
- priorização da data mais cedo;
- listas vazias;
- linhas com menos de 4 colunas;
- datas inválidas;
- preservação de colunas extras no retorno.

### Decisões e trade-offs

- Comparação literal e case-sensitive: `"16.00"` e `"16.0"` não são equivalentes; `"AWS"` e `"aws"` também não.
- Colunas extras são preservadas no retorno, mas não participam do match.
- A função valida o formato mínimo das linhas e a data ISO `YYYY-MM-DD`, mas não tenta normalizar valores de entrada.

## Desafio `last_lines`

Implementação em `last_lines.py`.

### Objetivo

Retornar um iterador que percorre um arquivo texto de trás para frente, no estilo de `tac`, sem carregar o arquivo inteiro em memória.

### Abordagem

- Abertura do arquivo em modo binário e posicionamento no fim do arquivo.
- Leitura reversa em blocos de até `chunk_size` bytes.
- Montagem das linhas completas a partir dos blocos, preservando a ordem reversa de emissão.
- Decodificação em UTF-8 apenas no momento de produzir cada linha.
- Preservação do terminador de linha quando ele existe no arquivo original.

### Complexidade

- Tempo: `O(n)` sobre o tamanho do arquivo.
- Memória auxiliar: proporcional ao `chunk_size` e ao tamanho da linha em montagem, não ao arquivo completo.

### Casos cobertos

- exemplo do enunciado;
- `chunk_size` pequeno;
- linhas maiores que o bloco;
- arquivo vazio;
- arquivo sem quebra de linha final;
- múltiplas linhas vazias;
- conteúdo UTF-8 com caracteres multibyte;
- arquivo inexistente.

### Decisões e trade-offs

- `chunk_size <= 0` gera `ValueError`.
- Exceções de abertura e leitura, como `FileNotFoundError`, `PermissionError` e `UnicodeDecodeError`, são propagadas.
- O comportamento preserva `\n` quando ele já existe; uma última linha sem terminador é retornada como está.

## Desafio `computed_property`

Implementação em `computed_property.py`.

### Objetivo

Implementar um descriptor análogo a `property`, mas com cache baseado em dependências declaradas.

### Abordagem

- O decorator recebe os nomes dos atributos dos quais a propriedade depende.
- No primeiro acesso, o getter é executado e o valor é armazenado no `__dict__` da instância.
- Em paralelo, é salvo um snapshot das dependências para comparação futura.
- Em leituras seguintes, o valor só é recomputado quando alguma dependência muda.
- Atributos ausentes são representados por um sentinel interno, permitindo detectar transições entre “ausente” e “presente”.
- `setter`, `deleter` e `docstring` são preservados para manter a interface próxima de `property`.
- O snapshot tenta congelar o estado observado com `copy.deepcopy`, cobrindo mutações in-place em dependências mutáveis usuais, como listas e dicionários.

### Complexidade

- Leitura sem invalidação: `O(k)` para comparar o estado das `k` dependências.
- Leitura com recomputação: `O(k + custo_do_getter)`, além do custo de capturar o snapshot.
- Memória auxiliar por instância: valor em cache e snapshot das dependências da propriedade.

### Casos cobertos

- cache por instância;
- recomputação após mudança de dependência;
- dependência ausente;
- valores falsy;
- acesso pela classe;
- `setter` e `deleter`;
- exceção no getter sem contaminar o cache;
- mutação in-place de lista e dicionário.

### Decisões e trade-offs

- A API pública permanece igual ao uso de um descriptor decorado: nenhuma assinatura foi alterada.
- O cache é invalidado por comparação de snapshot, não por interceptação de atribuições.
- Para objetos que não podem ser copiados em profundidade, o snapshot faz fallback para o próprio valor observado; nesses casos, a detecção de mutação in-place depende da semântica de igualdade do objeto.

## Testes

Os testes estão em:

- `tests/test_reconcile_accounts.py`
- `tests/test_last_lines.py`
- `tests/test_computed_property.py`

No estado atual do repositório, a suíte contém 45 testes automatizados cobrindo os cenários principais do enunciado e casos de borda relevantes para avaliação.
