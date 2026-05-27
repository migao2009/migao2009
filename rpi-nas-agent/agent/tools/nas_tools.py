"""
NAS 管理工具集
通过 SSH + Synology API + SMB 管理黑群晖
"""
import asyncio
import logging
import subprocess
from typing import Dict, Any, Optional

import aiohttp

logger = logging.getLogger(__name__)


class NASTools:
    """群晖 NAS 管理工具"""

    def __init__(self, config: Dict[str, Any]):
        self.cfg = config["nas"]
        self.host = self.cfg["host"]
        self.username = self.cfg["username"]
        self.password = self.cfg["password"]
        self.smb_mount = self.cfg["smb"]["mount_point"]

    def get_tool_definitions(self) -> list[dict]:
        """返回 OpenAI function calling 格式的工具定义"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "nas_status",
                    "description": "获取 NAS 系统状态，包括存储使用、运行时间、系统负载",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "nas_storage",
                    "description": "获取 NAS 详细存储使用情况（每个卷的使用率）",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "nas_reboot",
                    "description": "重启 NAS 系统（需要用户确认后再执行）",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "nas_shutdown",
                    "description": "关闭 NAS 系统（需要用户确认后再执行）",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "nas_disk_info",
                    "description": "获取 NAS 磁盘健康状态和温度信息",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "nas_active_backup",
                    "description": "触发 NAS 主动备份任务（从 NAS 备份到外接存储）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_name": {
                                "type": "string",
                                "description": "备份任务名称（Hyper Backup 中的任务名）",
                            }
                        },
                        "required": ["task_name"],
                    },
                },
            },
        ]

    async def execute(self, tool_name: str, params: dict) -> str:
        """执行工具调用"""
        tool_map = {
            "nas_status": self._get_status,
            "nas_storage": self._get_storage,
            "nas_reboot": self._reboot,
            "nas_shutdown": self._shutdown,
            "nas_disk_info": self._get_disk_info,
            "nas_active_backup": self._active_backup,
        }
        func = tool_map.get(tool_name)
        if not func:
            return f"错误：未知工具 {tool_name}"
        return await func(**params)

    async def _get_status(self) -> str:
        """通过 SSH 获取 NAS 状态"""
        cmd = [
            "sshpass", "-p", self.password,
            "ssh", f"{self.username}@{self.host}",
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=10",
            "uptime && echo '---' && free -h && echo '---' && df -h /",
        ]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                return f"NAS 状态：\n```\n{result.stdout.strip()}\n```"
            else:
                # fallback: 尝试通过 Synology API 获取
                return await self._get_status_via_api()
        except Exception as e:
            return f"获取 NAS 状态失败：{e}"

    async def _get_storage(self) -> str:
        """获取存储使用情况"""
        cmd = [
            "sshpass", "-p", self.password,
            "ssh", f"{self.username}@{self.host}",
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=10",
            "df -h | grep -E '^(/dev|volume)'",
        ]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0 and result.stdout.strip():
                return f"NAS 存储使用情况：\n```\n{result.stdout.strip()}\n```"
            return "无法获取存储信息"
        except Exception as e:
            return f"获取存储信息失败：{e}"

    async def _get_disk_info(self) -> str:
        """获取磁盘健康/温度"""
        cmd = [
            "sshpass", "-p", self.password,
            "ssh", f"{self.username}@{self.host}",
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=10",
            "synodisk --info 2>/dev/null || "
            "cat /proc/diskstats | head -20",
        ]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=15
            )
            output = result.stdout.strip() or "无法获取磁盘信息"
            return f"NAS 磁盘信息：\n```\n{output}\n```"
        except Exception as e:
            return f"获取磁盘信息失败：{e}"

    async def _reboot(self) -> str:
        """重启 NAS"""
        cmd = [
            "sshpass", "-p", self.password,
            "ssh", f"{self.username}@{self.host}",
            "-o", "StrictHostKeyChecking=no",
            "sudo", "reboot",
        ]
        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return "NAS 正在重启..."
        except Exception as e:
            return f"重启命令发送失败：{e}"

    async def _shutdown(self) -> str:
        """关闭 NAS"""
        cmd = [
            "sshpass", "-p", self.password,
            "ssh", f"{self.username}@{self.host}",
            "-o", "StrictHostKeyChecking=no",
            "sudo", "poweroff",
        ]
        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return "NAS 正在关机..."
        except Exception as e:
            return f"关机命令发送失败：{e}"

    async def _active_backup(self, task_name: str = "") -> str:
        """通过 Synology API 触发备份任务"""
        # Synology API: 需要先获取 SID
        login_url = (
            f"http://{self.host}:5000/webapi/auth.cgi?"
            f"api=SYNO.API.Auth&version=6&method=login"
            f"&account={self.username}&passwd={self.password}"
            f"&session=Backup&format=cookie"
        )
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(login_url) as resp:
                    data = await resp.json()
                    if not data.get("success"):
                        return "登录 NAS API 失败"
                    sid = data["data"]["sid"]

                # 执行备份任务
                task_url = (
                    f"http://{self.host}:5000/webapi/Backup.Repo.cgi?"
                    f"api=SYNO.Backup.Repo&version=1&method=run"
                    f"&_sid={sid}"
                )
                if task_name:
                    task_url += f"&name={task_name}"

                async with session.get(task_url) as resp:
                    data = await resp.json()
                    if data.get("success"):
                        return f"备份任务 '{task_name or '默认'}' 已启动"
                    return f"启动备份任务失败: {data}"

            except Exception as e:
                return f"备份操作失败: {e}"

    async def _get_status_via_api(self) -> str:
        """通过 Synology API 获取系统状态"""
        login_url = (
            f"http://{self.host}:5000/webapi/auth.cgi?"
            f"api=SYNO.API.Auth&version=6&method=login"
            f"&account={self.username}&passwd={self.password}"
            f"&session=SYNO&format=cookie"
        )
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(login_url) as resp:
                    data = await resp.json()
                    if not data.get("success"):
                        return "无法连接 NAS（SSH 和 API 都失败了）"
                    sid = data["data"]["sid"]

                info_url = (
                    f"http://{self.host}:5000/webapi/entry.cgi?"
                    f"api=SYNO.Core.System&version=3&method=get_info"
                    f"&_sid={sid}"
                )
                async with session.get(info_url) as resp:
                    data = await resp.json()
                    if data.get("success"):
                        info = data["data"]
                        return (
                            f"NAS 系统状态：\n"
                            f"- 型号: {info.get('model', '未知')}\n"
                            f"- 版本: DSM {info.get('firmware_ver', '未知')}\n"
                            f"- 运行时间: {info.get('uptime', '未知')}\n"
                            f"- 温度: {info.get('temperature', '未知')}°C"
                        )
                    return "NAS 已连接但无法获取系统信息"
            except Exception as e:
                return f"获取 NAS 信息失败：{e}"

    async def check_mount(self) -> bool:
        """检查 NAS 共享目录是否已挂载"""
        cmd = f"mountpoint -q {self.smb_mount}"
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True
        )
        return result.returncode == 0

    async def get_mount_status(self) -> str:
        """获取挂载状态"""
        if await self.check_mount():
            result = subprocess.run(
                f"df -h {self.smb_mount} | tail -1",
                shell=True, capture_output=True, text=True,
            )
            return f"NAS 已挂载\n{result.stdout.strip()}"
        return f"NAS 未挂载（挂载点: {self.smb_mount}）"
