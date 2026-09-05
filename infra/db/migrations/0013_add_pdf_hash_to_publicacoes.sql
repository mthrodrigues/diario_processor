ALTER TABLE {schema}.publicacoes
ADD COLUMN IF NOT EXISTS pdf_hash TEXT;