# diario_processor

Pipeline determinístico para extração, normalização e estruturação de conhecimento institucional a partir do Diário Oficial Eletrônico do Município de Teresópolis/RJ.

## Visão geral

O `diario_processor` automatiza o processamento de publicações oficiais, transformando documentos em PDF em dados estruturados persistidos em PostgreSQL.

O projeto foi desenvolvido com foco em determinismo, rastreabilidade e qualidade dos dados, evitando heurísticas probabilísticas e privilegiando regras explícitas de extração e validação.

O pipeline realiza:

- extração e segmentação de documentos;
- classificação documental;
- extração de metadados;
- geração de eventos institucionais;
- normalização de entidades;
- persistência em banco de dados;
- auditorias de qualidade;
- testes automatizados de regressão.

## Arquitetura

                          Diário Oficial (PDF)
                                   │
                                   ▼
                        Extração de Texto (OCR/PDF)
                                   │
                                   ▼
                           Segmentação em Blocos
                                   │
                                   ▼
                               Parser
      ┌────────────────────────────────────────────────────┐
      │ Tipo │ Processo │ Contrato │ Valores │ Objeto ... │
      └────────────────────────────────────────────────────┘
                                   │
                                   ▼
                              Processor
                                   │
                                   ▼
                        Geração de Eventos
                                   │
                                   ▼
                      Normalização de Entidades
                                   │
                                   ▼
                            PostgreSQL
        ┌──────────────────────────────────────────────┐
        │ publicacoes │ eventos │ entidades │ órgãos │
        └──────────────────────────────────────────────┘
                                   │
                                   ▼
                     Auditorias + Regras de Qualidade
                                   │
                                   ▼
                       Testes + Corpus de Regressão