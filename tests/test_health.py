"""骨架冒烟测试：两个服务能构造出来，/health 与最小图都能跑通。

运行：uv run pytest -q
不依赖数据库、外部模型或网络。
"""

from fastapi.testclient import TestClient
from gateway.main import create_app as create_gateway_app
from orchestrator.main import create_app as create_orchestrator_app


def test_gateway_health() -> None:
    response = TestClient(create_gateway_app()).get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "gateway"


def test_orchestrator_health() -> None:
    response = TestClient(create_orchestrator_app()).get("/health")

    assert response.status_code == 200
    assert response.json()["service"] == "orchestrator"


def test_orchestrator_preview_runs_minimal_graph() -> None:
    response = TestClient(create_orchestrator_app()).post(
        "/internal/pipeline/preview", json={"prompt": "民国上海的电影院闹鬼"}
    )

    assert response.status_code == 200
    assert response.json()["steps"] == ["plan", "draft"]
