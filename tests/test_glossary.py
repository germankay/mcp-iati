"""
El glosario central (glossary.py) contiene los términos IATI mínimos y sus
builders de texto se comportan como esperan las tools y el plugin_info.
"""

import pytest

from mcp_iati.glossary import IATI_GLOSSARY, full_glossary_text, glossary_text


EXPECTED_TERMS = {
    "actividad IATI",
    "identificador IATI",
    "organización reportante",
    "estado de actividad",
    "transacción",
    "compromiso",
    "desembolso",
    "gasto",
    "moneda predeterminada",
    "organización participante",
    "sector",
    "país o región receptora",
}


def test_glossary_contains_expected_iati_terms():
    assert EXPECTED_TERMS <= IATI_GLOSSARY.keys()
    assert all(IATI_GLOSSARY[term].strip() for term in EXPECTED_TERMS)


def test_glossary_text_only_includes_requested_terms():
    text = glossary_text("compromiso", "desembolso")

    assert "Compromiso:" in text
    assert "Desembolso:" in text
    assert "Gasto:" not in text


def test_full_glossary_text_includes_every_definition():
    text = full_glossary_text()

    for term, definition in IATI_GLOSSARY.items():
        assert term.title() in text
        assert definition in text


def test_glossary_text_rejects_unknown_terms():
    with pytest.raises(KeyError, match="desconocido"):
        glossary_text("término desconocido")
