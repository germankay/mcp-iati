"""
Regression tests for the queries over synthetic data (see `seed_cache` in
conftest.py: preloaded cache, no network).
"""

from mcp_iati.activities import queries


def _text(result):
    return result.content[0].text


def test_search_activities_preserves_table_and_source(seed_cache):
    result = queries.search_activities("transport")

    assert _text(result).startswith(
        "Found 1 IATI activity(ies) matching 'transport'."
    )
    assert result.structuredContent["table"] == [
        ["IATI identifier", "Title", "Status"],
        ["IATI-001", "Sustainable transport programme", "Implementation"],
    ]
    assert result.structuredContent["sources"] == [seed_cache.source]


def test_search_activities_preserves_empty_response(seed_cache):
    result = queries.search_activities("nonexistent")

    assert _text(result) == (
        "No IATI activities found with 'nonexistent' in the title."
    )
    assert "table" not in result.structuredContent
    assert result.structuredContent["sources"] == [seed_cache.source]


def test_activity_summary_preserves_details_totals_and_currency(seed_cache):
    result = queries.activity_summary("IATI-001")
    text = _text(result)

    assert "Sustainable transport programme (IATI-001)" in text
    assert "Status: Implementation" in text
    assert "Reporting organisation: Development Bank" in text
    # The totals travel in the table (and embedded in the text via text_result).
    assert "Out Commitment | 1,500.00 | USD" in text
    assert "Disbursement | 750.00 | USD" in text

    assert result.structuredContent["table"] == [
        ["Transaction type", "Total", "Currency"],
        ["Out Commitment", "1,500.00", "USD"],
        ["Disbursement", "750.00", "USD"],
    ]
    assert result.structuredContent["sources"] == [seed_cache.source]


def test_activity_summary_falls_back_to_org_ref(seed_cache):
    result = queries.activity_summary("IATI-002")

    assert "Reporting organisation: ORG-002" in _text(result)


def test_activity_summary_preserves_not_found_response(seed_cache):
    result = queries.activity_summary("UNKNOWN")

    assert _text(result) == (
        "No IATI activity found with identifier 'UNKNOWN'."
    )
    assert "table" not in result.structuredContent
    assert result.structuredContent["sources"] == [seed_cache.source]
