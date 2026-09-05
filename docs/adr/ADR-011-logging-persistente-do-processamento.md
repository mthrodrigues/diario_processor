# ADR 011 — Logging Persistente do Processamento

Data: 2026-09-05

Status: implementada

## Contexto
O `main.py` já produzia saída operacional via `print()` e, em caso de erro, `traceback.print_exc()` no console. Essa saída não era persistida em nenhum arquivo: ao encerrar o processo (execução automatizada, terminal fechado, etc.), a trilha de diagnóstico se perdia. Não havia identificador de execução, nem indicação de em qual etapa do processamento (extração de texto, segmentação, persistência etc.) uma falha havia ocorrido. Além disso, o `except` principal do loop de PDFs podia ser alcançado antes de `diario_id` estar atribuído, o que arriscava mascarar a exceção original com um `NameError` ao montar a mensagem de erro. Havia também dois pontos de falha silenciosa: o enriquecimento contextual (`except Exception: pass`) e a publicação do evento canônico na outbox, cujos erros eram apenas impressos no console, sem traceback persistido.

## Decisão
Introduzir um módulo dedicado, `logging_setup.py`, responsável exclusivamente pela configuração do logging persistente, mantendo `config.py` restrito à configuração de aplicação. A solução usa somente a biblioteca padrão (`logging`, `logging.handlers.RotatingFileHandler`).

Elementos da decisão:

- Logger central nomeado `diario_processor`, configurado por `setup_logging()`, com um `RotatingFileHandler` apontando para `logs/diario_processor.log` (5MB por arquivo, 5 backups) e nível configurável via parâmetro ou variável de ambiente `LOG_LEVEL`.
- Um `run_id` simples e legível (`YYYYMMDD-HHMMSS`), gerado uma única vez no início de `main.run()` e reutilizado em todas as mensagens daquela execução.
- Regra de volume: **sucesso gera uma única linha** por Diário processado; **erro gera um registro com contexto completo** (`run_id`, `diario_id`, `arquivo`, `bloco`, `etapa`) e traceback.
- `diario_id` e o número do bloco (`i`) passam a ser inicializados como `None` no início de cada iteração do loop de PDFs, para que uma falha ocorrida antes de `extrair_diario_id()` não gere uma segunda exceção ao montar a mensagem de erro, preservando a exceção original.
- Uma variável simples (`etapa_atual`) é atualizada ao longo do fluxo já existente em `main.py` (sem reestruturar o pipeline em classes ou serviços), permitindo identificar a etapa da falha entre um conjunto pequeno e significativo de etapas: `extrair_diario_id`, `extrair_texto`, `extrair_data_publicacao`, `segmentar_publicacoes`, `extrair_metadados_bloco`, `enriquecimento_contextual`, `extrair_eventos`, `salvar_evento`, `publicar_evento_canonico`, `salvar_publicacao`, `salvar_pot`, `commit`.
- As falhas até então silenciosas do enriquecimento contextual e da publicação do evento canônico passam a ser registradas no log persistente (contexto + traceback), sem alterar a política funcional existente: nenhuma das duas passa a interromper o processamento do Diário.
- Erros na consolidação de processos e de contratos são registrados antes do `rollback()`/`raise`, pois representam falha da execução global, e não de um Diário isolado.
- O console permanece com a saída operacional enxuta já existente; o arquivo de log é complementar e não reproduz SQL, parâmetros, eventos completos, metadados completos ou texto de blocos.

## Alternativas consideradas
- Manter apenas `print`/`traceback.print_exc()` no console. Rejeitado por não deixar trilha persistente.
- Configurar o logging dentro de `config.py`. Rejeitado por decisão explícita de manter `config.py` restrito à configuração de aplicação.
- Um arquivo de log por execução. Rejeitado como primeira iteração: o processamento é sequencial (sem concorrência), e um arquivo único com rotação (`RotatingFileHandler`) já resolve o volume sem multiplicar arquivos.

## Consequências
- Positivo: cada execução deixa uma trilha mínima e útil (sucesso ou erro) sem poluir o console; falhas antes de `diario_id` deixam de mascarar a exceção original; os dois pontos de falha silenciosa passam a deixar evidência.
- Positivo: a solução usa apenas biblioteca padrão e não introduz camadas novas (sem classes de serviço, sem fila, sem infraestrutura externa).
- Negativo/limitação: a auditoria de aplicações bem-sucedidas da Regra 001 (EC), feita por um logger isolado (`diario_processor.enrichment`, ADR-0001), permanece sem handler configurado e continua sem efeito observável — este ADR cobre apenas as falhas da EC, não o registro de auditoria das aplicações bem-sucedidas.
- Negativo/limitação: não há rotação por data nem envio a um sistema externo de observabilidade; é uma solução mínima, pensada para viabilizar diagnóstico local antes de qualquer evolução futura.

## Implementação
- Módulo: `logging_setup.py` (`setup_logging()`, `get_logger()`, `novo_run_id()`, `log_sucesso()`, `log_erro()`).
- Integração: `main.py` chama `setup_logging()` e `novo_run_id()` no início de `run()`, e usa `log_sucesso()`/`log_erro()` nos pontos descritos acima.
- Testes: `tests/test_logging_setup.py` cobre criação do arquivo, nível configurado, mensagem de sucesso em linha única, mensagem de erro com contexto e traceback, o caso de erro antes de `diario_id` estar disponível, e os erros não fatais (enriquecimento contextual e publicação de evento canônico).

## Backlog
- Conectar (ou substituir) o logger de auditoria `diario_processor.enrichment` da EC a um handler persistente, para que aplicações bem-sucedidas da Regra 001 também deixem trilha auditável.
- Avaliar, no futuro, uso da nova infraestrutura de logging para investigar erros históricos de reprocessamento já conhecidos, sem que isso faça parte do escopo desta ADR.
