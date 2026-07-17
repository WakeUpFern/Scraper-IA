import os
from pathlib import Path
from typing import Any

import httpx


class CoreApiClient:
    def __init__(self) -> None:
        self._base_url = os.getenv("CORE_API_BASE_URL", "http://naat-api:8080").rstrip("/")
        self._service_key = os.getenv("SCRAPER_SERVICE_API_KEY", "")

    @property
    def headers(self) -> dict[str, str]:
        if not self._service_key:
            raise RuntimeError("SCRAPER_SERVICE_API_KEY no está configurada")
        return {"X-Service-Key": self._service_key}

    async def notify(self, analysis_id: int, payload: dict[str, Any]) -> None:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                f"{self._base_url}/internal/scraper/analyses/{analysis_id}/event",
                headers=self.headers,
                json=payload,
            )
            response.raise_for_status()

    async def upload_artifact(self, analysis_id: int, artifact: dict[str, Any]) -> dict[str, Any]:
        source = Path(str(artifact["path"]))
        if not source.is_file():
            raise FileNotFoundError(f"Artefacto no encontrado: {source}")
        async with httpx.AsyncClient(timeout=120.0) as client:
            with source.open("rb") as content:
                response = await client.post(
                    f"{self._base_url}/internal/scraper/analyses/{analysis_id}/artifacts",
                    headers=self.headers,
                    data={"type": artifact.get("type", "file")},
                    files={"file": (artifact.get("name", source.name), content)},
                )
            response.raise_for_status()
            return response.json()
