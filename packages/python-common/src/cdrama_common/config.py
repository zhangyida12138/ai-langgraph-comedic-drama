"""跨服务配置加载。

约定：
- 通用配置用不带前缀的环境变量：APP_ENV / LOG_LEVEL / DATABASE_URL / REDIS_URL / CORS_ORIGINS；
- 服务专属配置由各服务继承 ServiceSettings 扩展，使用 `<SERVICE>_` 前缀；
- 真实密钥只写在仓库根的 `.env`（已被 .gitignore 忽略），仓库内只提交键名说明。
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = ".env"


class ServiceSettings(BaseSettings):
    """所有微服务共用的最小配置。

    字段名与环境变量大小写不敏感地对应（pydantic-settings 默认行为），
    例如 `database_url` 读取 `DATABASE_URL`。
    """

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    service_name: str = "service"
    version: str = "0.1.0"
    app_env: str = "local"
    log_level: str = "INFO"

    # 依赖地址：骨架阶段允许为空，缺失不阻断启动（数据库接入见 steps.md 卷 A）
    database_url: str | None = None
    redis_url: str | None = None

    # 本地 Vite dev server 的来源；生产同源部署时用不到
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]


@lru_cache(maxsize=1)
def get_settings() -> ServiceSettings:
    """返回进程级单例配置，便于 FastAPI 依赖注入与测试覆盖。"""
    return ServiceSettings()
