# ai-langgraph-comedic-drama

基于 Python + LangGraph 的漫剧生成平台。Monorepo 架构：前端为一套面向浏览器的 React 单页应用；后端以 FastAPI + LangGraph 拆分为多个微服务，由网关统一对外；业务数据存于 PostgreSQL。

> 当前状态：已完成目录骨架与文档，业务代码待实现（见文末「下一步」）。

## 目录结构

```
ai-langgraph-comedic-drama/
├── apps/
│   └── web/                     # React Web 前端（Vite + TypeScript）
├── services/
│   ├── gateway/                 # FastAPI API 网关 / BFF
│   ├── orchestrator/            # LangGraph 生成流程编排（核心）
│   ├── script/                  # 剧本 / 分镜文本生成
│   ├── image/                   # 画面生成
│   ├── video/                   # 运镜与成片合成
│   ├── tts/                     # 配音与字幕对齐
│   └── media/                   # 素材与产物存储
├── packages/
│   ├── shared-types/            # 前端与后端共享的 TypeScript 类型与协议
│   ├── ui/                      # 共享 React 组件库
│   ├── sdk/                     # 前端 API SDK（HTTP + SSE）
│   └── python-common/           # Python 共享库
├── infra/
│   ├── docker/                  # Dockerfile 与 compose
│   ├── nginx/                   # 反向代理配置
│   └── scripts/                 # 运维与开发脚本
├── docs/                        # 架构设计、接口契约、ADR
├── tests/                       # 端到端与契约测试
├── Makefile                     # 待添加：一键启动 / 构建
└── README.md
```

各目录内已放置 README.md（职责说明）或 .gitkeep（占位），保证空目录可被 git 跟踪。

## 目录职责

| 目录 | 职责 |
| --- | --- |
| apps/web | Web 端界面：剧本编辑、角色设定、生成进度、成片预览 |
| services/gateway | 唯一对外入口：鉴权、限流、参数校验、聚合下游、透传 SSE |
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
| 通信 | HTTP（同步）+ 消息队列（异步） | 长耗时生成走队列，进度经网关以 SSE 回推 |
| 基础设施 | Docker Compose / Nginx / 对象存储 | 本地一键拉起，生产可替换为托管服务 |

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
- 微服务之间只通过 packages/python-common 定义的契约交互，不互相 import 业务代码。
- 生成类任务全部异步化，前端凭任务 ID 订阅 SSE 获取进度。

## 计划中的 Makefile 入口

> Makefile 尚未创建，下表是约定好的目标名，实现时以此为准。

| 目标 | 作用 |
| --- | --- |
| make dev | 并行启动 gateway、各微服务与 Web dev server |
| make build | 构建 Web 前端并打包各微服务镜像 |
| make package | 产出可部署的 Web 静态资源包（dist + nginx 配置） |
| make test | 运行单元测试与跨服务契约测试 |
| make lint | 前端与 Python 的静态检查 |
| make down | 停止并清理本地容器与进程 |

## 开发约定

- 每个服务目录自带依赖清单，可独立构建与部署。
- 新增微服务时，需同时在 infra/docker 注册，并更新本 README 的目录职责表。
- 保持 apps 与 services 之间零直接依赖，跨层类型统一放 packages。

## 下一步

1. 引入 pnpm workspace 与根 Makefile。
2. 搭建 services/gateway 与 services/orchestrator 的最小 FastAPI 骨架，并接入 PostgreSQL（连接池 + 迁移脚本）。
3. 搭建 apps/web 的 Vite + React 骨架，打通一次从 orchestrator 到前端的 SSE 进度推送。