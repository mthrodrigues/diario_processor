CREATE TABLE IF NOT EXISTS {schema}.publicacoes (
    id BIGSERIAL PRIMARY KEY,
    diario_id INTEGER,
    numero_bloco INTEGER,
    arquivo_path TEXT,
    texto_bloco TEXT,
    tipo TEXT,
    processo TEXT,
    contrato TEXT,
    contratante TEXT,
    fornecedor TEXT,
    fornecedor_normalizado TEXT,
    contratante_normalizado TEXT,
    cnpj TEXT,
    valores JSONB,
    valor_principal NUMERIC(18, 2),
    vigencia TEXT,
    objeto TEXT,
    data_processamento TIMESTAMPTZ,
    processo_normalizado TEXT
);

CREATE INDEX IF NOT EXISTS idx_diario_publicacoes_arquivo_path
ON {schema}.publicacoes (arquivo_path);

CREATE INDEX IF NOT EXISTS idx_diario_publicacoes_fornecedor_normalizado
ON {schema}.publicacoes (fornecedor_normalizado);

CREATE INDEX IF NOT EXISTS idx_diario_publicacoes_contratante_normalizado
ON {schema}.publicacoes (contratante_normalizado);

CREATE INDEX IF NOT EXISTS idx_diario_publicacoes_processo_normalizado
ON {schema}.publicacoes (processo_normalizado);

CREATE INDEX IF NOT EXISTS idx_diario_publicacoes_valor_principal
ON {schema}.publicacoes (valor_principal);

CREATE INDEX IF NOT EXISTS idx_diario_publicacoes_tipo
ON {schema}.publicacoes (tipo);

CREATE INDEX IF NOT EXISTS idx_diario_publicacoes_data_processamento
ON {schema}.publicacoes (data_processamento);
