# apps/web

漫剧生成平台 Web 前端（React + Vite + TypeScript）。

- 负责分镜脚本编辑、角色设定、生成进度与成片预览等界面
- 通过 packages/sdk 调用 services/gateway 暴露的 HTTP/SSE 接口
- 构建产物 dist 为可直接部署的静态站点，由 infra/nginx 托管
