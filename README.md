# MCP IATI

**Note:** Local proof of concept. Starting point for a future `mcp-server`
plugin that processes files following the
[IATI](https://iatistandard.org/) standard (activities and organisations):
documented Python tools, with `plugin_info`/`instructions`/`sample_questions`,
a `no_tool_disponible` fallback tool and a tools module separate from the
registration wiring.

For now it defines two real tools over a sample IATI XML (IADB activities in
Brazil, `iadb-Brazil.xml`, downloaded on demand from
[okfn/okfn_iati](https://github.com/okfn/okfn_iati/tree/main/data-samples/xml)):

- `search_activities(text, limit=10)`: search activities by title.
- `activity_summary(iati_identifier)`: title, status and committed/disbursed
  totals for one activity.
- `define_term(term)`: explain what an IATI term means ("what does X
  mean?"), from the central glossary.

**Guiding principle:** these tools only use generic IATI standard fields
(identifier, status, transaction type), never Brazil- or IADB-specific logic -
they must work just as well with any other IATI XML (see the configuration
variables below).

## Where the data comes from

The sample XMLs are real-life data but are **not versioned in this repo**:
they are downloaded on demand from `data-samples/xml/` in the
[okfn/okfn_iati](https://github.com/okfn/okfn_iati) repo into the user data
directory (`~/.local/share/mcp-iati/xml/` on Linux, via `platformdirs`) and
refreshed when its configured TTL expires. The `.gitignore` excludes any
`*.xml` just in case.

## How the XML is processed

1. `mcp_iati/activities/data.py` converts the configured XML to flat CSVs and
   reuses the source-specific cache until its TTL expires, using
   `okfn_iati.IatiMultiCsvConverter().xml_to_csv_folder(...)`
   (the same library `ckanext-iati-generator` uses in production, but in the
   XML -> CSV direction instead of CSV -> XML).
2. The tools (`mcp_iati/activities/queries.py`) query those CSVs with
   `pandas`, not the XML - this avoids reparsing a multi-MB file on every
   call.
3. It uses `iadb-Brazil.xml` by default. To use another sample from the
   `okfn_iati` repo, a remote URL or a local file, without touching code:

   ```bash
   # another sample from https://github.com/okfn/okfn_iati/tree/main/data-samples/xml
   export MCP_IATI_SAMPLE=iadb-Argentina.xml

   # or any remote IATI XML
   export MCP_IATI_XML_URL=https://example.org/activities.xml

   # or any local file (downloads nothing)
   export MCP_IATI_XML_PATH=/path/to/another-iati-file.xml
   ```

## Configuration

Configuration is read once when the process starts. Restart the server after
changing the source, data directory or cache duration.

| Variable | Description | Default |
| --- | --- | --- |
| `MCP_IATI_XML_PATH` | Path to a local XML. It has priority and performs no download. | Not set. |
| `MCP_IATI_XML_URL` | HTTP(S) URL of a remote XML, used when no local path is configured. | Not set. |
| `MCP_IATI_SAMPLE` | Name of an `okfn-iati` sample, used when neither a path nor URL is configured. | `iadb-Brazil.xml`. |
| `MCP_IATI_DATA_DIR` | Directory for downloaded XML files and generated CSV files. | User data directory provided by `platformdirs`. |
| `MCP_IATI_CACHE_TTL_SECONDS` | Configurable cache duration in seconds; must be greater than zero. | `604800` (7 days). |

Downloaded XML files and converted CSV folders are reused while they remain
inside this TTL. Once it expires, the XML is downloaded again and the CSVs
are regenerated. CSV caches use a key derived from the configured origin, so
Argentina, Brazil and custom URLs never share the same converted files.
If a remote refresh fails and a previous XML exists, that stale copy is used
with a runtime warning instead of making the tools unavailable.

The source precedence is:

1. `MCP_IATI_XML_PATH`.
2. `MCP_IATI_XML_URL`.
3. `MCP_IATI_SAMPLE`.
4. The default `iadb-Brazil.xml` sample.

Example:

```bash
export MCP_IATI_XML_URL=https://example.org/iadb-Argentina.xml
export MCP_IATI_DATA_DIR=/var/cache/mcp-iati
export MCP_IATI_CACHE_TTL_SECONDS=604800
uv run mcp-server
```

### CSV tables used by the plugin

| Table | Columns currently used | Relationship |
|---|---|---|
| `activities.csv` | `activity_identifier`, `title`, `activity_status`, `reporting_org_name`, `reporting_org_ref`, `default_currency` | `activity_identifier` identifies the activity |
| `transactions.csv` | `activity_identifier`, `transaction_type`, `value` | `activity_identifier` references `activities.csv` |

CSV files are loaded with pandas and cached in memory. Repeated tool calls
reuse the same DataFrame instances. Transaction values are converted to
numeric values, while identifiers and categorical columns remain strings.

The data preparation and conversion logic is kept separate from the query
logic. Additional CSV tables can be added through `DATAFRAME_SPECS`.


## Development

```bash
# Install dependencies (mcp-server from git, okfn-iati from PyPI;
# the dev extra brings ruff and pytest)
uv sync --extra dev

# Lint
uv run ruff check src
```

## Adding this to a local mcp-server

From the `mcp-server/` folder, install this package into the same virtual
environment:

```bash
uv pip install -e ../mcp-iati
uv run mcp-server
```

The tools become available with the `mcp_iati_` prefix.

## IATI glossary

The tool descriptions and the plugin instructions share a central glossary
defined in `src/mcp_iati/glossary.py`. Its goal is that the model interprets
the standard's terms consistently and explains the distinctions that tend to
be ambiguous, especially between reporting, funding and implementing
organisations, and between commitment, disbursement and expenditure. The
`define_term` tool exposes it directly, so questions like "what does
'disbursement' mean?" are answered from the glossary (with the IATI standard
as the cited source) instead of from the model's own knowledge.

The glossary covers the whole IATI 2.03 activity standard as modelled by the
[okfn/okfn_iati](https://github.com/okfn/okfn_iati) library (its enums mirror
the IATI codelists and its converter flattens each element to a CSV), grouped
in these areas:

| Area | Terms |
| --- | --- |
| Identification and lifecycle | IATI activity, IATI identifier, activity status, activity date, description, hierarchy, related activity, activity scope, humanitarian flag |
| Organisations | reporting organisation, participating organisation, organisation role, organisation type, provider organisation, receiver organisation, contact information |
| Financial data | transaction, transaction type, transaction value, commitment, disbursement, expenditure, budget, planned disbursement, default currency, country budget item |
| Aid classifications | aid type, finance type, flow type, tied status, collaboration type, disbursement channel, policy marker |
| Sectors and geography | sector, recipient country or region, location |
| Results and monitoring | result, indicator, indicator period |
| Documentation and cross-cutting | document link, condition, vocabulary, codelist, narrative |

When adding a new tool, reuse the definitions from the central module
instead of duplicating them in its docstring (via `glossary_text(...)` for
the relevant terms). When the underlying library starts exposing a new IATI
element, add its term to the glossary in the matching group.

## Tests

```bash
uv run pytest
```

The tests run offline: `tests/conftest.py` preloads the data cache with
synthetic DataFrames and sets `MCP_IATI_XML_PATH`, so nothing is downloaded.
They cover:

- that the glossary includes the minimum concepts and that the tool
  descriptions expose the relevant terms to the model;
- regression of the queries (tables, sources, empty cases);
- the **raw-data contract** (`test_raw_data_in_ai_response.py`): the gateway
  sends the AI only the text of the response, so every tool that returns a
  table must embed it verbatim in that text (done by `helpers.text_result`).
  When adding a new tool with a table, add it to the `DATA_TOOLS` list in
  that test.

On GitHub, `.github/workflows/python-lint.yml` runs ruff + pytest on every
push.
