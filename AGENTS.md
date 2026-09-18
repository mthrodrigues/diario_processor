# Diario Processor — AGENT INSTRUCTIONS

## 1. Papel deste arquivo

Este arquivo define as instruções operacionais para agentes e copilotos que trabalham no repositório `diario_processor`.

Ele **não é a fonte de verdade para cada detalhe da implementação**. Para afirmações específicas sobre arquitetura, fluxo, banco, módulos e limitações, consulte primeiro:

1. o código presente na branch em trabalho;
2. `documentacao_tecnica.md`;
3. as ADRs em `docs/adr/`;
4. a especificação do parser em `docs/especificacao_parser.md`;
5. testes e fixtures do próprio repositório.

Não invente detalhes ausentes dessas fontes.

---

## 2. Objetivo do projeto

O `diario_processor` é um pipeline determinístico de inteligência documental para Diários Oficiais municipais.

Seu objetivo é transformar PDFs de Diários Oficiais em evidência documental preservada, metadados estruturados, eventos institucionais, entidades e relacionamentos, além de catálogos consolidados de processos e contratos.

O sistema prioriza:

- determinismo;
- rastreabilidade;
- preservação da evidência;
- precisão semântica;
- idempotência das consolidações;
- qualidade dos dados;
- capacidade de auditoria e regressão.

A arquitetura atual é híbrida no sentido de que mantém evidência documental bruta e dados estruturados. A IA futura pode consumir essas informações, mas **não substitui a extração e as regras determinísticas existentes**.

---

## 3. Arquitetura atual

O fluxo principal atual é, em linhas gerais:

```text
PDF do Diário Oficial
        ↓
scanner
        ↓
extração de texto paginado
        ↓
saneamento do texto
        ↓
segmentação em blocos/publicações
        ↓
parser / metadados estruturados
        ↓
Enriquecimento Contextual determinístico
        ↓
eventos institucionais
        ↓
normalização / taxonomias
        ↓
repositórios PostgreSQL
        ↓
processos e contratos consolidados
```

Também fazem parte do fluxo atual:

- extração estruturada de beneficiários do Programa Operação Trabalho (POT);
- persistência de relações entre eventos e entidades;
- timelines de vínculos funcionais;
- publicação condicional de eventos canônicos em outbox;
- logging persistente por execução;
- testes unitários, regressões, auditorias SQL e corpus versionado.

Módulos e responsabilidades principais estão detalhados em `documentacao_tecnica.md`.

---

## 4. Persistência

### PostgreSQL é a persistência oficial atual

O pipeline principal usa PostgreSQL por meio de:

- `config.py`;
- `infra/db/connection.py`;
- `infra/db/migrations/`;
- `infra/db/repositories/`.

A configuração obrigatória do PostgreSQL é obtida por variáveis de ambiente.

### SQLite é legado/auxiliar

`database.py`, `analytics.py`, `analytics_cli.py` e `backfill.py` permanecem para compatibilidade local, testes ou utilitários auxiliares.

**Não descreva SQLite como banco institucional principal do sistema.**

Ao modificar componentes legados, preserve sua finalidade de compatibilidade e não trate a camada SQLite como justificativa para alterar o fluxo principal em PostgreSQL.

---

## 5. Invariantes arquiteturais

### 5.1. O texto bruto é evidência primária

O texto original de cada bloco deve ser preservado.

Nunca descarte ou substitua silenciosamente o texto bruto para armazenar apenas dados derivados.

### 5.2. O Diário é um container de publicações

Um PDF não deve ser tratado como uma única entidade lógica.

A segmentação em blocos/publicações é parte fundamental da arquitetura.

Extração, classificação, eventos e persistência devem respeitar a unidade documental do bloco.

### 5.3. Não misturar publicações

Processos, contratos, fornecedores, contratantes e demais entidades não devem ser associados entre blocos apenas por proximidade textual ou heurística.

Qualquer enriquecimento entre blocos precisa de uma regra determinística explicitamente definida e testada.

### 5.4. Precisão vem antes de cobertura

Falsos positivos são considerados mais graves que campos ausentes.

Não introduza regex ou heurísticas amplas apenas para aumentar a quantidade de extrações.

Prefira evidência contextual e rótulos documentais explícitos.

### 5.5. Extração e interpretação são responsabilidades diferentes

O parser é responsável pela extração estruturada.

`events.py` interpreta metadados já extraídos para construir eventos institucionais.

Não duplique regras de extração em módulos posteriores sem uma razão arquitetural explícita.

### 5.6. IA não substitui regras determinísticas

O pipeline atual deve continuar reproduzível e determinístico.

Não introduza LLMs, embeddings ou inferência probabilística no caminho de extração sem uma decisão arquitetural explícita, documentação e testes adequados.

### 5.7. Rastreabilidade

Eventos e relações devem conservar a origem documental necessária para auditoria, incluindo referência ao Diário, bloco e evidência textual quando aplicável.

### 5.8. Incrementalidade

Existe suporte para processamento incremental por `ja_processado()`, mas o fluxo principal atual mantém:

```python
REPROCESSAR_TUDO = True
```

Portanto, **o pipeline padrão atualmente reprocessa todos os PDFs**.

Não descreva incrementalidade como comportamento padrão ativo sem verificar o código atual.

---

## 6. Enriquecimento Contextual

O projeto possui uma camada de Enriquecimento Contextual entre o parser e a persistência.

A Regra 001 está implementada de forma determinística e pode herdar o contratante institucional do bloco anterior quando as pré-condições documentadas na ADR-0001 forem satisfeitas.

A EC:

- não altera o texto bruto;
- não altera a segmentação;
- deve operar com critérios determinísticos;
- deve ser conservadora para evitar falsos positivos.

Consulte `docs/adr/0001-enriquecimento-contextual.md` antes de alterar essa regra.

---

## 7. Eventos, entidades e consolidação

O sistema possui atualmente:

- eventos institucionais;
- entidades nominativas;
- vínculos evento-entidade;
- relacionamentos entre entidades;
- timelines funcionais;
- outbox de eventos canônicos;
- catálogos consolidados de processos;
- catálogos consolidados de contratos.

Processos e contratos são objetos consolidados e não devem ser tratados simplesmente como atributos descartáveis das publicações.

As consolidações devem preservar idempotência e usar as chaves normalizadas já estabelecidas.

---

## 8. Beneficiários do POT

A aplicação possui uma etapa específica para beneficiários do Programa Operação Trabalho.

A extração usa a geometria do PDF para reconstruir as colunas e associa os registros às publicações POT.

Ao modificar essa parte:

- preserve a associação com a publicação de origem;
- preserve a cardinalidade validada pelo fluxo;
- mantenha os testes existentes;
- trate alterações de segmentação com especial cautela.

---

## 9. Logging e observabilidade

O logging persistente do processamento é uma parte implementada da arquitetura.

O módulo `logging_setup.py` fornece:

- logger central `diario_processor`;
- `run_id` por execução;
- registro de sucesso por Diário;
- registro de erro com contexto e traceback;
- rotação do arquivo de log.

Consulte a ADR-011 antes de alterar o comportamento de logging.

O console continua sendo uma saída operacional resumida. O arquivo persistente de log é complementar e não deve ser transformado em dump de SQL, parâmetros ou texto completo dos blocos.

---

## 10. Testes

Toda correção funcional deve ter teste de regressão quando tecnicamente aplicável.

Mudanças no parser, regras de extração, consolidação, persistência ou contratos de dados devem considerar a suíte de testes e o corpus de regressão.

A especificação atual do parser estabelece que melhorias devem ser acompanhadas de validação por auditoria SQL quando houver impacto no SQL ou na persistência.

Não remova testes existentes para acomodar uma alteração sem justificar explicitamente a mudança de comportamento.

---

## 11. Processo de desenvolvimento

Antes de alterar código:

1. leia o módulo afetado;
2. procure documentação e ADRs relacionadas;
3. verifique testes e fixtures relevantes;
4. identifique dependências e impactos;
5. escolha a menor alteração compatível com a arquitetura atual.

Ao implementar:

- faça alterações incrementais;
- preserve APIs internas existentes quando não houver motivo para quebrá-las;
- evite abstrações desnecessárias;
- não introduza dependências novas sem justificativa;
- trate erros de forma explícita;
- mantenha nomes e responsabilidades coerentes com a arquitetura atual.

Depois da implementação:

- execute os testes relevantes;
- avalie regressões;
- atualize a documentação quando o comportamento ou a arquitetura tiver mudado;
- registre uma ADR quando houver decisão arquitetural relevante.

---

## 12. Inconsistências e limitações conhecidas

As seguintes questões já estão documentadas e **não devem ser tratadas silenciosamente como se não existissem**:

1. `main.py` mantém `REPROCESSAR_TUDO = True`, portanto a capacidade incremental existe, mas o fluxo padrão reprocessa tudo.
2. `InstitutionalEventOutboxRepository.publish()` e `build_institutional_event()` possuem atualmente um contrato incompatível documentado: o repositório espera `to_dict()`, enquanto o builder retorna `dict`. Consulte `documentacao_tecnica.md` antes de alterar ou habilitar esse caminho.
3. O logger de auditoria de aplicações bem-sucedidas da Regra 001 (`diario_processor.enrichment`) não possui handler persistente configurado no estado atual. A ADR-011 cobre as falhas da EC, não a auditoria de sucesso.
4. A taxonomia de eventos contém mais tipos do que os tipos atualmente emitidos pelo fluxo de `events.py`.

Quando uma tarefa envolver uma dessas áreas, confirme o estado atual no código e na documentação antes de propor uma correção.

---

## 13. Atualização de documentação

Quando uma mudança alterar:

- arquitetura;
- fluxo de dados;
- contrato entre módulos;
- modelo de dados;
- comportamento funcional;
- política de processamento;
- observabilidade;
- uma decisão técnica relevante;

a documentação correspondente deve ser atualizada.

Não crie documentação paralela que contradiga `documentacao_tecnica.md`.

ADRs devem registrar decisões arquiteturais, alternativas consideradas, consequências e limitações.

---

## 14. Política obrigatória de idioma

O idioma padrão do repositório e de todas as entregas de desenvolvimento é **português do Brasil (pt-BR)**.

Essa regra se aplica obrigatoriamente a:

- mensagens de commit;
- títulos e descrições de Pull Requests;
- títulos, descrições e comentários de Issues;
- resumos de alterações e releases;
- documentação nova ou alterada;
- nomes de arquivos e diretórios novos;
- nomes de recursos, funcionalidades e componentes novos, quando o domínio permitir;
- textos de interface, mensagens de log, mensagens de erro e demais textos voltados a usuários ou operadores;
- comentários de código quando forem necessários.

Ao criar novos nomes, **priorize o português**. Evite introduzir inglês por hábito.

Exceções aceitáveis:

- nomes já definidos por bibliotecas, frameworks, APIs, protocolos ou serviços externos;
- identificadores técnicos cujo nome em inglês seja exigido por uma interface externa;
- termos técnicos universalmente estabelecidos quando traduzi-los prejudicar clareza ou compatibilidade;
- nomes já existentes no código, que não devem ser renomeados apenas por preferência linguística.

Não renomeie componentes existentes em inglês sem uma decisão explícita de refatoração.

Quando houver uma escolha livre para uma nova implementação, prefira nomes em português que expressem claramente o domínio.

**Toda subida ao GitHub deve possuir mensagem, título e resumo em português.**

---

## 15. Regra final para agentes

A implementação real e a documentação atual do repositório têm precedência sobre suposições.

Quando houver conflito entre:

- código;
- `AGENTS.md`;
- `documentacao_tecnica.md`;
- ADRs;
- histórico de conversa;

investigue o estado atual do código, identifique a inconsistência e trate-a explicitamente.

**Nunca presuma que um detalhe antigo continua verdadeiro só porque aparece em uma instrução anterior.**
