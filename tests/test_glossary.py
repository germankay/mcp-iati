"""
The central glossary (glossary.py) contains the minimum IATI terms and its
text builders behave as the tools and plugin_info expect.
"""

import pytest

from mcp_iati.glossary import IATI_GLOSSARY, full_glossary_text, glossary_text


EXPECTED_TERMS = {
    "IATI activity",
    "IATI identifier",
    "reporting organisation",
    "activity status",
    "transaction",
    "commitment",
    "disbursement",
    "expenditure",
    "default currency",
    "participating organisation",
    "sector",
    "recipient country or region",
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
