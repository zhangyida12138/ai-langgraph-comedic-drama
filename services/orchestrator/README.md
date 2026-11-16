# services/orchestrator

LangGraph 编排服务（FastAPI），平台的核心。

- 定义漫剧生成状态机：题材 → 大纲 → 分镜 → 画面 → 配音 → 合成
- 负责检查点（checkpoint）、失败重试、人工介入（HITL）分支
- 通过消息队列调用 script / image / video / tts 等微服务，并流式推送状态

## 当前实现（骨架）

- `src/orchestrator/graph.py`：最小 StateGraph（`plan → draft`）+ `build_graph()`，用于验证依赖与装配
- `src/orchestrator/main.py`：`GET /health`；`POST /internal/pipeline/preview` 跑一次最小图并返回经过的节点
- 尚未实现：检查点、Redis 队列、下游微服务调用、`thread_id` 带租户前缀（steps.md A22）

启动：`make dev-backend`，或 `uv run uvicorn orchestrator.main:app --reload --port 8001`。
