"""Loads a real IATI activities XML into flat pandas DataFrames.

Genericity note: this module works with ANY IATI 2.x activities XML, not just
the default sample - the columns it reads (activity_identifier,
transaction_type, value, ...) come straight from the IATI standard, produced
by okfn_iati's `IatiMultiCsvConverter.xml_to_csv_folder()`.

Real-life sample XMLs are NOT stored in this repo: on first use the configured
sample is downloaded from the okfn_iati GitHub repo
(https://github.com/okfn/okfn_iati, `data-samples/xml/`) into a per-user data
directory. Pick a different sample with MCP_IATI_SAMPLE (e.g.
`iadb-Argentina.xml`), or set MCP_IATI_XML_PATH to use a local file with no
download at all.
"""
import os
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd
from okfn_iati import IatiMultiCsvConverter
from platformdirs import user_data_path

APP_DIR = "mcp-iati"

# Samples live in the okfn_iati repo (a few MB each), downloaded on demand.
_SAMPLES_BASE_URL = "https://raw.githubusercontent.com/okfn/okfn_iati/main/data-samples/xml"
_DEFAULT_SAMPLE = "iadb-Brazil.xml"

_cache: dict = {}


def _download_sample(name: str) -> Path:
    """Download a sample XML from the okfn_iati repo unless already cached locally."""
    target = user_data_path(APP_DIR) / "xml" / name
    if target.exists():
        return target
    url = f"{_SAMPLES_BASE_URL}/{name}"
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            content = resp.read()
    except (urllib.error.URLError, OSError) as exc:
        raise FileNotFoundError(
            f"Could not download IATI sample '{name}' from {url} ({exc}). "
            "Check MCP_IATI_SAMPLE, or set MCP_IATI_XML_PATH to a local file."
        ) from exc
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return target


def xml_path() -> Path:
    """Path to the IATI XML file to load.

    MCP_IATI_XML_PATH points at a local file (no download). Otherwise the
    sample named by MCP_IATI_SAMPLE (default iadb-Brazil.xml) is fetched from
    the okfn_iati repo on first use and cached in the per-user data dir.
    """
    local = os.environ.get("MCP_IATI_XML_PATH")
    if local:
        return Path(local)
    return _download_sample(os.environ.get("MCP_IATI_SAMPLE", _DEFAULT_SAMPLE))


def xml_source() -> str:
    """Human-readable reference to the currently loaded XML, used as the tool's `sources`."""
    return str(xml_path())


def _csv_folder() -> Path:
    """Convert the configured XML to flat CSVs once per process and cache the folder."""
    if "csv_folder" not in _cache:
        path = xml_path()
        if not path.exists():
            raise FileNotFoundError(f"IATI XML not found at {path}. Set MCP_IATI_XML_PATH to a valid file.")
        tmp_dir = Path(tempfile.mkdtemp(prefix="mcp_iati_"))
        converter = IatiMultiCsvConverter()
        if not converter.xml_to_csv_folder(path, tmp_dir):
            raise RuntimeError(f"Failed to convert {path} to CSV: {converter.latest_errors}")
        _cache["csv_folder"] = tmp_dir
    return _cache["csv_folder"]


def activities_df() -> pd.DataFrame:
    if "activities" not in _cache:
        _cache["activities"] = pd.read_csv(_csv_folder() / "activities.csv", dtype=str)
    return _cache["activities"]


def transactions_df() -> pd.DataFrame:
    if "transactions" not in _cache:
        df = pd.read_csv(_csv_folder() / "transactions.csv", dtype=str)
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        _cache["transactions"] = df
    return _cache["transactions"]
