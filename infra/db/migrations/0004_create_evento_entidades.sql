CREATE TABLE IF NOT EXISTS diario.evento_entidades (

    id BIGSERIAL PRIMARY KEY,

    evento_id BIGINT NOT NULL,

    entidade_id BIGINT NOT NULL,

    papel TEXT NOT NULL,

    criado_em TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_evento
        FOREIGN KEY (evento_id)
        REFERENCES diario.eventos(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_entidade
        FOREIGN KEY (entidade_id)
        REFERENCES diario.entidades(id)
        ON DELETE CASCADE
);

-- =========================================================
-- ÍNDICES
-- =========================================================

CREATE INDEX IF NOT EXISTS idx_evento_entidades_evento
ON diario.evento_entidades(evento_id);

CREATE INDEX IF NOT EXISTS idx_evento_entidades_entidade
ON diario.evento_entidades(entidade_id);

CREATE INDEX IF NOT EXISTS idx_evento_entidades_papel
ON diario.evento_entidades(papel);