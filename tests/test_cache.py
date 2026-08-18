import os
import time
from types import SimpleNamespace

from mcp_iati.activities import data


def _settings(tmp_path, ttl=604800):
    return SimpleNamespace(
        xml_path=None,
        xml_url=None,
        sample="iadb-Brazil.xml",
        data_dir=tmp_path,
        cache_ttl_seconds=ttl,
        ensure_data_dir=lambda: tmp_path,
    )


def test_cache_is_fresh_inside_ttl(monkeypatch, tmp_path):
    cached_file = tmp_path / "source.xml"
    cached_file.write_text("<iati-activities />")
    monkeypatch.setattr(data, "get_settings", lambda: _settings(tmp_path))

    assert data._cache_is_fresh(cached_file) is True


def test_cache_expires_after_ttl(monkeypatch, tmp_path):
    cached_file = tmp_path / "source.xml"
    cached_file.write_text("<iati-activities />")
    expired_time = time.time() - 604801
    os.utime(cached_file, (expired_time, expired_time))
    monkeypatch.setattr(data, "get_settings", lambda: _settings(tmp_path))

    assert data._cache_is_fresh(cached_file) is False


def test_fresh_xml_is_not_downloaded_again(monkeypatch, tmp_path):
    settings = _settings(tmp_path)
    target = tmp_path / "xml" / "sample.xml"
    target.parent.mkdir(parents=True)
    target.write_text("<iati-activities />")
    monkeypatch.setattr(data, "get_settings", lambda: settings)
    monkeypatch.setattr(
        data.urllib.request,
        "urlopen",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("unexpected download")
        ),
    )

    assert data._download_xml("https://example.org/sample.xml", "sample.xml") == target


def test_expired_xml_is_downloaded_again(monkeypatch, tmp_path):
    settings = _settings(tmp_path, ttl=10)
    target = tmp_path / "xml" / "sample.xml"
    target.parent.mkdir(parents=True)
    target.write_text("old")
    expired_time = time.time() - 11
    os.utime(target, (expired_time, expired_time))
    monkeypatch.setattr(data, "get_settings", lambda: settings)

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self):
            return b"new"

    monkeypatch.setattr(
        data.urllib.request,
        "urlopen",
        lambda *args, **kwargs: Response(),
    )

    assert data._download_xml("https://example.org/sample.xml", "sample.xml") == target
    assert target.read_bytes() == b"new"


def test_csv_cache_requires_complete_fresh_files(monkeypatch, tmp_path):
    folder = tmp_path / "csv-cache"
    folder.mkdir()
    (folder / "activities.csv").write_text("id\n1\n")
    (folder / "transactions.csv").write_text("id\n1\n")
    (folder / ".complete").touch()
    monkeypatch.setattr(data, "get_settings", lambda: _settings(tmp_path))

    assert data._csv_cache_is_fresh(folder) is True


def test_different_origins_have_different_csv_cache_keys(monkeypatch, tmp_path):
    settings = _settings(tmp_path)
    settings.sample = "iadb-Argentina.xml"
    monkeypatch.setattr(data, "get_settings", lambda: settings)
    argentina_key = data._source_cache_key()

    settings.sample = "iadb-Brazil.xml"
    brazil_key = data._source_cache_key()

    assert argentina_key != brazil_key


def test_expired_disk_cache_clears_in_process_data(monkeypatch, tmp_path):
    folder = tmp_path / "csv-cache"
    folder.mkdir()
    (folder / "activities.csv").write_text("id\n1\n")
    (folder / "transactions.csv").write_text("id\n1\n")
    marker = folder / ".complete"
    marker.touch()
    expired_time = time.time() - 604801
    os.utime(marker, (expired_time, expired_time))
    monkeypatch.setattr(data, "get_settings", lambda: _settings(tmp_path))
    monkeypatch.setitem(data._cache, "csv_folder", folder)
    monkeypatch.setitem(data._cache, "activities", object())
    monkeypatch.setitem(data._cache, "transactions", object())

    data._clear_expired_memory_cache()

    assert "csv_folder" not in data._cache
    assert "activities" not in data._cache
    assert "transactions" not in data._cache
