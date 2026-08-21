"""
Guarantees that the response the AI receives (the text in `content`) includes
the RAW DATA, not just a summary.

Context: the gateway sends the AI only `content[0].text`; the table in
`structuredContent` is rendered for the user alone. That is why `text_result`
embeds the table as text in `content`. If this breaks, the AI analyses
blindly (for example, it never sees the identifiers returned by
search_activities and cannot chain into activity_summary).
"""

import pytest

from mcp_iati import helpers as h
from mcp_iati import terms
from mcp_iati.helpers.format import _table_to_text
from mcp_iati.activities import queries


def _text(res):
    return res.content[0].text


# --- Unit: the text_result builder embeds the raw table -------------------

def test_text_result_embeds_full_table_verbatim():
    table = [
        ["IATI identifier", "Title", "Status"],
        ["IATI-001", "Programme A", "Implementation"],
        ["IATI-002", "Programme B", "Finalisation"],
    ]
    res = h.text_result("summary", source_url="http://src", table=table)

    txt = _text(res)
    # The AI-facing data block is present...
    assert "=== Full data" in txt
    # ...and contains the COMPLETE table verbatim (not just the last row).
    assert _table_to_text(table) in txt
    for row in table:
        for cell in row:
            assert cell in txt
    # structuredContent (what the user sees) stays intact.
    assert res.structuredContent["table"] == table
    assert res.structuredContent["sources"] == ["http://src"]


def test_text_result_without_table_adds_no_block():
    res = h.text_result("text only", source_url="http://src")
    txt = _text(res)
    assert "=== Full data" not in txt
    assert "table" not in res.structuredContent


def test_text_result_appends_guardrail():
    res = h.text_result("text", source_url="http://src")
    assert h.NO_SPECULATION in _text(res)


def test_table_to_text_pipe_format():
    table = [["a", "b"], ["1", "2"]]
    assert _table_to_text(table) == "a | b\n1 | 2"
    assert _table_to_text([]) == ""


# --- Contract: EVERY data tool sends the raw table to the AI --------------

# (name, callable, kwargs) for every data tool in the repo. When adding a
# new table-returning tool, add it here.
DATA_TOOLS = [
    (
        "search_activities",
        queries.search_activities,
        {"text": "programme"},
    ),
    (
        "list_activity_statuses",
        queries.list_activity_statuses,
        {},
    ),
    (
        "list_reporting_organisations",
        queries.list_reporting_organisations,
        {},
    ),
    (
        "activity_summary",
        queries.activity_summary,
        {"iati_identifier": "IATI-001"},
    ),
    (
        "define_term",
        terms.define_term,
        {"term": "organisation"},
    ),
        (
        "list_recipient_countries",
        queries.list_recipient_countries,
        {},
    ),
        (
        "filter_activities_by_country",
        queries.filter_activities_by_country,
        {"country": "AR"},
    ),
        (
        "list_sectors",
        queries.list_sectors,
        {},
    ),
        (
        "activity_transactions",
        queries.activity_transactions,
        {"iati_identifier": "IATI-001"},
    ),
    (
        "transaction_totals_by_year",
        queries.transaction_totals_by_year,
        {},
    ),
    (
        "transaction_totals_by_organisation",
        queries.transaction_totals_by_organisation,
        {},
    ),
    (
        "transaction_totals_by_sector",
        queries.transaction_totals_by_sector,
        {"transaction_type": "commitment"},
    ),
    (
        "transaction_totals_by_country",
        queries.transaction_totals_by_country,
        {"transaction_type": "commitment"},
    ),
    (
        "top_activities_by_amount",
        queries.top_activities_by_amount,
        {"transaction_type": "commitment"},
    ),
]


@pytest.mark.parametrize("name,fn,kwargs", DATA_TOOLS, ids=[t[0] for t in DATA_TOOLS])
def test_tool_embeds_full_table_in_ai_text(seed_cache, name, fn, kwargs):
    res = fn(**kwargs)
    txt = _text(res)
    sc = res.structuredContent

    # 1. The tool produced a table (data for the user).
    assert "table" in sc, f"{name}: returned no table"
    assert len(sc["table"]) >= 2, f"{name}: table has no data rows"

    # 2. That SAME complete table is embedded in the text the AI receives.
    assert "=== Full data" in txt, f"{name}: data block missing"
    assert _table_to_text(sc["table"]) in txt, (
        f"{name}: the user-facing table is not verbatim in the AI text"
    )
