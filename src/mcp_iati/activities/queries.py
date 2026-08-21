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
