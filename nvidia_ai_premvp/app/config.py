"""
Configuración del servicio nvidia_ai_premvp.
Todas las variables se leen desde el entorno / .env.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    nvidia_api_key: str
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_default_model: str = "qwen/qwen3.5-122b-a10b"
    nvidia_timeout_seconds: int = 60
    nvidia_max_tokens: int = 16384
    nvidia_temperature: float = 0.60
    nvidia_top_p: float = 0.95

    # DB settings
    db_host: str = "postgres-naat3"
    db_port: int = 5432
    db_name: str = "naat_db2"
    db_user: str = "postgres"
    db_password: str = "postgres"


settings = Settings()

