from pathlib import Path
from types import SimpleNamespace

from mcp_iati.activities import data


def test_local_path_keeps_priority_over_url_and_sample(monkeypatch):
    local_path = Path("/data/local.xml")
    settings = SimpleNamespace(
        xml_path=local_path,
        xml_url="https://example.org/remote.xml",
        sample="iadb-Argentina.xml",
    )
    monkeypatch.setattr(data, "get_settings", lambda: settings)

    assert data.xml_path() == local_path


def test_custom_url_has_priority_over_sample(monkeypatch):
    downloaded_path = Path("/data/downloaded.xml")
    settings = SimpleNamespace(
        xml_path=None,
        xml_url="https://example.org/remote.xml",
        sample="iadb-Argentina.xml",
    )
    monkeypatch.setattr(data, "get_settings", lambda: settings)
    monkeypatch.setattr(
        data,
        "_download_configured_url",
        lambda url: downloaded_path,
    )

    assert data.xml_path() == downloaded_path


def test_sample_download_is_preserved_as_fallback(monkeypatch):
    downloaded_path = Path("/data/iadb-Brazil.xml")
    settings = SimpleNamespace(
        xml_path=None,
        xml_url=None,
        sample="iadb-Brazil.xml",
    )
    monkeypatch.setattr(data, "get_settings", lambda: settings)
    monkeypatch.setattr(
        data,
        "_download_sample",
        lambda sample: downloaded_path,
    )

    assert data.xml_path() == downloaded_path


def test_custom_urls_generate_source_specific_names(monkeypatch):
    first_url = "https://one.example.org/activities.xml"
    second_url = "https://two.example.org/activities.xml"
    filenames = []
    monkeypatch.setattr(
        data,
        "_download_xml",
        lambda url, filename: filenames.append(filename) or Path(filename),
    )

    data._download_configured_url(first_url)
    data._download_configured_url(second_url)

    assert filenames[0] != filenames[1]
    assert filenames[0].endswith("-activities.xml")
    assert filenames[1].endswith("-activities.xml")
