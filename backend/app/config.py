from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
    )

    GEMINI_API_KEY: str
    DATA_DIR: str = "data"
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def data_dir_path(self) -> Path:
        return Path(self.DATA_DIR)

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


settings = Settings()
