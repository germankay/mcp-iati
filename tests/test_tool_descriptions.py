"""
Plugin registration: expected tools, glossary in the instructions and the
`no_tool_disponible` fallback message (uses `fake_mcp` from conftest.py).
"""

from mcp_iati import register_tools


def test_register_tools_adds_expected_tools(fake_mcp):
    register_tools(fake_mcp)

    assert list(fake_mcp.tools) == [
        "no_tool_disponible",
        "search_activities",
        "list_activity_statuses",
        "list_reporting_organisations",
        "list_recipient_countries",
        "filter_activities_by_country",
        "list_sectors",
        "activity_summary",
        "activity_transactions",
        "define_term",
    ]


def test_plugin_instructions_include_full_glossary(fake_mcp):
    register_tools(fake_mcp)

    assert fake_mcp.plugin_info is not None
    instructions = fake_mcp.plugin_info["instructions"]
    assert "IATI glossary:\n" in instructions
    assert "IATI activity" in instructions
    assert "commitment" in instructions
    assert "disbursement" in instructions


def test_plugin_sample_questions_cover_main_use_cases(fake_mcp):
    register_tools(fake_mcp)

    questions = fake_mcp.plugin_info["sample_questions"]
    assert "Search IATI activities about transport" in questions
    assert "Give me a summary of activity XI-IATI-IADB-BR-L1231" in questions
    assert "What activity statuses are present in this IATI file?" in questions
    assert "Which organisations report activities in this IATI file?" in questions
    assert "Which recipient countries are present in this IATI file?" in questions
    assert "Which IATI activities have Brazil as their recipient country?" in questions
    assert "Show the transactions for activity XI-IATI-IADB-BR-L1231" in questions

def test_no_tool_disponible_returns_clear_fallback_message(fake_mcp):
    register_tools(fake_mcp)

    result = fake_mcp.tools["no_tool_disponible"]("not a question about IATI activities")

    assert result.structuredContent == {"sources": []}
    text = result.content[0].text
    assert "only answers questions about the loaded IATI activities" in text
    assert "Reason: not a question about IATI activities." in text
