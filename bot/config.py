from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    bot_token: str = Field(..., alias="BOT_TOKEN")
    database_url: str = Field(..., alias="DATABASE_URL")
    redis_url: str = Field("redis://localhost:6379/0", alias="REDIS_URL")
    admin_ids: list[int] = Field(default_factory=list, alias="ADMIN_IDS")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    redis_password: str = Field("", alias="REDIS_PASSWORD")
    webhook_url: str = Field("", alias="WEBHOOK_URL")
    webhook_secret: str = Field("", alias="WEBHOOK_SECRET")

    gigachat_api_key: str = Field("", alias="GIGACHAT_API_KEY")
    gigachat_url: str = Field("https://gigachat.devices.sberbank.ru/api/v1", alias="GIGACHAT_URL")
    gigachat_model: str = Field("GigaChat", alias="GIGACHAT_MODEL")
    gigachat_oauth_url: str = Field("https://ngw.devices.sberbank.ru:9443/api/v2/oauth", alias="GIGACHAT_OAUTH_URL")
    admin_api_key: str = Field("", alias="ADMIN_API_KEY")

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
