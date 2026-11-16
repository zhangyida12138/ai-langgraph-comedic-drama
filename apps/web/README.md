# apps/web

漫剧生成平台 Web 前端（React + Vite + TypeScript）。

- 负责分镜脚本编辑、角色设定、生成进度与成片预览等界面
- 通过 packages/sdk 调用 services/gateway 暴露的 HTTP/SSE 接口
- 构建产物 dist 为可直接部署的静态站点，由 infra/nginx 托管

## 当前实现（骨架）

- `index.html` / `src/main.tsx` / `src/App.tsx` / `src/index.css`：入口页面，启动时请求 `/health` 并展示后端连通状态
- `vite.config.ts`：dev server 端口 5173（`strictPort`），把 `/api` 与 `/health` 代理到 `VITE_GATEWAY_TARGET`（默认 `http://127.0.0.1:8000`）
- `package.json`：`dev` / `build`（`tsc --noEmit && vite build`）/ `preview` / `typecheck`
- 依赖（实际解析）：React 19.3.1、Vite 8.3.8、TypeScript 7.0.2

启动：仓库根目录 `make dev-frontend`，或 `pnpm --filter @cdrama/web dev`。打开地址用 `http://localhost:5173`（Vite 8 默认只绑 IPv6 回环，`127.0.0.1:5173` 连不上）。
