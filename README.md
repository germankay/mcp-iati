# MCP IATI

**Nota:** Carpeta de prueba local. Es un punto de partida para un futuro plugin `mcp-server` que
procese archivos del estándar [IATI](https://iatistandard.org/) (actividades
y organizaciones): tools en Python documentadas, con
`plugin_info`/`instructions`/`sample_questions`, una tool de fallback
`no_tool_disponible` y un módulo de tools separado del wiring de registro.

Por ahora define dos tools reales sobre un XML IATI de muestra (actividades
del BID en Brasil, `iadb-Brazil.xml`, descargado bajo demanda desde
[okfn/okfn_iati](https://github.com/okfn/okfn_iati/tree/main/data-samples/xml)):

- `buscar_actividades(texto, limit=10)`: busca actividades por título.
- `resumen_actividad(iati_identifier)`: título, estado y totales
  comprometido/desembolsado de una actividad.

**Principio guía:** estas tools solo usan campos genéricos del estándar IATI
(identificador, estado, tipo de transacción), no lógica específica de Brasil
o del BID — deben servir igual para cualquier otro XML IATI (ver las variables
`MCP_IATI_SAMPLE` y `MCP_IATI_XML_PATH` más abajo).

## De dónde salen los datos

Los XML de muestra son datos reales pero **no se versionan en este repo**: se
descargan bajo demanda desde `data-samples/xml/` del repo
[okfn/okfn_iati](https://github.com/okfn/okfn_iati) al directorio de datos del
usuario (`~/.local/share/mcp-iati/xml/` en Linux, via `platformdirs`), una
sola vez. El `.gitignore` excluye cualquier `*.xml` por las dudas.

## Cómo procesa el XML

1. `mcp_iati/activities/data.py` convierte el XML configurado a CSVs planos
   una sola vez por proceso, usando `okfn_iati.IatiMultiCsvConverter().xml_to_csv_folder(...)`
   (la misma librería que usa `ckanext-iati-generator` en producción, pero en
   sentido XML → CSV en vez de CSV → XML).
2. Las tools (`mcp_iati/activities/queries.py`) consultan esos CSV con
   `pandas`, no el XML — así se evita reparsear un archivo de varios MB en
   cada llamada.
3. Por defecto usa `iadb-Brazil.xml`. Para usar otra muestra del repo
   `okfn_iati` (se descarga sola) o un archivo local, sin tocar código:

   ```bash
   # otra muestra de https://github.com/okfn/okfn_iati/tree/main/data-samples/xml
   export MCP_IATI_SAMPLE=iadb-Argentina.xml

   # o un archivo local cualquiera (no descarga nada)
   export MCP_IATI_XML_PATH=/ruta/a/otro-archivo-iati.xml
   ```

## Desarrollo

```bash
# Instalar dependencias (mcp-server desde git, okfn-iati desde PyPI)
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

## Glosario IATI

Las descripciones de las tools y las instrucciones del plugin comparten un
glosario central definido en `src/mcp_iati/glossary.py`. Su objetivo es que el
modelo interprete de forma consistente los términos del estándar y explique
las diferencias que suelen ser ambiguas, especialmente entre organización
reportante, financiadora y ejecutora, y entre compromiso, desembolso y gasto.

| Término | Definición |
| --- | --- |
| Actividad IATI | Intervención de cooperación o desarrollo; puede ser un proyecto, programa u otra unidad de trabajo. |
| Identificador IATI | Código global y único de una actividad, usado también para vincular sus transacciones. |
| Organización reportante | Organización responsable de publicar y mantener los datos; no necesariamente financia o ejecuta. |
| Estado de actividad | Etapa del ciclo de vida, como planificación, ejecución o cierre. |
| Transacción | Movimiento financiero asociado a una actividad, con tipo, fecha, valor y moneda. |
| Compromiso | Obligación financiera asumida para aportar fondos. |
| Desembolso | Fondos puestos a disposición o transferidos para una actividad. |
| Gasto | Fondos utilizados en la actividad por la organización reportante u otra organización. |
| Moneda predeterminada | Moneda usada cuando un valor no especifica otra. |
| Organización participante | Organización vinculada con un rol, como financiación, implementación o rendición. |
| Sector | Área temática o económica clasificada mediante un código. |
| País o región receptora | Ubicación que recibe los beneficios previstos de la actividad. |

Cuando se agregue una nueva tool, se deben reutilizar las definiciones del
módulo central en lugar de duplicarlas en su docstring.

## Pruebas

```bash
uv run pytest
```

Las pruebas corren offline: `tests/conftest.py` precarga el cache de datos con
DataFrames sintéticos y fija `MCP_IATI_XML_PATH`, así que no descargan nada.
Cubren:

- que el glosario incluya los conceptos mínimos y que las descripciones de las
  tools expongan los términos pertinentes al modelo;
- regresión de las queries (tablas, fuentes, casos vacíos);
- el **contrato de datos crudos** (`test_raw_data_in_ai_response.py`): el
  gateway le manda a la IA solamente el texto de la respuesta, así que toda
  tool que devuelva tabla debe embeberla verbatim en ese texto (lo hace
  `helpers.text_result`). Al agregar una
  tool nueva con tabla, sumarla a la lista `DATA_TOOLS` de ese test.

En GitHub, `.github/workflows/python-lint.yml` corre ruff + pytest en cada
push.
