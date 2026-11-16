# services/orchestrator

LangGraph 编排服务（FastAPI），平台的核心。

- 定义漫剧生成状态机：题材 → 大纲 → 分镜 → 画面 → 配音 → 合成
- 负责检查点（checkpoint）、失败重试、人工介入（HITL）分支
- 通过消息队列调用 script / image / video / tts 等微服务，并流式推送状态
