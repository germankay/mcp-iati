"""
Regression tests for the queries over synthetic data (see `seed_cache` in
conftest.py: preloaded cache, no network).
"""
import pandas as pd
import pytest
from mcp_iati.activities import queries, data


def _text(result):
    return result.content[0].text


def test_search_activities_preserves_table_and_source(seed_cache):
    result = queries.search_activities("transport")

    assert _text(result).startswith(
        "Found 1 IATI activity(ies) matching 'transport'."
    )
    assert result.structuredContent["table"] == [
        ["IATI identifier", "Title", "Status"],
        ["IATI-001", "Sustainable transport programme", "Implementation"],
    ]
    assert result.structuredContent["sources"] == [seed_cache.source]


def test_search_activities_preserves_empty_response(seed_cache):
    result = queries.search_activities("nonexistent")

    assert _text(result) == (
        "No IATI activities found with 'nonexistent' in the title."
    )
    assert "table" not in result.structuredContent
    assert result.structuredContent["sources"] == [seed_cache.source]


def test_activity_summary_preserves_details_totals_and_currency(seed_cache):
    result = queries.activity_summary("IATI-001")
    text = _text(result)

    assert "Sustainable transport programme (IATI-001)" in text
    assert "Status: Implementation" in text
    assert "Reporting organisation: Development Bank" in text
    # The totals travel in the table (and embedded in the text via text_result).
    assert "Out Commitment | 1,500.00 | USD" in text
    assert "Disbursement | 750.00 | USD" in text

    assert result.structuredContent["table"] == [
        ["Transaction type", "Total", "Currency"],
        ["Out Commitment", "1,500.00", "USD"],
        ["Disbursement", "750.00", "USD"],
    ]
    assert result.structuredContent["sources"] == [seed_cache.source]


def test_activity_summary_falls_back_to_org_ref(seed_cache):
    result = queries.activity_summary("IATI-002")

    assert "Reporting organisation: ORG-002" in _text(result)


def test_activity_summary_preserves_not_found_response(seed_cache):
    result = queries.activity_summary("UNKNOWN")

    assert _text(result) == (
        "No IATI activity found with identifier 'UNKNOWN'."
    )
    assert "table" not in result.structuredContent
    assert result.structuredContent["sources"] == [seed_cache.source]


def test_tools_use_preloaded_dataframes_without_preparing_data(
        seed_cache,
        monkeypatch,
    ):
    """
    This test confirms that:
        - the tools use preloaded DataFrames;
        - they don't re-read CSV files;
        - they don't download XML;
        - they don't execute okfn-iati;
        - search and summary continue to work.
    """
    def unexpected_preparation():
        raise AssertionError(
            "The tool attempted to read or prepare data again"
        )

    monkeypatch.setattr(
        data,
        "_csv_folder",
        unexpected_preparation,
    )

    search_result = queries.search_activities("transport")
    summary_result = queries.activity_summary("IATI-001")

    assert "IATI-001" in search_result.content[0].text
    assert "Sustainable transport programme" in summary_result.content[0].text


def test_list_activity_statuses_returns_counts_and_source(seed_cache):
    result = queries.list_activity_statuses()

    assert result.structuredContent["table"] == [
        ["Status code", "Activity status", "Activities"],
        ["2", "Implementation", 1],
        ["3", "Completion", 1],
    ]
    assert result.structuredContent["sources"] == [seed_cache.source]

    text = result.content[0].text
    assert "Found 2 activity status value(s) across 2 activities." in text
    assert "2 | Implementation | 1" in text
    assert "3 | Completion | 1" in text


def test_list_reporting_organisations_returns_counts_and_source(
    seed_cache,
):
    result = queries.list_reporting_organisations()

    assert result.structuredContent["table"] == [
        [
            "Organisation reference",
            "Reporting organisation",
            "Activities",
        ],
        ["ORG-001", "Development Bank", 1],
        ["ORG-002", "ORG-002", 1],
    ]
    assert result.structuredContent["sources"] == [seed_cache.source]

    text = result.content[0].text
    assert "Found 2 reporting organisation(s) across 2 activities." in text
    assert "ORG-001 | Development Bank | 1" in text
    assert "ORG-002 | ORG-002 | 1" in text
    assert "nan" not in text.lower()


def test_list_recipient_countries_returns_counts_and_source(
    seed_cache,
):
    result = queries.list_recipient_countries()

    assert result.structuredContent["table"] == [
        ["Country code", "Recipient country", "Activities"],
        ["AR", "Argentina", 1],
        ["BR", "Brazil", 1],
    ]
    assert result.structuredContent["sources"] == [seed_cache.source]

    text = result.content[0].text
    assert "Found 2 recipient country value(s) across 2 activities." in text
    assert "AR | Argentina | 1" in text
    assert "BR | Brazil | 1" in text
    assert "nan" not in text.lower()

@pytest.mark.parametrize(
    "country",
    ["AR", "Argentina", "argentina"],
)
def test_filter_activities_by_country_accepts_code_and_name(
    seed_cache,
    country,
):
    result = queries.filter_activities_by_country(country)

    assert result.structuredContent["table"] == [
        [
            "IATI identifier",
            "Title",
            "Status",
            "Country code",
            "Recipient country",
        ],
        [
            "IATI-001",
            "Sustainable transport programme",
            "Implementation",
            "AR",
            "Argentina",
        ],
    ]
    assert result.structuredContent["sources"] == [seed_cache.source]

    text = result.content[0].text
    assert "Found 1 IATI activity(ies)" in text
    assert "Showing 1 result(s) with limit 10." in text

def test_filter_activities_by_country_returns_clear_empty_result(
    seed_cache,
):
    result = queries.filter_activities_by_country("UY")

    assert result.content[0].text == (
        "No IATI activities were found for recipient country 'UY'."
    )
    assert "table" not in result.structuredContent
    assert result.structuredContent["sources"] == [seed_cache.source]


def test_list_sectors_returns_counts_and_source(seed_cache):
    result = queries.list_sectors()

    assert result.structuredContent["table"] == [
        ["Vocabulary", "Sector code", "Sector", "Activities"],
        ["1", "12220", "Basic health care", 1],
        ["99", "TR", "Transport", 1],
    ]
    assert result.structuredContent["sources"] == [seed_cache.source]

    text = result.content[0].text
    assert "Found 2 sector value(s)." in text
    assert "Showing 2 result(s) with limit 100." in text
    assert "nan" not in text.lower()


def test_transaction_totals_by_year_groups_by_year_type_and_currency(
    seed_cache,
    monkeypatch,
):
    data._cache["dataframe:transactions"] = pd.DataFrame([
        {
            "activity_identifier": "IATI-001",
            "transaction_type": "2",
            "transaction_date": "2023-01-01",
            "value": 500.0,
            "currency": "USD",
            "description": "First",
        },
        {
            "activity_identifier": "IATI-001",
            "transaction_type": "2",
            "transaction_date": "2024-02-01",
            "value": 1500.0,
            "currency": "USD",
            "description": "Second",
        },
        {
            "activity_identifier": "IATI-001",
            "transaction_type": "3",
            "transaction_date": "2024-03-01",
            "value": 750.0,
            "currency": "USD",
            "description": "Third",
        },
        {
            "activity_identifier": "IATI-001",
            "transaction_type": "2",
            "transaction_date": "2024-04-01",
            "value": 200.0,
            "currency": "EUR",
            "description": "Fourth",
        },
        {
            "activity_identifier": "IATI-001",
            "transaction_type": "3",
            "transaction_date": "2024-05-01",
            "value": 100.0,
            "currency": "EUR",
            "description": "Fifth",
        },
        {
            "activity_identifier": "IATI-001",
            "transaction_type": "2",
            "transaction_date": "bad-date",
            "value": 123.0,
            "currency": "USD",
            "description": "Ignored",
        },
        {
            "activity_identifier": "IATI-001",
            "transaction_type": "2",
            "transaction_date": "2024-06-01",
            "value": "not-a-number",
            "currency": "USD",
            "description": "Ignored",
        },
        {
            "activity_identifier": "IATI-001",
            "transaction_type": "2",
            "transaction_date": "2024-06-02",
            "value": 50.0,
            "currency": "",
            "description": "Falls back to default currency",
        },
        {
            "activity_identifier": "IATI-001",
            "transaction_type": "4",
            "transaction_date": "2024-06-03",
            "value": 999.0,
            "currency": "USD",
            "description": "Ignored type",
        },
    ])

    result = queries.transaction_totals_by_year()

    assert result.structuredContent["table"] == [
        ["Year", "Transaction type", "Currency", "Total"],
        [2023, "Out Commitment", "USD", "500.00"],
        [2024, "Out Commitment", "EUR", "200.00"],
        [2024, "Out Commitment", "USD", "1,550.00"],
        [2024, "Disbursement", "EUR", "100.00"],
        [2024, "Disbursement", "USD", "750.00"],
    ]
    assert result.structuredContent["sources"] == [seed_cache.source]

    text = result.content[0].text
    assert "Found 5 annual transaction total(s)." in text
    assert "2023 | Out Commitment | USD | 500.00" in text
    assert "2024 | Out Commitment | USD | 1,550.00" in text
    assert "2024 | Disbursement | USD | 750.00" in text
    assert "2024 | Out Commitment | EUR | 200.00" in text
    assert "2024 | Disbursement | EUR | 100.00" in text


def test_transaction_totals_by_year_applies_year_filters(seed_cache):
    result = queries.transaction_totals_by_year(year_from=2023, year_to=2024)

    assert result.structuredContent["table"][-1] == [2024, "Disbursement", "USD", "750.00"]
    assert all(row[0] == 2024 for row in result.structuredContent["table"][1:])


def test_transaction_totals_by_year_rejects_invalid_range(seed_cache):
    result = queries.transaction_totals_by_year(year_from=2025, year_to=2024)

    assert result.content[0].text == (
        "The year_from value cannot be greater than year_to."
    )
    assert "table" not in result.structuredContent
    assert result.structuredContent["sources"] == [seed_cache.source]


def test_activity_transactions_returns_chronological_rows_and_source(
    seed_cache,
):
    result = queries.activity_transactions("IATI-001")

    assert result.structuredContent["table"] == [
        [
            "Date",
            "Transaction type",
            "Value",
            "Currency",
            "Description",
        ],
        [
            "2024-01-10",
            "Out Commitment",
            "1,000.00",
            "USD",
            "Initial commitment",
        ],
        [
            "2024-02-10",
            "Out Commitment",
            "500.00",
            "USD",
            "Additional commitment",
        ],
        [
            "2024-03-10",
            "Disbursement",
            "750.00",
            "USD",
            "First disbursement",
        ],
    ]
    assert result.structuredContent["sources"] == [seed_cache.source]

    text = result.content[0].text
    assert "Found 3 transaction(s)" in text
    assert "Showing 3 result(s) with limit 50." in text


def test_activity_transactions_rejects_unknown_activity(seed_cache):
    result = queries.activity_transactions("UNKNOWN")

    assert result.content[0].text == (
        "No IATI activity found with identifier 'UNKNOWN'."
    )
    assert "table" not in result.structuredContent
    assert result.structuredContent["sources"] == [seed_cache.source]
