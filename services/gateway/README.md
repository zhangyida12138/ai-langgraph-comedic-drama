# services/gateway

API 网关 / BFF（FastAPI）。

- 统一对外入口：鉴权、限流、CORS、请求校验
- 聚合下游服务结果，向客户端提供稳定的对外契约
- 把编排服务的进度事件以 SSE / WebSocket 透传给前端

## 当前实现（骨架）

- `src/gateway/main.py`：`create_app()` 工厂（便于测试注入配置）+ 模块级 `app`
- `GET /health`：复用 `cdrama_common.create_health_router()`，返回 `status / service / version / time`
- 配置：`cdrama_common.ServiceSettings`，读仓库根 `.env`（`APP_ENV`、`LOG_LEVEL`、`DATABASE_URL`、`REDIS_URL`、`CORS_ORIGINS`）
- 尚未实现：`/api/v1` 路由组、登录与权限中间件（steps.md 卷 A 与 C9）

启动：`make dev-backend`，或 `uv run uvicorn gateway.main:app --reload --port 8000`。
