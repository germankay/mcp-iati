"""Shared helpers used by the IATI tools.

The package follows the organization used by ``mcp-datos-uruguay-ben``:
tool modules focus on queries while reusable formatting and response logic
lives under a single helpers namespace.
"""

from .format import (
    activity_status_label,
    build_table,
    empty_result,
    format_amount,
    text_result,
    transaction_type_label,
)

__all__ = [
    "activity_status_label",
    "build_table",
    "empty_result",
    "format_amount",
    "text_result",
    "transaction_type_label",
]
