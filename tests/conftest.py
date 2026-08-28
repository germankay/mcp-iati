"""
Test fixtures for the IATI tools.

`seed_cache` preloads the shared pandas DataFrame cache with synthetic data.
This avoids network access and XML-to-CSV conversion during query tests.

The cached DataFrames use the same `dataframe:<table>` keys as the production
data loader.

`fake_mcp` is a test double of the mcp-server registry that captures plugin
information and registered tools.
"""

from types import SimpleNamespace

import mcp_iati
import pandas as pd
import pytest

from mcp_iati.activities import data as data_mod


# Fictitious local path: xml_source() returns it as-is and queries report it
# as their source.
FAKE_XML = "/data/fake-iati-sample.xml"


def _activities_df():
    return pd.DataFrame(
        [
            {
                "activity_identifier": "IATI-001",
                "title": "Sustainable transport programme",
                "activity_status": "2",
                "reporting_org_name": "Development Bank",
                "reporting_org_ref": "ORG-001",
                "default_currency": "USD",
                "recipient_country_code": "AR",
                "recipient_country_name": "Argentina",
            },
            {
                "activity_identifier": "IATI-002",
                "title": "Health programme",
                "activity_status": "3",
                "reporting_org_name": "",
                "reporting_org_ref": "ORG-002",
                "default_currency": "USD",
                "recipient_country_code": "BR",
                "recipient_country_name": "Brazil",
            },
        ]
    )


def _transactions_df():
    return pd.DataFrame(
        [
            {
                "activity_identifier": "IATI-001",
                "transaction_type": "2",
                "transaction_date": "2024-01-10",
                "value": 1000.0,
                "currency": "USD",
                "description": "Initial commitment",
            },
            {
                "activity_identifier": "IATI-001",
                "transaction_type": "2",
                "transaction_date": "2024-02-10",
                "value": 500.0,
                "currency": "USD",
                "description": "Additional commitment",
            },
            {
                "activity_identifier": "IATI-001",
                "transaction_type": "3",
                "transaction_date": "2024-03-10",
                "value": 750.0,
                "currency": "USD",
                "description": "First disbursement",
            },
        ]
    )


@pytest.fixture
def seed_cache(monkeypatch):
    """Preload shared DataFrames and clear them after the test."""
    if hasattr(data_mod.get_settings, "cache_clear"):
        data_mod.get_settings.cache_clear()

    monkeypatch.setenv("MCP_IATI_XML_PATH", FAKE_XML)

    data_mod._cache.clear()
    data_mod._cache["dataframe:activities"] = _activities_df()
    data_mod._cache["dataframe:transactions"] = _transactions_df()
    data_mod._cache["dataframe:sectors"] = _sectors_df()

    yield SimpleNamespace(
        source=FAKE_XML,
        activities=data_mod._cache["dataframe:activities"],
        transactions=data_mod._cache["dataframe:transactions"],
        sectors=data_mod._cache["dataframe:sectors"],
    )

    data_mod._cache.clear()

    if hasattr(data_mod.get_settings, "cache_clear"):
        data_mod.get_settings.cache_clear()


class FakeMCP:
    def __init__(self):
        self.plugin_info = None
        self.tools = {}

    def set_plugin_info(self, **kwargs):
        self.plugin_info = kwargs

    def tool(self):
        def decorator(func):
            self.tools[func.__name__] = func
            return func

        return decorator


@pytest.fixture
def fake_mcp(monkeypatch, tmp_path):
    """Return an MCP registry without preparing real IATI data."""
    monkeypatch.setattr(
        mcp_iati,
        "prepare_data",
        lambda: tmp_path,
    )
    return FakeMCP()


def _sectors_df():
    return pd.DataFrame(
        [
            {
                "activity_identifier": "IATI-001",
                "sector_code": "TR",
                "sector_name": "Transport",
                "vocabulary": "99",
                "percentage": 100.0,
            },
            {
                "activity_identifier": "IATI-002",
                "sector_code": "12220",
                "sector_name": "Basic health care",
                "vocabulary": "1",
                "percentage": 100.0,
            },
        ]
    )
