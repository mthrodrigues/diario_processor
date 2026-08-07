from parser import extrair_contratante

p = open(r"tests/corpus/textos/q003_apostilamento.txt","r",encoding="utf-8").read()
print("==== BLOCO (orig) ====\n")
print(p)
print("\n==== FIM BLOCO ====\n")

res = extrair_contratante(p)
print("\n==== extrair_contratante RETURNED ====")
print(repr(res))
