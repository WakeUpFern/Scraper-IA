"""
Módulo de conexión y operaciones con PostgreSQL utilizando asyncpg.
Proporciona métodos directos, rápidos y asíncronos sin ORM.
"""

import logging
from typing import Any, Dict, List, Optional
import asyncpg
from app.config import settings

logger = logging.getLogger(__name__)

_pool: Optional[asyncpg.Pool] = None


async def init_db_pool() -> None:
    """Inicializa el pool de conexiones asíncronas."""
    global _pool
    if _pool is None:
        logger.info("Inicializando pool de conexiones a PostgreSQL en %s:%d/%s...", 
                    settings.db_host, settings.db_port, settings.db_name)
        _pool = await asyncpg.create_pool(
            host=settings.db_host,
            port=settings.db_port,
            database=settings.db_name,
            user=settings.db_user,
            password=settings.db_password,
            min_size=1,
            max_size=10
        )


async def get_pool() -> asyncpg.Pool:
    """Obtiene el pool de conexiones, inicializándolo si es necesario."""
    await init_db_pool()
    if _pool is None:
        raise RuntimeError("No se pudo conectar a la base de datos.")
    return _pool


async def close_db_pool() -> None:
    """Cierra el pool de conexiones en el apagado de la aplicación."""
    global _pool
    if _pool is not None:
        logger.info("Cerrando pool de conexiones de base de datos...")
        await _pool.close()
        _pool = None


async def execute(query: str, *args: Any) -> str:
    """Ejecuta una sentencia SQL (INSERT, UPDATE, DELETE)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.execute(query, *args)


async def fetch(query: str, *args: Any) -> List[Dict[str, Any]]:
    """Ejecuta una consulta SQL y devuelve una lista de diccionarios."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        records = await conn.fetch(query, *args)
        return [dict(r) for r in records]


async def fetchrow(query: str, *args: Any) -> Optional[Dict[str, Any]]:
    """Ejecuta una consulta SQL y devuelve una sola fila o None."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        record = await conn.fetchrow(query, *args)
        return dict(record) if record else None


async def ensure_digital_identity(platform: str, username: str, profile_url: str | None = None, nombre_publico: str | None = None) -> int:
    """
    Asegura que exista una fila en personas.identidad_digital para la plataforma y username dados.
    Devuelve id_identidad_digital.
    """
    # 1. Obtener id_plataforma
    plat_row = await fetchrow("SELECT id_plataforma FROM redes.plataforma WHERE codigo = $1", platform.lower())
    if not plat_row:
        # Si no existe, lo creamos
        plat_name = platform.capitalize()
        row = await fetchrow(
            "INSERT INTO redes.plataforma (codigo, nombre, url_base) VALUES ($1, $2, $3) RETURNING id_plataforma",
            platform.lower(), plat_name, f"https://{platform.lower()}.com"
        )
        id_plataforma = row["id_plataforma"]
    else:
        id_plataforma = plat_row["id_plataforma"]

    # 2. Buscar si ya existe la identidad digital
    id_row = await fetchrow(
        "SELECT id_identidad_digital FROM personas.identidad_digital WHERE id_plataforma = $1 AND username = $2",
        id_plataforma, username
    )
    if id_row:
        return id_row["id_identidad_digital"]

    # 3. Si no existe, crearla (id_persona = NULL por defecto)
    url = profile_url or f"https://{platform.lower()}.com/{username}"
    row = await fetchrow(
        """
        INSERT INTO personas.identidad_digital (id_plataforma, username, usuario_url, nombre_publico, estado)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id_identidad_digital
        """,
        id_plataforma, username, url, nombre_publico or username, "activa"
    )
    return row["id_identidad_digital"]


async def get_tipo_vinculo_id(codigo: str) -> int:
    """Obtiene o crea un id_tipo_vinculo en la base de datos."""
    row = await fetchrow("SELECT id_tipo_vinculo FROM redes.tipo_vinculo_social WHERE codigo = $1", codigo)
    if row:
        return row["id_tipo_vinculo"]
    # Fallback/Default
    row = await fetchrow(
        "INSERT INTO redes.tipo_vinculo_social (codigo, descripcion) VALUES ($1, $2) RETURNING id_tipo_vinculo",
        codigo, f"Vínculo tipo {codigo}"
    )
    return row["id_tipo_vinculo"]

