# Langfuse 接入步骤

> 目标：把 Langfuse 作为漫剧平台的观测平台，覆盖 orchestrator 的 LangGraph 图执行与各微服务的 LLM / 生成调用。
> 本文档记录拆解与进度；每条已完成项都能在仓库内找到证据（见文末「证据索引」）。
> 基线：本次盘点时仓库只有文档骨架（4 个根文件 + 17 个模块 README），业务代码与依赖清单尚未创建。

## 一、已完成

- [x] **1. 现状盘点：仓库内没有 Langfuse 依赖、配置或 tracing 代码**
  全仓文件清单与正则检索均无命中。结论：从零接入，不存在需要迁移的旧实现。

- [x] **2. 确认依赖清单基线：仓库尚无 `package.json`、`pyproject.toml`、`requirements.txt`**
  README.md:106 已约定「每个服务目录自带依赖清单」，但文件尚未创建。因此 SDK 引入必须排在骨架创建之后（即 T2 / T5 的顺序）。

- [x] **3. 确认环境变量文件存在**：`.env` 与 `.env.example`（dotenv 格式）已在仓库根目录。
  局限：本机策略「file」规则禁止读取这两个文件，现有键名**尚未核实**，故 T0 仍为待办；键名统一在 T0 结论之后进行。

- [x] **4. 确认接入层：LangGraph 通过 LangChain 的 callback 机制上报**
  已确认的事实：Langfuse 官方文档存在专门的 LangChain 集成页（路径 integrations/frameworks/langchain，标题明确覆盖 LangChain **与 LangGraph** 的 tracing / callbacks），说明官方支持将 LangGraph 执行纳入 trace。
  待实测的部分：该页正文由前端渲染，本轮抓取只拿到标题，**「把 handler 注入 `config["callbacks"]` 即自动成树」这一步属于按 LangChain callback 通用机制推断**，须在 T6 用实际 SDK 版本验证（不同大版本的导入路径不同），验证后再把本条目改为确定结论。

- [x] **5. 记录选型决策**（本文件 + 长期记忆）
  观测平台 = Langfuse，自托管部署，存储与业务 PostgreSQL 隔离。

## 二、方案要点（已确认的前提）

| 项 | 结论 |
| --- | --- |
| 部署 | 自托管 docker compose，独立于业务 compose（用 profile 隔离，不进入默认 dev 链路） |
| 追踪粒度 | 一次生成任务 = 1 个 trace；每个图节点 = 1 个 observation；LLM 调用记录 model / tokens / 成本 |
| 关键标识 | `session_id` = 任务 ID，`user_id` = 用户 ID，`tags` = 服务名 / 题材 / 模型 |
| 存储 | Langfuse 独立实例，不复用业务库。官方 compose 中已确认存在 `langfuse-web`、`minio`、`langfuse-ai-gateway`；完整依赖组件以官方 `docker-compose.yml` 为准（T1 逐项核对） |
| 降级 | 未配置 key 时全链路 no-op，不阻断本地开发与测试 |

## 三、待办

### 阶段 0 · 前置核对

- [ ] T0 打开 `.env` / `.env.example` 列出已有键名（当前被本机策略拦截，需你提供或授权读取）
- [ ] T1 锁定官方 compose 的依赖组件与镜像 tag（本轮抓取只覆盖文件头尾，需逐项核对 web / worker / PostgreSQL / ClickHouse / Redis / S3 兼容存储）

### 阶段 1 · 基础设施

- [ ] T2 `infra/docker` 新增 langfuse compose（独立文件 + `--profile obs`）
- [ ] T3 根 Makefile 增加 `make obs-up` / `make obs-down`（Makefile 尚未创建，随骨架一并落地）
- [ ] T4 首次启动后在 Langfuse 创建 project，签发 public / secret key

### 阶段 2 · 配置与共享库

- [ ] T5 `.env.example` 增补 `LANGFUSE_HOST` / `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_TRACING_ENABLED`（键名按 T0 结论统一风格）；`.env` 只存真实值（已核实 `.env` 不出现在 `git status -uall` 的未跟踪列表中，即已被 `.gitignore` 忽略，不会入库）
- [ ] T6 `packages/python-common` 增加 `observability.py`：读取配置、构造 callback handler、提供 `@observe` 装饰器
- [ ] T7 实现 no-op 降级：key 缺失或 `LANGFUSE_TRACING_ENABLED=false` 时返回空 handler

### 阶段 3 · 接入 orchestrator（核心链路）

- [ ] T8 在 LangGraph `invoke` / `astream` 的 `config` 中集中注入 callbacks，禁止各节点自行创建 handler
- [ ] T9 trace 属性规范落地：`session_id=task_id`、`user_id`、`tags`、`metadata`
- [ ] T10 节点级命名规范 `${service}.${node}`，保证 UI 中可直接定位状态机节点
- [ ] T11 trace 与检查点关联：`thread_id` / `checkpoint_id` 写入 trace metadata，便于从失败任务反查

### 阶段 4 · 覆盖其余微服务

- [ ] T12 script / image / tts / video 的 LLM 与第三方 API 调用加 span
- [ ] T13 gateway 透传 trace 上下文（请求头携带标识），避免前端请求与后端 trace 断裂
- [ ] T14 采样策略：高并发生成任务下按比例采样，避免 Langfuse 写入放大

### 阶段 5 · 验证与文档

- [ ] T15 端到端验证：跑一次完整生成任务，在 Langfuse UI 看到「任务 → 节点 → LLM 调用」的完整 trace 树
- [ ] T16 补测试：未配置 key 时 no-op 通过；配置后能取到 trace id
- [ ] T17 `README.md` 技术栈表新增「可观测性 = Langfuse」行；`docs/` 增加 ADR（选型理由、数据保留期、脱敏策略）
- [ ] T18 隐私处理：剧本与提示词含创作内容，明确上报字段白名单与脱敏规则（是否上报全文需产品决策）

### 阶段 6 · 生产

- [ ] T19 生产环境仅内网暴露 `langfuse-web`，加鉴权与 TLS
- [ ] T20 备份与容量规划（trace 保留期、ClickHouse 磁盘水位告警）

## 四、验收标准（接入完成的定义）

1. 一次生成任务在 Langfuse UI 中呈现为单个 trace，包含全部图节点与模型调用。
2. 从 trace 能反查到 task_id、thread_id、checkpoint_id 与执行服务。
3. 未配置 key 时服务正常启动，且不发起上报请求。
4. 敏感内容按白名单上报，脱敏规则有文档记录。

## 五、证据索引

| 勾选项 | 证据 |
| --- | --- |
| 1 | `**/*` 全量清单仅含 `.env`、`.env.example`、`.gitignore`、`README.md` 与 17 个模块 README；正则 `(?i)langfuse|tracing|observability|otel|opentelemetry` 在非 `.git` 文件零命中 |
| 2 | `**/*` 清单中不存在 `package.json` / `pyproject.toml` / `requirements.txt`；README.md:106 约定「每个服务目录自带依赖清单」 |
| 3 | `**/.env*` 命中 `.env`、`.env.example`；`repo.read` 对这两个路径返回策略拒绝（file 规则） |
| 4 | 官方集成页存在且标题覆盖 LangChain 与 LangGraph（integrations/frameworks/langchain）；**正文未取到**（前端渲染），注入 `config["callbacks"]` 的细节为推断，待 T6 实测 |
| 5 | 长期记忆 decision 条目（本次会话写入）+ 本文件第二节 |
