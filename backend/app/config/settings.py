"""Application configuration using environment variables with sensible defaults."""
from functools import lru_cache
import os
from pydantic import BaseSettings


class Settings(BaseSettings):
	app_name: str = "wifi-monitor-backend"
	secret_key: str = "change_me"
	jwt_secret_key: str = "change_me_jwt"
	database_url: str = "sqlite:///../wifi_monitor.db"
	redis_url: str = "redis://localhost:6379/0"
	api_prefix: str = "/api/v1"
	debug: bool = False
	cors_origins: str = "*"

	class Config:
		env_file = os.getenv(
			"BACKEND_ENV_FILE",
			os.path.join(os.path.dirname(__file__), "../../../config/.env"),
		)
		env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
	return Settings()
