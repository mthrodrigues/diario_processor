# Corpus de Validacao

Esta pasta guarda amostras pequenas e expectativas por bloco para regressao do parser.

Estrutura sugerida:

- `pdfs/`: PDFs reais ou anonimizados, quando for seguro versionar.
- `textos/`: textos extraidos e anonimizados para testes rapidos.
- `expected/`: JSON esperado por bloco.

Regra de uso:

- Preserve o texto bruto usado no teste.
- Adicione um JSON esperado para cada bloco relevante.
- Prefira exemplos reais anonimizados a casos artificiais.
- Inclua apenas campos semanticamente confiaveis.
