"""
企业微信 Bot 通道
支持两种接入方式:
  1. 企业微信群机器人 Webhook（接收消息需要配置回调 URL）
  2. 企业微信自建应用（完整的消息接收&回复）
"""
import hashlib
import json
import logging
import xml.etree.ElementTree as ET
from typing import Any, Callable, Optional

from aiohttp import web

from . import MessageChannel

logger = logging.getLogger(__name__)


class WeComBot(MessageChannel):
    """企业微信 bot 通道"""

    def __init__(self, agent, config: dict):
        super().__init__("wecom", agent, config)
        self.corp_id = config.get("WECOM_CORP_ID", "")
        self.agent_id = config.get("WECOM_AGENT_ID", "")
        self.secret = config.get("WECOM_SECRET", "")
        self.token = config.get("WECOM_TOKEN", "")
        self.encoding_aes_key = config.get("WECOM_ENCODING_AES_KEY", "")
        self.webhook_url = config.get("WECOM_WEBHOOK_URL", "")

    async def start(self):
        logger.info("企业微信 Bot 已就绪")

    async def stop(self):
        pass

    def get_webhook_routes(self) -> list[tuple[str, str, Callable]]:
        routes = []
        # 自建应用回调（GET=验证URL, POST=接收消息）
        if self.token:
            routes.append(("GET", "/webhook/wecom", self._verify_url))
            routes.append(("POST", "/webhook/wecom", self._callback_handler))
        return routes

    # ========== 方式一：群机器人 Webhook（主动推送） ==========

    async def send_to_group(self, text: str) -> bool:
        """
        通过群机器人 webhook 发送消息
        需要在企业微信群里添加机器人，拿到 webhook URL
        """
        if not self.webhook_url:
            logger.warning("未配置 WECOM_WEBHOOK_URL")
            return False

        import aiohttp
        async with aiohttp.ClientSession() as session:
            try:
                payload = {
                    "msgtype": "markdown",
                    "markdown": {"content": text},
                }
                async with session.post(
                    self.webhook_url, json=payload
                ) as resp:
                    result = await resp.json()
                    if result.get("errcode") == 0:
                        return True
                    logger.error(f"企业微信推送失败: {result}")
                    return False
            except Exception as e:
                logger.error(f"企业微信推送异常: {e}")
                return False

    # ========== 方式二：自建应用（双向消息） ==========

    async def _verify_url(self, request: web.Request) -> web.Response:
        """企业微信 URL 验证（GET 请求）"""
        query = request.query
        msg_signature = query.get("msg_signature", "")
        timestamp = query.get("timestamp", "")
        nonce = query.get("nonce", "")
        echostr = query.get("echostr", "")

        # 验证签名
        if self._check_signature(msg_signature, timestamp, nonce, echostr):
            return web.Response(
                text=echostr,
                content_type="text/plain",
            )
        return web.Response(status=403, text="signature check failed")

    async def _callback_handler(self, request: web.Request) -> web.Response:
        """处理企业微信消息回调"""
        body = await request.text()
        query = request.query
        msg_signature = query.get("msg_signature", "")
        timestamp = query.get("timestamp", "")
        nonce = query.get("nonce", "")

        # 验证签名
        if not self._check_signature(msg_signature, timestamp, nonce, body):
            return web.Response(status=403)

        try:
            root = ET.fromstring(body)
            msg_type = root.findtext("MsgType", "")
            content = root.findtext("Content", "")
            from_user = root.findtext("FromUserName", "")

            if msg_type == "text" and content:
                # 异步处理
                import asyncio
                asyncio.ensure_future(
                    self._process_and_reply(from_user, content)
                )
        except Exception as e:
            logger.error(f"解析企业微信消息失败: {e}")

        return web.Response(text="ok", content_type="text/plain")

    async def _process_and_reply(self, user_id: str, text: str):
        """处理消息并回复"""
        import aiohttp
        try:
            reply = await self.handle_message(user_id, text)

            # 获取 access_token
            token_url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
            params = {
                "corpid": self.corp_id,
                "corpsecret": self.secret,
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(token_url, params=params) as resp:
                    data = await resp.json()
                    access_token = data.get("access_token", "")

                if not access_token:
                    logger.error("获取企业微信 token 失败")
                    return

                # 发送回复消息
                send_url = (
                    "https://qyapi.weixin.qq.com/cgi-bin/message/send"
                    f"?access_token={access_token}"
                )
                payload = {
                    "touser": user_id,
                    "msgtype": "text",
                    "agentid": self.agent_id,
                    "text": {"content": reply},
                    "safe": 0,
                }
                async with session.post(send_url, json=payload) as resp:
                    result = await resp.json()
                    if result.get("errcode") != 0:
                        logger.error(f"企业微信回复失败: {result}")

        except Exception as e:
            logger.error(f"企业微信处理异常: {e}")

    def _check_signature(self, msg_signature: str, timestamp: str,
                         nonce: str, content: str) -> bool:
        """验证企业微信回调签名"""
        if not self.token:
            return True  # 未配置 token 时不验证
        if not content:
            return False
        arr = sorted([self.token, timestamp, nonce, content])
        s = "".join(arr)
        sig = hashlib.sha1(s.encode("utf-8")).hexdigest()
        return sig == msg_signature
