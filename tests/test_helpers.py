import pytest
from mcp_iati import helpers as h
from mcp_iati.glossary import IATI_STANDARD_URL


def test_activity_status_label_uses_iati_enum():
    assert h.activity_status_label("2") == "Implementation"


def test_activity_status_label_preserves_unknown_code():
    assert h.activity_status_label("999") == "999"


def test_transaction_type_label_uses_iati_enum():
    assert h.transaction_type_label("2") == "Out Commitment"


def test_format_amount_uses_two_decimal_places():
    assert h.format_amount(1234.5) == "1,234.50"


def test_build_table_applies_headers_and_formatters():
    table = h.build_table(
        [{"identifier": "IATI-1", "status": "2"}],
        [("identifier", "Identifier"), ("status", "Status")],
        formatters={"status": h.activity_status_label},
    )

    assert table == [
        ["Identifier", "Status"],
        ["IATI-1", "Implementation"],
    ]

def test_text_result_appends_only_relevant_glossary_terms():
    result = h.text_result(
        "Annual totals.",
        source_url="/data/example.xml",
        tool_name="transaction_totals_by_year",
    )

    text = result.content[0].text

    assert "=== Relevant IATI terms ===" in text
    assert "Commitment:" in text
    assert "Disbursement:" in text
    assert "Sector:" not in text
    assert "Reporting organisation:" not in text


def test_text_result_adds_iati_standard_as_glossary_source():
    result = h.text_result(
        "Annual totals.",
        source_url="/data/example.xml",
        tool_name="transaction_totals_by_year",
    )

    assert result.structuredContent["sources"] == [
        "/data/example.xml",
        IATI_STANDARD_URL,
    ]


def test_text_result_without_tool_preserves_existing_behavior():
    result = h.text_result(
        "Result without glossary.",
        source_url="/data/example.xml",
    )

    assert "=== Relevant IATI terms ===" not in result.content[0].text
    assert result.structuredContent["sources"] == [
        "/data/example.xml",
    ]

def test_empty_result_does_not_include_glossary():
    result = h.empty_result(
        "No matching activities.",
        source_url="/data/example.xml",
    )

    assert result.content[0].text == "No matching activities."
    assert result.structuredContent["sources"] == [
        "/data/example.xml",
    ]


def test_text_result_includes_common_query_details():
    result = h.text_result(
        "Found matching IATI activities.",
        source_url="/data/sample.xml",
        total=25,
        shown=10,
        filters={
            "country": "AR",
            "currency": "USD",
            "year_from": None,
        },
        limit=10,
    )

    response_text = result.content[0].text

    assert "=== Query details ===" in response_text
    assert "Total results: 25" in response_text
    assert "Records shown: 10" in response_text
    assert "Applied filters: country=AR, currency=USD" in response_text
    assert "Applied limit: 10" in response_text
    assert "year_from" not in response_text


def test_text_result_omits_query_details_when_not_provided():
    result = h.text_result(
        "IATI response.",
        source_url="/data/sample.xml",
    )

    assert "=== Query details ===" not in result.content[0].text


@pytest.mark.parametrize(
    "category,code,expected",
    [
        ("activity_status", "2", "Implementation"),
        ("transaction_type", "3", "Disbursement"),
        ("organisation_type", "40", "Multilateral"),
        ("aid_type", "C01", "Project Type"),
        ("humanitarian", "1", "Yes"),
        ("humanitarian", "0", "No"),
        ("default_currency", "USD", "USD"),
    ],
)
def test_category_value_label(category, code, expected):
    assert h.category_value_label(category, code) == expected
