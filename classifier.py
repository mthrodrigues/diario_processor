TIPOS_ENRIQUECIMENTO_CONTRATUAL = {
    "contrato",
    "extrato",
    "aditivo",
    "apostilamento",
}

def deve_enriquecer_contratual(tipo):
    return tipo in TIPOS_ENRIQUECIMENTO_CONTRATUAL
