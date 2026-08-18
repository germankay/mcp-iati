"""
Registro del plugin: tools esperadas, glosario en las instrucciones y
mensaje del fallback `no_tool_disponible` (usa el `fake_mcp` de conftest.py).
"""

from mcp_iati import register_tools


def test_register_tools_adds_expected_tools(fake_mcp):
    register_tools(fake_mcp)

    assert list(fake_mcp.tools) == [
        "no_tool_disponible",
        "buscar_actividades",
        "resumen_actividad",
    ]


def test_plugin_instructions_include_full_glossary(fake_mcp):
    register_tools(fake_mcp)

    assert fake_mcp.plugin_info is not None
    instructions = fake_mcp.plugin_info["instructions"]
    assert "Glosario IATI:\n" in instructions
    assert "actividad IATI" in instructions
    assert "compromiso" in instructions
    assert "desembolso" in instructions


def test_plugin_sample_questions_cover_main_use_cases(fake_mcp):
    register_tools(fake_mcp)

    questions = fake_mcp.plugin_info["sample_questions"]
    assert "Buscá actividades IATI sobre transporte" in questions
    assert "Dame el resumen de la actividad XI-IATI-IADB-BR-L1231" in questions


def test_no_tool_disponible_returns_clear_fallback_message(fake_mcp):
    register_tools(fake_mcp)

    result = fake_mcp.tools["no_tool_disponible"]("no es una pregunta IATI")

    assert result.structuredContent == {"sources": []}
    text = result.content[0].text
    assert "responde únicamente sobre las actividades IATI cargadas" in text
    assert "Motivo: no es una pregunta IATI." in text
