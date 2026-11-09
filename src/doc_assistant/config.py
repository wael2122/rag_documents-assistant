"""Configuration centralisée, lue depuis les variables d'environnement et le fichier .env."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Base de données
    database_url: PostgresDsn = Field(
        default=PostgresDsn("postgresql://rag:rag@localhost:5432/rag"),
        description="Chaîne de connexion PostgreSQL (pgvector).",
    )

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    generation_model: str = "qwen3:8b"
    vision_model: str = "qwen2.5vl:7b"
    embedding_model: str = "bge-m3"
    embedding_dim: int = Field(default=1024, gt=0, le=2000)

    # Reranking (sentence-transformers)
    reranker_model: str = "BAAI/bge-reranker-v2-m3"

    # Chemins
    raw_data_dir: Path = Path("data/raw")
    golden_set_path: Path = Path("data/eval/golden_set.jsonl")

    # Logs
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_json: bool = True


@lru_cache
def get_settings() -> Settings:
    """Retourne une instance unique des paramètres (mise en cache)."""
    return Settings()
