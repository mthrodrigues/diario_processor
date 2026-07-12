1. Objetivo
O parser é responsável por transformar texto bruto do Diário Oficial em metadados estruturados e determinísticos.

Todas as regras devem ser explícitas, reproduzíveis e independentes de modelos probabilísticos.

2. Campos extraídos
Campo	Obrigatório	Origem
tipo	Sim	Parser
processo	Quando existir	Parser
contrato	Quando existir	Parser
contratante	Tipos contratuais	Parser
fornecedor	Tipos contratuais	Parser
CNPJ	Quando existir	Parser
valor	Quando existir	Parser
vigência	Quando existir	Parser
objeto	Quando existir	Parser

3. Tipos documentais

Começamos preenchendo apenas o que já existe.

Tipo	Suportado	Caso de teste
Contrato	✅	extrato_contrato_anon
Extrato	✅	extrato_contrato_anon
Apostilamento	✅	q003_apostilamento
Aditivo	✅	aditivo_001
Corrigenda	✅	q003_corrigenda
Portaria	✅	testes parser
Aviso	✅	
Edital	⚠️	
Dispensa	⚠️	
Inexigibilidade	⚠️	
Empenho	⚠️	

4. Eventos
Evento	Origem
CONTRATACAO	contrato/extrato
DESIGNACAO_FISCAL	portaria
NOMEACAO	portaria
EXONERACAO	portaria

5. Princípios

Aqui eu colocaria as regras arquiteturais que descobrimos durante a investigação.

Por exemplo:

Regra 1

Toda extração textual ocorre exclusivamente no parser.

Regra 2

events.py apenas interpreta metadados previamente extraídos.

Regra 3

Toda correção funcional deve possuir teste de regressão.

Regra 4

Toda melhoria deve ser validada por auditoria SQL.