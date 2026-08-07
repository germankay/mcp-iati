"""Loads a real IATI activities XML into flat pandas DataFrames.

Genericity note: this module works with ANY IATI 2.x activities XML, not just
the bundled Brazil sample - the columns it reads (activity_identifier,
transaction_type, value, ...) come straight from the IATI standard, produced
by okfn_iati's `IatiMultiCsvConverter.xml_to_csv_folder()`. Point
MCP_IATI_XML_PATH at a different file (e.g. iadb-Argentina.xml) to query it
instead, with no code changes.
"""
import os
import tempfile
from pathlib import Path

import pandas as pd
from okfn_iati import IatiMultiCsvConverter

# Default: the IADB Brazil sample bundled in this monorepo (see okfn_iati/data-samples).
_DEFAULT_XML_PATH = (
    Path(__file__).resolve().parents[4] / "okfn_iati" / "data-samples" / "xml" / "iadb-Brazil.xml"
)

_cache: dict = {}


def xml_path() -> Path:
    """Path to the IATI XML file to load, overridable via MCP_IATI_XML_PATH."""
    return Path(os.environ.get("MCP_IATI_XML_PATH", _DEFAULT_XML_PATH))


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
