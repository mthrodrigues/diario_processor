CREATE TABLE IF NOT EXISTS {schema}.pot_beneficiarios (
    id BIGSERIAL PRIMARY KEY,
    publicacao_id BIGINT NOT NULL
        REFERENCES {schema}.publicacoes(id)
        ON DELETE CASCADE,

    numero INTEGER,
    beneficiario TEXT,
    unidade TEXT,
    horario_atuacao TEXT,
    area_aprendizado TEXT,
    data_inclusao DATE,
    data_desligamento DATE,
    substituicao TEXT,
    texto_bruto TEXT,

    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_diario_pot_beneficiarios_publicacao
ON {schema}.pot_beneficiarios (publicacao_id);

CREATE INDEX IF NOT EXISTS idx_diario_pot_beneficiarios_numero
ON {schema}.pot_beneficiarios (publicacao_id, numero);