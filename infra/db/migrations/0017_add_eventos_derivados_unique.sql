ALTER TABLE {schema}.evento_entidades
ADD CONSTRAINT uq_evento_entidade_papel
UNIQUE (evento_id, entidade_id, papel);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
                FROM pg_attribute
                WHERE attrelid = '{schema}.relacionamentos_entidades'::regclass
                    AND attname = 'evento_id'
                    AND NOT attisdropped
    ) THEN
        ALTER TABLE {schema}.relacionamentos_entidades
        ADD COLUMN evento_id BIGINT;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = '{schema}.relacionamentos_entidades'::regclass
          AND conname = 'fk_relacionamento_evento'
    ) THEN
        ALTER TABLE {schema}.relacionamentos_entidades
        DROP CONSTRAINT fk_relacionamento_evento;
    END IF;
END $$;

ALTER TABLE {schema}.relacionamentos_entidades
ADD CONSTRAINT fk_relacionamento_evento
FOREIGN KEY (evento_id)
REFERENCES {schema}.eventos(id)
ON DELETE CASCADE;

ALTER TABLE {schema}.relacionamentos_entidades
ADD CONSTRAINT uq_relacionamento_evento_entidades_tipo
UNIQUE (
    evento_id,
    entidade_origem_id,
    entidade_destino_id,
    tipo_relacao
);