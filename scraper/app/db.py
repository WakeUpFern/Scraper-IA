"""
app/db.py — Conexión asyncpg a naat_db2 en el contenedor PostgreSQL d6e6a0efef96.
ponytail: pool global, sin ORM.
"""
import asyncpg
import os

# Dentro del contenedor, postgres-naat3 es el hostname del contenedor de DB en la red naat_default
# Fuera del contenedor (dev local), usar DATABASE_URL env var con host:5435
_DSN = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@postgres-naat3:5432/naat_db2",
)

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(_DSN, min_size=2, max_size=10)
    return _pool


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
