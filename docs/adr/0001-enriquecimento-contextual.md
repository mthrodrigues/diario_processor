# ADR 0001 — Camada de Enriquecimento Contextual (EC)

Data: 2026-08-07

Status: proposta -> implementada (Regra 001)

## Contexto
Durante auditoria foi identificado que, em casos raros, a segmentação quebra um ato administrativo em dois blocos consecutivos. O bloco anterior contém o rótulo institucional "Contratante: O Município..." enquanto o bloco seguinte contém apenas o signatário "PELO CONTRATANTE: Nome". Como a extração de campos é feita por bloco, o contratante institucional acaba não sendo associado ao bloco persistido.

## Decisão
Inserir uma camada de Enriquecimento Contextual (EC) entre o parser (extração por bloco) e a etapa de normalização/persistência. A primeira iteração implementa apenas uma regra determinística (Regra 001) que herda o contratante institucional do bloco anterior para o bloco atual quando:

- existe bloco anterior e os blocos são consecutivos (n e n+1);
- o bloco anterior contém rótulo institucional "Contratante:" (e não "PELO CONTRATANTE");
- o bloco atual não contém rótulo institucional;
- os blocos pertencem ao mesmo ato administrativo por evidência determinística: mesmo contrato OU mesmo processo.

A EC não altera texto_bloco nem segmentação. Toda herança é registrada em log estrutural para auditoria.

## Alternativas consideradas
- Alterar segmentação para evitar split (corrigir na origem). Rejeitado como primeira ação por maior risco (mudança de unidade de persistência, impacto em números de bloco, necessidade de migração de dados).
- Corrigir no consolidador/post-persistência. Considerado, mas EC fornece correção imediata antes da persistência e com menor impacto em integrações.

## Consequências
- Positivo: resolve o caso identificado sem alterar segmentação nem texto; permite backfill e auditoria.
- Negativo: exige cuidado na definição da regra para evitar falsos positivos; implementada de forma conservadora (determinística).

## Future work
- Expandir EC para outras regras de herança contextual (e.g., fornecedor, processo quando faltante) com critérios configuráveis e tabela de auditoria persistente.
- Avaliar alteração da segmentação a médio prazo, com plano de migração e reprocessamento.
- Conectar o logger de auditoria `diario_processor.enrichment` a um handler persistente (ou migrar a auditoria de aplicações bem-sucedidas para o logger central `diario_processor` introduzido pela ADR-011), hoje sem efeito observável.

## Implementação
- Módulo: contextual_enrichment.py
- Integração: invocado em main.py imediatamente após extrair_metadados_bloco e antes de salvar_publicacao.
- Logging: a auditoria da aplicação da regra (JSON, linha por evento) é emitida via `logging.getLogger('diario_processor.enrichment')`. Este logger é isolado e, até o momento, não possui handler configurado em nenhum ponto do código — ou seja, essa chamada não produz saída persistida. Desde a ADR-011 (`docs/adr/ADR-011-logging-persistente-do-processamento.md`), falhas (exceções) na aplicação da EC são registradas no logger central `diario_processor`, com contexto (`diario_id`, `arquivo`, `bloco`, `etapa=enriquecimento_contextual`) e traceback, sem interromper o processamento do Diário. O registro de auditoria das aplicações bem-sucedidas da regra continua sendo um ponto em aberto (ver Future work).

## Conclusão da Regra 001
- A Regra 001 foi definida e implementada utilizando apenas os critérios determinísticos A, B e C:
  - A) igualdade de número de contrato (pós-normalização);
  - B) igualdade de número de processo (pós-normalização);
  - C) correspondência textual direta: o número de contrato extraído em um bloco aparece, após a mesma normalização do parser, no texto integral do outro bloco.
- A decisão deliberada foi não incluir heurísticas, pontuações ou critérios baseados em layout textual. A regra é totalmente determinística e reutiliza as rotinas de normalização existentes no parser para contratos e processos.

## Política de substituição de metadados
- A EC não é apenas uma camada de preenchimento de campos vazios; é uma camada de enriquecimento de metadados derivados.
- Quando todas as pré-condições forem satisfeitas e pelo menos um dos critérios A, B ou C for verdadeiro, a EC está autorizada a substituir o valor existente de `contratante` no bloco atual pelo contratante institucional herdado do bloco anterior, mesmo que o campo já contenha o nome do signatário.
- Toda substituição é considerada uma correção determinística do metadado com base em evidência documental superior.

## Auditoria obrigatória
- Toda substituição gerada pela EC deve registrar, no log de auditoria, pelo menos os seguintes campos: valor anterior (`previous_contratante`), valor novo (`inherited_contratante`), critério aplicado (A, B ou C), PDF (`pdf_path`), número dos blocos (`prev_numero_bloco`, `curr_numero_bloco`), contrato e processo (`contrato_prev`, `contrato_curr`, `processo_prev`, `processo_curr`) e timestamp (UTC timezone-aware).

## Caso conhecido sem cobertura
- Existe um caso identificado na auditoria (Caso 5: C:\automacoes\diario_bot\pdfs\2026\08\diario_3417.pdf) que, segundo as evidências textuais extraídas, NÃO é coberto pelos critérios A, B ou C. Em particular, o número do contrato do bloco anterior (002.031.2026) não aparece no texto integral do bloco atual e não há igualdade determinística de contrato ou processo entre os blocos.
- Conclusão: este caso não pode ser resolvido pela Regra 001 sem introduzir inferência contextual adicional além das evidências documentais presentes nos blocos. Portanto, não será incluído nesta implementação.

## Backlog
- Criar tarefa separada para investigar um mecanismo de "continuidade contextual entre blocos" (investigação arquitetural distinta da Regra 001). Esta tarefa deverá avaliar alternativas como: detecção de continuidade textual avançada, indexação por tokens e símbolos, e/ou revisão controlada da segmentação. A tarefa será tratada como backlog separado e só será implementada após nova investigação e aprovação.

