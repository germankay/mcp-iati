"""Shared helpers used by the IATI tools.

Tool modules focus on queries while reusable formatting and response logic
lives under a single helpers namespace. ``text_result`` embeds the raw table
as text for the AI and appends the ``NO_SPECULATION`` guardrail (see
``format.py``).
"""

from .format import (
    ALREADY_TABLE,
    NO_SPECULATION,
    activity_status_label,
    build_table,
    empty_result,
    format_amount,
    text_result,
    transaction_type_label,
    category_value_label,
)

__all__ = [
    "ALREADY_TABLE",
    "NO_SPECULATION",
    "activity_status_label",
    "build_table",
    "empty_result",
    "format_amount",
    "text_result",
    "transaction_type_label",
    "category_value_label",
]
