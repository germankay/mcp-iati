"""
Garantiza que la respuesta que recibe la IA (el texto de `content`) incluye los
DATOS CRUDOS, no sólo un resumen.

Contexto: el gateway manda a la IA únicamente `content[0].text`; la tabla de
`structuredContent` se renderiza sólo para el usuario. Por eso `text_result`
embebe la tabla como texto en `content`. Si esto se rompe, la IA analiza a
ciegas (por ejemplo, no ve los identificadores que devuelve buscar_actividades
y no puede encadenar resumen_actividad).
"""

import pytest

from mcp_iati import helpers as h
from mcp_iati.helpers.format import _table_to_text
from mcp_iati.activities import queries


def _text(res):
    return res.content[0].text


# ─── Unit: el builder text_result embebe la tabla cruda ───────────────────

def test_text_result_embeds_full_table_verbatim():
    table = [
        ["Identificador IATI", "Título", "Estado"],
        ["IATI-001", "Programa A", "Implementation"],
        ["IATI-002", "Programa B", "Finalisation"],
    ]
    res = h.text_result("resumen", source_url="http://src", table=table)

    txt = _text(res)
    # El bloque de datos para la IA está presente...
    assert "=== Datos completos" in txt
    # ...y contiene la tabla COMPLETA verbatim (no sólo la última fila).
    assert _table_to_text(table) in txt
    for row in table:
        for cell in row:
            assert cell in txt
    # structuredContent (lo que ve el usuario) queda intacto.
    assert res.structuredContent["table"] == table
    assert res.structuredContent["sources"] == ["http://src"]


def test_text_result_sin_tabla_no_agrega_bloque():
    res = h.text_result("solo texto", source_url="http://src")
    txt = _text(res)
    assert "=== Datos completos" not in txt
    assert "table" not in res.structuredContent


def test_text_result_appends_guardrail():
    res = h.text_result("texto", source_url="http://src")
    assert h.SIN_ESPECULAR in _text(res)


def test_table_to_text_formato_pipe():
    table = [["a", "b"], ["1", "2"]]
    assert _table_to_text(table) == "a | b\n1 | 2"
    assert _table_to_text([]) == ""


# ─── Contrato: TODA tool de datos manda la tabla cruda a la IA ────────────

# (nombre, callable, kwargs) para cada tool de datos del repo. Al agregar una
# tool nueva que devuelva tabla, sumarla acá.
DATA_TOOLS = [
    ("buscar_actividades", queries.buscar_actividades, {"texto": "Programa"}),
    ("resumen_actividad", queries.resumen_actividad, {"iati_identifier": "IATI-001"}),
]


@pytest.mark.parametrize("name,fn,kwargs", DATA_TOOLS, ids=[t[0] for t in DATA_TOOLS])
def test_tool_embeds_full_table_in_ai_text(seed_cache, name, fn, kwargs):
    res = fn(**kwargs)
    txt = _text(res)
    sc = res.structuredContent

    # 1. La tool produjo una tabla (datos para el usuario).
    assert "table" in sc, f"{name}: no devolvió tabla"
    assert len(sc["table"]) >= 2, f"{name}: tabla sin filas de datos"

    # 2. Esa MISMA tabla completa está embebida en el texto que recibe la IA.
    assert "=== Datos completos" in txt, f"{name}: falta el bloque de datos"
    assert _table_to_text(sc["table"]) in txt, (
        f"{name}: la tabla del usuario no está verbatim en el texto de la IA"
    )
