ALTER TABLE diario.publicacoes
ADD COLUMN IF NOT EXISTS data_publicacao DATE;

ALTER TABLE diario.eventos
ADD COLUMN IF NOT EXISTS data_publicacao DATE;

-- =========================================================
-- ÍNDICES TEMPORAIS
-- =========================================================

CREATE INDEX IF NOT EXISTS idx_publicacoes_data
ON diario.publicacoes(data_publicacao);

CREATE INDEX IF NOT EXISTS idx_eventos_data
ON diario.eventos(data_publicacao);