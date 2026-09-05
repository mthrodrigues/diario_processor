ALTER TABLE {schema}.publicacoes
ADD COLUMN IF NOT EXISTS parser_version TEXT;