from pathlib import Path
import unittest


REGISTER_MODULE = Path(__file__).parents[1] / "src" / "mcp_iati" / "__init__.py"


class ToolDescriptionsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = REGISTER_MODULE.read_text(encoding="utf-8")

    def test_search_tool_uses_shared_glossary(self):
        self.assertIn(
            'glossary_text("actividad IATI", "identificador IATI", "estado de actividad")',
            self.source,
        )

    def test_summary_tool_uses_financial_glossary_terms(self):
        for term in ("organización reportante", "compromiso", "desembolso", "gasto"):
            self.assertIn(f'"{term}"', self.source)

    def test_plugin_instructions_include_full_glossary(self):
        self.assertIn('"Glosario IATI:\\n" + full_glossary_text()', self.source)
