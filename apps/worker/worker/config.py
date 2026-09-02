"""Worker 配置（pydantic-settings，环境变量 / .env）。"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    redis_url: str = "redis://127.0.0.1:6379/0"
    comfyui_url: str = "http://127.0.0.1:8188"
    # M1 本地 dev 走 8000；生产走 http://TAILNET_IP:8001（内部接口）
    api_internal_url: str = "http://127.0.0.1:8000"
    internal_token: str = "change-me"
    metrics_port: int = 9101


settings = Settings()
