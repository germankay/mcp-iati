"""
Regresión de las queries sobre datos sintéticos (ver `seed_cache` en
conftest.py: cache precargado, sin red).
"""

from mcp_iati.activities import queries


def _text(result):
    return result.content[0].text


def test_buscar_actividades_preserves_table_and_source(seed_cache):
    result = queries.buscar_actividades("transporte")

    assert _text(result).startswith(
        "Se encontraron 1 actividad(es) IATI que coinciden con 'transporte'."
    )
    assert result.structuredContent["table"] == [
        ["Identificador IATI", "Título", "Estado"],
        ["IATI-001", "Programa de transporte sostenible", "Implementation"],
    ]
    assert result.structuredContent["sources"] == [seed_cache.source]


def test_buscar_actividades_preserves_empty_response(seed_cache):
    result = queries.buscar_actividades("inexistente")

    assert _text(result) == (
        "No se encontraron actividades IATI con 'inexistente' en el título."
    )
    assert "table" not in result.structuredContent
    assert result.structuredContent["sources"] == [seed_cache.source]


def test_resumen_actividad_preserves_details_totals_and_currency(seed_cache):
    result = queries.resumen_actividad("IATI-001")
    text = _text(result)

    assert "Programa de transporte sostenible (IATI-001)" in text
    assert "Estado: Implementation" in text
    assert "Organización reportante: Banco de Desarrollo" in text
    # Los totales viajan en la tabla (y embebidos en el texto vía text_result).
    assert "Out Commitment | 1,500.00 | USD" in text
    assert "Disbursement | 750.00 | USD" in text

    assert result.structuredContent["table"] == [
        ["Tipo de transacción", "Total", "Moneda"],
        ["Out Commitment", "1,500.00", "USD"],
        ["Disbursement", "750.00", "USD"],
    ]
    assert result.structuredContent["sources"] == [seed_cache.source]


def test_resumen_actividad_falls_back_to_org_ref(seed_cache):
    result = queries.resumen_actividad("IATI-002")

    assert "Organización reportante: ORG-002" in _text(result)


def test_resumen_actividad_preserves_not_found_response(seed_cache):
    result = queries.resumen_actividad("UNKNOWN")

    assert _text(result) == (
        "No se encontró ninguna actividad IATI con identificador 'UNKNOWN'."
    )
    assert "table" not in result.structuredContent
    assert result.structuredContent["sources"] == [seed_cache.source]
