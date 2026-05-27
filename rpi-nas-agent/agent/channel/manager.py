"""
通道管理器
负责加载、启动、停止所有消息通道（飞书/企业微信等）
"""
import importlib
import logging
from typing import Dict, List, Optional

from aiohttp import web

from . import MessageChannel

logger = logging.getLogger(__name__)

BUILTIN_CHANNELS = {
    "feishu": "agent.channel.feishu:FeishuBot",
    "wecom": "agent.channel.wecom:WeComBot",
}


class ChannelManager:
    """管理所有消息通道的注册和路由"""

    def __init__(self, agent: "Agent", config: dict):
        self.agent = agent
        self.config = config
        self.channels: Dict[str, MessageChannel] = {}
        self._routes: list = []

    def load_all(self):
        """从配置加载启用的通道"""
        channels_cfg = self.config.get("channels", {})

        for name, enabled in channels_cfg.items():
            if not enabled:
                continue

            channel_config = self.config.get(name, {})
            self._load_channel(name, channel_config)

    def load(self, name: str, channel_config: dict):
        """加载指定通道"""
        self._load_channel(name, channel_config)

    def _load_channel(self, name: str, channel_config: dict):
        """加载单个通道"""
        if name not in BUILTIN_CHANNELS:
            logger.warning(f"未知通道: {name}，跳过")
            return

        import_path = BUILTIN_CHANNELS[name]
        module_path, class_name = import_path.split(":", 1)

        try:
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)

            # 检查是否满足必要条件
            missing = self._check_requirements(name, channel_config)
            if missing:
                logger.info(f"通道 [{name}] 跳过: 缺少配置 {', '.join(missing)}")
                return

            channel = cls(self.agent, channel_config)
            self.channels[name] = channel
            logger.info(f"✅ 通道 [{name}] 已加载")

        except ImportError as e:
            logger.warning(f"通道 [{name}] 导入失败: {e}（请 pip install 相关依赖）")
        except Exception as e:
            logger.error(f"通道 [{name}] 加载异常: {e}")

    def _check_requirements(self, name: str, config: dict) -> list[str]:
        """检查通道的必要配置项"""
        required_map = {
            "feishu": ["FEISHU_APP_ID", "FEISHU_APP_SECRET"],
            "wecom": ["WECOM_CORP_ID", "WECOM_AGENT_ID", "WECOM_SECRET"],
        }
        required = required_map.get(name, [])
        return [k for k in required if not config.get(k)]

    def get_routes(self) -> list[tuple]:
        """收集所有通道的 webhook 路由"""
        routes = []
        for name, channel in self.channels.items():
            for route in channel.get_webhook_routes():
                routes.append(route)
                logger.info(f"  📡 {name}: {route[0]} {route[1]}")
        return routes

    async def start_all(self):
        """启动所有通道"""
        for name, channel in self.channels.items():
            try:
                await channel.start()
            except Exception as e:
                logger.error(f"通道 [{name}] 启动失败: {e}")

    async def stop_all(self):
        """停止所有通道"""
        for name, channel in self.channels.items():
            try:
                await channel.stop()
            except Exception as e:
                logger.error(f"通道 [{name}] 停止失败: {e}")

    def register_routes(self, app: web.Application):
        """将所有通道的路由注册到 aiohttp app"""
        for method, path, handler in self.get_routes():
            method_lower = method.lower()
            if method_lower == "get":
                app.router.add_get(path, handler)
            elif method_lower == "post":
                app.router.add_post(path, handler)
