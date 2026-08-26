"""Shared IATI terminology used in tool descriptions and plugin instructions.

Covers the IATI 2.03 activity standard as modelled by the okfn_iati library:
its enums mirror the IATI codelists and its CSV converter flattens activities,
dates, descriptions, participating organisations, sectors, transactions,
budgets, locations, documents, results, indicators, indicator periods,
conditions, contact info and country budget items. Every entry below maps to
one of those elements or codelists.
"""

IATI_GLOSSARY = {
    # --- Identification and lifecycle -------------------------------------
    "IATI activity": (
        "A development or cooperation intervention published under the IATI standard; "
        "it can represent a project, a programme or another unit of work."
    ),
    "IATI identifier": (
        "Globally unique code identifying an IATI activity, also used to link it "
        "to its transactions and other information."
    ),
    "activity status": (
        "Stage of an activity within its lifecycle: pipeline/identification, "
        "implementation, completion, post-completion, cancelled or suspended."
    ),
    "activity date": (
        "Start or end date of an activity. Each date declares one of four types: "
        "planned start, actual start, planned end or actual end."
    ),
    "description": (
        "Narrative text describing an activity, with a type such as general "
        "description, objectives or target groups; may be published in several "
        "languages."
    ),
    "hierarchy": (
        "Level of an activity within its publisher's structure: 1 for a standalone "
        "activity or parent programme, 2 or more for components reported as "
        "separate child activities."
    ),
    "related activity": (
        "Link from one activity to another, typed as parent, child, sibling, "
        "co-funded or third party."
    ),
    "activity scope": (
        "Geographical ambit of an activity: global, regional, multi-national, "
        "national or one of several sub-national levels."
    ),
    "humanitarian flag": (
        "Marker declaring that an activity (or an individual transaction) relates "
        "entirely or partially to humanitarian aid."
    ),

    # --- Organisations ----------------------------------------------------
    "reporting organisation": (
        "Organisation responsible for publishing and maintaining an activity's data; "
        "not necessarily the one funding or implementing the project."
    ),
    "participating organisation": (
        "Organisation linked to an activity with a given role, such as funding, "
        "accountability, extension or implementation."
    ),
    "organisation role": (
        "Code describing the function of a participating organisation within "
        "an activity: funding, accountable, extending or implementing."
    ),
    "organisation type": (
        "Classification of an organisation, such as government, local government, "
        "other public sector, international/national/regional NGO, public-private "
        "partnership, multilateral, foundation, private sector or academic."
    ),
    "provider organisation": (
        "Organisation providing the funds associated with a transaction "
        "or a planned disbursement."
    ),
    "receiver organisation": (
        "Organisation receiving the funds associated with a transaction "
        "or a planned disbursement."
    ),
    "contact information": (
        "Contact details published for an activity, typed as general enquiries, "
        "project management, financial management or communications."
    ),

    # --- Financial data ---------------------------------------------------
    "transaction": (
        "Financial operation associated with an IATI activity, identified by "
        "its type, date, value and currency."
    ),
    "transaction type": (
        "Code indicating the nature of a financial operation: incoming funds, "
        "commitment, disbursement, expenditure, interest payment, loan repayment, "
        "reimbursement, purchase or sale of equity, credit guarantee, incoming "
        "commitment, or outgoing/incoming pledge."
    ),
    "transaction value": (
        "Amount of an individual transaction, expressed in the currency stated on the "
        "value or, if unspecified, in the activity's default currency."
    ),
    "commitment": (
        "Financial obligation undertaken to provide funds to an activity; "
        "it does not necessarily represent a payment already made."
    ),
    "disbursement": (
        "Transfer of funds from a provider organisation to a receiver "
        "organisation to finance an activity."
    ),
    "expenditure": (
        "Use of funds to purchase goods or services related to an activity; "
        "not a synonym of disbursement."
    ),
    "budget": (
        "Amount planned for an activity over a given period, with a status "
        "(indicative or committed) and a type (original or revised); it does not "
        "necessarily represent funds actually disbursed or spent."
    ),
    "planned disbursement": (
        "Amount expected to be disbursed during a future period; different "
        "from a disbursement transaction that already took place."
    ),
    "default currency": (
        "Currency declared for an activity and used whenever a financial value "
        "does not explicitly specify another currency."
    ),
    "country budget item": (
        "Mapping of an activity to the recipient country's own budget "
        "classification, so aid can be aligned with national budgets."
    ),

    # --- Aid classifications ----------------------------------------------
    "aid type": (
        "Modality of the aid, such as budget support, pooled funds, project-type "
        "interventions, technical assistance, debt relief or cash transfers; "
        "declared as an activity default and overridable per transaction."
    ),
    "finance type": (
        "Financial instrument of the flow, such as standard grant, standard loan, "
        "reimbursable grant, bonds, equity, guarantees or debt "
        "relief/rescheduling; declared as an activity default."
    ),
    "flow type": (
        "Classification of the resource flow's origin: official development "
        "assistance (ODA), other official flows, private development finance, "
        "foreign direct investment or other private flows."
    ),
    "tied status": (
        "Whether the aid's procurement is restricted to suppliers from specific "
        "countries: tied, partially tied or untied."
    ),
    "collaboration type": (
        "Institutional channel of the activity: bilateral, multilateral (inflows), "
        "bilateral through an NGO, bilateral through a multilateral, private "
        "sector outflows, or other."
    ),
    "disbursement channel": (
        "Route the funds take: through the recipient's central Ministry of "
        "Finance or treasury, directly to an implementing institution, in-kind "
        "through a third party, or in-kind managed by the donor."
    ),
    "policy marker": (
        "Cross-cutting policy objective an activity targets, such as gender "
        "equality, environment, biodiversity, climate change mitigation or "
        "adaptation, disaster risk reduction, disability or nutrition; each "
        "marker carries a significance from 'not targeted' through 'significant "
        "objective' to 'principal objective'."
    ),

    # --- Sectors and geography --------------------------------------------
    "sector": (
        "Thematic or economic area an activity contributes to, indicated by "
        "a code, a vocabulary and, where applicable, a percentage; sectors can "
        "be declared at activity level or per transaction."
    ),
    "recipient country or region": (
        "Country (ISO code) or supra-national DAC region that receives the "
        "intended benefits of an activity. May include a percentage when the "
        "activity is split across several territories."
    ),
    "location": (
        "Sub-national place where an activity happens, with name, coordinates or "
        "administrative area, a geographical precision (from exact location down "
        "to country level) and a reach (where the activity is carried out vs "
        "where the beneficiaries live)."
    ),

    # --- Results and monitoring -------------------------------------------
    "result": (
        "Intended or achieved change reported for an activity, typed as output, "
        "outcome, impact or other, and measured through indicators."
    ),
    "indicator": (
        "Metric used to measure a result, with a measure type (unit, percentage, "
        "nominal, ordinal or qualitative), an optional baseline, and reporting "
        "periods with target and actual values."
    ),
    "indicator period": (
        "Reporting window of an indicator, with the target value expected for "
        "the period and the actual value achieved."
    ),

    # --- Documentation and cross-cutting ----------------------------------
    "document link": (
        "URL of a document related to the activity, categorised for example as "
        "objectives, budget, memorandum of understanding, contract, tender, "
        "results, or review and evaluation."
    ),
    "condition": (
        "Condition attached to an activity, typed as policy (requiring a policy "
        "change), performance (linked to achieving results) or fiduciary "
        "(on the use of funds)."
    ),
    "vocabulary": (
        "Classification system used to interpret an IATI code, such as the OECD "
        "DAC CRS for sectors and policy markers, UN COFOG, the SDG goals and "
        "targets, or the IASC humanitarian clusters."
    ),
    "codelist": (
        "Catalogue mapping the codes used in IATI to their allowed meanings."
    ),
    "narrative": (
        "Human-readable text attached to an IATI element, which may be "
        "published in one or more languages."
    ),
}


IATI_STANDARD_URL = "https://iatistandard.org/en/iati-standard/203/"


TOOL_GLOSSARY_TERMS = {
    "file_overview": (
        "IATI activity",
        "reporting organisation",
        "recipient country or region",
        "transaction",
        "transaction type",
        "transaction value",
        "default currency",
        "commitment",
        "disbursement",
        "expenditure",
    ),
    "search_activities": (
        "IATI activity",
        "IATI identifier",
        "activity status",
    ),
    "list_activity_statuses": (
        "activity status",
        "IATI activity",
    ),
    "list_reporting_organisations": (
        "reporting organisation",
        "IATI activity",
    ),
    "list_recipient_countries": (
        "recipient country or region",
        "IATI activity",
    ),
    "filter_activities_by_country": (
        "recipient country or region",
        "IATI activity",
        "IATI identifier",
        "activity status",
    ),
    "list_sectors": (
        "sector",
        "vocabulary",
        "IATI activity",
    ),
    "activity_summary": (
        "IATI identifier",
        "reporting organisation",
        "activity status",
        "transaction",
        "commitment",
        "disbursement",
        "expenditure",
        "default currency",
    ),
    "activity_transactions": (
        "IATI identifier",
        "transaction",
        "transaction type",
        "transaction value",
        "commitment",
        "disbursement",
        "expenditure",
    ),
    "transaction_totals_by_year": (
        "transaction",
        "transaction type",
        "transaction value",
        "commitment",
        "disbursement",
        "default currency",
    ),
    "transaction_totals_by_organisation": (
        "reporting organisation",
        "transaction",
        "transaction type",
        "transaction value",
        "commitment",
        "disbursement",
        "default currency",
    ),
    "transaction_totals_by_sector": (
        "sector",
        "vocabulary",
        "transaction",
        "transaction type",
        "transaction value",
        "commitment",
        "disbursement",
        "default currency",
    ),
    "transaction_totals_by_country": (
        "recipient country or region",
        "transaction",
        "transaction type",
        "transaction value",
        "commitment",
        "disbursement",
        "default currency",
    ),
    "top_activities_by_amount": (
        "IATI activity",
        "IATI identifier",
        "reporting organisation",
        "recipient country or region",
        "transaction",
        "transaction type",
        "transaction value",
        "commitment",
        "disbursement",
        "default currency",
    ),
}


def _capitalize(term: str) -> str:
    """Capitalize only the first letter, preserving acronyms like IATI."""
    return term[0].upper() + term[1:]


def search_terms(query: str) -> list[tuple[str, str]]:
    """Find glossary entries matching a free-text query.

    Matching is case-insensitive and tries, in order: exact term, substring
    of a term, substring of a definition. A trailing 's' is also tried
    without it, so simple plurals ("sectors") still match. Returns a list of
    (term, definition) pairs, empty when nothing matches.
    """
    q = query.strip().strip("\"'?.").lower()
    if not q:
        return []
    variants = [q]
    if q.endswith("s"):
        variants.append(q[:-1])
    for match in (
        lambda variant, term, definition: term.lower() == variant,
        lambda variant, term, definition: variant in term.lower(),
        lambda variant, term, definition: variant in definition.lower(),
    ):
        for variant in variants:
            found = [
                (term, definition)
                for term, definition in IATI_GLOSSARY.items()
                if match(variant, term, definition)
            ]
            if found:
                return found
    return []


def glossary_text(*terms: str) -> str:
    """Return selected glossary entries as a compact, human-readable string."""
    unknown_terms = [term for term in terms if term not in IATI_GLOSSARY]
    if unknown_terms:
        raise KeyError(
            f"Unknown IATI terms: {', '.join(unknown_terms)}"
        )

    return "\n".join(
        f"- {_capitalize(term)}: {IATI_GLOSSARY[term]}"
        for term in terms
    )


def full_glossary_text() -> str:
    """Return all glossary entries for the MCP plugin instructions."""
    return glossary_text(*IATI_GLOSSARY)


def tool_glossary_terms(tool_name: str) -> tuple[str, ...]:
    """Return the glossary terms relevant to an IATI tool."""
    return TOOL_GLOSSARY_TERMS.get(tool_name, ())


def tool_glossary_text(tool_name: str) -> str:
    """Return only the definitions relevant to an IATI tool."""
    terms = tool_glossary_terms(tool_name)

    if not terms:
        return ""

    return glossary_text(*terms)
