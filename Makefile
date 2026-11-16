# 漫剧生成平台 · 一键开发与构建入口
# Windows 下由 GnuWin32 make + cmd.exe 执行：recipe 里不要用 POSIX 专用命令。

SHELL := cmd.exe
.SHELLFLAGS := /c
.DEFAULT_GOAL := help

GATEWAY_PORT ?= 8000
ORCHESTRATOR_PORT ?= 8001
WEB_PORT ?= 5173

.PHONY: help setup dev dev-backend dev-frontend build test lint clean

help:
	@echo Targets:
	@echo   setup        安装依赖（uv sync --all-packages + pnpm install）
	@echo   dev          启动 gateway :$(GATEWAY_PORT) / orchestrator :$(ORCHESTRATOR_PORT) + web :$(WEB_PORT)
	@echo   dev-backend  只启动两个后端服务（各自新窗口）
	@echo   dev-frontend 只启动 Vite dev server
	@echo   build        构建 apps/web 到 apps/web/dist
	@echo   test         uv run pytest
	@echo   lint         ruff + tsc 类型检查
	@echo   clean        清理 .venv / node_modules / dist

# --all-packages 必需：根目录是 uv 虚拟聚合根（package = false），不带该参数会跳过各服务的依赖
setup:
	uv sync --all-packages
	pnpm install

dev-backend:
	start "gateway" cmd /c "uv run uvicorn gateway.main:app --reload --port $(GATEWAY_PORT)"
	start "orchestrator" cmd /c "uv run uvicorn orchestrator.main:app --reload --port $(ORCHESTRATOR_PORT)"

dev-frontend:
	pnpm --filter @cdrama/web dev --port $(WEB_PORT)

dev: dev-backend
	pnpm --filter @cdrama/web dev --port $(WEB_PORT)

build:
	pnpm --filter @cdrama/web build

test:
	uv run pytest -q

lint:
	uv run ruff check .
	pnpm --filter @cdrama/web typecheck

clean:
	if exist .venv rmdir /s /q .venv
	if exist apps\web\node_modules rmdir /s /q apps\web\node_modules
	if exist apps\web\dist rmdir /s /q apps\web\dist
