"""
Fixtures de test para las tools IATI.

`seed_cache` precarga el cache de `activities/data.py` con DataFrames
sintéticos (sin red ni conversión XML→CSV) y fija `MCP_IATI_XML_PATH` a una
ruta local para que `xml_source()` no dispare descargas. `activities_df` /
`transactions_df` devuelven el cache si la key existe, así que basta con
poblar `data._cache`.

`fake_mcp` es un doble del registry de mcp-server que captura `plugin_info`
y las tools registradas, por nombre y en orden de registro.
"""

from types import SimpleNamespace

import pandas as pd
import pytest

from mcp_iati.activities import data as data_mod


# Ruta local ficticia: xml_source() la devuelve tal cual (sin descargar) y
# las queries la reportan como fuente.
FAKE_XML = "/data/fake-iati-sample.xml"


def _activities_df():
    return pd.DataFrame(
        [
            {
                "activity_identifier": "IATI-001",
                "title": "Programa de transporte sostenible",
                "activity_status": "2",
                "reporting_org_name": "Banco de Desarrollo",
                "reporting_org_ref": "ORG-001",
                "default_currency": "USD",
            },
            {
                "activity_identifier": "IATI-002",
                "title": "Programa de salud",
                "activity_status": "3",
                "reporting_org_name": "",
                "reporting_org_ref": "ORG-002",
                "default_currency": "USD",
            },
        ]
    )


def _transactions_df():
    return pd.DataFrame(
        [
            {"activity_identifier": "IATI-001", "transaction_type": "2", "value": 1000.0},
            {"activity_identifier": "IATI-001", "transaction_type": "2", "value": 500.0},
            {"activity_identifier": "IATI-001", "transaction_type": "3", "value": 750.0},
        ]
    )


@pytest.fixture
def seed_cache(monkeypatch):
    """Precarga el cache de datos y lo limpia al terminar."""
    monkeypatch.setenv("MCP_IATI_XML_PATH", FAKE_XML)
    data_mod._cache.clear()
    data_mod._cache["activities"] = _activities_df()
    data_mod._cache["transactions"] = _transactions_df()
    yield SimpleNamespace(
        source=FAKE_XML,
        activities=data_mod._cache["activities"],
        transactions=data_mod._cache["transactions"],
    )
    data_mod._cache.clear()


class FakeMCP:
    def __init__(self):
        self.plugin_info = None
        self.tools = {}

    def set_plugin_info(self, **kwargs):
        self.plugin_info = kwargs

    def tool(self):
        def decorator(func):
            self.tools[func.__name__] = func
            return func

        return decorator


@pytest.fixture
def fake_mcp():
    return FakeMCP()
