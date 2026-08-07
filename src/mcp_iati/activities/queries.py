""" Simple pandas queries over the flattened IATI activities/transactions CSV.

Field names and codes (activity_status, transaction_type) come from the IATI
standard codelists, so these queries work for any IATI activities XML, not
just the bundled sample - see data.py.
"""
from okfn_iati.enums import ActivityStatus, TransactionType

from mcp_server.results import text_result

from mcp_iati.activities.data import activities_df, transactions_df, xml_source

_STATUS_LABELS = {str(s.value): s.name.replace("_", " ").title() for s in ActivityStatus}
_TRANSACTION_TYPE_LABELS = {t.value: t.name.replace("_", " ").title() for t in TransactionType}


def buscar_actividades(texto: str, limit: int = 10):
    """Search IATI activities by a substring of their title."""
    df = activities_df()
    matches = df[df["title"].str.contains(texto, case=False, na=False)].head(limit)

    if matches.empty:
        return text_result(
            f"No se encontraron actividades IATI con '{texto}' en el título.",
            source_url=xml_source(),
        )

    rows = matches[["activity_identifier", "title", "activity_status"]].copy()
    rows["activity_status"] = rows["activity_status"].map(_STATUS_LABELS).fillna(rows["activity_status"])
    table = [["Identificador IATI", "Título", "Estado"]] + rows.values.tolist()
    text = f"Se encontraron {len(matches)} actividad(es) IATI que coinciden con '{texto}'."
    return text_result(text, source_url=xml_source(), table=table)


def resumen_actividad(iati_identifier: str):
    """Return title, status and total committed/disbursed amounts for one IATI activity."""
    activities = activities_df()
    activity = activities[activities["activity_identifier"] == iati_identifier]

    if activity.empty:
        return text_result(
            f"No se encontró ninguna actividad IATI con identificador '{iati_identifier}'.",
            source_url=xml_source(),
        )

    row = activity.iloc[0]
    status_label = _STATUS_LABELS.get(str(row["activity_status"]), str(row["activity_status"]))

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
        label = _TRANSACTION_TYPE_LABELS.get(str(code), str(code))
        lines.append(f"{label}: {total:,.2f} {currency}")
        table.append([label, f"{total:,.2f}", currency])

    return text_result("\n".join(lines), source_url=xml_source(), table=table)
