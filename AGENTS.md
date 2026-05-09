# Diário Processor — AGENT INSTRUCTIONS

## Objetivo do projeto

O projeto "diario_processor" é um pipeline de inteligência documental focado em Diários Oficiais municipais.

A arquitetura foi desenhada para:

1. Ler PDFs de Diários Oficiais já baixados por outro robô
2. Extrair o texto completo
3. Segmentar o Diário em publicações/blocos independentes
4. Extrair metadados estruturados
5. Persistir os dados em SQLite
6. Futuramente integrar:
   - APIs de Transparência
   - IA/NLP
   - embeddings
   - dashboards
   - monitoramento automatizado

---

# Arquitetura atual

O pipeline atual funciona assim:

PDF
↓
Texto bruto
↓
Segmentação em blocos/publicações
↓
Extração contextual
↓
Persistência estruturada

Cada bloco/publicação gera um registro independente no banco.

---

# Filosofia do projeto

## MUITO IMPORTANTE

O Diário Oficial NÃO deve ser tratado como:
- um único documento lógico

Ele deve ser tratado como:
- um container de múltiplas publicações independentes

Por isso:
- a segmentação em blocos é obrigatória
- extrações devem ocorrer por bloco
- nunca por PDF inteiro

---

# Estrutura atual de dados

Tabela principal:
publicacoes

Campos atuais:
- diario_id
- numero_bloco
- arquivo_path
- texto_bloco
- tipo
- processo
- contrato
- contratante
- fornecedor
- cnpj
- valores
- data_processamento

---

# Regras arquiteturais obrigatórias

## 1. Nunca remover texto bruto

O texto original do bloco deve SEMPRE ser preservado.

O sistema usa:
- dados estruturados
- + texto bruto

A IA futura utilizará ambos.

---

## 2. Priorizar precisão sobre cobertura

Evitar regex agressivas.

Falsos positivos são piores que ausência de extração.

Exemplo:
- melhor perder um fornecedor
- do que relacionar fornecedor errado ao contrato errado

---

## 3. Extração deve ser contextual

Evitar regex genéricas como:
- ".*LTDA"
- ".*SA"

Priorizar contexto documental:
- CONTRATADA:
- CONTRATANTE:
- FORNECEDOR:
- EMPRESA:

---

## 4. Não misturar blocos/publicações

Cada bloco representa:
- uma entidade documental independente

Nunca relacionar:
- processo
- fornecedor
- contrato

entre blocos diferentes.

---

## 5. Não remover incrementalidade

O sistema possui processamento incremental.

A função ja_processado() é crítica.

Evitar reprocessamento desnecessário.

---

# Objetivos futuros do sistema

## Curto prazo
- melhorar parser documental
- extrair vigência
- extrair valor principal
- extrair modalidade
- extrair aditivos
- normalizar fornecedores

## Médio prazo
- integração com API da Transparência
- enriquecimento de fornecedores
- cruzamento contratual

## Longo prazo
- IA/NLP
- embeddings
- busca semântica
- alertas automáticos
- monitoramento recorrente
- detecção de padrões

---

# Diretrizes para o Codex

## Antes de alterar código:
- entender o fluxo completo
- verificar impacto arquitetural
- preservar segmentação por bloco

## Ao criar regex:
- priorizar contexto
- minimizar falso positivo
- evitar capturas excessivas

## Ao alterar banco:
- manter compatibilidade com pipeline
- evitar perda de dados
- considerar crescimento futuro

## Ao criar novas extrações:
Preferir:
- contexto semântico
- labels documentais
- padrões administrativos reais

Evitar:
- regex excessivamente amplas

---

# Objetivo principal do sistema

Construir uma base de inteligência documental pública capaz de:
- interpretar Diários Oficiais
- estruturar informações contratuais
- permitir cruzamento com transparência
- servir de base para IA futura

---

# Status atual

O sistema já realiza:
- leitura de PDFs
- extração de texto
- segmentação documental
- extração de:
  - processo
  - contrato
  - contratante
  - fornecedor
  - CNPJ
  - valores
- persistência estruturada em SQLite

---

# Observações importantes

- Muitos Diários NÃO possuem CNPJ
- O identificador principal atual tende a ser:
  - fornecedor + processo + contrato

- A IA futura NÃO substituirá dados estruturados.
- O sistema deve continuar híbrido:
  - RAW + STRUCTURED

---

# Regra final

A qualidade semântica dos dados é mais importante do que quantidade de campos extraídos.

# Diretriz estratégica atual

O sistema deve priorizar inteligência contratual pública.

Embora todos os blocos/publicações continuem sendo preservados e armazenados, o enriquecimento semântico avançado deve priorizar:

- contratos
- extratos contratuais

Motivo:
Esses tipos possuem maior densidade semântica e maior valor analítico para:
- monitoramento público
- recorrência contratual
- integração com transparência
- IA futura

Documentos de baixa relevância analítica:
- avisos genéricos
- portarias
- publicações administrativas sem relação contratual

podem continuar sendo armazenados, porém com menor prioridade de enriquecimento.