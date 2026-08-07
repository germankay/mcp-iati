from mcp.types import CallToolResult, TextContent

from mcp_server import DataToolOutput

from mcp_iati.activities import queries as activities


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
            "Herramientas de prueba sobre datos abiertos del estandar IATI "
            "de cooperacion internacional (por defecto, actividades del BID "
            "en Brasil)."
        ),
        instructions=(
            "Sos un asistente de prueba para el plugin IATI. Los datos "
            "cargados son actividades de cooperacion internacional segun el "
            "estandar IATI (identificador, titulo, estado, transacciones de "
            "compromiso/desembolso). Si te preguntan algo que no se pueda "
            "responder con estas tools, llama a no_tool_disponible "
            "explicando el motivo."
        ),
        sample_questions=[
            "Buscá actividades IATI sobre transporte",
            "Dame el resumen de la actividad XI-IATI-IADB-BR-L1231",
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
        return CallToolResult(
            content=[TextContent(type="text", text=msg)],
            structuredContent={"sources": []},
        )

    @mcp.tool()
    def buscar_actividades(texto: str, limit: int = 10) -> DataToolOutput:
        """Busca actividades IATI cuyo título contenga el texto indicado.

        Útil como primer paso para descubrir el identificador IATI de una
        actividad, antes de pedir su resumen con resumen_actividad.

        Args:
            texto: Subcadena a buscar en el título de la actividad (sin
                distinguir mayúsculas/minúsculas). Ej: "transporte", "road".
            limit: Cantidad máxima de resultados a devolver. Default: 10.

        Returns:
            Una tabla con identificador IATI, título y estado de cada
            actividad que coincide.

        Examples:
            - buscar_actividades(texto="transporte")
            - buscar_actividades(texto="road", limit=5)
        """
        return activities.buscar_actividades(texto, limit=limit)

    @mcp.tool()
    def resumen_actividad(iati_identifier: str) -> DataToolOutput:
        """Devuelve el resumen de una actividad IATI: título, estado,
            organización reportante y los totales comprometido/desembolsado
            (y otros tipos de transacción presentes) según sus transacciones.

        Args:
            iati_identifier: Identificador IATI de la actividad, ej.
                "XI-IATI-IADB-BR-L1231". Se obtiene con buscar_actividades.

        Examples:
            - resumen_actividad(iati_identifier="XI-IATI-IADB-BR-L1231")
        """
        return activities.resumen_actividad(iati_identifier)


def main() -> None:
    print("Hello from mcp-iati")
