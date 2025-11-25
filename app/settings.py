import os
from pathlib import Path
import pydantic
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = str(BASE_DIR / ".env")


class DB(BaseSettings):
    host: str = "localhost"
    port: int = 5432
    user: str
    password: str
    name: str
    model_config = SettingsConfigDict(
        env_prefix="bookshelf_db_", 
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_database_url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class RABBIT(BaseSettings):
    host: str = "localhost"
    port: int = 5672
    user: str
    password: str
    model_config = SettingsConfigDict(
        env_prefix="bookshelf_rabbit_", 
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore"
    )
    def get_broker_url(self) -> str:
        return f"amqp://{self.user}:{self.password}@{self.host}:{self.port}"


class Settings(BaseSettings):
    db: DB = pydantic.Field(default_factory=DB)
    rabbit: RABBIT = pydantic.Field(default_factory=RABBIT)
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
