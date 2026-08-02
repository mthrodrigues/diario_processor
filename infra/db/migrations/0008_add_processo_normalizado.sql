ALTER TABLE {schema}.publicacoes
ADD COLUMN IF NOT EXISTS processo_normalizado TEXT;

CREATE INDEX IF NOT EXISTS idx_diario_publicacoes_processo_normalizado
ON {schema}.publicacoes (processo_normalizado);
