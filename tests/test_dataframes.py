from types import SimpleNamespace
from pathlib import Path

import pandas as pd
import pytest

from mcp_iati.activities import data as data_mod


@pytest.fixture(autouse=True)
def clear_data_cache(monkeypatch):
    original_get_settings = data_mod.get_settings
    if hasattr(original_get_settings, "cache_clear"):
        original_get_settings.cache_clear()

    data_mod._cache.clear()
    monkeypatch.setenv("MCP_IATI_XML_PATH", "/tmp/fake-iati.xml")
    yield
    data_mod._cache.clear()
    if hasattr(original_get_settings, "cache_clear"):
        original_get_settings.cache_clear()


def _write_csv(folder: Path, filename: str, dataframe: pd.DataFrame) -> Path:
    path = folder / filename
    dataframe.to_csv(path, index=False)
    return path


def test_dataframes_are_loaded_once_and_reused(tmp_path, monkeypatch):
    _write_csv(
        tmp_path,
        "activities.csv",
        pd.DataFrame(
            [
                {
                    "activity_identifier": "IATI-001",
                    "title": "Health programme",
                    "activity_status": "2",
                    "reporting_org_name": "Development Bank",
                    "reporting_org_ref": "ORG-001",
                    "default_currency": "USD",
                }
            ]
        ),
    )
    _write_csv(
        tmp_path,
        "transactions.csv",
        pd.DataFrame(
            [
                {
                    "activity_identifier": "IATI-001",
                    "transaction_type": "2",
                    "value": "1000",
                }
            ]
        ),
    )
    monkeypatch.setattr(data_mod, "_csv_folder", lambda: tmp_path)

    read_calls = []
    original_read_csv = data_mod.pd.read_csv

    def counting_read_csv(path, *args, **kwargs):
        read_calls.append(Path(path).name)
        return original_read_csv(path, *args, **kwargs)

    monkeypatch.setattr(data_mod.pd, "read_csv", counting_read_csv)

    first_activities = data_mod.activities_df()
    second_activities = data_mod.activities_df()
    first_transactions = data_mod.transactions_df()
    second_transactions = data_mod.transactions_df()

    assert first_activities is second_activities
    assert first_transactions is second_transactions
    assert read_calls.count("activities.csv") == 1
    assert read_calls.count("transactions.csv") == 1
    assert pd.api.types.is_numeric_dtype(first_transactions["value"])
    assert first_transactions.loc[0, "value"] == 1000.0


def test_missing_required_columns_raise_runtime_error(tmp_path, monkeypatch):
    _write_csv(
        tmp_path,
        "activities.csv",
        pd.DataFrame(
            [
                {
                    "activity_identifier": "IATI-001",
                    "title": "Health programme",
                }
            ]
        ),
    )
    _write_csv(
        tmp_path,
        "transactions.csv",
        pd.DataFrame(
            [
                {
                    "activity_identifier": "IATI-001",
                    "transaction_type": "2",
                    "value": "1000",
                }
            ]
        ),
    )
    monkeypatch.setattr(data_mod, "_csv_folder", lambda: tmp_path)

    with pytest.raises(RuntimeError, match="activities.csv is missing required columns: activity_status"):
        data_mod.activities_df()


def test_unknown_table_raises_value_error(tmp_path, monkeypatch):
    monkeypatch.setattr(data_mod, "_csv_folder", lambda: tmp_path)

    with pytest.raises(ValueError, match="Unknown IATI CSV table: unknown"):
        data_mod._dataframe("unknown")


def test_expired_cache_removes_dataframe_entries(monkeypatch, tmp_path):
    monkeypatch.setattr(data_mod, "_csv_cache_is_fresh", lambda *args, **kwargs: False)
    monkeypatch.setattr(
        data_mod,
        "get_settings",
        lambda: SimpleNamespace(xml_path=None),
    )

    data_mod._cache["dataframe:activities"] = pd.DataFrame({"a": [1]})
    data_mod._cache["dataframe:transactions"] = pd.DataFrame({"b": [2]})
    data_mod._cache["csv_folder"] = tmp_path

    data_mod._clear_expired_memory_cache()

    assert all(not key.startswith("dataframe:") for key in data_mod._cache)


def test_stale_fallback_remains_available_in_memory(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(
        data_mod,
        "_csv_cache_is_fresh",
        lambda *args, **kwargs: False,
    )
    monkeypatch.setattr(
        data_mod,
        "get_settings",
        lambda: SimpleNamespace(xml_path=None),
    )

    activities = pd.DataFrame({"activity_identifier": ["IATI-001"]})

    data_mod._cache["csv_folder"] = tmp_path
    data_mod._cache["dataframe:activities"] = activities
    data_mod._cache["using_stale_csv"] = True

    data_mod._clear_expired_memory_cache()

    assert data_mod._cache["csv_folder"] == tmp_path
    assert data_mod._cache["dataframe:activities"] is activities


def test_activities_and_transactions_can_be_joined_by_activity_identifier(tmp_path, monkeypatch):
    _write_csv(
        tmp_path,
        "activities.csv",
        pd.DataFrame(
            [
                {
                    "activity_identifier": "IATI-001",
                    "title": "Health programme",
                    "activity_status": "2",
                    "reporting_org_name": "Org 1",
                    "reporting_org_ref": "ORG-001",
                    "default_currency": "USD",
                },
                {
                    "activity_identifier": "IATI-002",
                    "title": "Water programme",
                    "activity_status": "3",
                    "reporting_org_name": "Org 2",
                    "reporting_org_ref": "ORG-002",
                    "default_currency": "EUR",
                }
            ]
        ),
    )
    _write_csv(
        tmp_path,
        "transactions.csv",
        pd.DataFrame(
            [
                {
                    "activity_identifier": "IATI-001",
                    "transaction_type": "2",
                    "value": "1000",
                },
                {
                    "activity_identifier": "IATI-001",
                    "transaction_type": "3",
                    "value": "250",
                },
            ]
        ),
    )
    monkeypatch.setattr(data_mod, "_csv_folder", lambda: tmp_path)

    activities = data_mod.activities_df()
    transactions = data_mod.transactions_df()

    joined = transactions.merge(
        activities[["activity_identifier", "title"]],
        on="activity_identifier",
        how="left",
    )

    assert joined["title"].tolist() == ["Health programme", "Health programme"]
    assert joined["activity_identifier"].tolist() == ["IATI-001", "IATI-001"]
