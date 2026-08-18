"""Shared IATI terminology used in tool descriptions and plugin instructions."""

IATI_GLOSSARY = {
    "IATI activity": (
        "A development or cooperation intervention published under the IATI standard; "
        "it can represent a project, a programme or another unit of work."
    ),
    "IATI identifier": (
        "Globally unique code identifying an IATI activity, also used to link it "
        "to its transactions and other information."
    ),
    "reporting organisation": (
        "Organisation responsible for publishing and maintaining an activity's data; "
        "not necessarily the one funding or implementing the project."
    ),
    "activity status": (
        "Stage of an activity within its lifecycle, such as pipeline, implementation, "
        "finalisation, closed, cancelled or suspended."
    ),
    "activity date": (
        "Planned or actual start or end date of an activity. "
        "Its meaning depends on the declared date type."
    ),
    "transaction": (
        "Financial operation associated with an IATI activity, identified by "
        "its type, date, value and currency."
    ),
    "transaction type": (
        "Code indicating the nature of a financial operation, such as commitment, "
        "disbursement, expenditure or incoming funds."
    ),
    "transaction value": (
        "Amount of an individual transaction, expressed in the currency stated on the "
        "value or, if unspecified, in the activity's default currency."
    ),
    "commitment": (
        "Financial obligation undertaken to provide funds to an activity; "
        "it does not necessarily represent a payment already made."
    ),
    "disbursement": (
        "Transfer of funds from a provider organisation to a receiver "
        "organisation to finance an activity."
    ),
    "expenditure": (
        "Use of funds to purchase goods or services related to an activity; "
        "not a synonym of disbursement."
    ),
    "budget": (
        "Amount planned for an activity over a given period; it does not "
        "necessarily represent funds actually disbursed or spent."
    ),
    "planned disbursement": (
        "Amount expected to be disbursed during a future period; different "
        "from a disbursement transaction that already took place."
    ),
    "default currency": (
        "Currency declared for an activity and used whenever a financial value "
        "does not explicitly specify another currency."
    ),
    "participating organisation": (
        "Organisation linked to an activity with a given role, such as funding, "
        "accountability, extension or implementation."
    ),
    "organisation role": (
        "Code describing the function of a participating organisation within "
        "an activity, such as funding, accountable, extending or implementing."
    ),
    "provider organisation": (
        "Organisation providing the funds associated with a transaction "
        "or a planned disbursement."
    ),
    "receiver organisation": (
        "Organisation receiving the funds associated with a transaction "
        "or a planned disbursement."
    ),
    "sector": (
        "Thematic or economic area an activity contributes to, indicated by "
        "a code, a vocabulary and, where applicable, a percentage."
    ),
    "recipient country or region": (
        "Country or region that receives the intended benefits of an activity. May "
        "include a percentage when the activity is split across several territories."
    ),
    "vocabulary": (
        "Classification system used to interpret an IATI code, "
        "such as the DAC vocabulary used to classify sectors."
    ),
    "codelist": (
        "Catalogue mapping the codes used in IATI to their allowed meanings."
    ),
    "narrative": (
        "Human-readable text attached to an IATI element, which may be "
        "published in one or more languages."
    ),
}


def _capitalize(term: str) -> str:
    """Capitalize only the first letter, preserving acronyms like IATI."""
    return term[0].upper() + term[1:]


def glossary_text(*terms: str) -> str:
    """Return selected glossary entries as a compact, human-readable string."""
    unknown_terms = [term for term in terms if term not in IATI_GLOSSARY]
    if unknown_terms:
        raise KeyError(
            f"Unknown IATI terms: {', '.join(unknown_terms)}"
        )

    return "\n".join(
        f"- {_capitalize(term)}: {IATI_GLOSSARY[term]}"
        for term in terms
    )


def full_glossary_text() -> str:
    """Return all glossary entries for the MCP plugin instructions."""
    return glossary_text(*IATI_GLOSSARY)
