import unittest

from mcp_iati import register_tools


class FakeMCP:
    def __init__(self):
        self.plugin_info = None
        self.tools = []

    def set_plugin_info(self, **kwargs):
        self.plugin_info = kwargs

    def tool(self):
        def decorator(func):
            self.tools.append(func)
            return func

        return decorator


class ToolDescriptionsTest(unittest.TestCase):
    def test_register_tools_adds_expected_tools(self):
        mcp = FakeMCP()

        register_tools(mcp)

        self.assertEqual(
            [tool.__name__ for tool in mcp.tools],
            ["no_tool_disponible", "buscar_actividades", "resumen_actividad"],
        )

    def test_plugin_instructions_include_full_glossary(self):
        mcp = FakeMCP()

        register_tools(mcp)

        self.assertIsNotNone(mcp.plugin_info)
        self.assertIn("Glosario IATI:\n", mcp.plugin_info["instructions"])
        self.assertIn("actividad IATI", mcp.plugin_info["instructions"])
        self.assertIn("compromiso", mcp.plugin_info["instructions"])
        self.assertIn("desembolso", mcp.plugin_info["instructions"])

    def test_plugin_sample_questions_cover_main_use_cases(self):
        mcp = FakeMCP()

        register_tools(mcp)

        self.assertIn("Buscá actividades IATI sobre transporte", mcp.plugin_info["sample_questions"])
        self.assertIn("Dame el resumen de la actividad XI-IATI-IADB-BR-L1231", mcp.plugin_info["sample_questions"])

    def test_no_tool_disponible_returns_clear_fallback_message(self):
        mcp = FakeMCP()

        register_tools(mcp)

        no_tool_disponible = next(tool for tool in mcp.tools if tool.__name__ == "no_tool_disponible")
        result = no_tool_disponible("no es una pregunta IATI")

        self.assertEqual(result.structuredContent, {"sources": []})
        self.assertIn("responde únicamente sobre las actividades IATI cargadas", result.content[0].text)
        self.assertIn("Motivo: no es una pregunta IATI.", result.content[0].text)
