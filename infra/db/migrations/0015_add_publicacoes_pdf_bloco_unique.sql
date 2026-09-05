DO $$
DECLARE
    definicao_constraint TEXT;
BEGIN
    SELECT pg_get_constraintdef(constraint_oid.oid)
    INTO definicao_constraint
    FROM pg_constraint AS constraint_oid
    WHERE constraint_oid.conrelid = '{schema}.publicacoes'::regclass
      AND constraint_oid.conname = 'uq_publicacoes_pdf_bloco';

    IF definicao_constraint IS NULL THEN
        ALTER TABLE {schema}.publicacoes
        ADD CONSTRAINT uq_publicacoes_pdf_bloco
        UNIQUE (pdf_hash, numero_bloco);
    ELSIF definicao_constraint <> 'UNIQUE (pdf_hash, numero_bloco)' THEN
        RAISE EXCEPTION
            'Constraint uq_publicacoes_pdf_bloco possui definicao incompativel: %',
            definicao_constraint;
    END IF;
END $$;