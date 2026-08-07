from pathlib import Path

corpus = Path('tests/corpus/textos/q003_apostilamento.txt').read_text(encoding='utf-8')
provided = '''termo aditivo ao Contrato n.º 008.009.2025, a prorrogação de prazo por mais 12 (doze)
meses a partir da data de vencimento em (25/06/2026), com fundamento no art. 107 da
Lei 14.133/21.. Valor R$: 629.332,62 (seiscentos e vinte e nove mil, trezentos e trinta e
dois reais e sessenta e dois centavos). Processo n° 1.438/2025.
PELO CONTRATANTE: CARLA RABELLO FERREIRA.
PELA CONTRATADA: RENATA NUNES FERREIRA.
'''

# normalize line endings
c = corpus.replace('\r\n','\n')
p = provided.replace('\r\n','\n')

# quick equality
print('Equal?', c == p)

# find first difference
minlen = min(len(c), len(p))
idx = None
for i in range(minlen):
    if c[i] != p[i]:
        idx = i
        break
if idx is None and len(c) != len(p):
    idx = minlen

if idx is None:
    print('No difference found')
else:
    print('First difference at index', idx)
    start = max(0, idx-80)
    end = min(max(len(c),len(p)), idx+80)
    print('\n--- Corpus context (around difference) ---')
    print(c[start:end])
    print('\n--- Provided context (around difference) ---')
    print(p[start:end])
