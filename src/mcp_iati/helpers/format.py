"""Formatting and response helpers shared by IATI queries."""

from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any

from okfn_iati.enums import ActivityStatus, TransactionType

from mcp_server.results import text_result as _text_result


# Note for the AI: the rendered table was already shown on screen via
# structuredContent; the text copy is there so it analyses the real numbers.
ALREADY_TABLE = (
    "The user has already been shown a rendered table with this data on "
    "screen. The same data is attached below as text so you can analyse the "
    "numbers; do not copy the table back into your answer, interpret it."
)

# Guardrail for the AI, appended automatically to every response by
# `text_result`. Keeps the model from inventing data that is not in the XML
# and from mixing up the IATI roles/concepts that are commonly confused.
NO_SPECULATION = (
    "Answer only with the data present in this response and in the loaded "
    "IATI data. Do NOT invent amounts, currencies, dates or organisation "
    "names that do not appear explicitly in the data. Do not confuse the "
    "reporting organisation with the one funding or implementing the "
    "activity, nor a commitment with a disbursement or an expenditure. Limit "
    "yourself to describing what the data shows."
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
    """Render the table (list of rows) as a ' | '-delimited text block."""
    if not table:
        return ""
    return "\n".join(" | ".join(str(cell) for cell in row) for row in table)


def text_result(
    text: str,
    source_url: str | list[str],
    table: list[list[Any]] | None = None,
):
    """Build the standard IATI response.

    The chat gateway forwards only the text content to the LLM (the
    structuredContent table is rendered for the user alone), so the full
    table is embedded as text for the AI, followed by the no-speculation
    guardrail. `source_url` is explicit so this module stays independent
    from the data layer; queries pass `data.xml_source()`.
    """
    body = text
    if table:
        body += (
            f"\n\n{ALREADY_TABLE}\n\n"
            "=== Full data (for your analysis) ===\n"
            + _table_to_text(table)
        )
    body = f"{body}\n\n{NO_SPECULATION}"
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
