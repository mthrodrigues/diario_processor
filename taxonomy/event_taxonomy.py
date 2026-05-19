# =====================================================
# EVENT TYPES
# =====================================================

APPOINTMENT = "appointment"
BIDDING = "bidding"
BIDDING_WAIVER = "bidding_waiver"
CONTRACT_AMENDMENT = "contract_amendment"
DESIGNATION = "designation"
EXONERATION = "exoneration"
PUBLIC_CONTRACT = "public_contract"

# =====================================================
# RELATION TYPES
# =====================================================

APPOINTED = "appointed"
AUTHORIZED = "authorized"
CONTRACTED = "contracted"
DESIGNATED_TO = "designated_to"
DISMISSED = "dismissed"
PARTICIPATED_IN_CONTRACT = "participated_in_contract"

# =====================================================
# EVENT -> RELATION MAP
# =====================================================

EVENT_RELATION_TYPES = {
    APPOINTMENT: APPOINTED,
    EXONERATION: DISMISSED,
    DESIGNATION: DESIGNATED_TO,
    PUBLIC_CONTRACT: CONTRACTED,
    CONTRACT_AMENDMENT: CONTRACTED,
    BIDDING_WAIVER: AUTHORIZED,
    BIDDING: PARTICIPATED_IN_CONTRACT,

    # =================================================
    # LEGACY COMPATIBILITY
    # =================================================

    "nomeacao": APPOINTED,
    "exoneracao": DISMISSED,
    "designacao": DESIGNATED_TO,
    "contratacao": CONTRACTED,
    "aditivo": CONTRACTED,
    "dispensa": AUTHORIZED,
    "licitacao": PARTICIPATED_IN_CONTRACT,
}