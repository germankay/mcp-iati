"""
The define_term tool answers "what does X mean?" from the central glossary,
returning a term/definition table and pointing its source at the IATI
standard instead of the loaded XML.
"""

from mcp_iati.glossary import IATI_GLOSSARY
from mcp_iati.terms import IATI_STANDARD_URL, define_term


def _text(result):
    return result.content[0].text


def test_define_term_single_match_returns_definition_table():
    result = define_term("disbursement")

    assert _text(result).startswith(
        "Found 1 IATI glossary entry(ies) matching 'disbursement'."
    )
    assert result.structuredContent["table"] == [
        ["Term", "Definition"],
        ["disbursement", IATI_GLOSSARY["disbursement"]],
    ]
    assert result.structuredContent["sources"] == [IATI_STANDARD_URL]


def test_define_term_partial_match_returns_all_matching_terms():
    result = define_term("organisation")

    table = result.structuredContent["table"]
    listed = [row[0] for row in table[1:]]
    assert "reporting organisation" in listed
    assert "participating organisation" in listed
    assert len(table) >= 4


def test_define_term_unknown_lists_available_terms():
    result = define_term("xyzzy")

    text = _text(result)
    assert text.startswith("No IATI glossary entry matches 'xyzzy'.")
    # The AI can retry with one of the listed terms.
    assert "disbursement" in text
    assert "policy marker" in text
    assert "table" not in result.structuredContent
    assert result.structuredContent["sources"] == [IATI_STANDARD_URL]
