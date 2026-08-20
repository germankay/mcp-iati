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
    "sectors.csv",
)


DATAFRAME_SPECS = {
    "activities": {
        "filename": "activities.csv",
        "required_columns": (
            "activity_identifier",
            "title",
            "activity_status",
            "reporting_org_name",
            "reporting_org_ref",
            "default_currency",
            "recipient_country_code",
            "recipient_country_name",
        ),
        "numeric_columns": (),
    },
    "transactions": {
        "filename": "transactions.csv",
        "required_columns": (
            "activity_identifier",
            "transaction_type",
            "transaction_date",
            "value",
            "currency",
            "description",
        ),
        "numeric_columns": ("value",),
    },
    "sectors": {
        "filename": "sectors.csv",
        "required_columns": (
            "activity_identifier",
            "sector_code",
            "sector_name",
            "vocabulary",
            "percentage",
        ),
        "numeric_columns": ("percentage",),
    },
}


TABLE_RELATIONSHIPS = {
     "transactions.activity_identifier": (
        "activities.activity_identifier"
    ),
    "sectors.activity_identifier": (
        "activities.activity_identifier"
    ),
}


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


def _csv_cache_is_complete(folder: Path) -> bool:
    """Return whether the CSV cache contains all files required by the tools."""
    required_files = (
        *(folder / filename for filename in REQUIRED_TOOL_CSVS),
        folder / ".complete",
    )
    return all(path.is_file() for path in required_files)


def _csv_cache_is_fresh(
    folder: Path,
    source_path: Path | None = None,
) -> bool:
    """Return whether a complete CSV cache is still valid."""
    marker = folder / ".complete"

    if not _csv_cache_is_complete(folder):
        return False
    if not _cache_is_fresh(marker):
        return False
    if source_path and not source_path.exists():
        return False

    return (
        source_path is None
        or marker.stat().st_mtime >= source_path.stat().st_mtime
    )


def _clear_expired_memory_cache() -> None:
    """Drop in-process data when their disk cache has expired."""
    if _cache.get("using_stale_csv"):
        return

    cached_folder = _cache.get("csv_folder")
    local_source = get_settings().xml_path

    if cached_folder and not _csv_cache_is_fresh(
        Path(cached_folder),
        local_source,
    ):
        _cache.clear()


def _replace_csv_cache(tmp_dir: Path, cache_dir: Path) -> None:
    """Atomically replace a CSV cache while preserving rollback data."""
    backup_dir = cache_dir.with_name(f".{cache_dir.name}.previous")

    if backup_dir.exists():
        shutil.rmtree(backup_dir)

    if cache_dir.exists():
        cache_dir.rename(backup_dir)

    try:
        tmp_dir.rename(cache_dir)
    except Exception:
        if backup_dir.exists() and not cache_dir.exists():
            backup_dir.rename(cache_dir)
        raise
    else:
        if backup_dir.exists():
            shutil.rmtree(backup_dir)


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

            missing_files = [
                filename
                for filename in REQUIRED_TOOL_CSVS
                if not (tmp_dir / filename).is_file()
            ]
            if missing_files:
                missing = ", ".join(missing_files)
                raise RuntimeError(
                    "IATI conversion did not produce the required CSVs "
                    f"for {path}: {missing}"
                )

            (tmp_dir / ".complete").touch()
            _replace_csv_cache(tmp_dir, cache_dir)

        except Exception as error:
            if _csv_cache_is_complete(cache_dir):
                warnings.warn(
                    "Could not refresh IATI CSV cache from "
                    f"{xml_source()}; using the last complete cache "
                    f"at {cache_dir}: {error}",
                    RuntimeWarning,
                    stacklevel=2,
                )
                _cache["csv_folder"] = cache_dir
                _cache["using_stale_csv"] = True
                return cache_dir

            raise RuntimeError(
                "Could not create IATI CSV cache from "
                f"{xml_source()}: {error}"
            ) from error

        finally:
            if tmp_dir.exists():
                shutil.rmtree(tmp_dir)

        _cache.pop("using_stale_csv", None)
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


def _dataframe(table_name: str) -> pd.DataFrame:
    """Load, validate and share a configured CSV as a pandas DataFrame."""
    try:
        spec = DATAFRAME_SPECS[table_name]
    except KeyError as error:
        raise ValueError(
            f"Unknown IATI CSV table: {table_name}"
        ) from error

    cache_key = f"dataframe:{table_name}"
    _clear_expired_memory_cache()

    if cache_key in _cache:
        return _cache[cache_key]

    csv_path = _csv_folder() / spec["filename"]
    dataframe = pd.read_csv(csv_path, dtype=str)

    missing_columns = [
        column
        for column in spec["required_columns"]
        if column not in dataframe.columns
    ]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise RuntimeError(
            f"{spec['filename']} is missing required columns: "
            f"{missing}"
        )

    for column in spec["numeric_columns"]:
        dataframe[column] = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        )

    _cache[cache_key] = dataframe
    return _cache[cache_key]


def activities_df() -> pd.DataFrame:
    """Return the shared activities DataFrame."""
    return _dataframe("activities")


def transactions_df() -> pd.DataFrame:
    """Return the shared transactions DataFrame."""
    return _dataframe("transactions")


def sectors_df() -> pd.DataFrame:
    """Return the shared sectors DataFrame."""
    return _dataframe("sectors")
