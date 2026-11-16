# services/gateway

API 网关 / BFF（FastAPI）。

- 统一对外入口：鉴权、限流、CORS、请求校验
- 聚合下游服务结果，向客户端提供稳定的对外契约
- 把编排服务的进度事件以 SSE / WebSocket 透传给前端
