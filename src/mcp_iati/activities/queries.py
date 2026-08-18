""" Simple pandas queries over the flattened IATI activities/transactions CSV.

Field names and codes (activity_status, transaction_type) come from the IATI
standard codelists, so these queries work for any IATI activities XML, not
just the bundled sample - see data.py.

Cada query pasa `xml_source()` como fuente; los datos crudos de la tabla los
embebe `h.text_result` en el texto para la IA (ver helpers/format.py).
"""
from mcp_iati import helpers as h
from mcp_iati.activities.data import activities_df, transactions_df, xml_source


def buscar_actividades(texto: str, limit: int = 10):
    """Search IATI activities by a substring of their title."""
    df = activities_df()
    matches = df[df["title"].str.contains(texto, case=False, na=False)].head(limit)

    if matches.empty:
        return h.empty_result(
            f"No se encontraron actividades IATI con '{texto}' en el título.",
            source_url=xml_source(),
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
    return h.text_result(text, source_url=xml_source(), table=table)


def resumen_actividad(iati_identifier: str):
    """Return title, status and total committed/disbursed amounts for one IATI activity."""
    activities = activities_df()
    activity = activities[activities["activity_identifier"] == iati_identifier]

    if activity.empty:
        return h.empty_result(
            f"No se encontró ninguna actividad IATI con identificador '{iati_identifier}'.",
            source_url=xml_source(),
        )

    row = activity.iloc[0]
    status_label = h.activity_status_label(row["activity_status"])

    txns = transactions_df()
    txns = txns[txns["activity_identifier"] == iati_identifier]
    totals = txns.groupby("transaction_type")["value"].sum()
    currency = row.get("default_currency") or ""

    # El texto lleva sólo el encabezado; los totales por tipo van en la tabla,
    # que `text_result` embebe completa en el texto para la IA.
    lines = [
        f"{row['title']} ({iati_identifier})",
        f"Estado: {status_label}",
        f"Organización reportante: {row.get('reporting_org_name') or row.get('reporting_org_ref')}",
    ]
    table = [["Tipo de transacción", "Total", "Moneda"]]
    for code, total in totals.items():
        table.append([h.transaction_type_label(code), h.format_amount(total), currency])

    return h.text_result("\n".join(lines), source_url=xml_source(), table=table)
