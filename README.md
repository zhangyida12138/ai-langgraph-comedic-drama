# ai-langgraph-comedic-drama

基于 Python + LangGraph 的漫剧生成平台。Monorepo 架构：前端为一套面向浏览器的 React 单页应用；后端以 FastAPI + LangGraph 拆分为多个微服务，由网关统一对外；业务数据存于 PostgreSQL。

> 当前状态：目录骨架与前后端最小可运行骨架均已落地（`make setup` + `make dev` 即可启动），业务功能待实现（见文末「下一步」）。

## 快速开始

前置：Node ≥ 20.19、pnpm；Python 由 [uv](https://docs.astral.sh/uv/) 管理（版本固定在 `.python-version`，首次运行会自动下载）。

```bash
make setup      # uv sync --all-packages + pnpm install
make dev        # gateway :8000 + orchestrator :8001 + web :5173
```

| 地址 | 说明 |
| --- | --- |
| <http://localhost:5173> | 前端首页，展示后端连通状态 |
| <http://localhost:8000/health> | gateway 存活检查 |
| <http://localhost:8001/health> | orchestrator 存活检查 |
| `POST http://localhost:8001/internal/pipeline/preview` | 内部接口：跑一次内置最小 LangGraph 图 |

- 开发时用 `localhost` 而非 `127.0.0.1`：Vite 8 默认只监听 IPv6 回环（实测 `127.0.0.1:5173` 拒绝连接）。
- 前端只通过 Vite 代理访问后端：`/api`（业务）与 `/health`（探测）两个前缀都转发到 gateway。
- 只跑一半：`make dev-backend` / `make dev-frontend`；验证：`make test`、`make lint`、`make build`。

## 目录结构

```
ai-langgraph-comedic-drama/
├── apps/
│   └── web/                     # React Web 前端（Vite + TypeScript，已初始化）
├── services/
│   ├── gateway/                 # FastAPI API 网关 / BFF（已初始化，含 /health）
│   ├── orchestrator/            # LangGraph 生成流程编排（核心，已初始化最小图）
│   ├── script/                  # 剧本 / 分镜文本生成
│   ├── image/                   # 画面生成
│   ├── video/                   # 运镜与成片合成
│   ├── tts/                     # 配音与字幕对齐
│   └── media/                   # 素材与产物存储
├── packages/
│   ├── shared-types/            # 前端与后端共享的 TypeScript 类型与协议
│   ├── ui/                      # 共享 React 组件库
│   ├── sdk/                     # 前端 API SDK（HTTP + SSE）
│   └── python-common/           # Python 共享库（配置 / 日志 / 健康检查，已初始化）
├── infra/
│   ├── docker/                  # Dockerfile 与 compose
│   ├── nginx/                   # 反向代理配置
│   └── scripts/                 # 运维与开发脚本
├── docs/                        # 架构设计、接口契约、ADR
├── tests/                       # 端到端与契约测试
├── Makefile                     # 一键启动 / 构建
├── pyproject.toml / uv.lock     # Python workspace（uv，3 个成员包）
├── package.json / pnpm-workspace.yaml / pnpm-lock.yaml
└── README.md
```

各目录内已放置 README.md（职责说明），保证空目录可被 git 跟踪。当前已有代码的目录：`apps/web`、`services/gateway`、`services/orchestrator`、`packages/python-common`；其余目录待初始化。

## 目录职责

| 目录 | 职责 |
| --- | --- |
| apps/web | Web 端界面：剧本编辑、角色设定、生成进度、成片预览 |
| services/gateway | 唯一对外入口：登录与令牌校验、权限校验、限流、参数校验、聚合下游、透传 SSE |
| services/orchestrator | LangGraph 状态机：题材 → 大纲 → 分镜 → 画面 → 配音 → 合成，含检查点与重试 |
| services/script | 分集大纲、分镜表、台词与旁白生成 |
| services/image | 角色定妆图、场景参考图、分镜画面（文生图 / 图生图） |
| services/video | 镜头运镜、图生视频、成片拼接 |
| services/tts | 配音合成、音色选择、字幕时间轴对齐 |
| services/media | 对象存储读写、签名 URL、产物归档与清理 |
| packages/shared-types | 生成任务、状态机事件、DTO、错误码的统一类型定义 |
| packages/ui | 剧本编辑器、角色卡片、分镜时间轴、播放器等共享组件 |
| packages/sdk | 前端调用 gateway 的 HTTP / SSE 封装，含超时重试与断线重连 |
| packages/python-common | 配置加载、结构化日志、LLM / 图像客户端、消息契约与测试夹具 |
| infra | 容器化、反向代理与运维脚本 |
| docs / tests | 架构与决策文档；跨服务 E2E 与契约测试 |

## 技术栈

| 层 | 选型 | 说明 |
| --- | --- | --- |
| 前端 | React + TypeScript + Vite | 面向浏览器的单页应用，构建产物为静态资源 |
| 后端 | FastAPI + Pydantic | 每个微服务独立进程，自带 OpenAPI 文档 |
| 编排 | LangGraph | StateGraph 描述生成流程，支持检查点、HITL 中断与流式事件 |
| 数据库 | PostgreSQL | 唯一业务库：任务、剧本、分镜、角色与产物元数据，兼存 LangGraph 检查点 |
| 缓存 / 队列 | Redis | 异步生成任务的队列与进度缓存 |
| 认证与权限 | JWT（access + refresh）+ RBAC | 角色按租户授予；权限点统一为 `resource:action`，由 gateway 强制校验 |
| 多租户隔离 | 共享 schema + PostgreSQL 行级安全（RLS） | 每张业务表强制 `tenant_id`，应用层过滤与数据库行级安全双保险 |
| 通信 | HTTP（同步）+ 消息队列（异步） | 长耗时生成走队列，进度经网关以 SSE 回推 |
| 基础设施 | Docker Compose / Nginx / 对象存储 | 本地一键拉起，生产可替换为托管服务 |

当前实际解析到的版本（`uv sync` / `pnpm install` 结果）：Python 3.13.15 · FastAPI 0.163.1 · Pydantic 2.14.3 · LangGraph 1.2.22 · Uvicorn 0.54.0 · React 19.3.1 · Vite 8.3.8 · TypeScript 7.0.2。

## 架构与数据流

```
Web (React)
      │  HTTP + SSE
      ▼
gateway (FastAPI) ──► orchestrator (LangGraph StateGraph)
                            ├──► script  (剧本 / 分镜)
                            ├──► image   (画面生成)
                            ├──► tts     (配音 / 字幕)
                            └──► video   (运镜 / 合成)
                                    │
                                    ▼
                               media (对象存储)
```

约束原则：

- 前端只访问 gateway，不直连内部微服务。
- 租户上下文只来自 JWT 的 `tenant_id` claim；请求头与请求体中的 tenant_id 一律不可信。
- 微服务之间只通过 packages/python-common 定义的契约交互，不互相 import 业务代码。
- 生成类任务全部异步化，前端凭任务 ID 订阅 SSE 获取进度。

## 计划中的 Makefile 入口

根 `Makefile` 已创建，recipe 在 Windows 下由 GnuWin32 make + `cmd.exe` 执行；`package` 与 `down` 两个目标等 Docker Compose 落地后补。

| 目标 | 作用 |
| --- | --- |
| make setup | 安装依赖：`uv sync --all-packages` + `pnpm install` |
| make dev | 后台开新窗口跑 gateway 与 orchestrator，前台跑 Web dev server |
| make dev-backend | 只启动 gateway :8000 与 orchestrator :8001 |
| make dev-frontend | 只启动 Vite dev server :5173 |
| make build | 类型检查并构建 Web 到 `apps/web/dist` |
| make test | `uv run pytest`（含两个服务的 /health 冒烟） |
| make lint | `uv run ruff check .` + `tsc --noEmit` |
| make clean | 清理 `.venv` / `node_modules` / `dist` |

## 开发约定

- 每个服务目录自带依赖清单，可独立构建与部署。
- 新增微服务时，需同时在 infra/docker 注册，并更新本 README 的目录职责表。
- 保持 apps 与 services 之间零直接依赖，跨层类型统一放 packages。

## 下一步

1. 接入 PostgreSQL 连接池与 Alembic 迁移，先建租户相关表（steps.md 卷 A 的 A03–A09、C10）。
2. 落地登录与权限骨架：gateway 的 `/api/v1/auth/*` 与令牌校验中间件（A11–A19）。
3. 其余 5 个服务（script / image / tts / video / media）按 gateway 模板补骨架，并加进 uv workspace 成员（C8）。
4. 打通一次从 orchestrator 到前端的 SSE 进度推送。