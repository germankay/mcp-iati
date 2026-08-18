""" Simple pandas queries over the flattened IATI activities/transactions CSV.

Field names and codes (activity_status, transaction_type) come from the IATI
standard codelists, so these queries work for any IATI activities XML, not
just the bundled sample - see data.py.

Each query passes `xml_source()` as the source; the raw table data is
embedded into the AI-facing text by `h.text_result` (see helpers/format.py).
"""
from mcp_iati import helpers as h
from mcp_iati.activities.data import activities_df, transactions_df, xml_source


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
