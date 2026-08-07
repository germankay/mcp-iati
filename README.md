# MCP IATI

**Nota:** Carpeta de prueba local. Todavía no está pensada para commitear a
GitHub — es un punto de partida para un futuro plugin `mcp-server` que
procese archivos del estándar [IATI](https://iatistandard.org/) (actividades
y organizaciones), inspirado en los plugins existentes
[`mcp-datos-uruguay-ben`](../mcp-datos-uruguay-ben/README.md) (tools en
Python bien documentadas, con `plugin_info`/`instructions`/`sample_questions`
y una tool de fallback `no_tool_disponible`) y
[`mcp-dados-brasil`](../mcp-dados-brasil/README.md) (estructura de paquete
simple, un módulo de tools separado del wiring de registro).

Por ahora define dos tools reales sobre un XML IATI de muestra (actividades
del BID en Brasil, ver [`okfn_iati/data-samples/xml/iadb-Brazil.xml`](../okfn_iati/data-samples/xml/iadb-Brazil.xml)):

- `buscar_actividades(texto, limit=10)`: busca actividades por título.
- `resumen_actividad(iati_identifier)`: título, estado y totales
  comprometido/desembolsado de una actividad.

**Principio guía:** estas tools solo usan campos genéricos del estándar IATI
(identificador, estado, tipo de transacción), no lógica específica de Brasil
o del BID — deben servir igual para cualquier otro XML IATI (ver la variable
`MCP_IATI_XML_PATH` más abajo).

## Cómo procesa el XML

1. `mcp_iati/activities/data.py` convierte el XML configurado a CSVs planos
   una sola vez por proceso, usando `okfn_iati.IatiMultiCsvConverter().xml_to_csv_folder(...)`
   (la misma librería que usa `ckanext-iati-generator` en producción, pero en
   sentido XML → CSV en vez de CSV → XML).
2. Las tools (`mcp_iati/activities/queries.py`) consultan esos CSV con
   `pandas`, no el XML — así se evita reparsear un archivo de varios MB en
   cada llamada.
3. Por defecto usa `iadb-Brazil.xml`. Para apuntar a otro archivo (por
   ejemplo `iadb-Argentina.xml`) sin tocar código:

   ```bash
   export MCP_IATI_XML_PATH=/ruta/a/otro-archivo-iati.xml
   ```

## Desarrollo

```bash
# Instalar dependencias (usa el mcp-server y el okfn_iati locales del monorepo, ver [tool.uv.sources])
uv sync

# Lint
uv run ruff check src
```

## Agregar esto a un mcp-server local

Desde la carpeta `mcp-server/`, instalá este paquete en el mismo entorno virtual:

```bash
uv pip install -e ../mcp-iati
uv run mcp-server
```

Las tools quedarán disponibles con el prefijo `mcp_iati_`.

