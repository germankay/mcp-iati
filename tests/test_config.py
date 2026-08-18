import pytest
from platformdirs import user_data_path

from mcp_iati.config import (
    APP_NAME,
    DEFAULT_CACHE_TTL_SECONDS,
    DEFAULT_SAMPLE,
    get_settings,
)


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_default_configuration(monkeypatch):
    for variable in (
        "MCP_IATI_XML_PATH",
        "MCP_IATI_XML_URL",
        "MCP_IATI_SAMPLE",
        "MCP_IATI_DATA_DIR",
        "MCP_IATI_CACHE_TTL_SECONDS",
    ):
        monkeypatch.delenv(variable, raising=False)

    settings = get_settings()

    assert settings.xml_path is None
    assert settings.xml_url is None
    assert settings.sample == DEFAULT_SAMPLE
    assert settings.data_dir == user_data_path(APP_NAME)
    assert settings.cache_ttl_seconds == 604800
    assert settings.cache_ttl_seconds == DEFAULT_CACHE_TTL_SECONDS


def test_configuration_accepts_all_overrides(monkeypatch, tmp_path):
    xml_path = tmp_path / "argentina.xml"
    data_dir = tmp_path / "data"
    monkeypatch.setenv("MCP_IATI_XML_PATH", str(xml_path))
    monkeypatch.setenv("MCP_IATI_XML_URL", "https://example.org/brasil.xml")
    monkeypatch.setenv("MCP_IATI_SAMPLE", "iadb-Argentina.xml")
    monkeypatch.setenv("MCP_IATI_DATA_DIR", str(data_dir))
    monkeypatch.setenv("MCP_IATI_CACHE_TTL_SECONDS", "3600")

    settings = get_settings()

    assert settings.xml_path == xml_path
    assert settings.xml_url == "https://example.org/brasil.xml"
    assert settings.sample == "iadb-Argentina.xml"
    assert settings.data_dir == data_dir
    assert settings.cache_ttl_seconds == 3600


@pytest.mark.parametrize("value", ["0", "-1", "seven-days"])
def test_invalid_cache_duration_is_rejected(monkeypatch, value):
    monkeypatch.setenv("MCP_IATI_CACHE_TTL_SECONDS", value)

    with pytest.raises(ValueError, match="MCP_IATI_CACHE_TTL_SECONDS"):
        get_settings()


def test_environment_changes_require_reload(monkeypatch):
    monkeypatch.setenv("MCP_IATI_SAMPLE", "iadb-Argentina.xml")
    first_settings = get_settings()

    monkeypatch.setenv("MCP_IATI_SAMPLE", "iadb-Brazil.xml")

    assert get_settings() is first_settings
    assert get_settings().sample == "iadb-Argentina.xml"

    get_settings.cache_clear()
    assert get_settings().sample == "iadb-Brazil.xml"


def test_data_directory_is_created_on_demand(monkeypatch, tmp_path):
    data_dir = tmp_path / "nested" / "mcp-iati"
    monkeypatch.setenv("MCP_IATI_DATA_DIR", str(data_dir))

    assert get_settings().ensure_data_dir() == data_dir
    assert data_dir.is_dir()
