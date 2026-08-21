""" Simple pandas queries over the flattened IATI activities/transactions CSV.

Field names and codes (activity_status, transaction_type) come from the IATI
standard codelists, so these queries work for any IATI activities XML, not
just the bundled sample - see data.py.

Each query passes `xml_source()` as the source; the raw table data is
embedded into the AI-facing text by `h.text_result` (see helpers/format.py).
"""
import pandas as pd

from mcp_iati import helpers as h
from mcp_iati.activities.data import (
    activities_df,
    sectors_df,
    transactions_df,
    xml_source,
)


_TRANSACTION_TYPE_FILTERS = {
    "2": "2",
    "commitment": "2",
    "out commitment": "2",
    "3": "3",
    "disbursement": "3",
}


def _transaction_type_code(value: str) -> str | None:
    """Normalize a supported analytical transaction-type filter."""
    return _TRANSACTION_TYPE_FILTERS.get(str(value).strip().casefold())


def search_activities(text: str, limit: int = 10):
    """Search IATI activities by a substring of their title."""
    df = activities_df()
    matches = df[df["title"].str.contains(text, case=False, na=False)].head(limit)

    if matches.empty:
        return h.empty_result(
            f"No IATI activities found with '{text}' in the title.",
            source_url=xml_source(),
        )

    rows = matches[["activity_identifier", "title", "activity_status"]].copy()
    table = h.build_table(
        rows.to_dict("records"),
        [
            ("activity_identifier", "IATI identifier"),
            ("title", "Title"),
            ("activity_status", "Status"),
        ],
        formatters={"activity_status": h.activity_status_label},
    )
    summary = f"Found {len(matches)} IATI activity(ies) matching '{text}'."
    return h.text_result(summary, source_url=xml_source(), table=table)


def list_activity_statuses():
    """List the activity statuses present in the configured IATI data."""
    activities = activities_df()

    counts = (
        activities["activity_status"]
        .dropna()
        .astype(str)
        .value_counts()
        .sort_index()
    )

    if counts.empty:
        return h.empty_result(
            "No activity statuses were found in the loaded IATI data.",
            source_url=xml_source(),
        )

    rows = [
        {
            "code": code,
            "status": h.activity_status_label(code),
            "activities": int(count),
        }
        for code, count in counts.items()
    ]

    table = h.build_table(
        rows,
        [
            ("code", "Status code"),
            ("status", "Activity status"),
            ("activities", "Activities"),
        ],
    )

    summary = (
        f"Found {len(rows)} activity status value(s) "
        f"across {sum(counts)} activities."
    )

    return h.text_result(
        summary,
        source_url=xml_source(),
        table=table,
    )


def activity_summary(iati_identifier: str):
    """Return title, status and total committed/disbursed amounts for one IATI activity."""
    activities = activities_df()
    activity = activities[activities["activity_identifier"] == iati_identifier]

    if activity.empty:
        return h.empty_result(
            f"No IATI activity found with identifier '{iati_identifier}'.",
            source_url=xml_source(),
        )

    row = activity.iloc[0]
    status_label = h.activity_status_label(row["activity_status"])

    txns = transactions_df()
    txns = txns[txns["activity_identifier"] == iati_identifier]
    totals = txns.groupby("transaction_type")["value"].sum()
    currency = row.get("default_currency") or ""

    # The text carries only the header; the per-type totals travel in the
    # table, which `text_result` embeds in full into the AI-facing text.
    lines = [
        f"{row['title']} ({iati_identifier})",
        f"Status: {status_label}",
        f"Reporting organisation: {row.get('reporting_org_name') or row.get('reporting_org_ref')}",
    ]
    table = [["Transaction type", "Total", "Currency"]]
    for code, total in totals.items():
        table.append([h.transaction_type_label(code), h.format_amount(total), currency])

    return h.text_result("\n".join(lines), source_url=xml_source(), table=table)


def list_reporting_organisations():
    """List reporting organisations present in the configured IATI data."""
    activities = activities_df()

    organisations = activities[
        [
            "activity_identifier",
            "reporting_org_ref",
            "reporting_org_name",
        ]
    ].copy()

    # pandas represents empty CSV cells as NaN. Normalize them before
    # grouping so they never appear as "nan" in tool responses.
    organisations["reporting_org_ref"] = (
        organisations["reporting_org_ref"]
        .fillna("")
        .astype(str)
        .str.strip()
    )
    organisations["reporting_org_name"] = (
        organisations["reporting_org_name"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    organisations["display_name"] = organisations[
        "reporting_org_name"
    ].where(
        organisations["reporting_org_name"] != "",
        organisations["reporting_org_ref"],
    )

    organisations = organisations[
        organisations["display_name"] != ""
    ]

    if organisations.empty:
        return h.empty_result(
            "No reporting organisations were found in the loaded IATI data.",
            source_url=xml_source(),
        )

    counts = (
        organisations.groupby(
            ["reporting_org_ref", "display_name"],
            dropna=False,
        )["activity_identifier"]
        .nunique()
        .reset_index(name="activities")
        .sort_values(
            ["activities", "display_name"],
            ascending=[False, True],
        )
    )

    rows = counts.to_dict("records")

    table = h.build_table(
        rows,
        [
            ("reporting_org_ref", "Organisation reference"),
            ("display_name", "Reporting organisation"),
            ("activities", "Activities"),
        ],
    )

    summary = (
        f"Found {len(rows)} reporting organisation(s) "
        f"across {len(organisations)} activities."
    )

    return h.text_result(
        summary,
        source_url=xml_source(),
        table=table,
    )


def list_recipient_countries():
    """List recipient countries present in the configured IATI data."""
    activities = activities_df()

    countries = activities[
        [
            "activity_identifier",
            "recipient_country_code",
            "recipient_country_name",
        ]
    ].copy()

    countries["recipient_country_code"] = (
        countries["recipient_country_code"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )
    countries["recipient_country_name"] = (
        countries["recipient_country_name"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    countries["display_name"] = countries[
        "recipient_country_name"
    ].where(
        countries["recipient_country_name"] != "",
        countries["recipient_country_code"],
    )

    countries = countries[
        (countries["recipient_country_code"] != "")
        | (countries["display_name"] != "")
    ]

    if countries.empty:
        return h.empty_result(
            "No recipient countries were found in the loaded IATI data.",
            source_url=xml_source(),
        )

    counts = (
        countries.groupby(
            ["recipient_country_code", "display_name"],
            dropna=False,
        )["activity_identifier"]
        .nunique()
        .reset_index(name="activities")
        .sort_values(
            ["activities", "display_name"],
            ascending=[False, True],
        )
    )

    table = h.build_table(
        counts.to_dict("records"),
        [
            ("recipient_country_code", "Country code"),
            ("display_name", "Recipient country"),
            ("activities", "Activities"),
        ],
    )

    summary = (
        f"Found {len(counts)} recipient country value(s) "
        f"across {countries['activity_identifier'].nunique()} activities."
    )

    return h.text_result(
        summary,
        source_url=xml_source(),
        table=table,
    )

def filter_activities_by_country(
    country: str,
    limit: int = 10,
):
    """Filter IATI activities by recipient country code or name."""
    country = country.strip()

    if not country:
        return h.empty_result(
            "A recipient country code or name is required.",
            source_url=xml_source(),
        )

    if limit < 1:
        return h.empty_result(
            "The result limit must be greater than zero.",
            source_url=xml_source(),
        )

    activities = activities_df().copy()

    country_codes = (
        activities["recipient_country_code"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )
    country_names = (
        activities["recipient_country_name"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.casefold()
    )

    matches = activities[
        (country_codes == country.upper())
        | (country_names == country.casefold())
    ].drop_duplicates(subset=["activity_identifier"])

    total = len(matches)

    if matches.empty:
        return h.empty_result(
            f"No IATI activities were found for recipient country "
            f"'{country}'.",
            source_url=xml_source(),
        )

    shown = matches.head(limit).copy()

    rows = shown[
        [
            "activity_identifier",
            "title",
            "activity_status",
            "recipient_country_code",
            "recipient_country_name",
        ]
    ].fillna("")

    table = h.build_table(
        rows.to_dict("records"),
        [
            ("activity_identifier", "IATI identifier"),
            ("title", "Title"),
            ("activity_status", "Status"),
            ("recipient_country_code", "Country code"),
            ("recipient_country_name", "Recipient country"),
        ],
        formatters={
            "activity_status": h.activity_status_label,
        },
    )

    summary = (
        f"Found {total} IATI activity(ies) for recipient country "
        f"'{country}'. Showing {len(shown)} result(s) with limit {limit}."
    )

    return h.text_result(
        summary,
        source_url=xml_source(),
        table=table,
    )


def list_sectors(limit: int = 100):
    """List sectors present in the configured IATI data."""
    if limit < 1:
        return h.empty_result(
            "The result limit must be greater than zero.",
            source_url=xml_source(),
        )

    sectors = sectors_df().copy()

    for column in (
        "sector_code",
        "sector_name",
        "vocabulary",
    ):
        sectors[column] = (
            sectors[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    sectors["display_name"] = sectors["sector_name"].where(
        sectors["sector_name"] != "",
        sectors["sector_code"],
    )

    sectors = sectors[
        (sectors["sector_code"] != "")
        | (sectors["display_name"] != "")
    ]

    if sectors.empty:
        return h.empty_result(
            "No sectors were found in the loaded IATI data.",
            source_url=xml_source(),
        )

    counts = (
        sectors.groupby(
            [
                "vocabulary",
                "sector_code",
                "display_name",
            ],
            dropna=False,
        )["activity_identifier"]
        .nunique()
        .reset_index(name="activities")
        .sort_values(
            ["activities", "display_name"],
            ascending=[False, True],
        )
    )

    total = len(counts)
    shown = counts.head(limit)

    table = h.build_table(
        shown.to_dict("records"),
        [
            ("vocabulary", "Vocabulary"),
            ("sector_code", "Sector code"),
            ("display_name", "Sector"),
            ("activities", "Activities"),
        ],
    )

    summary = (
        f"Found {total} sector value(s). "
        f"Showing {len(shown)} result(s) with limit {limit}."
    )

    return h.text_result(
        summary,
        source_url=xml_source(),
        table=table,
    )


def transaction_totals_by_year(
    year_from: int | None = None,
    year_to: int | None = None,
):
    """Group commitments and disbursements by year and currency.

    Only commitment and disbursement transactions are included. Amounts with
    different currencies are always reported separately.

    Args:
        year_from: Optional first year to include.
        year_to: Optional last year to include.

    Returns:
        A chronological table containing year, transaction type, currency and
        total amount.
    """
    if year_from is not None and year_to is not None and year_from > year_to:
        return h.empty_result(
            "The year_from value cannot be greater than year_to.",
            source_url=xml_source(),
        )

    transactions = transactions_df().copy()

    if transactions.empty:
        return h.empty_result(
            "No transactions were found in the loaded IATI data.",
            source_url=xml_source(),
        )

    transactions["transaction_type"] = transactions["transaction_type"].fillna("")
    transactions["transaction_date"] = (
        transactions["transaction_date"].fillna("").astype(str).str.strip()
    )

    allowed_types = {"2", "3"}
    transactions = transactions[
        transactions["transaction_type"].isin(allowed_types)
    ].copy()

    transactions["year"] = pd.NA
    for idx, value in transactions["transaction_date"].items():
        try:
            year = pd.to_datetime(value, errors="coerce").year
        except Exception:
            year = pd.NA
        if pd.notna(year):
            transactions.at[idx, "year"] = int(year)

    transactions = transactions[pd.notna(transactions["year"])].copy()

    if year_from is not None:
        transactions = transactions[transactions["year"] >= year_from]
    if year_to is not None:
        transactions = transactions[transactions["year"] <= year_to]

    transactions["value"] = pd.to_numeric(
        transactions["value"],
        errors="coerce",
    )
    transactions = transactions[pd.notna(transactions["value"])]

    if transactions.empty:
        return h.empty_result(
            "No transaction totals were found for the requested year range.",
            source_url=xml_source(),
        )

    activities = activities_df()[["activity_identifier", "default_currency"]].copy()
    activities = activities.drop_duplicates(subset=["activity_identifier"])
    activities["default_currency"] = (
        activities["default_currency"].fillna("").astype(str).str.strip()
    )

    transactions = transactions.merge(
        activities,
        on="activity_identifier",
        how="left",
    )

    transactions["currency"] = transactions["currency"].fillna("")
    transactions["currency"] = transactions["currency"].astype(str).str.strip()
    transactions["currency"] = transactions["currency"].where(
        transactions["currency"] != "",
        transactions["default_currency"],
    )
    transactions["currency"] = transactions["currency"].fillna("")

    grouped = (
        transactions.groupby(
            ["year", "transaction_type", "currency"],
            dropna=False,
        )["value"]
        .sum()
        .reset_index()
    )
    grouped = grouped.sort_values(
        ["year", "transaction_type", "currency"],
        kind="mergesort",
    )

    rows = []
    for _, row in grouped.iterrows():
        rows.append(
            {
                "year": int(row["year"]),
                "transaction_type": row["transaction_type"],
                "currency": row["currency"],
                "total": row["value"],
            }
        )

    table = h.build_table(
        rows,
        [
            ("year", "Year"),
            ("transaction_type", "Transaction type"),
            ("currency", "Currency"),
            ("total", "Total"),
        ],
        formatters={
            "transaction_type": h.transaction_type_label,
            "total": h.format_amount,
        },
    )

    summary = f"Found {len(rows)} annual transaction total(s)."
    return h.text_result(summary, source_url=xml_source(), table=table)


def transaction_totals_by_organisation(limit: int = 50):
    """Group commitments and disbursements by reporting organisation.

    Amounts with different currencies and transaction types are reported
    separately. The reporting organisation publishes the activity data and is
    not necessarily the organisation funding or implementing the activity.

    Args:
        limit: Maximum number of grouped rows to return. Default: 50.

    Returns:
        A table containing the organisation reference and name, transaction
        type, currency and total amount.
    """
    if limit < 1:
        return h.empty_result(
            "The result limit must be greater than zero.",
            source_url=xml_source(),
        )

    activities = activities_df()[
        [
            "activity_identifier",
            "reporting_org_ref",
            "reporting_org_name",
            "default_currency",
        ]
    ].copy()
    activities = activities.drop_duplicates(subset=["activity_identifier"])
    activities["reporting_org_ref"] = (
        activities["reporting_org_ref"]
        .fillna("")
        .astype(str)
        .str.strip()
    )
    activities["reporting_org_name"] = (
        activities["reporting_org_name"]
        .fillna("")
        .astype(str)
        .str.strip()
    )
    activities["default_currency"] = (
        activities["default_currency"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    transactions = transactions_df().copy()
    if transactions.empty:
        return h.empty_result(
            "No transactions were found in the loaded IATI data.",
            source_url=xml_source(),
        )

    allowed_types = {"2", "3"}
    transactions = transactions[
        transactions["transaction_type"].isin(allowed_types)
    ].copy()
    transactions["value"] = pd.to_numeric(transactions["value"], errors="coerce")
    transactions = transactions[pd.notna(transactions["value"])].copy()

    if transactions.empty:
        return h.empty_result(
            "No transaction totals were found for the requested organisation grouping.",
            source_url=xml_source(),
        )

    transactions = transactions.merge(
        activities,
        on="activity_identifier",
        how="left",
    )

    transactions["reporting_org_ref"] = (
        transactions["reporting_org_ref"]
        .fillna("")
        .astype(str)
        .str.strip()
    )
    transactions["reporting_org_name"] = (
        transactions["reporting_org_name"]
        .fillna("")
        .astype(str)
        .str.strip()
    )
    transactions["default_currency"] = (
        transactions["default_currency"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    transactions["display_org_name"] = transactions["reporting_org_name"].where(
        transactions["reporting_org_name"] != "",
        transactions["reporting_org_ref"],
    )
    transactions["display_org_name"] = transactions["display_org_name"].where(
        transactions["display_org_name"] != "",
        "Unknown reporting organisation",
    )

    transactions["currency"] = (
        transactions["currency"]
        .fillna("")
        .astype(str)
        .str.strip()
    )
    transactions["currency"] = transactions["currency"].where(
        transactions["currency"] != "",
        transactions["default_currency"],
    )
    transactions["currency"] = transactions["currency"].fillna("")
    transactions["currency"] = transactions["currency"].astype(str).str.strip()
    transactions["currency"] = transactions["currency"].where(
        transactions["currency"] != "",
        "Unknown",
    )

    grouped = (
        transactions.groupby(
            [
                "reporting_org_ref",
                "display_org_name",
                "transaction_type",
                "currency",
            ],
            dropna=False,
        )["value"]
        .sum()
        .reset_index()
    )
    grouped = grouped.sort_values(
        ["display_org_name", "transaction_type", "currency"],
        kind="mergesort",
    )
    shown = grouped.head(limit)

    rows = [
        {
            "organisation_ref": row["reporting_org_ref"],
            "organisation_name": row["display_org_name"],
            "transaction_type": row["transaction_type"],
            "currency": row["currency"],
            "total": row["value"],
        }
        for _, row in shown.iterrows()
    ]

    table = h.build_table(
        rows,
        [
            ("organisation_ref", "Organisation reference"),
            ("organisation_name", "Reporting organisation"),
            ("transaction_type", "Transaction type"),
            ("currency", "Currency"),
            ("total", "Total"),
        ],
        formatters={
            "transaction_type": h.transaction_type_label,
            "total": h.format_amount,
        },
    )

    summary = f"Found {len(rows)} organisation transaction total(s)."
    interpretation = (
        "The amounts are associated with activities published by each "
        "reporting organisation. This does not necessarily imply that the "
        "organisation funded or implemented the funds."
    )
    return h.text_result(
        f"{summary}\n\n{interpretation}",
        source_url=xml_source(),
        table=table,
    )


def _sector_allocations(
    sectors: pd.DataFrame,
    vocabulary: str | None = None,
) -> pd.DataFrame:
    """Return sector allocation percentages that total 100 per activity."""
    sectors = sectors.copy()
    for column in [
        "activity_identifier",
        "sector_code",
        "sector_name",
        "vocabulary",
    ]:
        sectors[column] = (
            sectors[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )
    sectors["percentage"] = pd.to_numeric(
        sectors["percentage"],
        errors="coerce",
    )
    if vocabulary is not None:
        selected_vocabulary = str(vocabulary).strip()
        sectors = sectors[
            sectors["vocabulary"] == selected_vocabulary
        ].copy()
    allocation_rows = []
    for (activity_identifier, vocabulary_code), group in sectors.groupby(
        ["activity_identifier", "vocabulary"],
        dropna=False,
        sort=True,
    ):
        group = group.copy()
        if len(group) == 1 and group["percentage"].isna().all():
            group["percentage"] = 100.0
        valid = group[
            group["percentage"].notna()
            & group["percentage"].between(0, 100)
            & (group["percentage"] > 0)
        ].copy()
        valid_total = float(valid["percentage"].sum())
        if valid_total > 100.000001:
            allocation_rows.append({
                "activity_identifier": activity_identifier,
                "vocabulary": vocabulary_code or "Unknown",
                "sector_code": "",
                "sector_name": "Unallocated sector",
                "allocation_percentage": 100.0,
            })
            continue
        for row in valid.to_dict("records"):
            sector_name = row["sector_name"] or row["sector_code"]
            allocation_rows.append({
                "activity_identifier": activity_identifier,
                "vocabulary": vocabulary_code or "Unknown",
                "sector_code": row["sector_code"],
                "sector_name": sector_name or "Unknown sector",
                "allocation_percentage": float(row["percentage"]),
            })
        remainder = 100.0 - valid_total
        if remainder > 0.000001:
            allocation_rows.append({
                "activity_identifier": activity_identifier,
                "vocabulary": vocabulary_code or "Unknown",
                "sector_code": "",
                "sector_name": "Unallocated sector",
                "allocation_percentage": remainder,
            })
    return pd.DataFrame(
        allocation_rows,
        columns=[
            "activity_identifier",
            "vocabulary",
            "sector_code",
            "sector_name",
            "allocation_percentage",
        ],
    )


def transaction_totals_by_country(
    transaction_type: str = "2",
    currency: str | None = None,
    limit: int = 50,
):
    """Group commitments and disbursements by recipient country.

    Amounts with different currencies and transaction types are reported
    separately. Missing country names fall back to the country code, and
    missing country data falls back to "Unknown recipient country".
    """
    if limit < 1:
        return h.empty_result(
            "The result limit must be greater than zero.",
            source_url=xml_source(),
        )

    transaction_type_code = _transaction_type_code(transaction_type)
    if transaction_type_code is None:
        return h.empty_result(
            "Unsupported transaction type. Use commitment, disbursement, "
            "2 or 3.",
            source_url=xml_source(),
        )

    selected_currency = ""
    if currency is not None:
        selected_currency = str(currency).strip().upper()
        if not selected_currency:
            return h.empty_result(
                "Currency cannot be empty when provided.",
                source_url=xml_source(),
            )

    activities = activities_df()[
        [
            "activity_identifier",
            "recipient_country_code",
            "recipient_country_name",
            "default_currency",
        ]
    ].copy()
    activities = activities.drop_duplicates(subset=["activity_identifier"])
    for column in [
        "recipient_country_code",
        "recipient_country_name",
        "default_currency",
    ]:
        activities[column] = (
            activities[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    transactions = transactions_df().copy()
    if transactions.empty:
        return h.empty_result(
            "No transactions were found in the loaded IATI data.",
            source_url=xml_source(),
        )

    transactions["transaction_type"] = (
        transactions["transaction_type"]
        .fillna("")
        .astype(str)
        .str.strip()
    )
    transactions["value"] = pd.to_numeric(transactions["value"], errors="coerce")
    transactions = transactions[
        (transactions["transaction_type"] == transaction_type_code)
        & transactions["value"].notna()
    ].copy()

    if transactions.empty:
        return h.empty_result(
            "No matching transactions were found in the loaded IATI data.",
            source_url=xml_source(),
        )

    transactions = transactions.merge(
        activities,
        on="activity_identifier",
        how="left",
    )

    transactions["recipient_country_code"] = (
        transactions["recipient_country_code"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )
    transactions["recipient_country_name"] = (
        transactions["recipient_country_name"]
        .fillna("")
        .astype(str)
        .str.strip()
    )
    transactions["default_currency"] = (
        transactions["default_currency"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )
    transactions["currency"] = (
        transactions["currency"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )
    transactions["currency"] = transactions["currency"].where(
        transactions["currency"] != "",
        transactions["default_currency"],
    )
    transactions["currency"] = transactions["currency"].fillna("")
    transactions["currency"] = transactions["currency"].astype(str).str.strip()
    transactions["currency"] = transactions["currency"].where(
        transactions["currency"] != "",
        "Unknown",
    )

    if selected_currency:
        transactions = transactions[transactions["currency"] == selected_currency]

    if transactions.empty:
        return h.empty_result(
            f"No transactions were found for currency '{selected_currency}'.",
            source_url=xml_source(),
        )

    transactions["display_country_name"] = transactions[
        "recipient_country_name"
    ].where(
        transactions["recipient_country_name"] != "",
        transactions["recipient_country_code"],
    )
    transactions["display_country_name"] = transactions[
        "display_country_name"
    ].where(
        transactions["display_country_name"] != "",
        "Unknown recipient country",
    )

    grouped = (
        transactions.groupby(
            [
                "recipient_country_code",
                "display_country_name",
                "transaction_type",
                "currency",
            ],
            dropna=False,
        )["value"]
        .sum()
        .reset_index()
    )
    grouped = grouped.sort_values(
        ["currency", "value", "display_country_name"],
        ascending=[True, False, True],
        kind="mergesort",
    )
    grouped = grouped.groupby("currency", group_keys=False).head(limit)

    rows = []
    for _, row in grouped.iterrows():
        rows.append(
            {
                "country_code": row["recipient_country_code"],
                "country_name": row["display_country_name"],
                "transaction_type": row["transaction_type"],
                "currency": row["currency"],
                "total": row["value"],
            }
        )

    table = h.build_table(
        rows,
        [
            ("country_code", "Country code"),
            ("country_name", "Recipient country"),
            ("transaction_type", "Transaction type"),
            ("currency", "Currency"),
            ("total", "Total"),
        ],
        formatters={
            "transaction_type": h.transaction_type_label,
            "total": h.format_amount,
        },
    )

    summary = f"Found {len(rows)} country transaction total(s)."
    return h.text_result(summary, source_url=xml_source(), table=table)


def transaction_totals_by_sector(
    transaction_type: str = "2",
    currency: str | None = None,
    vocabulary: str | None = None,
    limit: int = 50,
):
    """Allocate commitments and disbursements across sectors.

    Amounts are distributed using the published sector percentages. Different
    vocabularies and currencies are reported separately.
    """
    if limit < 1:
        return h.empty_result(
            "The result limit must be greater than zero.",
            source_url=xml_source(),
        )

    transaction_type_code = _transaction_type_code(transaction_type)
    if transaction_type_code is None:
        return h.empty_result(
            "Unsupported transaction type. Use commitment, disbursement, "
            "2 or 3.",
            source_url=xml_source(),
        )

    selected_currency = ""
    if currency is not None:
        selected_currency = str(currency).strip().upper()
        if not selected_currency:
            return h.empty_result(
                "Currency cannot be empty when provided.",
                source_url=xml_source(),
            )

    transactions = transactions_df().copy()
    transactions["transaction_type"] = (
        transactions["transaction_type"]
        .fillna("")
        .astype(str)
        .str.strip()
    )
    transactions["value"] = pd.to_numeric(transactions["value"], errors="coerce")
    transactions = transactions[
        (transactions["transaction_type"] == transaction_type_code)
        & transactions["value"].notna()
    ].copy()

    if transactions.empty:
        return h.empty_result(
            "No matching transactions were found in the loaded IATI data.",
            source_url=xml_source(),
        )

    activities = activities_df()[["activity_identifier", "default_currency"]].copy()
    activities = activities.drop_duplicates(subset=["activity_identifier"])
    activities["default_currency"] = (
        activities["default_currency"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )
    transactions = transactions.merge(
        activities,
        on="activity_identifier",
        how="left",
    )

    transactions["currency"] = (
        transactions["currency"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )
    transactions["currency"] = transactions["currency"].where(
        transactions["currency"] != "",
        transactions["default_currency"],
    )
    transactions["currency"] = transactions["currency"].fillna("")
    transactions["currency"] = transactions["currency"].astype(str).str.strip()
    transactions["currency"] = transactions["currency"].where(
        transactions["currency"] != "",
        "Unknown",
    )

    if selected_currency:
        transactions = transactions[transactions["currency"] == selected_currency]

    if transactions.empty:
        return h.empty_result(
            f"No transactions were found for currency '{selected_currency}'.",
            source_url=xml_source(),
        )

    sectors = _sector_allocations(sectors_df(), vocabulary=vocabulary)
    transaction_activity_ids = set(
        transactions["activity_identifier"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    allocated_activity_ids = set(
        sectors["activity_identifier"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    missing_activity_ids = sorted(
        transaction_activity_ids - allocated_activity_ids
    )

    if missing_activity_ids:
        fallback_vocabulary = (
            str(vocabulary).strip()
            if vocabulary is not None
            else "Unknown"
        )

        missing_allocations = pd.DataFrame([
            {
                "activity_identifier": activity_identifier,
                "vocabulary": fallback_vocabulary,
                "sector_code": "",
                "sector_name": "Unallocated sector",
                "allocation_percentage": 100.0,
            }
            for activity_identifier in missing_activity_ids
        ])

        sectors = pd.concat(
            [sectors, missing_allocations],
            ignore_index=True,
        )
    if sectors.empty:
        return h.empty_result(
            "No sector allocations were found for the requested filters.",
            source_url=xml_source(),
        )

    merged = transactions.merge(
        sectors,
        on="activity_identifier",
        how="left",
    )
    merged["allocation_percentage"] = pd.to_numeric(
        merged["allocation_percentage"],
        errors="coerce",
    )
    merged = merged[merged["allocation_percentage"].notna()].copy()
    merged["allocated_value"] = (
        merged["value"] * merged["allocation_percentage"] / 100
    )

    grouped = (
        merged.groupby(
            [
                "vocabulary",
                "sector_code",
                "sector_name",
                "transaction_type",
                "currency",
            ],
            dropna=False,
        )["allocated_value"]
        .sum()
        .reset_index()
    )
    grouped = grouped.sort_values(
        ["vocabulary", "currency", "allocated_value", "sector_name"],
        ascending=[True, True, False, True],
        kind="mergesort",
    )
    shown = (
        grouped.groupby(
            ["vocabulary", "currency"],
            sort=False,
            group_keys=False,
        )
        .head(limit)
    )

    rows = []
    for _, row in shown.iterrows():
        rows.append(
            {
                "vocabulary": row["vocabulary"],
                "sector_code": row["sector_code"],
                "sector_name": row["sector_name"],
                "transaction_type": row["transaction_type"],
                "currency": row["currency"],
                "total": row["allocated_value"],
            }
        )

    table = h.build_table(
        rows,
        [
            ("vocabulary", "Vocabulary"),
            ("sector_code", "Sector code"),
            ("sector_name", "Sector"),
            ("transaction_type", "Transaction type"),
            ("currency", "Currency"),
            ("total", "Allocated total"),
        ],
        formatters={
            "transaction_type": h.transaction_type_label,
            "total": h.format_amount,
        },
    )

    summary = (
        "Transaction amounts are allocated using the published sector "
        "percentages. Currencies and sector vocabularies are reported "
        "separately."
    )
    return h.text_result(summary, source_url=xml_source(), table=table)


def top_activities_by_amount(
    transaction_type: str = "2",
    currency: str | None = None,
    limit: int = 10,
):
    """Return activities with the highest transaction totals.

    Rankings are calculated independently for each currency. Only commitments
    and disbursements are supported.
    """
    if limit < 1:
        return h.empty_result(
            "The result limit must be greater than zero.",
            source_url=xml_source(),
        )

    transaction_type_code = _transaction_type_code(transaction_type)
    if transaction_type_code is None:
        return h.empty_result(
            "Unsupported transaction type. Use commitment, disbursement, "
            "2 or 3.",
            source_url=xml_source(),
        )

    selected_currency = ""
    if currency is not None:
        selected_currency = str(currency).strip().upper()
        if not selected_currency:
            return h.empty_result(
                "Currency cannot be empty when provided.",
                source_url=xml_source(),
            )

    transactions = transactions_df().copy()
    transactions["transaction_type"] = (
        transactions["transaction_type"]
        .fillna("")
        .astype(str)
        .str.strip()
    )
    transactions["value"] = pd.to_numeric(transactions["value"], errors="coerce")
    transactions = transactions[
        (transactions["transaction_type"] == transaction_type_code)
        & transactions["value"].notna()
    ].copy()

    if transactions.empty:
        return h.empty_result(
            "No matching transactions were found in the loaded IATI data.",
            source_url=xml_source(),
        )

    activity_columns = [
        "activity_identifier",
        "title",
        "reporting_org_name",
        "reporting_org_ref",
        "recipient_country_code",
        "recipient_country_name",
        "default_currency",
    ]
    activities = (
        activities_df()[activity_columns]
        .drop_duplicates(subset=["activity_identifier"])
        .copy()
    )
    for column in activity_columns:
        activities[column] = (
            activities[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    transactions = transactions.merge(
        activities,
        on="activity_identifier",
        how="left",
    )

    transactions["currency"] = (
        transactions["currency"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )
    transactions["default_currency"] = (
        transactions["default_currency"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )
    transactions["currency"] = transactions["currency"].where(
        transactions["currency"] != "",
        transactions["default_currency"],
    )
    transactions["currency"] = transactions["currency"].fillna("")
    transactions["currency"] = transactions["currency"].astype(str).str.strip()
    transactions["currency"] = transactions["currency"].where(
        transactions["currency"] != "",
        "Unknown",
    )

    if selected_currency:
        transactions = transactions[transactions["currency"] == selected_currency]

    if transactions.empty:
        return h.empty_result(
            f"No transactions were found for currency '{selected_currency}'.",
            source_url=xml_source(),
        )

    transactions["reporting_org_name"] = (
        transactions["reporting_org_name"]
        .fillna("")
        .astype(str)
        .str.strip()
    )
    transactions["reporting_org_ref"] = (
        transactions["reporting_org_ref"]
        .fillna("")
        .astype(str)
        .str.strip()
    )
    transactions["display_org_name"] = transactions["reporting_org_name"].where(
        transactions["reporting_org_name"] != "",
        transactions["reporting_org_ref"],
    )
    transactions["display_org_name"] = transactions["display_org_name"].where(
        transactions["display_org_name"] != "",
        "Unknown reporting organisation",
    )

    transactions["recipient_country_name"] = (
        transactions["recipient_country_name"]
        .fillna("")
        .astype(str)
        .str.strip()
    )
    transactions["recipient_country_code"] = (
        transactions["recipient_country_code"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )
    transactions["display_country"] = transactions["recipient_country_name"].where(
        transactions["recipient_country_name"] != "",
        transactions["recipient_country_code"],
    )
    transactions["display_country"] = transactions["display_country"].where(
        transactions["display_country"] != "",
        "Unknown",
    )

    grouped = (
        transactions.groupby(
            [
                "activity_identifier",
                "title",
                "display_org_name",
                "display_country",
                "currency",
            ],
            dropna=False,
        )["value"]
        .sum()
        .reset_index()
    )
    grouped = grouped.sort_values(
        ["currency", "value", "activity_identifier"],
        ascending=[True, False, True],
        kind="mergesort",
    )
    grouped = grouped.groupby("currency", group_keys=False).head(limit)

    rows = []
    for _, row in grouped.iterrows():
        rows.append(
            {
                "activity_identifier": row["activity_identifier"],
                "title": row["title"],
                "organisation": row["display_org_name"],
                "country": row["display_country"],
                "transaction_type": transaction_type_code,
                "currency": row["currency"],
                "total": row["value"],
            }
        )

    table = h.build_table(
        rows,
        [
            ("activity_identifier", "IATI identifier"),
            ("title", "Title"),
            ("organisation", "Organisation"),
            ("country", "Country"),
            ("transaction_type", "Transaction type"),
            ("currency", "Currency"),
            ("total", "Total"),
        ],
        formatters={
            "transaction_type": h.transaction_type_label,
            "total": h.format_amount,
        },
    )

    summary = f"Found {len(rows)} top activity amount(s)."
    interpretation = (
        "Commitments do not necessarily represent payments made."
    )
    return h.text_result(
        f"{summary}\n\n{interpretation}",
        source_url=xml_source(),
        table=table,
    )


def activity_transactions(
    iati_identifier: str,
    limit: int = 50,
):
    """List transactions associated with one IATI activity."""
    iati_identifier = iati_identifier.strip()

    if not iati_identifier:
        return h.empty_result(
            "An IATI activity identifier is required.",
            source_url=xml_source(),
        )

    if limit < 1:
        return h.empty_result(
            "The result limit must be greater than zero.",
            source_url=xml_source(),
        )

    activities = activities_df()
    activity = activities[
        activities["activity_identifier"] == iati_identifier
    ]

    if activity.empty:
        return h.empty_result(
            f"No IATI activity found with identifier "
            f"'{iati_identifier}'.",
            source_url=xml_source(),
        )

    transactions = transactions_df()
    matches = transactions[
        transactions["activity_identifier"] == iati_identifier
    ].copy()

    if matches.empty:
        return h.empty_result(
            f"No transactions were found for IATI activity "
            f"'{iati_identifier}'.",
            source_url=xml_source(),
        )

    matches["transaction_date"] = (
        matches["transaction_date"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    matches = matches.sort_values(
        ["transaction_date", "transaction_type"],
        na_position="last",
    )

    total = len(matches)
    shown = matches.head(limit).copy()

    rows = shown[
        [
            "transaction_date",
            "transaction_type",
            "value",
            "currency",
            "description",
        ]
    ].copy()

    rows["currency"] = rows["currency"].fillna("")
    rows["description"] = rows["description"].fillna("")

    table = h.build_table(
        rows.to_dict("records"),
        [
            ("transaction_date", "Date"),
            ("transaction_type", "Transaction type"),
            ("value", "Value"),
            ("currency", "Currency"),
            ("description", "Description"),
        ],
        formatters={
            "transaction_type": h.transaction_type_label,
            "value": lambda value: (
                ""
                if value is None or str(value) == "nan"
                else h.format_amount(value)
            ),
        },
    )

    title = activity.iloc[0]["title"]

    summary = (
        f"Found {total} transaction(s) for {title} "
        f"({iati_identifier}). Showing {len(shown)} result(s) "
        f"with limit {limit}."
    )

    return h.text_result(
        summary,
        source_url=xml_source(),
        table=table,
    )
