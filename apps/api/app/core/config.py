"""应用配置（pydantic-settings，环境变量 / .env 注入）。"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # 数据存储
    database_url: str = "postgresql+psycopg://comfy:comfy@127.0.0.1:5432/comfyportal"
    redis_url: str = "redis://127.0.0.1:6379/0"

    # 认证
    jwt_secret: str = "change-me"
    jwt_expire_days: int = 7
    internal_token: str = "change-me"  # 内部接口 X-Internal-Token 闸门

    # 安全：内部接口仅允许 tailnet 源 IP（规格书 §1 双闸门）
    tailnet_cidr: str = "100.64.0.0/10"

    # 配额
    daily_quota_default: int = 20

    # 产物目录（本地 dev 默认相对路径；Docker 部署由 env 覆盖为 /data/artifacts）
    artifacts_dir: str = "./data/artifacts"


settings = Settings()
