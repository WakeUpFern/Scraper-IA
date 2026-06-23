"""
Ruta POST /chat — proxy hacia NVIDIA NIM.

Los errores HTTP de NVIDIA se re-lanzan con un mensaje claro
sin exponer la API key ni el stack interno.
"""

import logging

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.nvidia.client import chat_completion

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8192)
    model: str | None = Field(default=None)


class ChatResponse(BaseModel):
    reply: str
    model_used: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Acepta un mensaje del usuario y lo envía a NVIDIA NIM.
    Devuelve el texto de la primera choice.
    """
    try:
        raw = await chat_completion(message=request.message, model=request.model)
    except httpx.HTTPStatusError as exc:
        # Loguea el status sin incluir la key (no está en el body, solo en el header)
        logger.error(
            "NVIDIA NIM devolvió error HTTP | status=%s", exc.response.status_code
        )
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=f"NVIDIA NIM error: HTTP {exc.response.status_code}",
        ) from exc
    except httpx.TimeoutException:
        logger.error("NVIDIA NIM timeout")
        raise HTTPException(status_code=504, detail="NVIDIA NIM: timeout")
    except httpx.RequestError as exc:
        logger.error("NVIDIA NIM request error: %s", type(exc).__name__)
        raise HTTPException(status_code=502, detail="NVIDIA NIM: error de red")

    try:
        reply = raw["choices"][0]["message"]["content"]
        model_used = raw.get("model", request.model or "unknown")
    except (KeyError, IndexError) as exc:
        logger.error("Respuesta inesperada de NVIDIA NIM: %s", exc)
        raise HTTPException(status_code=502, detail="NVIDIA NIM: respuesta inesperada")

    return ChatResponse(reply=reply, model_used=model_used)
