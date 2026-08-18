from mcp_server import DataToolOutput

from mcp_iati import helpers as h
from mcp_iati.activities import queries as activities
from mcp_iati.glossary import full_glossary_text, glossary_text


def register_tools(mcp):
    """Entry point invoked by mcp-server (see the `mcp_server` entry point in pyproject.toml)."""
    _register_iati_tools(mcp)


def _register_iati_tools(mcp):  # noqa: C901
    """IATI - tools over the international aid transparency open data
    standard (https://iatistandard.org/).

    By default it operates on a sample IATI XML (IADB activities in Brazil,
    see okfn_iati/data-samples/xml/iadb-Brazil.xml), but the tools only use
    generic IATI standard fields (identifier, status, transaction type) so
    they work just as well with any other IATI XML (configurable via
    MCP_IATI_XML_PATH).
    """
    mcp.set_plugin_info(
        description=(
            "Tools for querying activities and transactions published under "
            "the IATI open data standard for development cooperation."
        ),
        instructions=(
            "You are an assistant for querying IATI data. Interpret questions "
            "using the glossary below and explain the terms whenever there may "
            "be ambiguity. Do not confuse the reporting organisation with the "
            "one funding or implementing an activity, nor a commitment with a "
            "disbursement or an expenditure. Use only the data returned by the "
            "tools; if a question falls outside their scope, call "
            "no_tool_disponible explaining why.\n\n"
            "IATI glossary:\n" + full_glossary_text()
        ),
        sample_questions=[
            "Search IATI activities about transport",
            "Give me a summary of activity XI-IATI-IADB-BR-L1231",
            "What does it mean for an activity to be in implementation?",
            "How much was committed and how much was disbursed in this activity?",
            "Is the reporting organisation also the one funding the project?",
        ],
    )

    # The tool name stays `no_tool_disponible`: the base server's system
    # preamble instructs the model to call the fallback tool whose name ends
    # in that suffix (see mcp-server registry.py), for every plugin.
    @mcp.tool()
    def no_tool_disponible(reason: str | None = None) -> DataToolOutput:
        """Call when no other tool can answer the question: topics that are
            not IATI activities, or questions outside the scope of the
            loaded data.

        Args:
            reason: Brief explanation (1 sentence) of why no tool applies.

        Examples:
            - no_tool_disponible(reason="not a question about IATI activities")
        """
        msg = "This plugin (mcp-iati) only answers questions about the loaded IATI activities."
        if reason:
            msg += f" Reason: {reason}."
        return h.text_result(msg, source_url="")

    def search_activities(text: str, limit: int = 10) -> DataToolOutput:
        return activities.search_activities(text, limit=limit)

    search_activities.__doc__ = (
        """Search IATI activities whose title contains the given text.

        Useful as a first step to discover an activity's IATI identifier,
        before requesting its summary with activity_summary.

        Args:
            text: Substring to search for in the title (case-insensitive).
            limit: Maximum number of results to return. Default: 10.

        Returns:
            A table with the IATI identifier, title and status of each match.

        Relevant IATI terms:
        """
        + glossary_text("IATI activity", "IATI identifier", "activity status")
    )
    mcp.tool()(search_activities)

    def activity_summary(iati_identifier: str) -> DataToolOutput:
        return activities.activity_summary(iati_identifier)

    activity_summary.__doc__ = (
        """Return the title, status, reporting organisation and totals per
        transaction type of an IATI activity.

        Args:
            iati_identifier: IATI identifier, for example "XI-IATI-IADB-BR-L1231".
                Obtained with search_activities.

        Relevant IATI terms:
        """
        + glossary_text(
            "IATI identifier",
            "reporting organisation",
            "activity status",
            "transaction",
            "commitment",
            "disbursement",
            "expenditure",
            "default currency",
        )
    )
    mcp.tool()(activity_summary)


def main() -> None:
    print("Hello from mcp-iati")
