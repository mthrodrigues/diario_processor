# Matriz de Cobertura do Parser

## Classificação documental

| Tipo documental | Cobertura | Caso de teste |
|-----------------|-----------|---------------|
| Contrato | ✅ | extrato_contrato_anon |
| Apostilamento | ✅ | q003_apostilamento |
| Aditivo | ❌ | |
| Corrigenda | ⚠️ | q003_corrigenda |
| Portaria | ❌ | |
| Edital | ❌ | |
| Aviso | ❌ | |
| Dispensa | ❌ | |
| Inexigibilidade | ❌ | |
| Homologação | ❌ | |
| Empenho | ❌ | |
| Licitação | ❌ | |
| Extrato | ✅ | extrato_contrato_anon |

---

## Extração

| Campo | Cobertura |
|--------|-----------|
| Processo | ✅ |
| Contrato | ✅ |
| Contratante | ✅ |
| Fornecedor | ✅ |
| CNPJ | ✅ |
| Valor | ✅ |
| Vigência | ⚠️ |
| Objeto | ✅ |

---

## Regras de qualidade

| Regra | Caso de regressão |
|--------|-------------------|
| Q001 | ❌ |
| Q002 | ❌ |
| Q003 | ✅ |
| Q005 | ❌ |
| Q006 | ❌ |
| Q007 | ❌ |