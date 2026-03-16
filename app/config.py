"""
Mini README:
This file centralizes runtime configuration loaded from environment variables.
It supports local development on Windows/macOS/Linux/RPi and deployment targets like Render.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "IoTDashV0"
    secret_key: str = "change-me-in-production"
    database_url: str = "sqlite:///./iotdash.db"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""
    mqtt_default_host: str = "localhost"
    mqtt_default_port: int = 1883
    mqtt_default_tls_enabled: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
