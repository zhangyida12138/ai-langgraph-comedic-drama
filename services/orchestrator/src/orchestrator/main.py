"""orchestrator 入口。

本阶段只有 /health 和 POST /internal/pipeline/preview（跑一次内置最小图），
不调用外部模型、不访问数据库，用于验证服务装配与依赖可用。

启动（仓库根目录，Makefile 的 dev-backend 目标即此命令）：
    uv run uvicorn orchestrator.main:app --reload --port 8001
"""

from __future__ import annotations

from uuid import uuid4

from cdrama_common import ServiceSettings, configure_logging, create_health_router
from fastapi import FastAPI
from pydantic import BaseModel, Field

from orchestrator import __version__
from orchestrator.graph import build_graph

SERVICE_NAME = "orchestrator"


class PreviewRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000, description="题材或一句话创意")


class PreviewResponse(BaseModel):
    task_id: str
    steps: list[str]


def create_app(settings: ServiceSettings | None = None) -> FastAPI:
    settings = settings or ServiceSettings(service_name=SERVICE_NAME, version=__version__)
    configure_logging(settings.log_level)

    app = FastAPI(title="漫剧平台 · orchestrator", version=__version__)
    app.state.settings = settings
    app.state.graph = build_graph()

    app.include_router(create_health_router(service_name=SERVICE_NAME, version=__version__))

    @app.post("/internal/pipeline/preview", response_model=PreviewResponse, tags=["internal"])
    async def preview(payload: PreviewRequest) -> PreviewResponse:
        """内部接口：仅 gateway 调用，不对外暴露。task_id 目前是占位值。"""
        result = await app.state.graph.ainvoke({"prompt": payload.prompt, "steps": []})
        return PreviewResponse(task_id=uuid4().hex, steps=result["steps"])

    return app


app = create_app()
