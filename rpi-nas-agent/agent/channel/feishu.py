"""
飞书 Bot 通道
接收飞书私聊/群聊消息，转发到 Agent 处理，异步回复

使用方式：
  1. 在 .env 中配置 FEISHU_ENABLED=true 及 AppID / AppSecret
  2. 在飞书开放平台 → 应用 → 事件回调 中配置:
     请求网址: http://<树莓派IP>:8765/webhook/feishu
  3. 订阅事件: im.message.receive_v1
"""
import asyncio
import json
import logging
import re
from typing import Any, Callable, Optional

from aiohttp import web

from . import MessageChannel

logger = logging.getLogger(__name__)


class FeishuBot(MessageChannel):
    """飞书自定义机器人"""

    def __init__(self, agent, config: dict):
        super().__init__("feishu", agent, config)
        self.app_id = config.get("FEISHU_APP_ID", "")
        self.app_secret = config.get("FEISHU_APP_SECRET", "")
        self.verify_token = config.get("FEISHU_VERIFY_TOKEN", "")

    async def start(self):
        logger.info(f"飞书 Bot 已就绪（AppID: {self.app_id[:8]}...）")

    async def stop(self):
        pass

    def get_webhook_routes(self) -> list[tuple[str, str, Callable]]:
        return [
            ("POST", "/webhook/feishu", self._webhook_handler),
        ]

    async def _webhook_handler(self, request: web.Request) -> web.Response:
        """处理飞书事件回调"""
        try:
            body = await request.json()
        except json.JSONDecodeError:
            return web.json_response({"error": "bad request"}, status=400)

        # -- 飞书 URL 验证挑战（首次配置回调地址时） --
        if body.get("type") == "url_verification":
            return web.json_response({"challenge": body.get("challenge")})

        # -- 事件回调（im.message.receive_v1）--
        header = body.get("header", {})
        event_type = header.get("event_type", "")
        if event_type != "im.message.receive_v1":
            return web.json_response({"code": 0})

        event = body.get("event", {})
        msg = event.get("message", {})
        msg_type = msg.get("msg_type", "")
        chat_type = msg.get("chat_type", "")  # p2p | group

        # 只处理文本消息
        if msg_type != "text":
            return web.json_response({"code": 0})

        # 解析文本内容（content 是 JSON 字符串）
        content_str = msg.get("content", "{}")
        try:
            content = json.loads(content_str) if isinstance(content_str, str) else content_str
        except json.JSONDecodeError:
            content = {}

        text = content.get("text", "")

        # 群聊消息去掉 @bot 前缀
        if chat_type == "group":
            text = self._strip_mention(text)

        text = text.strip()
        if not text:
            return web.json_response({"code": 0})

        # 提取发送者信息
        sender = event.get("sender", {})
        sender_id = sender.get("sender_id", {})
        open_id = sender_id.get("open_id", "")
        user_name = sender_id.get("union_id", "")

        # 异步处理（不阻塞 webhook 响应）
        asyncio.ensure_future(
            self._process_and_reply(open_id, text, user_name, chat_type)
        )

        # 立即返回 success，飞书不会超时重试
        return web.json_response({"code": 0, "msg": "ok"})

    def _strip_mention(self, text: str) -> str:
        """去掉群聊消息中的 @机器人 前缀"""
        # 飞书 @ 格式: @_user_123  或  @用户名
        text = re.sub(r"@_user_\d+\s*", "", text)
        # 如果 bot 有名字，也去掉
        return text

    async def _process_and_reply(self, user_id: str, text: str,
                                 user_name: str = "", chat_type: str = "p2p"):
        """处理消息并通过飞书 API 回复"""
        import aiohttp

        try:
            # 1. Agent 处理
            reply = await self.handle_message(user_id, text, user_name)

            # 2. 获取 tenant_access_token
            access_token = await self._get_tenant_token()
            if not access_token:
                return

            # 3. 发送飞书消息
            await self._send_message(access_token, user_id, reply)

        except Exception as e:
            logger.error(f"飞书消息处理异常: {e}")

    async def _get_tenant_token(self) -> Optional[str]:
        """获取飞书 tenant_access_token"""
        import aiohttp

        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json={
                    "app_id": self.app_id,
                    "app_secret": self.app_secret,
                }) as resp:
                    data = await resp.json()
                    token = data.get("tenant_access_token", "")
                    if not token:
                        logger.error(f"飞书获取 token 失败: {data}")
                    return token
            except Exception as e:
                logger.error(f"飞书 token 请求异常: {e}")
                return None

    async def _send_message(self, token: str, open_id: str, text: str):
        """通过飞书 API 发送文本消息"""
        import aiohttp

        url = "https://open.feishu.cn/open-apis/im/v1/messages"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        payload = {
            "receive_id": open_id,
            "msg_type": "text",
            "content": json.dumps({"text": text}),
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    url,
                    params={"receive_id_type": "open_id"},
                    headers=headers,
                    json=payload,
                ) as resp:
                    result = await resp.json()
                    if result.get("code") != 0:
                        logger.error(f"飞书消息发送失败: {result}")
            except Exception as e:
                logger.error(f"飞书消息发送异常: {e}")
