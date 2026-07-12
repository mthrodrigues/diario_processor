# Corpus de Testes do diario_processor

## Objetivo

O corpus contém documentos reais do Diário Oficial utilizados para validar o comportamento do parser.

Cada caso representa um comportamento esperado do sistema ou uma regressão corrigida anteriormente.

O objetivo do corpus não é medir cobertura de código.

O objetivo é garantir que melhorias futuras no parser não reintroduzam erros já corrigidos.

---

# Estrutura

```
tests/
└── corpus/
    ├── textos/
    ├── expected/
    └── README.md
```

Cada arquivo em `textos/` deve possuir um arquivo correspondente em `expected/`.

Exemplo:

```
textos/
    q003_apostilamento.txt

expected/
    q003_apostilamento.json
```

---

# Origem dos documentos

Todos os arquivos em `textos/` devem ser provenientes de documentos reais.

Não utilizar:

- exemplos fictícios;
- textos simplificados;
- documentos inventados.

Sempre que possível, utilizar exatamente o bloco persistido em `publicacoes.texto_bloco`.

---

# Estrutura do JSON esperado

Cada arquivo `.json` representa o resultado esperado da execução do parser.

Exemplo:

```json
{
    "blocos": [
        {
            "numero_bloco": 1,
            "tipo": "...",
            "processo": "...",
            "contrato": "...",
            ...
        }
    ]
}
```

O JSON representa o contrato funcional do parser.

---

# Como adicionar um novo caso

## 1. Criar o caso

```
py tools/novo_caso_teste.py nome_do_caso
```

---

## 2. Copiar o texto

Colar o bloco real do Diário Oficial em:

```
tests/corpus/textos/nome_do_caso.txt
```

---

## 3. Gerar o JSON inicial

```
py tools/gerar_expected.py nome_do_caso
```

---

## 4. Revisar o JSON

O JSON gerado automaticamente deve ser revisado.

Caso o parser esteja produzindo um resultado incorreto, o JSON deve ser ajustado para refletir o comportamento esperado após a correção.

---

## 5. Executar os testes

```
pytest tests/test_corpus.py -v
```

---

# Convenção de nomes

Utilizar nomes descritivos.

Exemplos:

```
q003_apostilamento

q003_memorando

q003_protocolo

q003_corrigenda

contrato_sem_processo

designacao_fiscal

portaria_nomeacao

portaria_exoneracao
```

---

# Regra do projeto

Todo bug corrigido no parser deve gerar um novo caso no corpus.

Nenhuma correção é considerada concluída enquanto não existir um caso de regressão correspondente.

---

# Filosofia

O corpus é composto por evidências documentais.

Cada documento representa um caso real encontrado durante a evolução do sistema.

O corpus constitui uma base permanente de regressão para garantir estabilidade, reprodutibilidade e auditabilidade do parser.