"""
The central glossary (glossary.py) contains the minimum IATI terms and its
text builders behave as the tools and plugin_info expect.
"""

import pytest

from mcp_iati.glossary import (
    IATI_GLOSSARY,
    TOOL_GLOSSARY_TERMS,
    full_glossary_text,
    glossary_text,
    search_terms,
    tool_glossary_terms,
    tool_glossary_text,
)
from mcp_iati.activities import queries


# One representative set per area of the IATI 2.03 standard covered by the
# okfn_iati library (identification, organisations, financials, aid
# classifications, geography, results, documentation).
EXPECTED_TERMS = {
    # identification and lifecycle
    "IATI activity",
    "IATI identifier",
    "activity status",
    "activity date",
    "description",
    "hierarchy",
    "related activity",
    "activity scope",
    "humanitarian flag",
    # organisations
    "reporting organisation",
    "participating organisation",
    "organisation role",
    "organisation type",
    "contact information",
    # financial data
    "transaction",
    "transaction type",
    "commitment",
    "disbursement",
    "expenditure",
    "budget",
    "planned disbursement",
    "default currency",
    "country budget item",
    # aid classifications
    "aid type",
    "finance type",
    "flow type",
    "tied status",
    "collaboration type",
    "disbursement channel",
    "policy marker",
    # sectors and geography
    "sector",
    "recipient country or region",
    "location",
    # results and monitoring
    "result",
    "indicator",
    "indicator period",
    # documentation and cross-cutting
    "document link",
    "condition",
    "vocabulary",
    "codelist",
    "narrative",
}


def test_glossary_contains_expected_iati_terms():
    assert EXPECTED_TERMS <= IATI_GLOSSARY.keys()
    assert all(IATI_GLOSSARY[term].strip() for term in EXPECTED_TERMS)


def test_glossary_text_only_includes_requested_terms():
    text = glossary_text("commitment", "disbursement")

    assert "Commitment:" in text
    assert "Disbursement:" in text
    assert "Expenditure:" not in text


def test_glossary_text_preserves_acronym_case():
    text = glossary_text("IATI activity")

    assert "- IATI activity:" in text
    assert "Iati" not in text


def test_full_glossary_text_includes_every_definition():
    text = full_glossary_text()

    for term, definition in IATI_GLOSSARY.items():
        assert f"- {term[0].upper()}{term[1:]}:" in text
        assert definition in text


def test_glossary_text_rejects_unknown_terms():
    with pytest.raises(KeyError, match="Unknown IATI terms"):
        glossary_text("unknown term")


def test_search_terms_exact_match_is_case_insensitive():
    assert search_terms("Disbursement") == [
        ("disbursement", IATI_GLOSSARY["disbursement"])
    ]


def test_search_terms_exact_match_wins_over_partial():
    # "budget" is also a substring of "country budget item"; the exact key
    # must be returned alone.
    assert search_terms("budget") == [("budget", IATI_GLOSSARY["budget"])]


def test_search_terms_partial_match_returns_all_terms():
    found = dict(search_terms("organisation"))
    assert "reporting organisation" in found
    assert "participating organisation" in found
    assert "organisation role" in found


def test_search_terms_matches_simple_plurals():
    assert ("sector", IATI_GLOSSARY["sector"]) in search_terms("sectors")


def test_search_terms_strips_question_punctuation():
    assert search_terms("'budget'?") == [("budget", IATI_GLOSSARY["budget"])]


def test_search_terms_falls_back_to_definitions():
    # "ODA" appears only inside the flow type definition, not in any key.
    found = dict(search_terms("ODA"))
    assert "flow type" in found


def test_search_terms_empty_for_unknown_or_blank():
    assert search_terms("xyzzy") == []
    assert search_terms("   ") == []

def test_every_tool_glossary_term_exists():
    for terms in TOOL_GLOSSARY_TERMS.values():
        assert all(term in IATI_GLOSSARY for term in terms)


def test_tool_glossary_terms_returns_relevant_terms():
    terms = tool_glossary_terms("transaction_totals_by_year")

    assert "commitment" in terms
    assert "disbursement" in terms
    assert "sector" not in terms
    assert "reporting organisation" not in terms


def test_tool_glossary_terms_returns_empty_tuple_for_unknown_tool():
    assert tool_glossary_terms("unknown_tool") == ()


def test_tool_glossary_text_only_contains_relevant_definitions():
    text = tool_glossary_text("list_sectors")

    assert "Sector:" in text
    assert "Vocabulary:" in text
    assert "Commitment:" not in text
    assert "Disbursement:" not in text


def test_tool_glossary_text_is_empty_for_unknown_tool():
    assert tool_glossary_text("unknown_tool") == ""

def test_search_activities_empty_response_has_no_glossary(seed_cache):
    result = queries.search_activities("not-present")

    text = result.content[0].text

    assert text.startswith("No IATI activities found")
    assert "=== Relevant IATI terms ===" not in text
    assert result.structuredContent["sources"] == [
        seed_cache.source,
    ]
