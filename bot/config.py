from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    bot_token: str = Field(..., alias="BOT_TOKEN")
    database_url: str = Field(
        "postgresql+asyncpg://astro:astro_secret@localhost:5432/astro_bot",
        alias="DATABASE_URL",
    )
    redis_url: str = Field("redis://localhost:6379/0", alias="REDIS_URL")
    ollama_url: str = Field("http://localhost:11434", alias="OLLAMA_URL")
    ollama_model: str = Field("gemma3:4b", alias="OLLAMA_MODEL")
    admin_ids: list[int] = Field(default_factory=list, alias="ADMIN_IDS")

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
