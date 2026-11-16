# packages/python-common

Python 共享库：配置加载、结构化日志、LLM / 图像客户端封装、消息契约与测试夹具。

## 当前实现（骨架）

| 模块 | 内容 |
| --- | --- |
| `cdrama_common/config.py` | `ServiceSettings`（pydantic-settings，读仓库根 `.env`；`database_url` / `redis_url` 允许为空）+ `get_settings()` |
| `cdrama_common/logging.py` | `configure_logging()`：单行 JSON 日志，不引入第三方依赖 |
| `cdrama_common/health.py` | `create_health_router()`：所有服务同构的 `GET /health` |

约束：只放跨服务基础设施，不放业务逻辑；服务间只通过本包定义的契约交互（见 README「约束原则」）。LLM / 图像客户端与消息契约尚未实现。
