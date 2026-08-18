from mcp_server import DataToolOutput

from mcp_iati import helpers as h
from mcp_iati.activities import queries as activities
from mcp_iati.glossary import full_glossary_text, glossary_text


def register_tools(mcp):
    """Entry point invoked by mcp-server (see the `mcp_server` entry point in pyproject.toml)."""
    _register_iati_tools(mcp)


def _register_iati_tools(mcp):  # noqa: C901
    """IATI - herramientas sobre el estandar de datos abiertos de cooperacion
    internacional (https://iatistandard.org/).

    Por defecto opera sobre un XML IATI de muestra (actividades del BID en
    Brasil, ver okfn_iati/data-samples/xml/iadb-Brazil.xml), pero las tools
    solo usan campos genericos del estandar IATI (identificador, estado,
    tipo de transaccion) por lo que sirven igual con cualquier otro XML IATI
    (configurable via MCP_IATI_XML_PATH).
    """
    mcp.set_plugin_info(
        description=(
            "Herramientas para consultar actividades y transacciones publicadas "
            "según el estándar IATI de datos abiertos sobre cooperación y desarrollo."
        ),
        instructions=(
            "Sos un asistente para consultar datos IATI. Interpretá las preguntas "
            "usando el siguiente glosario y explicá los términos cuando pueda haber "
            "ambigüedad. No confundas a la organización reportante con quien financia "
            "o ejecuta una actividad, ni un compromiso con un desembolso o gasto. "
            "Usá únicamente los datos devueltos por las tools; si la consulta queda "
            "fuera de su alcance, llamá a no_tool_disponible explicando el motivo.\n\n"
            "Glosario IATI:\n" + full_glossary_text()
        ),
        sample_questions=[
            "Buscá actividades IATI sobre transporte",
            "Dame el resumen de la actividad XI-IATI-IADB-BR-L1231",
            "¿Qué significa que una actividad esté en ejecución?",
            "¿Cuánto se comprometió y cuánto se desembolsó en esta actividad?",
            "¿La organización reportante es también quien financia el proyecto?",
        ],
    )

    @mcp.tool()
    def no_tool_disponible(razon: str | None = None) -> DataToolOutput:
        """Llamar cuando ninguna otra tool puede responder la pregunta: temas
            que no son actividades IATI, o preguntas fuera del alcance de
            los datos cargados.

        Args:
            razon: Breve explicación (1 frase) de por qué ninguna tool aplica.

        Examples:
            - no_tool_disponible(razon="no es una pregunta sobre actividades IATI")
        """
        msg = "Este plugin (mcp-iati) responde únicamente sobre las actividades IATI cargadas."
        if razon:
            msg += f" Motivo: {razon}."
        return h.text_result(msg, source_url="")

    def buscar_actividades(texto: str, limit: int = 10) -> DataToolOutput:
        return activities.buscar_actividades(texto, limit=limit)

    buscar_actividades.__doc__ = (
        """Busca actividades IATI cuyo título contenga el texto indicado.

        Útil como primer paso para descubrir el identificador IATI de una actividad,
        antes de pedir su resumen con resumen_actividad.

        Args:
            texto: Subcadena a buscar en el título (sin distinguir mayúsculas/minúsculas).
            limit: Cantidad máxima de resultados a devolver. Default: 10.

        Returns:
            Una tabla con identificador IATI, título y estado de cada coincidencia.

        Términos IATI relevantes:
        """
        + glossary_text("actividad IATI", "identificador IATI", "estado de actividad")
    )
    mcp.tool()(buscar_actividades)

    def resumen_actividad(iati_identifier: str) -> DataToolOutput:
        return activities.resumen_actividad(iati_identifier)

    resumen_actividad.__doc__ = (
        """Devuelve título, estado, organización reportante y totales por tipo
        de transacción de una actividad IATI.

        Args:
            iati_identifier: Identificador IATI, por ejemplo "XI-IATI-IADB-BR-L1231".
                Se obtiene con buscar_actividades.

        Términos IATI relevantes:
        """
        + glossary_text(
            "identificador IATI",
            "organización reportante",
            "estado de actividad",
            "transacción",
            "compromiso",
            "desembolso",
            "gasto",
            "moneda predeterminada",
        )
    )
    mcp.tool()(resumen_actividad)


def main() -> None:
    print("Hello from mcp-iati")
