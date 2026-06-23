"""
Implementación real de la herramienta summarize_scraping_analysis.
Consulta la base de datos real en PostgreSQL, cuenta los logros del análisis y devuelve un resumen descriptivo.
"""

import logging
from app.tools.base import BaseTool
from app.tools.schemas import SummarizeInput, SummarizeOutput
from app.tools import mock_db
from app.runtime import db

logger = logging.getLogger(__name__)


class SummarizeTool(BaseTool[SummarizeInput, SummarizeOutput]):
    """Herramienta real summarize_scraping_analysis."""

    def __init__(self):
        super().__init__(
            name="summarize_scraping_analysis",
            description="Genera el resumen real de adquisición del análisis consultando la base de datos.",
            input_model=SummarizeInput,
            output_model=SummarizeOutput
        )

    async def _run(self, id_analisis: int, id_usuario: int | None, input_data: SummarizeInput) -> SummarizeOutput:
        # 1. Contar tool_runs finalizados
        run_row = await db.fetchrow(
            "SELECT count(*) as cnt FROM redes.tool_run WHERE id_analisis = $1 AND status = 'completed'",
            id_analisis
        )
        total_runs = run_row["cnt"] if run_row else 0

        # 2. Contar identidades encontradas
        ident_row = await db.fetchrow(
            "SELECT count(distinct username_observado) as cnt FROM redes.identidad_observacion WHERE id_analisis = $1",
            id_analisis
        )
        total_idents = ident_row["cnt"] if ident_row else 0

        # 3. Contar relaciones/vínculos
        vinculo_row = await db.fetchrow(
            "SELECT count(*) as cnt FROM redes.vinculo_social WHERE id_analisis = $1",
            id_analisis
        )
        total_vinculos = vinculo_row["cnt"] if vinculo_row else 0

        # 4. Obtener nombre del objetivo principal
        target_row = await db.fetchrow(
            "SELECT username_observado FROM redes.identidad_observacion WHERE id_analisis = $1 ORDER BY id_identidad_observacion ASC LIMIT 1",
            id_analisis
        )
        target_username = target_row["username_observado"] if target_row else "N/A"

        summary_text = (
            f"Análisis {id_analisis} finalizado en base de datos. "
            f"Se ejecutaron y registraron {total_runs} pasos (tool_runs). "
            f"Se identificó el perfil de @{target_username} y se observaron {total_idents} identidades digitales. "
            f"Se recolectaron {total_vinculos} relaciones o vínculos técnicos."
        )

        return SummarizeOutput(
            analysis_id=id_analisis,
            summary=summary_text,
            total_tool_runs=total_runs,
            total_identities_found=total_idents,
            total_relationships_found=total_vinculos,
            warnings=[]
        )
