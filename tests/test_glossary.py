import importlib.util
from pathlib import Path
import unittest


GLOSSARY_MODULE = Path(__file__).parents[1] / "src" / "mcp_iati" / "glossary.py"
spec = importlib.util.spec_from_file_location("mcp_iati_glossary", GLOSSARY_MODULE)
glossary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(glossary)

IATI_GLOSSARY = glossary.IATI_GLOSSARY
full_glossary_text = glossary.full_glossary_text
glossary_text = glossary.glossary_text


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


class GlossaryTest(unittest.TestCase):
    def test_glossary_contains_expected_iati_terms(self):
        self.assertLessEqual(EXPECTED_TERMS, IATI_GLOSSARY.keys())
        self.assertTrue(all(IATI_GLOSSARY[term].strip() for term in EXPECTED_TERMS))

    def test_glossary_text_only_includes_requested_terms(self):
        text = glossary_text("compromiso", "desembolso")

        self.assertIn("Compromiso:", text)
        self.assertIn("Desembolso:", text)
        self.assertNotIn("Gasto:", text)

    def test_full_glossary_text_includes_every_definition(self):
        text = full_glossary_text()

        for term, definition in IATI_GLOSSARY.items():
            self.assertIn(term.title(), text)
            self.assertIn(definition, text)

    def test_glossary_text_rejects_unknown_terms(self):
        with self.assertRaisesRegex(KeyError, "desconocido"):
            glossary_text("término desconocido")
