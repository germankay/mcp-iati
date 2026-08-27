"""Formatting and response helpers shared by IATI queries."""

from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any

from okfn_iati.enums import (
    ActivityStatus,
    AidType,
    CollaborationType,
    FinanceType,
    FlowType,
    OrganisationType,
    TiedStatus,
    TransactionType,
)

from mcp_server.results import text_result as _text_result

from mcp_iati.glossary import (
    IATI_STANDARD_URL,
    tool_glossary_text,
)


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
_CATEGORY_ENUMS = {
    "organisation_type": OrganisationType,
    "aid_type": AidType,
    "finance_type": FinanceType,
    "flow_type": FlowType,
    "tied_status": TiedStatus,
    "collaboration_type": CollaborationType,
}
_HUMANITARIAN_LABELS = {
    "0": "No",
    "1": "Yes",
    "false": "No",
    "true": "Yes",
}


def _table_to_text(table):
    """Render the table (list of rows) as a ' | '-delimited text block."""
    if not table:
        return ""
    return "\n".join(" | ".join(str(cell) for cell in row) for row in table)


def _query_details_text(
    total: int | None = None,
    shown: int | None = None,
    filters: Mapping[str, Any] | None = None,
    limit: int | None = None,
) -> str:
    """Render the common metadata included in IATI query responses."""
    details = []

    if total is not None:
        details.append(f"Total results: {total}")

    if shown is not None:
        details.append(f"Records shown: {shown}")

    applied_filters = {
        name: value
        for name, value in (filters or {}).items()
        if value is not None and value != ""
    }
    if applied_filters:
        formatted_filters = ", ".join(
            f"{name}={value}"
            for name, value in applied_filters.items()
        )
        details.append(f"Applied filters: {formatted_filters}")

    if limit is not None:
        details.append(f"Applied limit: {limit}")

    if not details:
        return ""

    return "=== Query details ===\n" + "\n".join(details)


def _append_relevant_terms(body: str, tool_name: str | None) -> str:
    """Append only the IATI definitions relevant to the calling tool."""
    if not tool_name:
        return body

    definitions = tool_glossary_text(tool_name)
    if not definitions:
        return body

    return (
        f"{body}\n\n"
        "=== Relevant IATI terms ===\n"
        f"{definitions}"
    )


def _sources_with_iati_standard(
    source_url: str | list[str],
    tool_name: str | None,
) -> str | list[str]:
    """Include the IATI Standard when glossary definitions are attached."""
    if not tool_name or not tool_glossary_text(tool_name):
        return source_url

    sources = (
        list(source_url)
        if isinstance(source_url, list)
        else [source_url]
    )

    if IATI_STANDARD_URL not in sources:
        sources.append(IATI_STANDARD_URL)

    return sources

def text_result(
     text: str,
    source_url: str | list[str],
    table: list[list[Any]] | None = None,
    tool_name: str | None = None,
    total: int | None = None,
    shown: int | None = None,
    filters: Mapping[str, Any] | None = None,
    limit: int | None = None,
):
    """Build the standard IATI response.

    The chat gateway forwards only the text content to the LLM (the
    structuredContent table is rendered for the user alone), so the full
    table is embedded as text for the AI, followed by the no-speculation
    guardrail. `source_url` is explicit so this module stays independent
    from the data layer; queries pass `data.xml_source()`.
    """
    body = text

    query_details = _query_details_text(
        total=total,
        shown=shown,
        filters=filters,
        limit=limit,
    )
    if query_details:
        body = f"{body}\n\n{query_details}"

    body = _append_relevant_terms(body, tool_name)

    if table:
        body += (
            f"\n\n{ALREADY_TABLE}\n\n"
            "=== Full data (for your analysis) ===\n"
            + _table_to_text(table)
        )
    body = f"{body}\n\n{NO_SPECULATION}"

    result = _text_result(
        body,
        source_url=_sources_with_iati_standard(
            source_url,
            tool_name,
        ),
        table=table,
    )
    return result


def empty_result(
    message: str,
    source_url: str | list[str],
):
    """Build the standard response for a query with no matching rows."""

    result = _text_result(
        message,
        source_url=source_url,
    )
    return result


def activity_status_label(value: Any) -> str:
    """Return the human-readable label for an IATI activity status code."""
    key = str(value)
    return _STATUS_LABELS.get(key, key)


def transaction_type_label(value: Any) -> str:
    """Return the human-readable label for an IATI transaction type code."""
    key = str(value)
    return _TRANSACTION_TYPE_LABELS.get(key, key)


def category_value_label(category: str, value: Any) -> str:
    """Return a readable label for a supported categorical IATI code."""
    selected_category = str(category).strip().casefold()
    key = str(value).strip()

    if selected_category == "activity_status":
        return activity_status_label(key)

    if selected_category == "transaction_type":
        return transaction_type_label(key)

    if selected_category == "humanitarian":
        return _HUMANITARIAN_LABELS.get(key.casefold(), key)

    enum_class = _CATEGORY_ENUMS.get(selected_category)
    if enum_class is None:
        return key

    try:
        member = enum_class(key)
    except (TypeError, ValueError):
        return key

    return member.name.replace("_", " ").title()


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
