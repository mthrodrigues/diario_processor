ALTER TABLE {schema}.publicacoes
ADD COLUMN IF NOT EXISTS contrato_normalizado TEXT;

CREATE INDEX IF NOT EXISTS idx_diario_publicacoes_contrato_normalizado
ON {schema}.publicacoes (contrato_normalizado);
