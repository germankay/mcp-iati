"""Glossary lookup tool logic ("what does X mean?").

Answers terminology questions from the central glossary instead of the
loaded XML, so the source points at the IATI standard itself.
"""
from mcp_iati import helpers as h
from mcp_iati.glossary import IATI_GLOSSARY, search_terms

IATI_STANDARD_URL = "https://iatistandard.org/en/iati-standard/203/"


def define_term(term: str):
    """Look up an IATI term in the glossary and build the standard response."""
    matches = search_terms(term)

    if not matches:
        available = ", ".join(sorted(IATI_GLOSSARY))
        return h.empty_result(
            f"No IATI glossary entry matches '{term}'. Available terms: {available}.",
            source_url=IATI_STANDARD_URL,
        )

    table = [["Term", "Definition"]]
    for name, definition in matches:
        table.append([name, definition])
    text = f"Found {len(matches)} IATI glossary entry(ies) matching '{term}'."
    return h.text_result(text, source_url=IATI_STANDARD_URL, table=table)
