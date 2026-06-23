"""
Implementación real de la herramienta resolve_scraping_target.
Normaliza entradas y las convierte en referencias de identidad digital.
"""

import logging
from app.tools.base import BaseTool
from app.tools.schemas import ResolveTargetInput, ResolveTargetOutput

logger = logging.getLogger(__name__)


class ResolveTargetTool(BaseTool[ResolveTargetInput, ResolveTargetOutput]):
    """Herramienta real resolve_scraping_target."""

    def __init__(self):
        super().__init__(
            name="resolve_scraping_target",
            description="Normaliza y resuelve el username o URL de objetivo de adquisición.",
            input_model=ResolveTargetInput,
            output_model=ResolveTargetOutput
        )

    async def _run(self, id_analisis: int, id_usuario: int | None, input_data: ResolveTargetInput) -> ResolveTargetOutput:
        # ponytail: normalización de urls con lógica de strings simple
        raw_val = input_data.username_or_url.strip()
        if "facebook.com" in raw_val or "instagram.com" in raw_val or "x.com" in raw_val:
            username = raw_val.split("/")[-1].split("?")[0].strip("@")
        else:
            username = raw_val.strip("@")
            
        profile_url = f"https://{input_data.platform}.com/{username}"
        identity_ref = f"{input_data.platform}:{username}"
        
        await self.save_raw_evidence(
            id_analisis=id_analisis,
            id_tool_run=None,
            evidence_type="network_capture",
            platform=input_data.platform,
            source_url=None,
            raw_json={"input_raw": input_data.username_or_url, "resolved": username}
        )

        return ResolveTargetOutput(
            platform=input_data.platform,
            username=username,
            profile_url=profile_url,
            identity_ref=identity_ref,
            id_identidad_digital_objetivo=input_data.id_identidad_digital_objetivo,
            confidence=1.0
        )
