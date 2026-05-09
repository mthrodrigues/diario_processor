TIPOS_PRIORITARIOS = [
    "contrato",
    "extrato",
]

RELEVANCIA_ALTA = "alta"
RELEVANCIA_MEDIA = "media"
RELEVANCIA_BAIXA = "baixa"

RELEVANCIA_POR_TIPO = {
    "contrato": RELEVANCIA_ALTA,
    "extrato": RELEVANCIA_ALTA,
    "homologacao": RELEVANCIA_MEDIA,
    "adjudicacao": RELEVANCIA_MEDIA,
    "aditivo": RELEVANCIA_MEDIA,
    "licitacao": RELEVANCIA_MEDIA,
    "dispensa": RELEVANCIA_MEDIA,
    "inexigibilidade": RELEVANCIA_MEDIA,
    "aviso": RELEVANCIA_BAIXA,
    "portaria": RELEVANCIA_BAIXA,
    "termo": RELEVANCIA_BAIXA,
    "edital": RELEVANCIA_BAIXA,
    "errata": RELEVANCIA_BAIXA,
    "empenho": RELEVANCIA_BAIXA,
    "outro": RELEVANCIA_BAIXA,
}


def classificar_relevancia(tipo):
    return RELEVANCIA_POR_TIPO.get(tipo, RELEVANCIA_BAIXA)


def eh_tipo_prioritario(tipo):
    return tipo in TIPOS_PRIORITARIOS


def deve_enriquecer_contratual(tipo):
    return eh_tipo_prioritario(tipo)
