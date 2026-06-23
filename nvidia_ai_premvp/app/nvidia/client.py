"""
Cliente async para NVIDIA NIM — endpoint OpenAI-compatible /chat/completions.

Fuente verificada: build.nvidia.com/meta/llama-3_3-70b-instruct
  base_url : https://integrate.api.nvidia.com/v1
  endpoint : POST /chat/completions
  auth     : Authorization: Bearer <NVIDIA_API_KEY>
"""

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# El cliente se instancia una vez; httpx.AsyncClient es thread-safe y reutilizable.
_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    """Devuelve el cliente httpx singleton. La API key NO se loguea."""
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=settings.nvidia_base_url,
            headers={
                "Authorization": f"Bearer {settings.nvidia_api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=settings.nvidia_timeout_seconds,
        )
    return _client


async def chat_completion(
    message: str | list[dict[str, Any]], 
    model: str | None = None,
    tools: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    """
    Envía un mensaje o historial a NVIDIA NIM y retorna la respuesta completa.
    """
    resolved_model = model or settings.nvidia_default_model

    messages = message if isinstance(message, list) else [{"role": "user", "content": message}]

    payload: dict[str, Any] = {
        "model": resolved_model,
        "messages": messages,
        "temperature": settings.nvidia_temperature,
        "top_p": settings.nvidia_top_p,
        "max_tokens": settings.nvidia_max_tokens,
        "stream": False,
    }

    if tools:
        payload["tools"] = tools

    logger.debug("Enviando request a NVIDIA NIM | model=%s", resolved_model)

    client = get_client()
    response = await client.post("/chat/completions", json=payload)
    response.raise_for_status()

    return response.json()


async def close_client() -> None:
    """Cierra el cliente httpx (llamado en el shutdown de la app)."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
