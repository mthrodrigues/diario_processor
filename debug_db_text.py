import re
from parser import MARCADORES_FIM_CAMPO, _limpar_campo_documental, extrair_contratante

texto = '''termo aditivo ao Contrato n.º 008.009.2025, a prorrogação de prazo por mais 12 (doze)
meses a partir da data de vencimento em (25/06/2026), com fundamento no art. 107 da
Lei 14.133/21.. Valor R$: 629.332,62 (seiscentos e vinte e nove mil, trezentos e trinta e
dois reais e sessenta e dois centavos). Processo n° 1.438/2025.
PELO CONTRATANTE: CARLA RABELLO FERREIRA.
PELA CONTRATADA: RENATA NUNES FERREIRA.
'''

# rotulos used by extrair_contratante
rotulos = [r'CONTRATANTE', r'PERMITENTE', r'[ÓO]RG[ÃA]O\s*GERENCIADOR']
rotulos_regex = "|".join(rotulos)
marcadores_regex = "|".join(MARCADORES_FIM_CAMPO)

padrao = (
    rf'\b(?:{rotulos_regex})(?:\s*:\s*|\s*[-–—]\s*|(?:\r?\n)+\s*)'
    rf'(.+?)'
    rf'(?='
    rf'\s*[-–—]?\s*(?:{marcadores_regex})\s*:'
    rf'|\s+(?:VALOR(?:\s+(?:GLOBAL|TOTAL|ESTIMADO|CONTRATADO|DA\s+PROPOSTA|DO\s+CONTRATO))?\s*R\$|PROCESSO\s*N[°ºO\.]?)'
    rf'|$'
    rf')'
)

print('--- Running external match capture on provided texto_bloco ---')

matches = list(re.finditer(padrao, texto, flags=re.IGNORECASE | re.DOTALL))

if not matches:
    print('No matches found by re.finditer()')
else:
    for i, match in enumerate(matches, start=1):
        start_pos = match.start()
        end_pos = match.end()
        print(f'\nMatch {i}')
        print(f'Início: {start_pos}')
        print(f'Fim: {end_pos}')
        print('Trecho que casou:')
        print(match.group(0))
        print('\nGrupo capturado (match.group(1)):')
        print(match.group(1))
        candidato = _limpar_campo_documental(match.group(1))
        print('\nResultado após _limpar_campo_documental():')
        print(repr(candidato))
        if not candidato or len(candidato) < 3:
            print('\nDecisão: DESCARTADO (vazio ou <3 chars)')
        else:
            print('\nDecisão: ACEITO')

# Finally, call extrair_contratante on the same texto
print('\n--- extrair_contratante(texto) result ---')
print(repr(extrair_contratante(texto)))
