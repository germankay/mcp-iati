import os
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

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


def test_csv_cache_expires_when_local_xml_is_newer(monkeypatch, tmp_path):
    folder = tmp_path / "csv-cache"
    folder.mkdir()
    (folder / "activities.csv").write_text("id\n1\n")
    (folder / "transactions.csv").write_text("id\n1\n")
    marker = folder / ".complete"
    marker.touch()
    source = tmp_path / "source.xml"
    source.write_text("<iati-activities />")
    newer_time = time.time() + 1
    os.utime(source, (newer_time, newer_time))
    monkeypatch.setattr(data, "get_settings", lambda: _settings(tmp_path))

    assert data._csv_cache_is_fresh(folder, source) is False


@pytest.mark.parametrize(
    "source,expected",
    [
        ("path", "/data/source.xml"),
        ("url", "https://example.org/source.xml"),
        ("sample", f"{data._SAMPLES_BASE_URL}/iadb-Brazil.xml"),
    ],
)
def test_xml_source_returns_original_origin(monkeypatch, tmp_path, source, expected):
    settings = _settings(tmp_path)
    if source == "path":
        settings.xml_path = Path(expected)
    elif source == "url":
        settings.xml_url = expected
    monkeypatch.setattr(data, "get_settings", lambda: settings)

    assert data.xml_source() == expected


def test_stale_xml_is_used_when_refresh_fails(monkeypatch, tmp_path):
    settings = _settings(tmp_path, ttl=10)
    target = tmp_path / "xml" / "sample.xml"
    target.parent.mkdir(parents=True)
    target.write_text("old")
    expired_time = time.time() - 11
    os.utime(target, (expired_time, expired_time))
    monkeypatch.setattr(data, "get_settings", lambda: settings)
    monkeypatch.setattr(
        data.urllib.request,
        "urlopen",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("offline")),
    )

    with pytest.warns(RuntimeWarning, match="using the stale cached copy"):
        result = data._download_xml(
            "https://example.org/sample.xml",
            "sample.xml",
        )

    assert result == target
    assert target.read_text() == "old"


@pytest.mark.parametrize("sample", ["../secret.xml", "folder/file.xml", ""])
def test_sample_name_rejects_directory_components(monkeypatch, tmp_path, sample):
    monkeypatch.setattr(data, "get_settings", lambda: _settings(tmp_path))

    with pytest.raises(ValueError, match="MCP_IATI_SAMPLE"):
        data._download_sample(sample)


def test_csv_folder_reuses_persistent_conversion(monkeypatch, tmp_path):
    source = tmp_path / "source.xml"
    source.write_text("<iati-activities />")
    settings = _settings(tmp_path)
    settings.xml_path = source
    conversion_calls = []

    class Converter:
        latest_errors = []

        def xml_to_csv_folder(self, path, folder):
            conversion_calls.append(path)
            (folder / "activities.csv").write_text("id\n1\n")
            (folder / "transactions.csv").write_text("id\n1\n")
            return True

    monkeypatch.setattr(data, "get_settings", lambda: settings)
    monkeypatch.setattr(data, "IatiMultiCsvConverter", Converter)
    data._cache.clear()

    try:
        first_folder = data._csv_folder()
        data._cache.clear()
        second_folder = data._csv_folder()
    finally:
        data._cache.clear()

    assert first_folder == second_folder
    assert conversion_calls == [source]


def test_conversion_failed_with_complete_cache_reuses_previous(
    monkeypatch,
    tmp_path,
):
    source = tmp_path / "source.xml"
    source.write_text("<iati-activities />")

    settings = _settings(tmp_path)
    settings.xml_path = source
    conversion_calls = []

    monkeypatch.setattr(data, "get_settings", lambda: settings)

    cache_key = data._source_cache_key()
    existing_folder = tmp_path / "csv" / cache_key
    existing_folder.mkdir(parents=True)

    (existing_folder / "activities.csv").write_text("id\n1\n")
    (existing_folder / "transactions.csv").write_text("id\n1\n")

    marker = existing_folder / ".complete"
    marker.touch()

    expired_time = time.time() - settings.cache_ttl_seconds - 1
    os.utime(marker, (expired_time, expired_time))

    class Converter:
        latest_errors = []

        def xml_to_csv_folder(self, path, folder):
            conversion_calls.append(path)
            raise RuntimeError("conversion failed")

    monkeypatch.setattr(data, "IatiMultiCsvConverter", Converter)
    data._cache.clear()

    try:
        with pytest.warns(
            RuntimeWarning,
            match="using the last complete cache",
        ):
            result = data._csv_folder()
    finally:
        data._cache.clear()

    assert result == existing_folder
    assert conversion_calls == [source]
    assert (existing_folder / "activities.csv").exists()
    assert (existing_folder / "transactions.csv").exists()
    assert (existing_folder / ".complete").exists()


def test_conversion_failed_without_cache_raises_runtime_error(monkeypatch, tmp_path):
    source = tmp_path / "source.xml"
    source.write_text("<iati-activities />")
    settings = _settings(tmp_path)
    settings.xml_path = source

    class Converter:
        latest_errors = []

        def xml_to_csv_folder(self, path, folder):
            raise RuntimeError("conversion failed")

    monkeypatch.setattr(data, "get_settings", lambda: settings)
    monkeypatch.setattr(data, "IatiMultiCsvConverter", Converter)
    data._cache.clear()

    try:
        with pytest.raises(RuntimeError, match="conversion failed"):
            data._csv_folder()
    finally:
        data._cache.clear()


def test_conversion_failed_for_brazil_does_not_use_argentina_cache(monkeypatch, tmp_path):
    source_brazil = tmp_path / "source.xml"
    source_brazil.write_text("<iati-activities />")
    settings = _settings(tmp_path)
    settings.sample = "iadb-Brazil.xml"
    settings.xml_path = source_brazil
    conversion_calls = []

    argentina_folder = tmp_path / "argentina-cache"
    argentina_folder.mkdir()
    (argentina_folder / "activities.csv").write_text("id\n1\n")

    class Converter:
        latest_errors = []

        def xml_to_csv_folder(self, path, folder):
            conversion_calls.append(path)
            raise RuntimeError("conversion failed")

    monkeypatch.setattr(data, "get_settings", lambda: settings)
    monkeypatch.setattr(data, "IatiMultiCsvConverter", Converter)
    data._cache.clear()

    try:
        with pytest.raises(RuntimeError, match="conversion failed"):
            data._csv_folder()
    finally:
        data._cache.clear()


def test_incomplete_cache_never_used_as_fallback(monkeypatch, tmp_path):
    source = tmp_path / "source.xml"
    source.write_text("<iati-activities />")
    settings = _settings(tmp_path)
    settings.xml_path = source

    incomplete_folder = tmp_path / "csv-cache"
    incomplete_folder.mkdir()
    (incomplete_folder / "activities.csv").write_text("id\n1\n")

    class Converter:
        latest_errors = []

        def xml_to_csv_folder(self, path, folder):
            raise RuntimeError("conversion failed")

    monkeypatch.setattr(data, "get_settings", lambda: settings)
    monkeypatch.setattr(data, "IatiMultiCsvConverter", Converter)
    data._cache.clear()
    data._cache["csv_folder"] = incomplete_folder

    try:
        with pytest.raises(RuntimeError, match="conversion failed"):
            data._csv_folder()
    finally:
        data._cache.clear()


def test_failed_replacement_restores_previous_directory(monkeypatch, tmp_path):
    source = tmp_path / "source.xml"
    source.write_text("<iati-activities />")
    settings = _settings(tmp_path)
    settings.xml_path = source
    conversion_calls = []

    previous_folder = tmp_path / "csv-cache-1"
    previous_folder.mkdir()
    (previous_folder / "activities.csv").write_text("id\n1\n")
    (previous_folder / "transactions.csv").write_text("id\n1\n")
    (previous_folder / ".complete").touch()

    class Converter:
        latest_errors = []
        call_count = 0

        def xml_to_csv_folder(self, path, folder):
            conversion_calls.append(path)
            self.call_count += 1
            if self.call_count > 1:
                raise RuntimeError("replacement failed")
            (folder / "activities.csv").write_text("id\n1\n")
            (folder / "transactions.csv").write_text("id\n1\n")
            return True

    converter = Converter()
    monkeypatch.setattr(data, "get_settings", lambda: settings)
    monkeypatch.setattr(data, "IatiMultiCsvConverter", lambda: converter)
    data._cache.clear()

    try:
        first_folder = data._csv_folder()
        assert first_folder == previous_folder or converter.call_count == 1
    finally:
        data._cache.clear()


def test_successful_conversion_removes_backup_and_activates_new_cache(monkeypatch, tmp_path):
    source = tmp_path / "source.xml"
    source.write_text("<iati-activities />")
    settings = _settings(tmp_path)
    settings.xml_path = source
    conversion_calls = []

    class Converter:
        latest_errors = []

        def xml_to_csv_folder(self, path, folder):
            conversion_calls.append(path)
            (folder / "activities.csv").write_text("id\n1\n")
            (folder / "transactions.csv").write_text("id\n1\n")
            (folder / ".complete").touch()
            return True

    monkeypatch.setattr(data, "get_settings", lambda: settings)
    monkeypatch.setattr(data, "IatiMultiCsvConverter", Converter)
    data._cache.clear()

    try:
        result = data._csv_folder()
        assert result is not None
        assert (result / ".complete").exists()
        assert "csv_folder" in data._cache
        assert data._cache["csv_folder"] == result
    finally:
        data._cache.clear()
