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

**Guiding principle:** these tools only use generic IATI standard fields
(identifier, status, transaction type), never Brazil- or IADB-specific logic -
they must work just as well with any other IATI XML (see the
`MCP_IATI_SAMPLE` and `MCP_IATI_XML_PATH` variables below).

## Where the data comes from

The sample XMLs are real-life data but are **not versioned in this repo**:
they are downloaded on demand from `data-samples/xml/` in the
[okfn/okfn_iati](https://github.com/okfn/okfn_iati) repo into the user data
directory (`~/.local/share/mcp-iati/xml/` on Linux, via `platformdirs`), only
once. The `.gitignore` excludes any `*.xml` just in case.

## How the XML is processed

1. `mcp_iati/activities/data.py` converts the configured XML to flat CSVs
   once per process, using `okfn_iati.IatiMultiCsvConverter().xml_to_csv_folder(...)`
   (the same library `ckanext-iati-generator` uses in production, but in the
   XML -> CSV direction instead of CSV -> XML).
2. The tools (`mcp_iati/activities/queries.py`) query those CSVs with
   `pandas`, not the XML - this avoids reparsing a multi-MB file on every
   call.
3. It uses `iadb-Brazil.xml` by default. To use another sample from the
   `okfn_iati` repo (downloaded automatically) or a local file, without
   touching code:

   ```bash
   # another sample from https://github.com/okfn/okfn_iati/tree/main/data-samples/xml
   export MCP_IATI_SAMPLE=iadb-Argentina.xml

   # or any local file (downloads nothing)
   export MCP_IATI_XML_PATH=/path/to/another-iati-file.xml
   ```

## Development

```bash
# Install dependencies (mcp-server from git, okfn-iati from PyPI)
uv sync

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
organisations, and between commitment, disbursement and expenditure.

| Term | Definition |
| --- | --- |
| IATI activity | A development or cooperation intervention; it can be a project, a programme or another unit of work. |
| IATI identifier | Globally unique code for an activity, also used to link its transactions. |
| Reporting organisation | Organisation responsible for publishing and maintaining the data; not necessarily funding or implementing. |
| Activity status | Lifecycle stage, such as pipeline, implementation or closed. |
| Transaction | Financial movement associated with an activity, with type, date, value and currency. |
| Commitment | Financial obligation undertaken to provide funds. |
| Disbursement | Funds made available or transferred for an activity. |
| Expenditure | Funds spent on the activity by the reporting or another organisation. |
| Default currency | Currency used when a value does not specify another one. |
| Participating organisation | Organisation linked with a role, such as funding, implementation or accountability. |
| Sector | Thematic or economic area classified via a code. |
| Recipient country or region | Location receiving the intended benefits of the activity. |

When adding a new tool, reuse the definitions from the central module
instead of duplicating them in its docstring.

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
