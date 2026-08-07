# Contexto

Os catálogos consolidados precisam ser atualizados repetidamente sem duplicar ou corromper os registros já existentes.

# Problema

Processamentos repetidos poderiam gerar inconsistência ou registros duplicados se a consolidação não fosse tratada como operação segura.

# Decisão

Os consolidadores foram concebidos como operações idempotentes.

# Consequências

A execução repetida do fluxo não altera indevidamente o estado consolidado, preservando estabilidade e permitindo reprocessamentos controlados.
