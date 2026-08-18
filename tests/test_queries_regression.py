import pandas as pd

from mcp_iati import _register_iati_tools
from mcp_iati.activities import queries


SOURCE = "/data/iadb-Brazil.xml"


def _result_text(result):
    return result.content[0].text


def _result_table(result):
    return result.structuredContent["table"]


def _patch_source(monkeypatch):
    monkeypatch.setattr(
        "mcp_iati.helpers.format.xml_source",
        lambda: SOURCE,
    )


def test_buscar_actividades_preserves_table_and_source(monkeypatch):
    activities = pd.DataFrame(
        [
            {
                "activity_identifier": "IATI-001",
                "title": "Programa de transporte sostenible",
                "activity_status": "2",
            },
            {
                "activity_identifier": "IATI-002",
                "title": "Programa de salud",
                "activity_status": "3",
            },
        ]
    )

    monkeypatch.setattr(queries, "activities_df", lambda: activities)
    _patch_source(monkeypatch)

    result = queries.buscar_actividades("transporte")

    assert _result_text(result) == (
        "Se encontraron 1 actividad(es) IATI que coinciden con "
        "'transporte'."
    )
    assert _result_table(result) == [
        ["Identificador IATI", "Título", "Estado"],
        [
            "IATI-001",
            "Programa de transporte sostenible",
            "Implementation",
        ],
    ]
    assert result.structuredContent["sources"] == [SOURCE]


def test_buscar_actividades_preserves_empty_response(monkeypatch):
    activities = pd.DataFrame(
        [
            {
                "activity_identifier": "IATI-001",
                "title": "Programa de salud",
                "activity_status": "2",
            }
        ]
    )

    monkeypatch.setattr(queries, "activities_df", lambda: activities)
    _patch_source(monkeypatch)

    result = queries.buscar_actividades("transporte")

    assert _result_text(result) == (
        "No se encontraron actividades IATI con "
        "'transporte' en el título."
    )
    assert "table" not in result.structuredContent
    assert result.structuredContent["sources"] == [SOURCE]


def test_resumen_actividad_preserves_details_totals_and_currency(
    monkeypatch,
):
    activities = pd.DataFrame(
        [
            {
                "activity_identifier": "IATI-001",
                "title": "Programa de transporte",
                "activity_status": "2",
                "reporting_org_name": "Banco de Desarrollo",
                "reporting_org_ref": "ORG-001",
                "default_currency": "USD",
            }
        ]
    )
    transactions = pd.DataFrame(
        [
            {
                "activity_identifier": "IATI-001",
                "transaction_type": "2",
                "value": 1000.0,
            },
            {
                "activity_identifier": "IATI-001",
                "transaction_type": "2",
                "value": 500.0,
            },
            {
                "activity_identifier": "IATI-001",
                "transaction_type": "3",
                "value": 750.0,
            },
        ]
    )

    monkeypatch.setattr(queries, "activities_df", lambda: activities)
    monkeypatch.setattr(
        queries,
        "transactions_df",
        lambda: transactions,
    )
    _patch_source(monkeypatch)

    result = queries.resumen_actividad("IATI-001")
    text = _result_text(result)

    assert "Programa de transporte (IATI-001)" in text
    assert "Estado: Implementation" in text
    assert "Organización reportante: Banco de Desarrollo" in text
    assert "Out Commitment: 1,500.00 USD" in text
    assert "Disbursement: 750.00 USD" in text

    assert _result_table(result) == [
        ["Tipo de transacción", "Total", "Moneda"],
        ["Out Commitment", "1,500.00", "USD"],
        ["Disbursement", "750.00", "USD"],
    ]
    assert result.structuredContent["sources"] == [SOURCE]


def test_resumen_actividad_preserves_not_found_response(monkeypatch):
    activities = pd.DataFrame(
        columns=[
            "activity_identifier",
            "title",
            "activity_status",
        ]
    )

    monkeypatch.setattr(queries, "activities_df", lambda: activities)
    _patch_source(monkeypatch)

    result = queries.resumen_actividad("UNKNOWN")

    assert _result_text(result) == (
        "No se encontró ninguna actividad IATI con "
        "identificador 'UNKNOWN'."
    )
    assert "table" not in result.structuredContent
    assert result.structuredContent["sources"] == [SOURCE]


class FakeMCP:
    def __init__(self):
        self.tools = {}

    def set_plugin_info(self, **kwargs):
        self.plugin_info = kwargs

    def tool(self):
        def decorator(function):
            self.tools[function.__name__] = function
            return function

        return decorator


def test_no_tool_disponible_preserves_empty_sources():
    mcp = FakeMCP()
    _register_iati_tools(mcp)

    result = mcp.tools["no_tool_disponible"](
        razon="la consulta no corresponde a datos IATI"
    )

    assert _result_text(result) == (
        "Este plugin (mcp-iati) responde únicamente sobre las "
        "actividades IATI cargadas. Motivo: la consulta no "
        "corresponde a datos IATI."
    )
    assert result.structuredContent["sources"] == []
