# 项目实现步骤

> 用途：漫剧生成平台从文档骨架到可上线的落地清单，按主题分卷（卷 A 认证与多租户、卷 B 可观测性），每条可勾选；已完成项在文末「全局证据索引」有对应证据。
> 基线：仓库当前只有文档骨架（4 个根文件 + 17 个模块 README，最新提交 `26847da`，工作区干净），业务代码与依赖清单尚未创建。
> 更新记录：本轮新增卷 C「项目初始化」——前后端骨架已落地并实测可启动；卷 A（认证 / 多租户）与卷 B（Langfuse）的任务编号不变。

## 进度总览

| 卷 | 范围 | 已完成 | 待办 |
| --- | --- | --- | --- |
| A | 认证 / 权限 / 多租户隔离 | 3 | 28 |
| B | Langfuse 观测接入 | 5 | 21 |
| C | 项目初始化（前后端骨架） | 5 | 6 |

> 排序理由：`tenant_id` 必须随第一批业务表一起建，否则后续每张表都要重建并回填数据；因此卷 A 的数据模型排在生成链路之前，卷 B 可与业务并行、不阻塞功能开发。

## 卷 A · 认证 / 权限 / 多租户隔离

### A.1 已完成

- [x] **A-1. 需求登记并排定优先级**
  登录、权限、租户数据隔离三项合并为卷 A。优先级：基础骨架 → 卷 A 数据模型与鉴权 → 生成链路；理由见上方排序理由。

- [x] **A-2. 现状核查：仓库内没有任何认证 / 权限实现可复用**
  对 `**/*.md` 检索 `(?i)tenant` `rbac` `permission` `jwt` `auth` 与中文「鉴权 / 登录 / 权限 / 租户」，只命中两处规划性描述（`README.md:43` gateway 职责含「鉴权」、`services/gateway/README.md:5` 同义），无代码、无依赖；`package.json` / `pyproject.toml` / `requirements.txt` 仍不存在（见卷 B 已完成第 2 条）。结论：从零设计，无历史包袱，也没有既有用户表要迁移。

- [x] **A-3. 确认鉴权落点唯一**
  `README.md:87` 已约定「前端只访问 gateway，不直连内部微服务」→ 会话校验与权限判定的强制点只有 gateway 一处；下游服务不做会话校验，只做「该资源是否属于本租户」的二次校验。这条决定了 A16 / A18 的分工。

- [ ] A-4 环境变量键名核对（`JWT_SECRET`、`DATABASE_URL`、令牌时长）需读取 `.env` / `.env.example`，**仍被本机策略 `file` 规则拦截**，故未勾选（与卷 B T0 同一限制）。

### A.2 方案要点（建议默认值，待 A01 拍板）

| 项 | 建议默认 | 备选 / 权衡 |
| --- | --- | --- |
| 认证载体 | JWT：access 15min（前端存内存）+ refresh 7d（httpOnly cookie，服务端可撤销） | 服务端 session（Redis）：撤销更简单，但每请求一次查询、且下游每服务都要能查 |
| 密码存储 | argon2id（`argon2-cffi`），参数写入 docs；不落明文、不用 md5/sha1 | bcrypt 亦可，argon2id 抗 GPU 更好 |
| 租户模型 | 共享库 + 共享 schema + 每表 `tenant_id` + PostgreSQL RLS | schema-per-tenant：迁移随租户数线性增长；database-per-tenant：合规最强、运维最重 |
| 权限模型 | RBAC：角色绑定在「租户-用户」成员关系上（同一用户在不同租户可为不同角色）；权限点统一 `resource:action` | ABAC / 资源级 ACL：更灵活但复杂度高，暂不引入 |
| 内置角色 | `owner` / `admin` / `editor` / `viewer`，其中仅 `owner` 可分配角色与删除租户 | 自定义角色放到后续版本 |
| 鉴权强制点 | gateway 验签 + 权限判定，向下游注入 `X-User-Id` / `X-Tenant-Id` / `X-Scopes` | 下游各自验签：易遗漏且密钥扩散 |
| 前端权限 | 只做菜单与按钮可见性（UX），安全判定一律在后端 | 只靠隐藏按钮 = 越权漏洞 |
| 租户上下文来源 | JWT 的 `tenant_id` claim 唯一可信 | 请求头 / Query / Body 里的 tenant_id 一律不可信 |

### A.3 待决策（A01 需拍板，之后才能落 A03–A23）

- **D1 认证载体**：JWT（access + refresh）【推荐】/ 服务端 session（Redis）。影响 A11–A16 的实现形态。
- **D2 隔离粒度**：共享 schema + RLS【推荐】/ schema-per-tenant / database-per-tenant。影响 A07、A20、A21。
- **D3 认证代码落点**：`services/gateway` 内置 `auth` 模块【推荐，早期少一个进程】/ 独立 `services/auth` 服务。若选后者，需在 README 目录树与 `infra/docker` 同步新增。
- **D4 第三方登录与企业 SSO**：本期不做，仅在 `users` 表预留 `external_idp_sub` 字段，避免将来重建用户表。

### A.4 待办

#### 阶段 A0 · 决策与前置

- [ ] A01 拍板 D1–D3 并回写本节（默认值即 A.2 表）
- [ ] A02 列出 `.env` / `.env.example` 现有键名，统一命名：`JWT_SECRET`、`ACCESS_TOKEN_TTL`、`REFRESH_TOKEN_TTL`、`DATABASE_URL`（仍受策略拦截，需你提供或授权）

#### 阶段 A1 · 数据模型（PostgreSQL）

- [ ] A03 `users` 表：`id`(uuid) / `email`(citext 唯一) / `password_hash` / `status` / `external_idp_sub`(nullable) / `created_at`
- [ ] A04 `tenants` 表：`id` / `name` / `slug`(唯一) / `plan` / `status` / `created_at`
- [ ] A05 `tenant_members` 表：主键 `(tenant_id, user_id)` + `role_id` / `status` / `invited_at` —— 用户与租户多对多，角色随成员关系授予
- [ ] A06 `roles` / `permissions` / `role_permissions` 三表 + 种子数据（A.2 的四个内置角色）；权限点清单同时导出到 `packages/shared-types`
- [ ] A07 所有业务表强制 `tenant_id uuid NOT NULL`，主键仍为全局 id，但索引一律以 `(tenant_id, ...)` 开头；外键尽量带租户维度约束
- [ ] A08 `audit_logs` 表：`actor_user_id` / `tenant_id` / `action` / `target_type` / `target_id` / `result` / `ip` / `created_at`
- [ ] A09 迁移走 Alembic，脚本放 `infra/scripts`，并提供 `make db-migrate` / `make db-seed`（Makefile 随骨架创建）

#### 阶段 A2 · 认证

- [ ] A10 密码哈希 argon2id：参数固化在 `packages/python-common`，禁止明文、禁止 md5/sha1、禁止自行实现
- [ ] A11 端点：注册 / 登录 / 刷新 / 登出 / `GET /me`，实现于 gateway
- [ ] A12 refresh token 轮换 + 服务端可撤销：只存哈希，带 `jti` 与设备标识，登出即失效
- [ ] A13 登录防爆破：Redis 按 IP + 账号双维度计数与锁定；登录失败响应不区分「账号不存在」与「密码错误」
- [ ] A14 找回密码 / 邮箱验证：最小版本后置，但 `audit_logs` 先预留事件类型

#### 阶段 A3 · 授权

- [ ] A15 JWT claims 规范：`sub`(user_id) / `tenant_id` / `role` / `scopes[]` / `iat` / `exp` / `jti`；access 15min、refresh 7d（依 D1）
- [ ] A16 gateway 中间件：验签 → 载入成员关系与角色 → 覆盖注入 `X-User-Id` / `X-Tenant-Id` / `X-Scopes`；缺租户上下文一律 401
- [ ] A17 路由级权限：声明式装饰器 `@require("episode:export")`，权限点命名 `resource:action`，清单与 `packages/shared-types` 同源
- [ ] A18 资源级权限：服务内每条查询都必须带 `tenant_id` 条件，禁止「先按 id 取出再判租户」
- [ ] A19 前端：access 存内存 + refresh 走 httpOnly cookie；401 单飞刷新（并发 5 个 401 只触发 1 次刷新）；`usePermission()` 控制菜单与按钮，仅作 UX

#### 阶段 A4 · 租户隔离

- [ ] A20 PostgreSQL RLS：每张业务表 `ENABLE ROW LEVEL SECURITY` + `POLICY ... USING (tenant_id = current_setting('app.tenant_id')::uuid)`，连接 checkout 后 `SET LOCAL app.tenant_id`
- [ ] A21 验证 RLS 真正生效：绕过应用层过滤做全表查询，跨租户仍返回 0 行；确认业务连接使用的角色不是表属主 / 超级用户（超级用户与表属主默认绕过 RLS）
- [ ] A22 LangGraph 检查点隔离：`thread_id` 采用 `{tenant_id}:{task_id}`；读取前校验前缀与 token 中的租户一致（checkpointer 自有表无法加列，只能靠命名 + 查询封装）
- [ ] A23 周边资源隔离：对象存储 key 前缀 `tenants/{tenant_id}/`（签名 URL 由 media 校验归属）、Redis key 前缀 `t:{tenant_id}:`、队列消息体带 `tenant_id` 且 worker 消费时校验
- [ ] A24 跨租户越权测试集：用租户 A 的 token 访问租户 B 的资源返回 **404**（不用 403，避免通过状态码枚举资源是否存在）

#### 阶段 A5 · 审计与观测

- [ ] A25 审计事件落地：登录成功 / 失败、角色变更、越权拒绝、导出与下载；敏感字段脱敏
- [ ] A26 与卷 B 对齐：trace 的 `user_id` 与 `tags` 增加 `tenant_id`，但不上报剧本正文（受卷 B T18 决策约束）

#### 阶段 A6 · 文档

- [ ] A27 `docs/` 增加 ADR：认证与租户隔离方案 + 威胁模型（越权、token 泄露、RLS 遗漏、内网伪造 `X-Tenant-Id`）
- [ ] A28 `README.md` 技术栈表新增「认证与权限」「多租户隔离」两行（本轮已补），并把 gateway 职责细化为「登录与权限校验」

### A.5 验收标准（卷 A 完成的定义）

1. 未登录访问受保护接口返回 401；access 过期后由 refresh 自动续期，并发多个 401 只触发一次刷新。
2. 同一用户属于两个租户，切换租户后只能看到该租户数据，切回即时生效（换发 token，不靠前端过滤）。
3. 用租户 A 的 token 请求租户 B 的 task / episode ID 返回 404，且 `audit_logs` 有拒绝记录。
4. 显式篡改请求头 `X-Tenant-Id` 与请求体 `tenant_id` 不生效（以 token 为准，且 gateway 是覆盖写入而非追加）。
5. 故意注释掉应用层的 `tenant_id` 过滤条件后，跨租户查询仍返回 0 行（RLS 兜底）——这条是「真隔离」的判定标准。
6. `viewer` 角色调用写接口返回 403；权限点清单与 `packages/shared-types` 完全一致。
7. 不知道租户前缀时无法构造出可下载的对象存储签名 URL。
8. `make test` 覆盖上述越权场景并通过。

## 卷 B · Langfuse 观测接入

### B.1 已完成

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

### B.2 方案要点（已确认的前提）

| 项 | 结论 |
| --- | --- |
| 部署 | 自托管 docker compose，独立于业务 compose（用 profile 隔离，不进入默认 dev 链路） |
| 追踪粒度 | 一次生成任务 = 1 个 trace；每个图节点 = 1 个 observation；LLM 调用记录 model / tokens / 成本 |
| 关键标识 | `session_id` = 任务 ID，`user_id` = 用户 ID，`tags` = 服务名 / 题材 / 模型 |
| 存储 | Langfuse 独立实例，不复用业务库。官方 compose 中已确认存在 `langfuse-web`、`minio`、`langfuse-ai-gateway`；完整依赖组件以官方 `docker-compose.yml` 为准（T1 逐项核对） |
| 降级 | 未配置 key 时全链路 no-op，不阻断本地开发与测试 |

### B.3 待办（阶段 T0–T20）

#### 阶段 0 · 前置核对

- [ ] T0 打开 `.env` / `.env.example` 列出已有键名（当前被本机策略拦截，需你提供或授权读取）
- [ ] T1 锁定官方 compose 的依赖组件与镜像 tag（本轮抓取只覆盖文件头尾，需逐项核对 web / worker / PostgreSQL / ClickHouse / Redis / S3 兼容存储）

#### 阶段 1 · 基础设施

- [ ] T2 `infra/docker` 新增 langfuse compose（独立文件 + `--profile obs`）
- [ ] T3 根 Makefile 增加 `make obs-up` / `make obs-down`（Makefile 尚未创建，随骨架一并落地）
- [ ] T4 首次启动后在 Langfuse 创建 project，签发 public / secret key

#### 阶段 2 · 配置与共享库

- [ ] T5 `.env.example` 增补 `LANGFUSE_HOST` / `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_TRACING_ENABLED`（键名按 T0 结论统一风格）；`.env` 只存真实值（已核实 `.env` 不出现在 `git status -uall` 的未跟踪列表中，即已被 `.gitignore` 忽略，不会入库）
- [ ] T6 `packages/python-common` 增加 `observability.py`：读取配置、构造 callback handler、提供 `@observe` 装饰器
- [ ] T7 实现 no-op 降级：key 缺失或 `LANGFUSE_TRACING_ENABLED=false` 时返回空 handler

#### 阶段 3 · 接入 orchestrator（核心链路）

- [ ] T8 在 LangGraph `invoke` / `astream` 的 `config` 中集中注入 callbacks，禁止各节点自行创建 handler
- [ ] T9 trace 属性规范落地：`session_id=task_id`、`user_id`、`tags`、`metadata`
- [ ] T10 节点级命名规范 `${service}.${node}`，保证 UI 中可直接定位状态机节点
- [ ] T11 trace 与检查点关联：`thread_id` / `checkpoint_id` 写入 trace metadata，便于从失败任务反查

#### 阶段 4 · 覆盖其余微服务

- [ ] T12 script / image / tts / video 的 LLM 与第三方 API 调用加 span
- [ ] T13 gateway 透传 trace 上下文（请求头携带标识），避免前端请求与后端 trace 断裂
- [ ] T14 采样策略：高并发生成任务下按比例采样，避免 Langfuse 写入放大

#### 阶段 5 · 验证与文档

- [ ] T15 端到端验证：跑一次完整生成任务，在 Langfuse UI 看到「任务 → 节点 → LLM 调用」的完整 trace 树
- [ ] T16 补测试：未配置 key 时 no-op 通过；配置后能取到 trace id
- [ ] T17 `README.md` 技术栈表新增「可观测性 = Langfuse」行；`docs/` 增加 ADR（选型理由、数据保留期、脱敏策略）
- [ ] T18 隐私处理：剧本与提示词含创作内容，明确上报字段白名单与脱敏规则（是否上报全文需产品决策）

#### 阶段 6 · 生产

- [ ] T19 生产环境仅内网暴露 `langfuse-web`，加鉴权与 TLS
- [ ] T20 备份与容量规划（trace 保留期、ClickHouse 磁盘水位告警）

### B.4 验收标准（接入完成的定义）

1. 一次生成任务在 Langfuse UI 中呈现为单个 trace，包含全部图节点与模型调用。
2. 从 trace 能反查到 task_id、thread_id、checkpoint_id 与执行服务。
3. 未配置 key 时服务正常启动，且不发起上报请求。
4. 敏感内容按白名单上报，脱敏规则有文档记录。

## 卷 C · 项目初始化（前后端骨架）

### C.1 已完成

- [x] **C-1. 依赖管理定稿**
  Python 用 uv workspace：根 `pyproject.toml` 是 `package = false` 的聚合根，成员为 `packages/python-common`、`services/gateway`、`services/orchestrator`，共享一份 `uv.lock`；前端用 pnpm workspace（`pnpm-workspace.yaml` 覆盖 `apps/*`、`packages/*`）。与 README「每个服务目录自带依赖清单」不冲突：每个成员仍是能独立构建的包。

- [x] **C-2. 后端骨架 3 个包**
  `packages/python-common`：`ServiceSettings`（pydantic-settings，读根目录 `.env`）、单行 JSON 日志、`create_health_router()` 健康检查契约；`services/gateway`：FastAPI 入口 + `/health` + CORS；`services/orchestrator`：同构入口 + 最小 LangGraph 图 + `POST /internal/pipeline/preview`。

- [x] **C-3. 前端骨架 `apps/web`**
  Vite 8 + React 19 + TypeScript 7，`tsc --noEmit && vite build` 作为构建；`/api` 与 `/health` 两个前缀代理到 gateway，首页实时展示后端 `/health` 结果。

- [x] **C-4. 一键入口 `Makefile`**
  `setup / dev / dev-backend / dev-frontend / build / test / lint / clean`。环境事实：Windows 上 make 为 GNU Make 3.81（不支 `.RECIPEPREFIX`，recipe 必须用制表符），shell 为 `cmd.exe`，因此 recipe 不使用 POSIX 专用命令。

- [x] **C-5. 依赖安装 + 构建/类型检查/启动凒烟全部跑通**
  证据见文末 C-1 至 C-5。

### C.2 待办

- [ ] C6 `.env.example` 补齐键名：`APP_ENV` / `LOG_LEVEL` / `DATABASE_URL` / `REDIS_URL`（与 `ServiceSettings` 字段一一对应）——`.env` 与 `.env.example` 仍被本机策略 `file` 规则拒绝，需你授权或手动补
- [ ] C7 核对 `.gitignore` 当前工作区的新增内容：`git diff --stat` 显示 `+46` 行，其中 `.gitignore:87` 的 `node_modules/` 已覆盖前端依赖（`git check-ignore -v apps/web/node_modules` 命中该行）；这 46 行不是本轮改动，来源待你确认后再纳入首次提交
- [ ] C8 其余 5 个服务（script / image / tts / video / media）按 gateway 模板补骨架，并加入 `[tool.uv.workspace] members`
- [ ] C9 gateway 挂载 `/api/v1` 路由组，加请求 ID 中间件与统一错误响应
- [ ] C10 接入 PostgreSQL 连接池（asyncpg/SQLAlchemy）与 Alembic 迁移，接卷 A 的 A03–A09
- [ ] C11 CI：`make lint && make test && make build`，并缓存 uv / pnpm 存储

## 全局证据索引

| 勾选项 | 证据 |
| --- | --- |
| A-2 | `repo_grep` 正则 `(?i)tenant\|rbac\|permission\|jwt\|auth\|鉴权\|登录\|权限\|租户`（`**/*.md`）仅 2 处规划性描述命中：`README.md:43`、`services/gateway/README.md:5`；无实现、无依赖清单 |
| A-3 | `README.md:87`「前端只访问 gateway，不直连内部微服务」 |
| A-4 | `.env`、`.env.example` 读取被本机策略 `file` 规则拒绝（与证据行 B-3 同一限制），键名未核实 |
| B-1 | `**/*` 全量清单仅含 `.env`、`.env.example`、`.gitignore`、`README.md` 与 17 个模块 README；正则 `(?i)langfuse\|tracing\|observability\|otel\|opentelemetry` 在非 `.git` 文件零命中 |
| B-2 | `**/*` 清单中不存在 `package.json` / `pyproject.toml` / `requirements.txt`；README.md:106 约定「每个服务目录自带依赖清单」 |
| B-3 | `**/.env*` 命中 `.env`、`.env.example`；`repo.read` 对这两个路径返回策略拒绝（file 规则） |
| B-4 | 官方集成页存在且标题覆盖 LangChain 与 LangGraph（integrations/frameworks/langchain）；**正文未取到**（前端渲染），注入 `config["callbacks"]` 的细节为推断，待 T6 实测 |
| B-5 | 长期记忆 decision 条目（本次会话写入）+ 本文件 B.2 节 |
| C-1 | `uv sync --all-packages` 输出：`Resolved 60 packages`，安装 `cdrama-common` / `gateway` / `orchestrator` 三个本地包（fastapi 0.163.1、langgraph 1.2.22、pydantic 2.14.3、uvicorn 0.54.0）；`pnpm install` 输出 `Scope: all 2 workspace projects` |
| C-2 | `make test` → `3 passed`（gateway `/health`、orchestrator `/health`、preview 图执行返回 `["plan","draft"]`） |
| C-3 | `make build` → `vite v8.3.8` 构建成功，产物 `dist/assets/index-DGoSMATH.js 220.81 kB`；`make lint` → `All checks passed!` + `tsc --noEmit` 无输出 |
| C-4 | `make -n dev` 打印三条命令：两个 `uv run uvicorn ... --port 8000/8001` + `pnpm --filter @cdrama/web dev --port 5173`；`make --version` = GNU Make 3.81 |
| C-5 | 实机启动凒烟（非 TestClient）：`GET :8000/health` → 200 `{"status":"ok","service":"gateway","version":"0.1.0"}`；`GET :8001/health` → 200；`POST :8001/internal/pipeline/preview` → 200；`GET localhost:5173/` → 200 且含 `id="root"`；`GET localhost:5173/health` → 200 同一 JSON（Vite 代理转发生效）；`127.0.0.1:5173` 拒连接（Vite 8 默认只绑 IPv6 回环） |
