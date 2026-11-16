"""最小 LangGraph 图。

作用有两个：验证 langgraph 依赖可用；作为真实流程的替换点。
真实流程（题材 → 大纲 → 分镜 → 画面 → 配音 → 合成）由各微服务承担，
接入前需先完成 steps.md 卷 A 的租户隔离（A22：thread_id 带 tenant 前缀）。
"""

from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class PipelineState(TypedDict, total=False):
    """图状态；后续接入数据库与检查点后再补 task_id / tenant_id 等字段。"""

    prompt: str
    steps: list[str]


def _plan(state: PipelineState) -> dict[str, list[str]]:
    return {"steps": [*state.get("steps", []), "plan"]}


def _draft(state: PipelineState) -> dict[str, list[str]]:
    return {"steps": [*state.get("steps", []), "draft"]}


def build_graph():
    """编译最小两节点图：START → plan → draft → END。"""
    graph = StateGraph(PipelineState)
    graph.add_node("plan", _plan)
    graph.add_node("draft", _draft)
    graph.add_edge(START, "plan")
    graph.add_edge("plan", "draft")
    graph.add_edge("draft", END)
    return graph.compile()
