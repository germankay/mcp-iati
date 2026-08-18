"""Formatting and response helpers shared by IATI queries."""

from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any

from okfn_iati.enums import ActivityStatus, TransactionType

from mcp_server.results import text_result as _text_result


# Nota para la IA: la tabla renderizada ya se mostró en pantalla vía
# structuredContent; la copia en texto es para que analice los números reales.
ALREADY_TABLE = (
    "Al usuario ya se le mostró una tabla renderizada en pantalla con estos "
    "datos. Más abajo te adjuntamos los mismos datos en texto para que analices "
    "los números; no copies la tabla de vuelta en tu respuesta, interpretala."
)

# Guardrail para la IA: se appendea automáticamente a toda respuesta desde
# `text_result`. Evita que el modelo invente datos que no están en el XML y
# que mezcle los roles/conceptos IATI que suelen confundirse.
SIN_ESPECULAR = (
    "Respondé únicamente con los datos presentes en esta respuesta y en los "
    "datos IATI cargados. NO inventes montos, monedas, fechas ni nombres de "
    "organizaciones que no aparezcan explícitamente en los datos. No confundas "
    "a la organización reportante con quien financia o ejecuta la actividad, "
    "ni un compromiso con un desembolso o gasto. Limitate a describir qué "
    "muestran los datos."
)


_STATUS_LABELS = {
    str(status.value): status.name.replace("_", " ").title()
    for status in ActivityStatus
}
_TRANSACTION_TYPE_LABELS = {
    str(transaction_type.value): transaction_type.name.replace("_", " ").title()
    for transaction_type in TransactionType
}


def _table_to_text(table):
    """Renderiza la tabla (lista de filas) como bloque delimitado por ' | '."""
    if not table:
        return ""
    return "\n".join(" | ".join(str(cell) for cell in row) for row in table)


def text_result(
    text: str,
    source_url: str | list[str],
    table: list[list[Any]] | None = None,
):
    """Build the standard IATI response.

    Embeds the full table as text for the AI (see module docstring) and
    appends the no-speculation guardrail. `source_url` is explicit so this
    module stays independent from the data layer; queries pass
    `data.xml_source()`.
    """
    body = text
    if table:
        body += (
            f"\n\n{ALREADY_TABLE}\n\n"
            "=== Datos completos (para tu análisis) ===\n"
            + _table_to_text(table)
        )
    body = f"{body}\n\n{SIN_ESPECULAR}"
    return _text_result(body, source_url=source_url, table=table)


def empty_result(message: str, source_url: str | list[str]):
    """Build the standard response for a query with no matching rows."""
    return _text_result(message, source_url=source_url)


def activity_status_label(value: Any) -> str:
    """Return the human-readable label for an IATI activity status code."""
    key = str(value)
    return _STATUS_LABELS.get(key, key)


def transaction_type_label(value: Any) -> str:
    """Return the human-readable label for an IATI transaction type code."""
    key = str(value)
    return _TRANSACTION_TYPE_LABELS.get(key, key)


def format_amount(value: Any) -> str:
    """Format a numeric IATI amount consistently across text and tables."""
    return f"{float(value):,.2f}"


def build_table(
    rows: Iterable[Mapping[str, Any]],
    columns: Sequence[tuple[str, str]],
    formatters: Mapping[str, Callable[[Any], Any]] | None = None,
) -> list[list[Any]]:
    """Build an MCP table from mappings using shared headers and formatters."""
    formatters = formatters or {}
    table: list[list[Any]] = [[header for _, header in columns]]
    for row in rows:
        table.append([
            formatters.get(column, lambda value: value)(row[column])
            for column, _ in columns
        ])
    return table
