from mcp_server import DataToolOutput

from mcp_iati import helpers as h
from mcp_iati import terms
from mcp_iati.activities.data import prepare_data
from mcp_iati.activities import queries as activities
from mcp_iati.glossary import tool_glossary_text


def register_tools(mcp):
    """Entry point invoked by mcp-server (see the `mcp_server` entry point in pyproject.toml)."""
    prepare_data()
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
            "You are an assistant for querying IATI data. Use the definitions "
            "attached to the selected tool and its successful response. Explain "
            "only the IATI terms relevant to the user's question and do not add "
            "unrelated glossary entries. Do not confuse the reporting organisation "
            "with the organisation funding or implementing an activity, nor a "
            "commitment with a disbursement or an expenditure. Use only the data "
            "returned by the tools. When the user asks what a term means, call "
            "define_term. If a question falls outside the tools' scope, call "
            "no_tool_disponible and explain why."
        ),
        sample_questions=[
            "Search IATI activities about transport",
            "Give me a summary of activity XI-IATI-IADB-BR-L1231",
            "What does it mean for an activity to be in implementation?",
            "What is a policy marker?",
            "How much was committed and how much was disbursed in this activity?",
            "Is the reporting organisation also the one funding the project?",
            "What activity statuses are present in this IATI file?",
            "Which organisations report activities in this IATI file?",
            "Which recipient countries are present in this IATI file?",
            "Which IATI activities have Brazil as their recipient country?",
            "Which sectors are present in this IATI file?",
            "Show the transactions for activity XI-IATI-IADB-BR-L1231",
            "How much was committed and disbursed each year?",
            "How much was committed and disbursed by each reporting organisation?",
            "How much was committed by sector?",
            "How much was disbursed by sector in USD?",
            "How much was committed and disbursed by recipient country?",
            "Which activities have the highest commitment totals?",
            "Which activities have the highest disbursement totals in USD?",
            "Show annual commitments and disbursements from 2022 to 2024.",
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
        + tool_glossary_text("search_activities")
    )
    mcp.tool()(search_activities)

    def list_activity_statuses() -> DataToolOutput:
        return activities.list_activity_statuses()

    list_activity_statuses.__doc__ = (
        """List the activity statuses present in the loaded IATI data.

        Use this tool to discover which lifecycle statuses are available
        before filtering or analysing activities.

        Returns:
            A table containing each status code, its human-readable label
            and the number of activities using it.

        Relevant IATI terms:
        """
        + tool_glossary_text("list_activity_statuses")
    )
    mcp.tool()(list_activity_statuses)


    def list_reporting_organisations() -> DataToolOutput:
        return activities.list_reporting_organisations()

    list_reporting_organisations.__doc__ = (
        """List the organisations that report activities in the loaded
        IATI data.

        The reporting organisation is responsible for publishing and
        maintaining the activity data. It is not necessarily the funding
        or implementing organisation.

        Returns:
            A table containing the organisation reference, name and number
            of activities reported.

        Relevant IATI terms:
        """
        + tool_glossary_text("list_reporting_organisations")
    )
    mcp.tool()(list_reporting_organisations)


    def list_recipient_countries() -> DataToolOutput:
        return activities.list_recipient_countries()

    list_recipient_countries.__doc__ = (
        """List the recipient countries present in the loaded IATI data.

        Use this tool to discover which country codes are available before
        filtering activities by recipient country.

        Returns:
            A table containing the recipient country code, country name and
            number of related activities.

        Relevant IATI terms:
        """
        + tool_glossary_text("list_recipient_countries")
    )
    mcp.tool()(list_recipient_countries)

    def filter_activities_by_country(
        country: str,
        limit: int = 10,
    ) -> DataToolOutput:
        return activities.filter_activities_by_country(
            country,
            limit=limit,
        )

    filter_activities_by_country.__doc__ = (
        """Filter IATI activities by recipient country.

        The country may be provided as an ISO country code, such as "BR",
        or as the country name published in the IATI data, such as "Brazil".

        Use list_recipient_countries first when the available country codes
        or names are unknown.

        Args:
            country: Recipient country code or name.
            limit: Maximum number of activities to return. Default: 10.

        Returns:
            A table containing matching activity identifiers, titles,
            statuses and recipient-country information.

        Relevant IATI terms:
        """
        + tool_glossary_text("filter_activities_by_country")
    )
    mcp.tool()(filter_activities_by_country)


    def list_sectors(limit: int = 100) -> DataToolOutput:
        return activities.list_sectors(limit=limit)

    list_sectors.__doc__ = (
        """List the sectors present in the loaded IATI data.

        Use this tool to discover the available sector codes and
        vocabularies before performing sector-based analysis.

        Args:
            limit: Maximum number of sector values to return. Default: 100.

        Returns:
            A table containing vocabulary, sector code, sector name and
            number of related activities.

        Relevant IATI terms:
        """
        + tool_glossary_text("list_sectors")
    )
    mcp.tool()(list_sectors)


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
        + tool_glossary_text("activity_summary")
    )
    mcp.tool()(activity_summary)

    def activity_transactions(
        iati_identifier: str,
        limit: int = 50,
    ) -> DataToolOutput:
        return activities.activity_transactions(
            iati_identifier,
            limit=limit,
        )

    activity_transactions.__doc__ = (
        """List the transactions associated with an IATI activity.

        Transactions are returned in chronological order and include their
        type, value, currency and published description.

        Args:
            iati_identifier: IATI identifier of the activity.
            limit: Maximum number of transactions to return. Default: 50.

        Returns:
            A table containing the transactions associated with the
            requested activity.

        Relevant IATI terms:
        """
        + tool_glossary_text("activity_transactions")
    )
    mcp.tool()(activity_transactions)

    def transaction_totals_by_year(
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> DataToolOutput:
        return activities.transaction_totals_by_year(
            year_from=year_from,
            year_to=year_to,
        )

    transaction_totals_by_year.__doc__ = (
        """Group commitments and disbursements by year and currency.

        Only commitment and disbursement transactions are included. Amounts
        with different currencies are always reported separately.

        Args:
            year_from: Optional first year to include.
            year_to: Optional last year to include.

        Returns:
            A chronological table containing year, transaction type, currency
            and total amount.

        Relevant IATI terms:
        """
        + tool_glossary_text("transaction_totals_by_year")
    )
    mcp.tool()(transaction_totals_by_year)

    def transaction_totals_by_organisation(
        limit: int = 50,
    ) -> DataToolOutput:
        return activities.transaction_totals_by_organisation(limit=limit)

    transaction_totals_by_organisation.__doc__ = (
        """Group commitments and disbursements by reporting organisation.

        Amounts with different currencies and transaction types are reported
        separately. The reporting organisation publishes the activity data and
        is not necessarily the organisation funding or implementing the
        activity.

        Args:
            limit: Maximum number of grouped rows to return. Default: 50.

        Returns:
            A table containing the organisation reference and name,
            transaction type, currency and total amount.

        Relevant IATI terms:
        """
        + tool_glossary_text("transaction_totals_by_organisation")
    )
    mcp.tool()(transaction_totals_by_organisation)

    def transaction_totals_by_sector(
        transaction_type: str = "2",
        currency: str | None = None,
        vocabulary: str | None = None,
        limit: int = 50,
    ) -> DataToolOutput:
        return activities.transaction_totals_by_sector(
            transaction_type=transaction_type,
            currency=currency,
            vocabulary=vocabulary,
            limit=limit,
        )

    transaction_totals_by_sector.__doc__ = (
        """Allocate commitments and disbursements across sectors.

        Amounts are distributed using the published sector percentages.
        Different vocabularies and currencies are reported separately.

        Args:
            transaction_type: Commitment or disbursement. Accepts commitment,
                out commitment, disbursement, 2 or 3.
            currency: Optional currency code, for example USD or EUR.
            vocabulary: Optional sector vocabulary code, for example 1 or 2.
            limit: Maximum number of grouped rows to return per vocabulary and
                currency. Default: 50.

        Returns:
            A table containing the vocabulary, sector, transaction type,
            currency and allocated total amount.

        Relevant IATI terms:
        """
        + tool_glossary_text("transaction_totals_by_sector")
    )
    mcp.tool()(transaction_totals_by_sector)

    def transaction_totals_by_country(
        transaction_type: str = "2",
        currency: str | None = None,
        limit: int = 50,
    ) -> DataToolOutput:
        return activities.transaction_totals_by_country(
            transaction_type=transaction_type,
            currency=currency,
            limit=limit,
        )

    transaction_totals_by_country.__doc__ = (
        """Group commitments and disbursements by recipient country.

        Amounts with different currencies and transaction types are reported
        separately. Missing country names fall back to the country code, and
        missing country data falls back to "Unknown recipient country".

        Args:
            transaction_type: Commitment or disbursement. Accepts commitment,
                out commitment, disbursement, 2 or 3.
            currency: Optional currency code, for example USD or EUR.
            limit: Maximum number of grouped rows to return. Default: 50.

        Returns:
            A table containing the country code and name, transaction type,
            currency and total amount.

        Relevant IATI terms:
        """
        + tool_glossary_text("transaction_totals_by_country")
    )
    mcp.tool()(transaction_totals_by_country)

    def top_activities_by_amount(
        transaction_type: str = "2",
        currency: str | None = None,
        limit: int = 10,
    ) -> DataToolOutput:
        return activities.top_activities_by_amount(
            transaction_type=transaction_type,
            currency=currency,
            limit=limit,
        )

    top_activities_by_amount.__doc__ = (
        """List activities with the highest commitment or disbursement totals.

        Rankings are calculated independently for each currency, avoiding
        comparisons between amounts expressed in different currencies.

        Args:
            transaction_type: Commitment or disbursement. Accepts commitment,
                out commitment, disbursement, 2 or 3.
            currency: Optional currency code, for example USD or EUR.
            limit: Maximum results to return per currency. Default: 10.

        Returns:
            A table containing activity identifiers, titles, reporting
            organisations, recipient countries, transaction type, currency
            and total amount.

        Relevant IATI terms:
        """
        + tool_glossary_text("top_activities_by_amount")
    )
    mcp.tool()(top_activities_by_amount)

    @mcp.tool()
    def define_term(term: str) -> DataToolOutput:
        """Explain what an IATI term means, according to the standard's
            glossary (activities, organisations, financial data, aid
            classifications, sectors and geography, results, documentation).

        Useful for questions like "what does X mean?" or "what is the
        difference between X and Y?" (call it once per term).

        Args:
            term: Word or phrase to look up, in English (e.g. "disbursement",
                "policy marker"). Partial matches are accepted.

        Returns:
            A table with the matching glossary terms and their definitions.
        """
        return terms.define_term(term)
