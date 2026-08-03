from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://aiops:aiops@localhost:5432/aiops"
    redis_url: str = "redis://localhost:6379/0"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"

    api_key: str = "dev-local-key"

    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
