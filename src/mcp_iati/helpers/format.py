"""Formatting and response helpers shared by IATI queries."""

from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any

from okfn_iati.enums import ActivityStatus, TransactionType

from mcp_server.results import text_result as _text_result

from mcp_iati.activities.data import xml_source


_STATUS_LABELS = {
    str(status.value): status.name.replace("_", " ").title()
    for status in ActivityStatus
}
_TRANSACTION_TYPE_LABELS = {
    str(transaction_type.value): transaction_type.name.replace("_", " ").title()
    for transaction_type in TransactionType
}


def text_result(
    text: str,
    table: list[list[Any]] | None = None,
    source_url: str | None = None,
):
    """Build a standard IATI response pointing to the configured XML."""
    source = xml_source() if source_url is None else source_url
    return _text_result(text, source_url=source, table=table)


def empty_result(message: str):
    """Build the standard response for a query with no matching rows."""
    return text_result(message)


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
