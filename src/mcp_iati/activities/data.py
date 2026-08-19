"""Loads a real IATI activities XML into flat pandas DataFrames.

Genericity note: this module works with ANY IATI 2.x activities XML, not just
the default sample - the columns it reads (activity_identifier,
transaction_type, value, ...) come straight from the IATI standard, produced
by okfn_iati's `IatiMultiCsvConverter.xml_to_csv_folder()`.

Real-life sample XMLs are NOT stored in this repo: on first use the configured
sample is downloaded from the okfn_iati GitHub repo
(https://github.com/okfn/okfn_iati, `data-samples/xml/`) into a per-user data
directory. Pick a different sample with MCP_IATI_SAMPLE (e.g.
`iadb-Argentina.xml`), set MCP_IATI_XML_URL for another remote XML, or set
MCP_IATI_XML_PATH to use a local file with no download at all.
"""
import hashlib
import os
import shutil
import tempfile
import time
import urllib.error
import urllib.request
import warnings
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
from okfn_iati import IatiMultiCsvConverter

from mcp_iati.config import get_settings

# Samples live in the okfn_iati repo (a few MB each), downloaded on demand.
_SAMPLES_BASE_URL = "https://raw.githubusercontent.com/okfn/okfn_iati/main/data-samples/xml"
_cache: dict = {}

# These CSVs are required for the tools to work; if they are missing, the
# conversion failed or the XML is not a valid IATI activities file.
REQUIRED_TOOL_CSVS = (
    "activities.csv",
    "transactions.csv",
)


def _cache_is_fresh(path: Path) -> bool:
    """Return whether a cached file is still inside the configured TTL."""
    if not path.exists():
        return False
    age_seconds = max(0, time.time() - path.stat().st_mtime)
    return age_seconds < get_settings().cache_ttl_seconds


def _download_xml(url: str, filename: str) -> Path:
    """Download an XML source unless a fresh cached copy exists."""
    target = get_settings().ensure_data_dir() / "xml" / filename
    if _cache_is_fresh(target):
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            content = resp.read()
    except (urllib.error.URLError, OSError) as exc:
        if target.exists():
            warnings.warn(
                f"Could not refresh IATI XML from {url}; using the stale "
                f"cached copy at {target}: {exc}",
                RuntimeWarning,
                stacklevel=2,
            )
            return target
        raise FileNotFoundError(
            f"Could not download IATI XML from {url} ({exc}). Check "
            "MCP_IATI_XML_URL or MCP_IATI_SAMPLE, or set MCP_IATI_XML_PATH "
            "to a local file."
        ) from exc
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=target.parent,
            prefix=f".{target.name}-",
            delete=False,
        ) as temporary_file:
            temporary_file.write(content)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
            temporary_path = Path(temporary_file.name)
        temporary_path.replace(target)
    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()
    return target


def _download_sample(name: str) -> Path:
    """Download a named sample from the okfn_iati repository."""
    if not name or Path(name).name != name or name in {".", ".."}:
        raise ValueError(
            "MCP_IATI_SAMPLE must be a filename without directory components."
        )
    url = f"{_SAMPLES_BASE_URL}/{name}"
    return _download_xml(url, name)


def _download_configured_url(url: str) -> Path:
    """Download a custom URL using a source-specific local filename."""
    source_name = Path(urlparse(url).path).name or "source.xml"
    source_hash = hashlib.sha256(url.encode()).hexdigest()[:12]
    return _download_xml(url, f"{source_hash}-{source_name}")


def xml_path() -> Path:
    """Path to the IATI XML file to load.

    MCP_IATI_XML_PATH points at a local file (no download). If it is absent,
    MCP_IATI_XML_URL can point at a remote XML. Otherwise the sample named by
    MCP_IATI_SAMPLE is fetched from okfn_iati on first use.
    """
    settings = get_settings()
    if settings.xml_path:
        return settings.xml_path
    if settings.xml_url:
        return _download_configured_url(settings.xml_url)
    return _download_sample(settings.sample)


def xml_source() -> str:
    """Return the original configured source used by tool responses."""
    settings = get_settings()
    if settings.xml_path:
        return str(settings.xml_path)
    if settings.xml_url:
        return settings.xml_url
    return f"{_SAMPLES_BASE_URL}/{settings.sample}"


def _source_cache_key() -> str:
    """Return a stable cache key for the configured XML origin."""
    settings = get_settings()
    if settings.xml_path:
        source = f"path:{settings.xml_path.resolve()}"
    elif settings.xml_url:
        source = f"url:{settings.xml_url}"
    else:
        source = f"sample:{settings.sample}"
    return hashlib.sha256(source.encode()).hexdigest()[:16]


def _csv_cache_is_fresh(
    folder: Path,
    source_path: Path | None = None,
) -> bool:
    """Return whether a complete CSV cache exists and is still valid."""
    marker = folder / ".complete"
    required_files = (
        folder / "activities.csv",
        folder / "transactions.csv",
        marker,
    )
    if not all(path.exists() for path in required_files):
        return False
    if not _cache_is_fresh(marker):
        return False
    if source_path and not source_path.exists():
        return False

    return not source_path or marker.stat().st_mtime >= source_path.stat().st_mtime


def _clear_expired_memory_cache() -> None:
    """Drop in-process DataFrames when their disk cache has expired."""
    cached_folder = _cache.get("csv_folder")
    local_source = get_settings().xml_path
    if cached_folder and not _csv_cache_is_fresh(
        Path(cached_folder),
        local_source,
    ):
        for key in ("csv_folder", "activities", "transactions"):
            _cache.pop(key, None)


def _csv_folder() -> Path:
    """Return fresh, source-specific CSVs, converting the XML when needed."""
    _clear_expired_memory_cache()
    if "csv_folder" not in _cache:
        path = xml_path()
        if not path.exists():
            raise FileNotFoundError(
                f"IATI XML not found at {path}. "
                "Set MCP_IATI_XML_PATH to a valid file."
            )
        csv_parent = get_settings().ensure_data_dir() / "csv"
        csv_parent.mkdir(parents=True, exist_ok=True)
        cache_key = _source_cache_key()
        cache_dir = csv_parent / cache_key
        if _csv_cache_is_fresh(cache_dir, path):
            _cache["csv_folder"] = cache_dir
            return cache_dir

        tmp_dir = Path(
            tempfile.mkdtemp(prefix=f"{cache_key}-", dir=csv_parent)
        )
        try:
            converter = IatiMultiCsvConverter()
            if not converter.xml_to_csv_folder(path, tmp_dir):
                raise RuntimeError(
                    f"Failed to convert {path} to CSV: "
                    f"{converter.latest_errors}"
                )
            required_files = (
                tmp_dir / "activities.csv",
                tmp_dir / "transactions.csv",
            )
            if not all(file.exists() for file in required_files):
                raise RuntimeError(
                    "IATI conversion did not produce the required CSVs "
                    f"for {path}."
                )

            (tmp_dir / ".complete").touch()
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
            tmp_dir.rename(cache_dir)
        finally:
            if tmp_dir.exists():
                shutil.rmtree(tmp_dir)
        _cache["csv_folder"] = cache_dir
    return _cache["csv_folder"]


def prepare_data() -> Path:
    """Prepare and validate the configured IATI data before serving tools."""
    source = xml_source()

    try:
        folder = _csv_folder()
    except (FileNotFoundError, RuntimeError) as error:
        raise RuntimeError(
            f"Could not prepare IATI data from {source}: {error}"
        ) from error

    missing_files = [
        filename
        for filename in REQUIRED_TOOL_CSVS
        if not (folder / filename).exists()
    ]
    if missing_files:
        missing = ", ".join(missing_files)
        raise RuntimeError(
            f"IATI data from {source} is missing required CSV files: "
            f"{missing}"
        )

    generated_csvs = sorted(path.name for path in folder.glob("*.csv"))

    print(
        f"IATI data prepared from {source}: "
        f"{len(generated_csvs)} CSV files in {folder}"
    )

    return folder


def activities_df() -> pd.DataFrame:
    _clear_expired_memory_cache()
    if "activities" not in _cache:
        _cache["activities"] = pd.read_csv(_csv_folder() / "activities.csv", dtype=str)
    return _cache["activities"]


def transactions_df() -> pd.DataFrame:
    _clear_expired_memory_cache()
    if "transactions" not in _cache:
        df = pd.read_csv(_csv_folder() / "transactions.csv", dtype=str)
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        _cache["transactions"] = df
    return _cache["transactions"]
