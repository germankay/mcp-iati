"""Shared IATI terminology used in tool descriptions and plugin instructions."""

IATI_GLOSSARY = {
    "actividad IATI": (
        "Intervención de cooperación o desarrollo publicada según el estándar IATI; "
        "puede representar un proyecto, programa u otra unidad de trabajo."
    ),
    "identificador IATI": (
        "Código global y único que identifica una actividad IATI y permite relacionarla "
        "con sus transacciones y demás información."
    ),
    "organización reportante": (
        "Organización responsable de publicar y mantener los datos de una actividad; "
        "no necesariamente es quien financia o implementa el proyecto."
    ),
    "estado de actividad": (
        "Situación de una actividad dentro de su ciclo de vida, como planificación, "
        "implementación, finalización, cierre, cancelación o suspensión."
    ),
    "fecha de actividad": (
        "Fecha planificada o real de inicio o finalización de una actividad. "
        "Su significado depende del tipo de fecha indicado."
    ),
    "transacción": (
        "Operación financiera asociada a una actividad IATI, identificada mediante "
        "su tipo, fecha, valor y moneda."
    ),
    "tipo de transacción": (
        "Código que indica la naturaleza de una operación financiera, como compromiso, "
        "desembolso, gasto o fondos recibidos."
    ),
    "valor de transacción": (
        "Importe de una transacción individual, expresado en la moneda indicada en el "
        "valor o, si no se especifica, en la moneda predeterminada de la actividad."
    ),
    "compromiso": (
        "Obligación financiera asumida para proporcionar fondos a una actividad; "
        "no representa necesariamente un pago ya realizado."
    ),
    "desembolso": (
        "Transferencia de fondos desde una organización proveedora hacia una "
        "organización receptora para financiar una actividad."
    ),
    "gasto": (
        "Uso de fondos para adquirir bienes o servicios relacionados con una actividad; "
        "no es sinónimo de desembolso."
    ),
    "presupuesto": (
        "Importe previsto para una actividad durante un período determinado; "
        "no representa necesariamente fondos efectivamente desembolsados o gastados."
    ),
    "desembolso planificado": (
        "Importe que se espera desembolsar durante un período futuro; se diferencia "
        "de una transacción de desembolso que ya fue realizada."
    ),
    "moneda predeterminada": (
        "Moneda declarada para una actividad y utilizada cuando un valor financiero "
        "no especifica explícitamente otra moneda."
    ),
    "organización participante": (
        "Organización vinculada a una actividad con un rol determinado, como financiación, "
        "rendición de cuentas, extensión o implementación."
    ),
    "rol de organización": (
        "Código que describe la función de una organización participante dentro de "
        "una actividad, como financiar, rendir cuentas, extender o implementar."
    ),
    "organización proveedora": (
        "Organización que proporciona los fondos asociados a una transacción "
        "o a un desembolso planificado."
    ),
    "organización receptora": (
        "Organización que recibe los fondos asociados a una transacción "
        "o a un desembolso planificado."
    ),
    "sector": (
        "Área temática o económica a la que contribuye una actividad, indicada mediante "
        "un código, un vocabulario y, cuando corresponde, un porcentaje."
    ),
    "país o región receptora": (
        "País o región que recibe los beneficios previstos de una actividad. Puede incluir "
        "un porcentaje cuando la actividad se distribuye entre varios territorios."
    ),
    "vocabulario": (
        "Sistema de clasificación utilizado para interpretar un código IATI, "
        "como el vocabulario DAC utilizado para clasificar sectores."
    ),
    "lista de códigos": (
        "Catálogo que relaciona los códigos utilizados en IATI con sus significados "
        "permitidos. También se conoce como codelist."
    ),
    "narrativa": (
        "Texto legible asociado a un elemento IATI, que puede publicarse en uno "
        "o varios idiomas."
    ),
}


def glossary_text(*terms: str) -> str:
    """Return selected glossary entries as a compact, human-readable string."""
    unknown_terms = [term for term in terms if term not in IATI_GLOSSARY]
    if unknown_terms:
        raise KeyError(
            f"Términos IATI desconocidos: {', '.join(unknown_terms)}"
        )

    return "\n".join(
        f"- {term.title()}: {IATI_GLOSSARY[term]}"
        for term in terms
    )


def full_glossary_text() -> str:
    """Return all glossary entries for the MCP plugin instructions."""
    return glossary_text(*IATI_GLOSSARY)
