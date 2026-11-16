"""健康检查契约。

所有服务暴露同构的 `/health` 响应，键固定为 status / service / version / time，
gateway 与 tests/test_health.py 都依赖这组键，改动时需同步。
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter

HEALTH_PATH = "/health"


def create_health_router(*, service_name: str, version: str) -> APIRouter:
    """构造带 /health 的路由；探测端点放在根路径，不经过 /api 前缀。"""
    router = APIRouter(tags=["ops"])

    @router.get(HEALTH_PATH, summary="存活与版本检查")
    async def health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": service_name,
            "version": version,
            "time": datetime.now(UTC).isoformat(),
        }

    return router
