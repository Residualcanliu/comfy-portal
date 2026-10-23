"""应用配置（pydantic-settings，环境变量 / .env 注入）。"""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 示例值 / 占位值：本仓库是公开的，这些值等于公开的密钥。
# 部署时若忘了覆盖，任何人都能伪造 JWT 或直接调内部接口。
_PLACEHOLDERS = {"change-me", "changeme", "please_change_me", "placeholder"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # 数据存储
    database_url: str = "postgresql+psycopg://comfy:comfy@127.0.0.1:5432/comfyportal"
    redis_url: str = "redis://127.0.0.1:6379/0"

    # 认证
    jwt_secret: str = "change-me"
    jwt_expire_days: int = 7
    internal_token: str = "change-me"  # 内部接口 X-Internal-Token 闸门

    @field_validator("jwt_secret", "internal_token")
    @classmethod
    def _reject_placeholder_secret(cls, v: str, info) -> str:
        """拒绝空值与示例占位值，让配置失误在启动时就暴露。

        不做长度下限校验 —— 本地开发用的是短的 dev 值，卡长度会把开发环境一起搞坏。
        这里只拦「明显是忘了改」的情况。
        """
        if not v or v.strip().lower() in _PLACEHOLDERS:
            raise ValueError(
                f"{info.field_name} 不能为空或使用示例占位值（change-me 等）。"
                f"本仓库公开，这类值等于公开密钥，请换成随机长串。"
            )
        return v

    # 安全：内部接口仅允许 tailnet 源 IP（规格书 §1 双闸门）
    tailnet_cidr: str = "100.64.0.0/10"

    # 配额
    daily_quota_default: int = 20

    # 产物目录（本地 dev 默认相对路径；Docker 部署由 env 覆盖为 /data/artifacts）
    artifacts_dir: str = "./data/artifacts"

    # CORS 允许源，逗号分隔。默认只放本地开发前端；
    # 生产用 CORS_ORIGINS=https://<前端域名> 收紧（规格书 §9）。
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # 是否开放 /docs /redoc /openapi.json。
    # 默认关闭：公开部署时 schema 会把 /internal/* 在内的全部路由一起暴露。
    docs_enabled: bool = False

    # 只读演示模式：true 时服务端拒绝注册与生成，公开站点仅展示已有内容。
    # 合规用途是「不向公众提供生成式 AI 服务」—— 关闭能力，而不是只藏按钮。
    readonly_demo: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
