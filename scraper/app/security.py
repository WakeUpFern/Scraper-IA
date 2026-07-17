import hmac
import os

from fastapi import Header, HTTPException, status


async def require_service_key(x_service_key: str | None = Header(default=None)) -> None:
    expected = os.getenv("SCRAPER_SERVICE_API_KEY", "")
    if not expected or not x_service_key or not hmac.compare_digest(expected, x_service_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credencial de servicio inválida")
