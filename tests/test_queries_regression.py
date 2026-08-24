"""
Regression tests for the queries over synthetic data (see `seed_cache` in
conftest.py: preloaded cache, no network).
"""
import pandas as pd
import pytest
from mcp_iati.activities import queries, data
from mcp_iati.glossary import IATI_STANDARD_URL

def _text(result):
    return result.content[0].text

def _assert_data_and_glossary_sources(result, data_source):
    assert result.structuredContent["sources"] == [
        data_source,
        IATI_STANDARD_URL,
    ]


def _assert_data_source_only(result, data_source):
    assert result.structuredContent["sources"] == [
        data_source,
    ]


def test_search_activities_preserves_table_and_source(seed_cache):
    result = queries.search_activities("transport")
    text = _text(result)

    assert text.startswith(
        "Found 1 IATI activity(ies) matching 'transport'."
    )
    assert "Total results: 1" in text
    assert "Records shown: 1" in text
    assert "Applied filters: title_contains=transport" in text
    assert "Applied limit: 10" in text

    assert result.structuredContent["table"] == [
        ["IATI identifier", "Title", "Status"],
        [
            "IATI-001",
            "Sustainable transport programme",
            "Implementation",
        ],
    ]
    _assert_data_and_glossary_sources(
        result,
        seed_cache.source,
    )


def test_search_activities_reports_total_and_applied_limit(seed_cache):
    result = queries.search_activities("t", limit=1)
    text = _text(result)

    assert "Found 2 IATI activity(ies) matching 't'." in text
    assert "Total results: 2" in text
    assert "Records shown: 1" in text
    assert "Applied filters: title_contains=t" in text
    assert "Applied limit: 1" in text
    assert len(result.structuredContent["table"]) == 2


def test_search_activities_rejects_invalid_limit(seed_cache):
    result = queries.search_activities("transport", limit=0)

    assert _text(result) == (
        "The result limit must be greater than zero."
    )
    assert "table" not in result.structuredContent
    _assert_data_source_only(
        result,
        seed_cache.source,
    )


def test_search_activities_preserves_empty_response(seed_cache):
    result = queries.search_activities("nonexistent")

    assert _text(result).startswith(
        "No IATI activities found with 'nonexistent' in the title."
    )
    assert "=== Relevant IATI terms ===" not in _text(result)
    assert "table" not in result.structuredContent
    _assert_data_source_only(
        result,
        seed_cache.source,
    )


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
    _assert_data_and_glossary_sources(
        result,
        seed_cache.source,
    )
    assert "=== Query details ===" in text
    assert "Total results: 1" in text
    assert "Records shown: 1" in text
    assert (
        "Applied filters: iati_identifier=IATI-001"
        in text
    )
    assert "Applied limit:" not in text


def test_activity_summary_falls_back_to_org_ref(seed_cache):
    result = queries.activity_summary("IATI-002")

    assert "Reporting organisation: ORG-002" in _text(result)
    text = _text(result)

    assert "Total results: 1" in text
    assert "Records shown: 1" in text
    assert (
        "Applied filters: iati_identifier=IATI-002"
        in text
    )


def test_activity_summary_preserves_not_found_response(seed_cache):
    result = queries.activity_summary("UNKNOWN")

    assert _text(result) == (
        "No IATI activity found with identifier 'UNKNOWN'."
    )
    assert "table" not in result.structuredContent
    _assert_data_source_only(
        result,
        seed_cache.source,
    )
    assert "=== Query details ===" not in _text(result)


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
    _assert_data_and_glossary_sources(
        result,
        seed_cache.source,
    )

    text = result.content[0].text
    assert "Found 2 activity status value(s) across 2 activities." in text
    assert "2 | Implementation | 1" in text
    assert "3 | Completion | 1" in text
    assert "=== Query details ===" in text
    assert "Total results: 2" in text
    assert "Records shown: 2" in text
    assert "Applied filters:" not in text
    assert "Applied limit:" not in text


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
    _assert_data_and_glossary_sources(
        result,
        seed_cache.source,
    )

    text = result.content[0].text
    assert "Total results: 2" in text
    assert "Records shown: 2" in text
    assert "Applied filters:" not in text
    assert "Applied limit:" not in text
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
    _assert_data_and_glossary_sources(
        result,
        seed_cache.source,
    )

    text = result.content[0].text
    assert "Total results: 2" in text
    assert "Records shown: 2" in text
    assert "Applied filters:" not in text
    assert "Applied limit:" not in text
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
    _assert_data_and_glossary_sources(
        result,
        seed_cache.source,
    )

    text = result.content[0].text
    assert "Found 1 IATI activity(ies)" in text
    assert "Total results: 1" in text
    assert "Records shown: 1" in text
    assert (
        f"Applied filters: recipient_country={country}"
        in text
    )
    assert "Applied limit: 10" in text


def test_filter_activities_by_country_rejects_blank_country(
    seed_cache,
):
    result = queries.filter_activities_by_country("   ")

    assert _text(result) == (
        "A recipient country code or name is required."
    )
    assert "table" not in result.structuredContent
    assert "=== Query details ===" not in _text(result)
    _assert_data_source_only(
        result,
        seed_cache.source,
    )


def test_filter_activities_by_country_rejects_invalid_limit(
    seed_cache,
):
    result = queries.filter_activities_by_country("AR", limit=0)

    assert _text(result) == (
        "The result limit must be greater than zero."
    )
    assert "table" not in result.structuredContent
    assert "=== Query details ===" not in _text(result)
    _assert_data_source_only(
        result,
        seed_cache.source,
    )


def test_filter_activities_by_country_returns_clear_empty_result(
    seed_cache,
):
    result = queries.filter_activities_by_country("UY")

    assert result.content[0].text == (
        "No IATI activities were found for recipient country 'UY'."
    )
    assert "table" not in result.structuredContent
    _assert_data_source_only(
        result,
        seed_cache.source,
    )
    assert "=== Query details ===" not in _text(result)


def test_list_sectors_returns_counts_and_source(seed_cache):
    result = queries.list_sectors()

    assert result.structuredContent["table"] == [
        ["Vocabulary", "Sector code", "Sector", "Activities"],
        ["1", "12220", "Basic health care", 1],
        ["99", "TR", "Transport", 1],
    ]
    _assert_data_and_glossary_sources(
        result,
        seed_cache.source,
    )

    text = result.content[0].text
    assert "Found 2 sector value(s)." in text
    assert "Total results: 2" in text
    assert "Records shown: 2" in text
    assert "Applied filters:" not in text
    assert "Applied limit: 100" in text
    assert "nan" not in text.lower()


def test_list_sectors_reports_total_and_applied_limit(seed_cache):
    result = queries.list_sectors(limit=1)
    text = _text(result)

    assert "Found 2 sector value(s)." in text
    assert "Total results: 2" in text
    assert "Records shown: 1" in text
    assert "Applied limit: 1" in text
    assert len(result.structuredContent["table"]) == 2


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
    _assert_data_and_glossary_sources(
        result,
        seed_cache.source,
    )

    text = result.content[0].text
    assert "Found 5 annual transaction total(s)." in text
    assert "2023 | Out Commitment | USD | 500.00" in text
    assert "2024 | Out Commitment | USD | 1,550.00" in text
    assert "2024 | Disbursement | USD | 750.00" in text
    assert "2024 | Out Commitment | EUR | 200.00" in text
    assert "2024 | Disbursement | EUR | 100.00" in text
    assert "=== Query details ===" in text
    assert "Total results: 5" in text
    assert "Records shown: 5" in text
    assert "Applied filters:" not in text
    assert "Applied limit:" not in text


def test_transaction_totals_by_year_applies_year_filters(seed_cache):
    result = queries.transaction_totals_by_year(year_from=2023, year_to=2024)

    assert result.structuredContent["table"][-1] == [2024, "Disbursement", "USD", "750.00"]
    assert all(row[0] == 2024 for row in result.structuredContent["table"][1:])
    text = _text(result)

    assert "Total results: 2" in text
    assert "Records shown: 2" in text
    assert (
        "Applied filters: year_from=2023, year_to=2024"
        in text
    )
    assert "Applied limit:" not in text


def test_transaction_totals_by_year_rejects_invalid_range(seed_cache):
    result = queries.transaction_totals_by_year(year_from=2025, year_to=2024)

    assert result.content[0].text == (
        "The year_from value cannot be greater than year_to."
    )
    assert "table" not in result.structuredContent
    _assert_data_source_only(
        result,
        seed_cache.source,
    )
    assert "=== Query details ===" not in _text(result)


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
    _assert_data_and_glossary_sources(
        result,
        seed_cache.source,
    )

    text = result.content[0].text
    assert "Found 3 transaction(s)" in text
    assert "Total results: 3" in text
    assert "Records shown: 3" in text
    assert (
        "Applied filters: iati_identifier=IATI-001"
        in text
    )
    assert "Applied limit: 50" in text


def test_activity_transactions_reports_truncated_results(
    seed_cache,
):
    result = queries.activity_transactions(
        "IATI-001",
        limit=2,
    )
    text = _text(result)

    assert "Found 3 transaction(s)" in text
    assert "Total results: 3" in text
    assert "Records shown: 2" in text
    assert (
        "Applied filters: iati_identifier=IATI-001"
        in text
    )
    assert "Applied limit: 2" in text
    assert len(result.structuredContent["table"]) == 3


def test_activity_transactions_rejects_blank_identifier(
    seed_cache,
):
    result = queries.activity_transactions("   ")

    assert _text(result) == (
        "An IATI activity identifier is required."
    )
    assert "table" not in result.structuredContent
    assert "=== Query details ===" not in _text(result)
    _assert_data_source_only(
        result,
        seed_cache.source,
    )


def test_activity_transactions_rejects_invalid_limit(
    seed_cache,
):
    result = queries.activity_transactions(
        "IATI-001",
        limit=0,
    )

    assert _text(result) == (
        "The result limit must be greater than zero."
    )
    assert "table" not in result.structuredContent
    assert "=== Query details ===" not in _text(result)
    _assert_data_source_only(
        result,
        seed_cache.source,
    )


def test_activity_transactions_rejects_unknown_activity(seed_cache):
    result = queries.activity_transactions("UNKNOWN")

    assert result.content[0].text == (
        "No IATI activity found with identifier 'UNKNOWN'."
    )
    assert "table" not in result.structuredContent
    _assert_data_source_only(
        result,
        seed_cache.source,
    )
    assert "=== Query details ===" not in _text(result)


def test_transaction_totals_by_organisation_groups_by_org_type_and_currency(
    seed_cache,
    monkeypatch,
):
    activities = pd.DataFrame([
        {
            "activity_identifier": "IATI-001",
            "reporting_org_name": "Development Bank",
            "reporting_org_ref": "ORG-001",
            "default_currency": "USD",
        },
        {
            "activity_identifier": "IATI-002",
            "reporting_org_name": "",
            "reporting_org_ref": "ORG-002",
            "default_currency": "EUR",
        },
        {
            "activity_identifier": "IATI-003",
            "reporting_org_name": "",
            "reporting_org_ref": "",
            "default_currency": "USD",
        },
    ])
    transactions = pd.DataFrame([
        {
            "activity_identifier": "IATI-001",
            "transaction_type": "2",
            "value": 1500.0,
            "currency": "USD",
        },
        {
            "activity_identifier": "IATI-001",
            "transaction_type": "2",
            "value": 100.0,
            "currency": "",
        },
        {
            "activity_identifier": "IATI-001",
            "transaction_type": "2",
            "value": 200.0,
            "currency": "EUR",
        },
        {
            "activity_identifier": "IATI-001",
            "transaction_type": "3",
            "value": 750.0,
            "currency": "USD",
        },
        {
            "activity_identifier": "IATI-002",
            "transaction_type": "2",
            "value": 300.0,
            "currency": "",
        },
        {
            "activity_identifier": "IATI-003",
            "transaction_type": "2",
            "value": 500.0,
            "currency": "",
        },
        {
            "activity_identifier": "IATI-001",
            "transaction_type": "4",
            "value": 999.0,
            "currency": "USD",
        },
        {
            "activity_identifier": "IATI-001",
            "transaction_type": "2",
            "value": "not-a-number",
            "currency": "USD",
        },
    ])
    data._cache["dataframe:activities"] = activities
    data._cache["dataframe:transactions"] = transactions

    result = queries.transaction_totals_by_organisation()

    assert result.structuredContent["table"] == [
        [
            "Organisation reference",
            "Reporting organisation",
            "Transaction type",
            "Currency",
            "Total",
        ],
        ["ORG-001", "Development Bank", "Out Commitment", "EUR", "200.00"],
        ["ORG-001", "Development Bank", "Out Commitment", "USD", "1,600.00"],
        ["ORG-001", "Development Bank", "Disbursement", "USD", "750.00"],
        ["ORG-002", "ORG-002", "Out Commitment", "EUR", "300.00"],
        ["", "Unknown reporting organisation", "Out Commitment", "USD", "500.00"],
    ]
    _assert_data_and_glossary_sources(
        result,
        seed_cache.source,
    )

    text = result.content[0].text
    assert "Found 5 organisation transaction total(s)." in text
    assert "ORG-001 | Development Bank | Out Commitment | USD | 1,600.00" in text
    assert "ORG-002 | ORG-002 | Out Commitment | EUR | 300.00" in text
    assert "Unknown reporting organisation" in text
    assert "This does not necessarily imply" in text
    assert "=== Query details ===" in text
    assert "Total results: 5" in text
    assert "Records shown: 5" in text
    assert "Applied filters:" not in text
    assert "Applied limit: 50" in text


def test_transaction_totals_by_organisation_reports_applied_limit(
    seed_cache,
):
    result = queries.transaction_totals_by_organisation(limit=1)
    text = _text(result)

    assert "Records shown: 1" in text
    assert "Applied limit: 1" in text
    assert len(result.structuredContent["table"]) == 2

    total_line = next(
        line
        for line in text.splitlines()
        if line.startswith("Total results:")
    )
    total = int(total_line.removeprefix("Total results:").strip())

    assert total >= 1


def test_transaction_totals_by_organisation_rejects_invalid_limit(seed_cache):
    result = queries.transaction_totals_by_organisation(limit=0)

    assert result.content[0].text == (
        "The result limit must be greater than zero."
    )
    assert "table" not in result.structuredContent
    _assert_data_source_only(
        result,
        seed_cache.source,
    )
    assert "=== Query details ===" not in _text(result)


def test_sector_allocations_over_100_become_unallocated():
    sectors = pd.DataFrame([
        {
            "activity_identifier": "IATI-001",
            "sector_code": "111",
            "sector_name": "Transport",
            "vocabulary": "1",
            "percentage": 70,
        },
        {
            "activity_identifier": "IATI-001",
            "sector_code": "112",
            "sector_name": "Health",
            "vocabulary": "1",
            "percentage": 50,
        },
    ])

    allocations = queries._sector_allocations(sectors)

    assert allocations.to_dict("records") == [{
        "activity_identifier": "IATI-001",
        "vocabulary": "1",
        "sector_code": "",
        "sector_name": "Unallocated sector",
        "allocation_percentage": 100.0,
    }]


def test_transaction_totals_by_sector_keeps_activities_without_sectors(
    seed_cache,
):
    data._cache["dataframe:activities"] = pd.DataFrame([
        {
            "activity_identifier": "IATI-001",
            "default_currency": "USD",
        },
    ])
    data._cache["dataframe:transactions"] = pd.DataFrame([
        {
            "activity_identifier": "IATI-001",
            "transaction_type": "2",
            "value": 1000.0,
            "currency": "USD",
        },
    ])
    data._cache["dataframe:sectors"] = pd.DataFrame(
        columns=[
            "activity_identifier",
            "sector_code",
            "sector_name",
            "vocabulary",
            "percentage",
        ]
    )

    result = queries.transaction_totals_by_sector("commitment")
    table = result.structuredContent["table"]

    assert table[1] == [
        "Unknown",
        "",
        "Unallocated sector",
        "Out Commitment",
        "USD",
        "1,000.00",
    ]


def test_transaction_totals_by_sector_allocates_percentages_and_unallocated_share(
    seed_cache,
):
    data._cache["dataframe:activities"] = pd.DataFrame([
        {
            "activity_identifier": "IATI-001",
            "default_currency": "USD",
        },
    ])
    data._cache["dataframe:transactions"] = pd.DataFrame([
        {
            "activity_identifier": "IATI-001",
            "transaction_type": "2",
            "value": 1000.0,
            "currency": "USD",
        },
    ])
    data._cache["dataframe:sectors"] = pd.DataFrame([
        {
            "activity_identifier": "IATI-001",
            "sector_code": "111",
            "sector_name": "Transport",
            "vocabulary": "1",
            "percentage": 60,
        },
        {
            "activity_identifier": "IATI-001",
            "sector_code": "112",
            "sector_name": "Health",
            "vocabulary": "1",
            "percentage": 30,
        },
    ])

    result = queries.transaction_totals_by_sector(transaction_type="commitment")
    table = result.structuredContent["table"]

    assert table[1][-1] == "600.00"
    assert table[2][-1] == "300.00"
    assert table[3][-1] == "100.00"
    assert table[3][2] == "Unallocated sector"
    assert "Transaction amounts are allocated using the published sector percentages." in _text(result)
    text = _text(result)
    assert "Total results: 3" in text
    assert "Records shown: 3" in text
    assert "Applied filters: transaction_type=2" in text
    assert "Applied limit: 50" in text

    # Test that the limit is applied to the number of rows shown, but the total count is preserved.
    limited_result = queries.transaction_totals_by_sector(
        transaction_type="commitment",
        limit=2,
    )
    limited_text = _text(limited_result)

    assert "Total results: 3" in limited_text
    assert "Records shown: 2" in limited_text
    assert "Applied filters: transaction_type=2" in limited_text
    assert "Applied limit: 2" in limited_text
    assert len(limited_result.structuredContent["table"]) == 3

def test_transaction_totals_by_sector_treats_single_unpercentaged_sector_as_100(
    seed_cache,
):
    data._cache["dataframe:activities"] = pd.DataFrame([
        {
            "activity_identifier": "IATI-001",
            "default_currency": "USD",
        },
    ])
    data._cache["dataframe:transactions"] = pd.DataFrame([
        {
            "activity_identifier": "IATI-001",
            "transaction_type": "2",
            "value": 1000.0,
            "currency": "USD",
        },
    ])
    data._cache["dataframe:sectors"] = pd.DataFrame([
        {
            "activity_identifier": "IATI-001",
            "sector_code": "111",
            "sector_name": "Transport",
            "vocabulary": "1",
            "percentage": None,
        },
    ])

    result = queries.transaction_totals_by_sector(transaction_type="commitment")

    assert result.structuredContent["table"][1][-1] == "1,000.00"
    assert result.structuredContent["table"][1][2] == "Transport"


def test_transaction_totals_by_sector_separates_vocabularies_and_currencies(
    seed_cache,
):
    data._cache["dataframe:activities"] = pd.DataFrame([
        {
            "activity_identifier": "IATI-001",
            "default_currency": "USD",
        },
        {
            "activity_identifier": "IATI-002",
            "default_currency": "EUR",
        },
    ])
    data._cache["dataframe:transactions"] = pd.DataFrame([
        {
            "activity_identifier": "IATI-001",
            "transaction_type": "2",
            "value": 1000.0,
            "currency": "USD",
        },
        {
            "activity_identifier": "IATI-002",
            "transaction_type": "2",
            "value": 500.0,
            "currency": "EUR",
        },
        {
            "activity_identifier": "IATI-001",
            "transaction_type": "3",
            "value": 250.0,
            "currency": "USD",
        },
    ])
    data._cache["dataframe:sectors"] = pd.DataFrame([
        {
            "activity_identifier": "IATI-001",
            "sector_code": "111",
            "sector_name": "Transport",
            "vocabulary": "1",
            "percentage": 100,
        },
        {
            "activity_identifier": "IATI-002",
            "sector_code": "112",
            "sector_name": "Health",
            "vocabulary": "2",
            "percentage": 100,
        },
    ])

    result = queries.transaction_totals_by_sector(
        transaction_type="commitment",
        currency="USD",
        vocabulary="1",
    )
    table = result.structuredContent["table"]

    assert table[1][0] == "1"
    assert table[1][4] == "USD"
    assert table[1][5] == "1,000.00"
    text = _text(result)

    assert "Total results: 1" in text
    assert "Records shown: 1" in text
    assert (
        "Applied filters: transaction_type=2, "
        "currency=USD, vocabulary=1"
        in text
    )
    assert "Applied limit: 50" in text


def test_transaction_totals_by_sector_rejects_blank_currency(
    seed_cache,
):
    result = queries.transaction_totals_by_sector(currency="   ")

    assert _text(result) == (
        "Currency cannot be empty when provided."
    )
    assert "table" not in result.structuredContent
    assert "=== Query details ===" not in _text(result)
    _assert_data_source_only(
        result,
        seed_cache.source,
    )


def test_transaction_totals_by_sector_rejects_invalid_transaction_type(seed_cache):
    result = queries.transaction_totals_by_sector(transaction_type="invalid")

    assert result.content[0].text == (
        "Unsupported transaction type. Use commitment, disbursement, 2 or 3."
    )
    assert "table" not in result.structuredContent
    _assert_data_source_only(
        result,
        seed_cache.source,
    )


def test_transaction_totals_by_sector_rejects_invalid_limit(seed_cache):
    result = queries.transaction_totals_by_sector(limit=0)

    assert result.content[0].text == (
        "The result limit must be greater than zero."
    )
    assert "table" not in result.structuredContent
    _assert_data_source_only(
        result,
        seed_cache.source,
    )


def test_transaction_totals_by_country_groups_by_country_and_currency(
    seed_cache,
):
    data._cache["dataframe:activities"] = pd.DataFrame([
        {
            "activity_identifier": "IATI-001",
            "recipient_country_name": "Argentina",
            "recipient_country_code": "AR",
            "default_currency": "USD",
        },
        {
            "activity_identifier": "IATI-002",
            "recipient_country_name": "Brazil",
            "recipient_country_code": "BR",
            "default_currency": "EUR",
        },
        {
            "activity_identifier": "IATI-003",
            "recipient_country_name": "",
            "recipient_country_code": "",
            "default_currency": "USD",
        },
    ])
    data._cache["dataframe:transactions"] = pd.DataFrame([
        {
            "activity_identifier": "IATI-001",
            "transaction_type": "2",
            "value": 1000.0,
            "currency": "USD",
        },
        {
            "activity_identifier": "IATI-001",
            "transaction_type": "2",
            "value": 200.0,
            "currency": "EUR",
        },
        {
            "activity_identifier": "IATI-002",
            "transaction_type": "2",
            "value": 300.0,
            "currency": "EUR",
        },
        {
            "activity_identifier": "IATI-003",
            "transaction_type": "2",
            "value": 500.0,
            "currency": "USD",
        },
        {
            "activity_identifier": "IATI-001",
            "transaction_type": "3",
            "value": 50.0,
            "currency": "USD",
        },
    ])

    result = queries.transaction_totals_by_country(transaction_type="commitment")

    assert result.structuredContent["table"] == [
        [
            "Country code",
            "Recipient country",
            "Transaction type",
            "Currency",
            "Total",
        ],
        ["BR", "Brazil", "Out Commitment", "EUR", "300.00"],
        ["AR", "Argentina", "Out Commitment", "EUR", "200.00"],
        ["AR", "Argentina", "Out Commitment", "USD", "1,000.00"],
        ["", "Unknown recipient country", "Out Commitment", "USD", "500.00"],
    ]
    _assert_data_and_glossary_sources(
        result,
        seed_cache.source,
    )
    assert "Found 4 country transaction total(s)." in _text(result)


def test_transaction_totals_by_country_filters_by_currency_and_uses_default_currency(
    seed_cache,
):
    data._cache["dataframe:activities"] = pd.DataFrame([
        {
            "activity_identifier": "IATI-001",
            "recipient_country_name": "Argentina",
            "recipient_country_code": "AR",
            "default_currency": "USD",
        },
        {
            "activity_identifier": "IATI-002",
            "recipient_country_name": "Brazil",
            "recipient_country_code": "BR",
            "default_currency": "EUR",
        },
    ])
    data._cache["dataframe:transactions"] = pd.DataFrame([
        {
            "activity_identifier": "IATI-001",
            "transaction_type": "2",
            "value": 1000.0,
            "currency": "USD",
        },
        {
            "activity_identifier": "IATI-002",
            "transaction_type": "2",
            "value": 300.0,
            "currency": "",
        },
    ])

    result = queries.transaction_totals_by_country(
        transaction_type="commitment",
        currency="EUR",
    )

    assert result.structuredContent["table"][1][0] == "BR"
    assert result.structuredContent["table"][1][-2] == "EUR"
    assert result.structuredContent["table"][1][-1] == "300.00"


def test_transaction_totals_by_country_rejects_invalid_transaction_type(
    seed_cache,
):
    result = queries.transaction_totals_by_country(transaction_type="invalid")

    assert result.content[0].text == (
        "Unsupported transaction type. Use commitment, disbursement, 2 or 3."
    )
    assert "table" not in result.structuredContent
    _assert_data_source_only(
        result,
        seed_cache.source,
    )


@pytest.mark.parametrize(
    "transaction_type",
    ["2", "commitment", "out commitment"],
)
def test_top_activities_accepts_commitment_aliases(
    seed_cache,
    transaction_type,
):
    result = queries.top_activities_by_amount(transaction_type)
    table = result.structuredContent["table"]

    assert table[0][-3:] == [
        "Transaction type",
        "Currency",
        "Total",
    ]
    assert table[1][0] == "IATI-001"
    assert table[1][-3:] == [
        "Out Commitment",
        "USD",
        "1,500.00",
    ]
    _assert_data_and_glossary_sources(
        result,
        seed_cache.source,
    )


@pytest.mark.parametrize(
    "transaction_type",
    ["3", "disbursement"],
)
def test_top_activities_accepts_disbursement_aliases(
    seed_cache,
    transaction_type,
):
    result = queries.top_activities_by_amount(transaction_type)

    assert result.structuredContent["table"][1][-3:] == [
        "Disbursement",
        "USD",
        "750.00",
    ]


def test_top_activities_keeps_currencies_separate_and_sorted(seed_cache):
    data._cache["dataframe:activities"] = pd.DataFrame([
        {
            "activity_identifier": "IATI-001",
            "title": "Alpha",
            "reporting_org_name": "Org A",
            "reporting_org_ref": "ORG-A",
            "recipient_country_name": "Argentina",
            "recipient_country_code": "AR",
            "default_currency": "USD",
        },
        {
            "activity_identifier": "IATI-002",
            "title": "Beta",
            "reporting_org_name": "Org B",
            "reporting_org_ref": "ORG-B",
            "recipient_country_name": "Brazil",
            "recipient_country_code": "BR",
            "default_currency": "EUR",
        },
        {
            "activity_identifier": "IATI-003",
            "title": "Gamma",
            "reporting_org_name": "Org C",
            "reporting_org_ref": "ORG-C",
            "recipient_country_name": "Chile",
            "recipient_country_code": "CL",
            "default_currency": "USD",
        },
    ])
    data._cache["dataframe:transactions"] = pd.DataFrame([
        {
            "activity_identifier": "IATI-001",
            "transaction_type": "2",
            "value": 1000.0,
            "currency": "USD",
        },
        {
            "activity_identifier": "IATI-003",
            "transaction_type": "2",
            "value": 500.0,
            "currency": "USD",
        },
        {
            "activity_identifier": "IATI-002",
            "transaction_type": "2",
            "value": 300.0,
            "currency": "EUR",
        },
    ])

    result = queries.top_activities_by_amount(transaction_type="commitment")
    table = result.structuredContent["table"]

    assert table[1][-3:] == ["Out Commitment", "EUR", "300.00"]
    assert table[2][-3:] == ["Out Commitment", "USD", "1,000.00"]
    assert table[3][-3:] == ["Out Commitment", "USD", "500.00"]


def test_top_activities_filters_by_currency(seed_cache):
    data._cache["dataframe:activities"] = pd.DataFrame([
        {
            "activity_identifier": "IATI-001",
            "title": "Alpha",
            "reporting_org_name": "Org A",
            "reporting_org_ref": "ORG-A",
            "recipient_country_name": "Argentina",
            "recipient_country_code": "AR",
            "default_currency": "USD",
        },
        {
            "activity_identifier": "IATI-002",
            "title": "Beta",
            "reporting_org_name": "Org B",
            "reporting_org_ref": "ORG-B",
            "recipient_country_name": "Brazil",
            "recipient_country_code": "BR",
            "default_currency": "EUR",
        },
    ])
    data._cache["dataframe:transactions"] = pd.DataFrame([
        {
            "activity_identifier": "IATI-001",
            "transaction_type": "2",
            "value": 1000.0,
            "currency": "USD",
        },
        {
            "activity_identifier": "IATI-002",
            "transaction_type": "2",
            "value": 300.0,
            "currency": "EUR",
        },
    ])

    result = queries.top_activities_by_amount(
        transaction_type="commitment",
        currency="USD",
    )

    assert all(row[-2] == "USD" for row in result.structuredContent["table"][1:])
    assert result.structuredContent["table"][1][0] == "IATI-001"


def test_top_activities_uses_default_currency_when_missing(seed_cache):
    data._cache["dataframe:activities"] = pd.DataFrame([
        {
            "activity_identifier": "IATI-001",
            "title": "Alpha",
            "reporting_org_name": "Org A",
            "reporting_org_ref": "ORG-A",
            "recipient_country_name": "Argentina",
            "recipient_country_code": "AR",
            "default_currency": "USD",
        },
        {
            "activity_identifier": "IATI-002",
            "title": "Beta",
            "reporting_org_name": "Org B",
            "reporting_org_ref": "ORG-B",
            "recipient_country_name": "Brazil",
            "recipient_country_code": "BR",
            "default_currency": "EUR",
        },
    ])
    data._cache["dataframe:transactions"] = pd.DataFrame([
        {
            "activity_identifier": "IATI-002",
            "transaction_type": "2",
            "value": 300.0,
            "currency": "",
        },
    ])

    result = queries.top_activities_by_amount(
        transaction_type="commitment",
        currency="EUR",
    )

    assert result.structuredContent["table"][1][0] == "IATI-002"
    assert result.structuredContent["table"][1][-2] == "EUR"


def test_top_activities_rejects_invalid_transaction_type(seed_cache):
    result = queries.top_activities_by_amount(transaction_type="invalid")

    assert result.content[0].text == (
        "Unsupported transaction type. Use commitment, disbursement, 2 or 3."
    )
    assert "table" not in result.structuredContent
    _assert_data_source_only(
        result,
        seed_cache.source,
    )


def test_top_activities_rejects_invalid_limit(seed_cache):
    result = queries.top_activities_by_amount(limit=0)

    assert result.content[0].text == (
        "The result limit must be greater than zero."
    )
    assert "table" not in result.structuredContent
    _assert_data_source_only(
        result,
        seed_cache.source,
    )


def test_top_activities_uses_org_ref_and_unknown_fallbacks(seed_cache):
    data._cache["dataframe:activities"] = pd.DataFrame([
        {
            "activity_identifier": "IATI-001",
            "title": "Alpha",
            "reporting_org_name": "Development Bank",
            "reporting_org_ref": "ORG-001",
            "recipient_country_name": "Argentina",
            "recipient_country_code": "AR",
            "default_currency": "USD",
        },
        {
            "activity_identifier": "IATI-002",
            "title": "Beta",
            "reporting_org_name": "",
            "reporting_org_ref": "ORG-002",
            "recipient_country_name": "Brazil",
            "recipient_country_code": "BR",
            "default_currency": "EUR",
        },
        {
            "activity_identifier": "IATI-003",
            "title": "Gamma",
            "reporting_org_name": "",
            "reporting_org_ref": "",
            "recipient_country_name": "",
            "recipient_country_code": "",
            "default_currency": "USD",
        },
    ])
    data._cache["dataframe:transactions"] = pd.DataFrame([
        {
            "activity_identifier": "IATI-001",
            "transaction_type": "2",
            "value": 1000.0,
            "currency": "USD",
        },
        {
            "activity_identifier": "IATI-002",
            "transaction_type": "2",
            "value": 300.0,
            "currency": "EUR",
        },
        {
            "activity_identifier": "IATI-003",
            "transaction_type": "2",
            "value": 500.0,
            "currency": "USD",
        },
    ])

    result = queries.top_activities_by_amount(transaction_type="commitment")

    assert "Development Bank" in _text(result)
    assert "ORG-002" in _text(result)
    assert "Unknown reporting organisation" in _text(result)


def test_top_activities_uses_country_code_fallback(seed_cache):
    data._cache["dataframe:activities"] = pd.DataFrame([
        {
            "activity_identifier": "IATI-001",
            "title": "Alpha",
            "reporting_org_name": "Development Bank",
            "reporting_org_ref": "ORG-001",
            "recipient_country_name": "",
            "recipient_country_code": "BR",
            "default_currency": "USD",
        },
        {
            "activity_identifier": "IATI-002",
            "title": "Beta",
            "reporting_org_name": "Org B",
            "reporting_org_ref": "ORG-B",
            "recipient_country_name": "",
            "recipient_country_code": "",
            "default_currency": "EUR",
        },
    ])
    data._cache["dataframe:transactions"] = pd.DataFrame([
        {
            "activity_identifier": "IATI-001",
            "transaction_type": "2",
            "value": 1000.0,
            "currency": "USD",
        },
        {
            "activity_identifier": "IATI-002",
            "transaction_type": "2",
            "value": 300.0,
            "currency": "EUR",
        },
    ])

    result = queries.top_activities_by_amount(transaction_type="commitment")

    assert "BR" in _text(result)
    assert "Unknown" in _text(result)
    table = result.structuredContent["table"]

    assert all(
        str(cell).strip().lower() != "nan"
        for row in table
        for cell in row
    )
