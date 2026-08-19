import pytest

import mcp_iati
from mcp_iati.activities import data


def test_prepare_data_returns_valid_csv_folder(monkeypatch, tmp_path):
    folder = tmp_path / "csv"
    folder.mkdir()
    (folder / "activities.csv").write_text("id\n1\n")
    (folder / "transactions.csv").write_text("id\n1\n")
    (folder / "locations.csv").write_text("id\n1\n")

    monkeypatch.setattr(data, "_csv_folder", lambda: folder)
    monkeypatch.setattr(
        data,
        "xml_source",
        lambda: "https://example.org/iati.xml",
    )

    assert data.prepare_data() == folder


@pytest.mark.parametrize(
    "missing_filename",
    [
        "activities.csv",
        "transactions.csv",
    ],
)
def test_prepare_data_rejects_missing_required_csv(
    monkeypatch,
    tmp_path,
    missing_filename,
):
    folder = tmp_path / "csv"
    folder.mkdir()

    for filename in data.REQUIRED_TOOL_CSVS:
        if filename != missing_filename:
            (folder / filename).write_text("id\n1\n")

    monkeypatch.setattr(data, "_csv_folder", lambda: folder)
    monkeypatch.setattr(
        data,
        "xml_source",
        lambda: "https://example.org/iati.xml",
    )

    with pytest.raises(RuntimeError, match=missing_filename):
        data.prepare_data()


def test_prepare_data_reports_download_or_conversion_error(
    monkeypatch,
):
    def fail():
        raise RuntimeError("conversion failed")

    monkeypatch.setattr(data, "_csv_folder", fail)
    monkeypatch.setattr(
        data,
        "xml_source",
        lambda: "https://example.org/iati.xml",
    )

    with pytest.raises(
        RuntimeError,
        match="Could not prepare IATI data.*conversion failed",
    ):
        data.prepare_data()


def test_register_tools_prepares_data_before_registration(
    monkeypatch,
):
    events = []

    monkeypatch.setattr(
        mcp_iati,
        "prepare_data",
        lambda: events.append("prepare"),
    )
    monkeypatch.setattr(
        mcp_iati,
        "_register_iati_tools",
        lambda mcp: events.append("register"),
    )

    mcp_iati.register_tools(object())

    assert events == ["prepare", "register"]
