# Changelog

Todas as mudanças relevantes deste projeto serão documentadas neste arquivo.

O projeto segue o princípio de versionamento semântico.

---

## [1.0.0]

### Adicionado

- Pipeline completo de processamento dos Diários Oficiais.
- Parser determinístico.
- Classificação documental.
- Extração de contratos, processos, valores e objetos.
- Geração de eventos institucionais.
- Normalização de entidades.
- Persistência em PostgreSQL.
- Suite automatizada de testes.
- Corpus de regressão.
- Ferramentas de criação de casos de teste.
- Matriz de cobertura.
- Especificação funcional do parser.

### Corrigido

- Segmentação de contratos.
- Extração de Contrato de Locação.
- Reutilização de metadados em DESIGNACAO_FISCAL.
- Eliminação da Q005 (7 → 0).