from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    app_name: str = "SAR Narrative Generator"
    debug: bool = True

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/sar_db"

    # Redis (for async tasks)
    redis_url: str = "redis://localhost:6379"

    # Ollama LLM
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # ChromaDB
    chroma_persist_directory: str = "./data/chroma_db"

    # Embedding Model
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
