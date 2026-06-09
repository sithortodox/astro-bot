from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    bot_token: str = Field(..., alias="BOT_TOKEN")
    database_url: str = Field(..., alias="DATABASE_URL")
    redis_url: str = Field("redis://localhost:6379/0", alias="REDIS_URL")
    ollama_url: str = Field("http://localhost:11434", alias="OLLAMA_URL")
    ollama_model: str = Field("gemma3:4b", alias="OLLAMA_MODEL")
    admin_ids: list[int] = Field(default_factory=list, alias="ADMIN_IDS")

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        if isinstance(v, int):
            return [v]
        return v

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
