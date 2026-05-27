"""
下载管理工具集
通过 qBittorrent API + Aria2 RPC 管理下载任务
"""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


class DownloadTools:
    """下载管理工具（qBittorrent + Aria2）"""

    def __init__(self, config: Dict[str, Any]):
        svc = config.get("services", {})
        self.qb_cfg = svc.get("qbittorrent", {})
        self.aria2_cfg = svc.get("aria2", {})
        self._qb_token: Optional[str] = None

    def get_tool_definitions(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "download_add",
                    "description": "添加下载任务（支持磁力链接、HTTP、HTTPS、BT 种子文件）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "下载链接或磁力链接",
                            },
                            "save_path": {
                                "type": "string",
                                "description": "保存目录（可选，默认下载目录）",
                            },
                            "engine": {
                                "type": "string",
                                "enum": ["auto", "qbittorrent", "aria2"],
                                "description": "下载引擎（auto 自动选择）",
                            },
                        },
                        "required": ["url"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "download_list",
                    "description": "查看所有下载任务的状态和进度",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "enum": ["all", "downloading", "completed",
                                         "paused", "error"],
                                "description": "按状态筛选（默认全部）",
                            }
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "download_pause",
                    "description": "暂停指定的下载任务",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "任务 ID（不提供则暂停全部）",
                            }
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "download_resume",
                    "description": "恢复已暂停的下载任务",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "任务 ID（不提供则恢复全部）",
                            }
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "download_remove",
                    "description": "删除下载任务（可选择是否同时删除文件）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "任务 ID",
                            },
                            "delete_files": {
                                "type": "boolean",
                                "description": "是否同时删除已下载的文件",
                            },
                        },
                        "required": ["task_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "download_speed_limit",
                    "description": "设置下载/上传速度限制",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "download_limit": {
                                "type": "integer",
                                "description": "下载速度限制（KB/s，0 为不限速）",
                            },
                            "upload_limit": {
                                "type": "integer",
                                "description": "上传速度限制（KB/s，0 为不限速）",
                            },
                        },
                    },
                },
            },
        ]

    async def execute(self, tool_name: str, params: dict) -> str:
        tool_map = {
            "download_add": self._add,
            "download_list": self._list,
            "download_pause": self._pause,
            "download_resume": self._resume,
            "download_remove": self._remove,
            "download_speed_limit": self._speed_limit,
        }
        func = tool_map.get(tool_name)
        if not func:
            return f"错误：未知工具 {tool_name}"
        return await func(**params)

    async def _add(self, url: str, save_path: str = "",
                   engine: str = "auto") -> str:
        # 判断使用哪个引擎
        use_qb = engine == "qbittorrent" or (
            engine == "auto" and self.qb_cfg.get("url")
        )

        if use_qb:
            return await self._qb_add(url, save_path)
        else:
            return await self._aria2_add(url, save_path)

    async def _list(self, status: str = "all") -> str:
        if self.qb_cfg.get("url"):
            return await self._qb_list(status)
        return "未配置下载引擎（请设置 QBITTORRENT_URL 或 ARIA2_RPC_URL）"

    async def _pause(self, task_id: str = "") -> str:
        if self.qb_cfg.get("url"):
            return await self._qb_pause(task_id)
        return "暂停功能需要 qBittorrent"

    async def _resume(self, task_id: str = "") -> str:
        if self.qb_cfg.get("url"):
            return await self._qb_resume(task_id)
        return "恢复功能需要 qBittorrent"

    async def _remove(self, task_id: str, delete_files: bool = False) -> str:
        if self.qb_cfg.get("url"):
            return await self._qb_remove(task_id, delete_files)
        return "删除功能需要 qBittorrent"

    async def _speed_limit(self, download_limit: int = 0,
                           upload_limit: int = 0) -> str:
        if self.qb_cfg.get("url"):
            return await self._qb_set_speed(download_limit, upload_limit)
        return "限速功能需要 qBittorrent"

    # --- qBittorrent 实现 ---
    async def _qb_login(self, session: aiohttp.ClientSession) -> bool:
        if self._qb_token:
            return True
        try:
            async with session.post(
                f"{self.qb_cfg['url']}/api/v2/auth/login",
                data={
                    "username": self.qb_cfg.get("username", "admin"),
                    "password": self.qb_cfg.get("password", ""),
                },
            ) as resp:
                if resp.status == 200:
                    self._qb_token = resp.cookies.get("SID", "").value
                    return True
                return False
        except Exception as e:
            logger.error(f"qBittorrent 登录失败: {e}")
            return False

    async def _qb_add(self, url: str, save_path: str = "") -> str:
        async with aiohttp.ClientSession() as session:
            if not await self._qb_login(session):
                return "连接 qBittorrent 失败"
            data = {"urls": url}
            if save_path:
                data["savepath"] = save_path
            try:
                async with session.post(
                    f"{self.qb_cfg['url']}/api/v2/torrents/add",
                    data=data,
                ) as resp:
                    if resp.status in (200, 201):
                        return f"已添加下载任务: {url[:80]}..."
                    return f"添加失败: {resp.status}"
            except Exception as e:
                return f"添加任务失败: {e}"

    async def _qb_list(self, status_filter: str = "all") -> str:
        async with aiohttp.ClientSession() as session:
            if not await self._qb_login(session):
                return "连接 qBittorrent 失败"
            try:
                async with session.get(
                    f"{self.qb_cfg['url']}/api/v2/torrents/info",
                    params={"filter": status_filter},
                ) as resp:
                    torrents = await resp.json()
                    if not torrents:
                        return "没有下载任务"
                    lines = ["当前下载任务："]
                    for t in torrents[:20]:
                        pct = t.get("progress", 0) * 100
                        speed_d = t.get("dlspeed", 0) / 1024
                        speed_u = t.get("upspeed", 0) / 1024
                        state = t.get("state", "unknown")
                        name = t.get("name", "未知")[:50]
                        lines.append(
                            f"  [{t['hash'][:8]}] {name}\n"
                            f"    进度: {pct:.1f}% | 状态: {state}\n"
                            f"    速度: ↓{speed_d:.0f} KB/s ↑{speed_u:.0f} KB/s"
                        )
                    if len(torrents) > 20:
                        lines.append(f"  ... 还有 {len(torrents) - 20} 个任务")
                    return "\n".join(lines)
            except Exception as e:
                return f"获取下载列表失败: {e}"

    async def _qb_pause(self, task_id: str = "") -> str:
        async with aiohttp.ClientSession() as session:
            if not await self._qb_login(session):
                return "连接 qBittorrent 失败"
            try:
                hashes = task_id if task_id else "all"
                async with session.post(
                    f"{self.qb_cfg['url']}/api/v2/torrents/pause",
                    data={"hashes": hashes},
                ) as resp:
                    if resp.status == 200:
                        return "已暂停" + (f"任务 {task_id[:8]}" if task_id
                                          else "所有下载任务")
                    return f"暂停失败: {resp.status}"
            except Exception as e:
                return f"暂停失败: {e}"

    async def _qb_resume(self, task_id: str = "") -> str:
        async with aiohttp.ClientSession() as session:
            if not await self._qb_login(session):
                return "连接 qBittorrent 失败"
            try:
                hashes = task_id if task_id else "all"
                async with session.post(
                    f"{self.qb_cfg['url']}/api/v2/torrents/resume",
                    data={"hashes": hashes},
                ) as resp:
                    if resp.status == 200:
                        return "已恢复" + (f"任务 {task_id[:8]}" if task_id
                                          else "所有下载任务")
                    return f"恢复失败: {resp.status}"
            except Exception as e:
                return f"恢复失败: {e}"

    async def _qb_remove(self, task_id: str,
                         delete_files: bool = False) -> str:
        async with aiohttp.ClientSession() as session:
            if not await self._qb_login(session):
                return "连接 qBittorrent 失败"
            try:
                async with session.post(
                    f"{self.qb_cfg['url']}/api/v2/torrents/delete",
                    data={
                        "hashes": task_id,
                        "deleteFiles": str(delete_files).lower(),
                    },
                ) as resp:
                    if resp.status == 200:
                        return (f"已删除任务 {task_id[:8]}" +
                                ("（文件已删除）" if delete_files else ""))
                    return f"删除失败: {resp.status}"
            except Exception as e:
                return f"删除失败: {e}"

    async def _qb_set_speed(self, dl_limit: int = 0,
                            ul_limit: int = 0) -> str:
        async with aiohttp.ClientSession() as session:
            if not await self._qb_login(session):
                return "连接 qBittorrent 失败"
            try:
                async with session.post(
                    f"{self.qb_cfg['url']}/api/v2/transfer/setDownloadLimit",
                    data={"limit": dl_limit * 1024},
                ) as resp:
                    pass
                async with session.post(
                    f"{self.qb_cfg['url']}/api/v2/transfer/setUploadLimit",
                    data={"limit": ul_limit * 1024},
                ) as resp:
                    pass
                parts = []
                if dl_limit:
                    parts.append(f"下载限速 {dl_limit} KB/s")
                if ul_limit:
                    parts.append(f"上传限速 {ul_limit} KB/s")
                return f"已设置速度限制: {', '.join(parts) or '不限速'}"
            except Exception as e:
                return f"设置限速失败: {e}"

    # --- Aria2 实现（备用） ---
    async def _aria2_add(self, url: str, save_path: str = "") -> str:
        if not self.aria2_cfg.get("rpc_url"):
            return "未配置 Aria2（请在 .env 中设置 ARIA2_RPC_URL）"
        payload = {
            "jsonrpc": "2.0",
            "id": "rpi-agent",
            "method": "aria2.addUri",
            "params": [
                f"token:{self.aria2_cfg.get('secret', '')}",
                [url],
            ],
        }
        if save_path:
            payload["params"][1] = {"dir": save_path}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.aria2_cfg["rpc_url"],
                    json=payload,
                ) as resp:
                    data = await resp.json()
                    if "result" in data:
                        return f"已添加 Aria2 下载任务: {data['result'][:16]}"
                    return f"Aria2 添加失败: {data}"
            except Exception as e:
                return f"Aria2 连接失败: {e}"
