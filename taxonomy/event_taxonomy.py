import ecosystem_imports  # noqa: F401

from institutional_contracts.ontology.event_types import (
    APPOINTMENT,
    BIDDING,
    BIDDING_WAIVER,
    CONTRACT_AMENDMENT,
    DESIGNATION,
    EXONERATION,
    PUBLIC_CONTRACT,
)
from institutional_contracts.ontology.relationship_types import (
    APPOINTED,
    AUTHORIZED,
    CONTRACTED,
    DESIGNATED_TO,
    DISMISSED,
    PARTICIPATED_IN_CONTRACT,
)


EVENT_RELATION_TYPES = {
    APPOINTMENT: APPOINTED,
    EXONERATION: DISMISSED,
    DESIGNATION: DESIGNATED_TO,
    PUBLIC_CONTRACT: CONTRACTED,
    CONTRACT_AMENDMENT: CONTRACTED,
    BIDDING_WAIVER: AUTHORIZED,
    BIDDING: PARTICIPATED_IN_CONTRACT,

    # Legacy input compatibility. Producers should emit canonical values.
    "nomeacao": APPOINTED,
    "exoneracao": DISMISSED,
    "designacao": DESIGNATED_TO,
    "contratacao": CONTRACTED,
    "aditivo": CONTRACTED,
    "dispensa": AUTHORIZED,
    "licitacao": PARTICIPATED_IN_CONTRACT,
}
