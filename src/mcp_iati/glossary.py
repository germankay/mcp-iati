"""Shared IATI terminology used in tool descriptions and plugin instructions."""

IATI_GLOSSARY = {
    "actividad IATI": (
        "Intervención de cooperación o desarrollo publicada en el estándar IATI; "
        "puede representar un proyecto, programa u otra unidad de trabajo."
    ),
    "identificador IATI": (
        "Código global y único que identifica una actividad IATI y permite relacionarla "
        "con sus transacciones y demás datos."
    ),
    "organización reportante": (
        "Organización responsable de publicar y mantener los datos de la actividad; "
        "no necesariamente es quien financia o ejecuta el proyecto."
    ),
    "estado de actividad": (
        "Etapa del ciclo de vida de una actividad, por ejemplo planificación, ejecución o cierre."
    ),
    "transacción": (
        "Movimiento financiero asociado a una actividad IATI, clasificado por tipo, fecha, "
        "valor y moneda."
    ),
    "compromiso": (
        "Obligación financiera asumida por una organización para aportar fondos a una actividad."
    ),
    "desembolso": (
        "Fondos puestos a disposición de otra organización o transferidos para una actividad."
    ),
    "gasto": (
        "Fondos utilizados por la organización reportante o por otra organización en la actividad."
    ),
    "moneda predeterminada": (
        "Moneda declarada por la actividad y utilizada cuando un valor no especifica otra moneda."
    ),
    "organización participante": (
        "Organización vinculada a una actividad con un rol, como financiación, implementación o rendición."
    ),
    "sector": (
        "Área temática o económica a la que contribuye una actividad, clasificada mediante un código."
    ),
    "país o región receptora": (
        "Ubicación geográfica que recibe los beneficios previstos de una actividad."
    ),
}


def glossary_text(*terms: str) -> str:
    """Return selected glossary entries as a compact, human-readable string."""
    unknown_terms = [term for term in terms if term not in IATI_GLOSSARY]
    if unknown_terms:
        raise KeyError(f"Términos IATI desconocidos: {', '.join(unknown_terms)}")
    return "\n".join(f"- {term.title()}: {IATI_GLOSSARY[term]}" for term in terms)


def full_glossary_text() -> str:
    """Return all glossary entries for the MCP plugin instructions."""
    return glossary_text(*IATI_GLOSSARY)
