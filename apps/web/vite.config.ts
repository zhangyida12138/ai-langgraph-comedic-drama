import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 后端地址默认与 Makefile 的 GATEWAY_PORT 对齐；需要改端口时用环境变量覆盖。
const GATEWAY_TARGET = process.env.VITE_GATEWAY_TARGET ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    // 前端只访问 gateway：/api 是业务接口，/health 是探测接口，均由 Vite 代理转发。
    proxy: {
      "/api": { target: GATEWAY_TARGET, changeOrigin: true },
      "/health": { target: GATEWAY_TARGET, changeOrigin: true },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: true,
  },
});
