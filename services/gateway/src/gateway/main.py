"""gateway 入口。

本阶段是最小可运行骨架：加载配置 → 注册 /health → 预留 /api/v1 挂载点。
登录、权限与租户上下文注入见 steps.md 卷 A（A11–A19），尚未实现。

启动（仓库根目录，Makefile 的 dev-backend 目标即此命令）：
    uv run uvicorn gateway.main:app --reload --port 8000
"""

from __future__ import annotations

from cdrama_common import ServiceSettings, configure_logging, create_health_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from gateway import __version__

SERVICE_NAME = "gateway"


def create_app(settings: ServiceSettings | None = None) -> FastAPI:
    """工厂函数：测试可注入自定义 settings，不依赖全局状态。"""
    settings = settings or ServiceSettings(service_name=SERVICE_NAME, version=__version__)
    configure_logging(settings.log_level)

    app = FastAPI(
        title="漫剧平台 · gateway",
        version=__version__,
        description="唯一对外入口；业务路由挂 /api/v1，内部服务由网关聚合。",
    )
    app.state.settings = settings

    app.include_router(create_health_router(service_name=SERVICE_NAME, version=__version__))

    # 生产环境前端与网关同源；本地直连 8000 调试时才需要 CORS，故按配置放开。
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


app = create_app()
