"""漫剧平台跨微服务共享库。

只放基础设施（配置 / 日志 / 健康检查，后续加消息契约），不放业务逻辑：
微服务之间只通过本包定义的契约交互，不互相 import 业务代码（见 README「约束原则」）。
"""

from cdrama_common.config import ServiceSettings, get_settings
from cdrama_common.health import HEALTH_PATH, create_health_router
from cdrama_common.logging import configure_logging

__all__ = [
    "HEALTH_PATH",
    "ServiceSettings",
    "configure_logging",
    "create_health_router",
    "get_settings",
]
