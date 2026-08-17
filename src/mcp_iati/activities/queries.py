""" Simple pandas queries over the flattened IATI activities/transactions CSV.

Field names and codes (activity_status, transaction_type) come from the IATI
standard codelists, so these queries work for any IATI activities XML, not
just the bundled sample - see data.py.
"""
from mcp_iati import helpers as h
from mcp_iati.activities.data import activities_df, transactions_df


def buscar_actividades(texto: str, limit: int = 10):
    """Search IATI activities by a substring of their title."""
    df = activities_df()
    matches = df[df["title"].str.contains(texto, case=False, na=False)].head(limit)

    if matches.empty:
        return h.empty_result(
            f"No se encontraron actividades IATI con '{texto}' en el título."
        )

    rows = matches[["activity_identifier", "title", "activity_status"]].copy()
    table = h.build_table(
        rows.to_dict("records"),
        [
            ("activity_identifier", "Identificador IATI"),
            ("title", "Título"),
            ("activity_status", "Estado"),
        ],
        formatters={"activity_status": h.activity_status_label},
    )
    text = f"Se encontraron {len(matches)} actividad(es) IATI que coinciden con '{texto}'."
    return h.text_result(text, table=table)


def resumen_actividad(iati_identifier: str):
    """Return title, status and total committed/disbursed amounts for one IATI activity."""
    activities = activities_df()
    activity = activities[activities["activity_identifier"] == iati_identifier]

    if activity.empty:
        return h.empty_result(
            f"No se encontró ninguna actividad IATI con identificador '{iati_identifier}'."
        )

    row = activity.iloc[0]
    status_label = h.activity_status_label(row["activity_status"])

    txns = transactions_df()
    txns = txns[txns["activity_identifier"] == iati_identifier]
    totals = txns.groupby("transaction_type")["value"].sum()
    currency = row.get("default_currency") or ""

    lines = [
        f"{row['title']} ({iati_identifier})",
        f"Estado: {status_label}",
        f"Organización reportante: {row.get('reporting_org_name') or row.get('reporting_org_ref')}",
    ]
    table = [["Tipo de transacción", "Total", "Moneda"]]
    for code, total in totals.items():
        label = h.transaction_type_label(code)
        amount = h.format_amount(total)
        lines.append(f"{label}: {amount} {currency}")
        table.append([label, amount, currency])

    return h.text_result("\n".join(lines), table=table)
