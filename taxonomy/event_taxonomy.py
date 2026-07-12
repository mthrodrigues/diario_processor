# =====================================================
# TIPOS DE EVENTOS
# =====================================================

NOMEACAO = "NOMEACAO"

EXONERACAO = "EXONERACAO"

DESIGNACAO = "DESIGNACAO"

CONTRATACAO = "CONTRATACAO"

DESIGNACAO_FISCAL = "DESIGNACAO_FISCAL"

ADITIVO = "ADITIVO"

DISPENSA = "DISPENSA"

LICITACAO = "LICITACAO"


# =====================================================
# TIPOS DE RELACOES
# =====================================================

NOMEADO_EM = "NOMEADO_EM"

EXONERADO_DE = "EXONERADO_DE"

DESIGNADO_PARA = "DESIGNADO_PARA"

CONTRATOU = "CONTRATOU"

AUTORIZOU = "AUTORIZOU"

PARTICIPOU_LICITACAO = "PARTICIPOU_LICITACAO"


# =====================================================
# MAPA EVENTO -> RELACAO
# =====================================================

EVENT_RELATION_TYPES = {

    NOMEACAO:
        NOMEADO_EM,

    EXONERACAO:
        EXONERADO_DE,

    DESIGNACAO:
        DESIGNADO_PARA,

    CONTRATACAO:
        CONTRATOU,

    ADITIVO:
        CONTRATOU,

    DISPENSA:
        AUTORIZOU,

    LICITACAO:
        PARTICIPOU_LICITACAO,

    # =================================================
    # COMPATIBILIDADE LEGADA
    # =================================================

    "nomeacao":
        NOMEADO_EM,

    "exoneracao":
        EXONERADO_DE,

    "designacao":
        DESIGNADO_PARA,

    "contratacao":
        CONTRATOU,

    "aditivo":
        CONTRATOU,

    "dispensa":
        AUTORIZOU,

    "licitacao":
        PARTICIPOU_LICITACAO,
}