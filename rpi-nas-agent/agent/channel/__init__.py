"""
消息通道适配器基类
支持扩展飞书、企业微信、钉钉、Telegram 等机器人平台
"""
from abc import ABC, abstractmethod
from typing import Any, Callable, Optional

from ..agent import Agent


class MessageChannel(ABC):
    """消息通道基类——所有机器人平台继承此类"""

    def __init__(self, name: str, agent: Agent, config: dict):
        self.name = name
        self.agent = agent
        self.config = config

    @abstractmethod
    async def start(self):
        """启动通道（注册 webhook 路由 / 建立长连接）"""
        ...

    @abstractmethod
    async def stop(self):
        """停止通道"""
        ...

    @abstractmethod
    def get_webhook_routes(self) -> list[tuple[str, str, Callable]]:
        """
        返回需要注册的 webhook 路由列表
        每个元素: (method, path, handler)
        """
        ...

    async def handle_message(self, user_id: str, text: str,
                             user_name: str = "") -> Optional[str]:
        """处理一条文本消息的通用流程"""
        self.agent.add_system_prompt()
        reply = await self.agent.process_text(text)
        return reply
