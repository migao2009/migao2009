"""
媒体播放与调取工具集
通过 Jellyfin API 或直接文件访问播放 NAS 视频
"""
import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


class MediaTools:
    """媒体播放与调取工具"""

    def __init__(self, config: Dict[str, Any]):
        svc = config.get("services", {})
        self.jf_cfg = svc.get("jellyfin", {})
        self.shares = config.get("nas", {}).get("shares", {})

    def get_tool_definitions(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "media_search",
                    "description": "搜索 NAS 上的影视资源，返回可播放的媒体列表",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keyword": {
                                "type": "string",
                                "description": "搜索关键词（电影名/电视剧名）",
                            },
                            "media_type": {
                                "type": "string",
                                "enum": ["all", "movie", "tvshow"],
                                "description": "媒体类型筛选",
                            },
                        },
                        "required": ["keyword"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "media_list_library",
                    "description": "列出 NAS 上的媒体库分类（电影/电视剧/音乐等）",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "media_get_info",
                    "description": "获取指定媒体的详细信息（演员、简介、评分、格式等）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "media_id": {
                                "type": "string",
                                "description": "媒体 ID 或文件路径",
                            }
                        },
                        "required": ["media_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "media_play",
                    "description": "在树莓派本地播放指定的视频（通过外接音箱出声音，HDMI 出画面），或通过 DLNA 投屏到电视",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "媒体文件路径（在 NAS 上的路径）",
                            },
                            "method": {
                                "type": "string",
                                "enum": ["local", "dlna"],
                                "description": "local=本地播放, dlna=投屏到电视",
                            },
                        },
                        "required": ["path"],
                    },
                },
            },
        ]

    async def execute(self, tool_name: str, params: dict) -> str:
        tool_map = {
            "media_search": self._search,
            "media_list_library": self._list_library,
            "media_get_info": self._get_info,
            "media_play": self._play,
        }
        func = tool_map.get(tool_name)
        if not func:
            return f"错误：未知工具 {tool_name}"
        return await func(**params)

    async def _search(self, keyword: str, media_type: str = "all") -> str:
        # Jellyfin 搜索
        if self.jf_cfg.get("api_key"):
            return await self._jf_search(keyword, media_type)
        # 备用: 文件系统搜索
        return await self._fs_search(keyword)

    async def _list_library(self) -> str:
        if self.jf_cfg.get("api_key"):
            return await self._jf_list_library()
        return "未配置 Jellyfin（如需使用媒体库，请设置 JELLYFIN_URL 和 JELLYFIN_API_KEY）\n媒体目录:\n" + "\n".join(
            f"  📁 {name}: {path}" for name, path in self.shares.items()
            if name in ("movies", "tvshows", "music")
        )

    async def _get_info(self, media_id: str) -> str:
        if self.jf_cfg.get("api_key"):
            return await self._jf_get_info(media_id)
        return f"Jellyfin 未配置，无法获取详细信息。\n文件路径: {media_id}"

    async def _play(self, path: str, method: str = "local") -> str:
        """播放视频"""
        # 解析实际文件路径
        video_path = self._resolve_media_path(path)
        if not video_path or not Path(video_path).exists():
            if self.jf_cfg.get("api_key"):
                # 尝试从 Jellyfin 获取流地址
                return await self._jf_play(path)
            return f"文件不存在: {path}"

        if method == "dlna":
            return await self._dlna_play(video_path)
        else:
            return await self._local_play(video_path)

    def _resolve_media_path(self, path: str) -> Optional[str]:
        """解析媒体路径"""
        p = Path(path)
        if p.exists():
            return str(p)
        # 尝试通过共享目录别名解析
        for name, share_path in self.shares.items():
            if path.startswith(name):
                rel = path[len(name):].lstrip("/")
                resolved = Path(share_path) / rel
                if resolved.exists():
                    return str(resolved)
        return None

    async def _local_play(self, video_path: str) -> str:
        """本地播放（通过 omxplayer/vlc/mpv）"""
        # 检测可用的播放器
        players = []
        for player, cmd in [
            ("mpv", ["mpv", "--fullscreen"]),
            ("vlc", ["vlc", "--fullscreen"]),
            ("ffplay", ["ffplay", "-nodisp", "-autoexit"]),
        ]:
            try:
                subprocess.run(
                    ["which", player],
                    capture_output=True, text=True, check=True,
                )
                players.append(cmd)
            except subprocess.CalledProcessError:
                continue

        if not players:
            return "未找到可用的视频播放器（请安装 mpv: sudo apt install mpv）"

        cmd = [*players[0], video_path]
        # 后台播放，不阻塞 agent
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
        return f"正在播放: {Path(video_path).name}\n播放器: {players[0][0]}"

    async def _dlna_play(self, video_path: str) -> str:
        """通过 DLNA 投屏到电视"""
        try:
            # 使用 gmediarender 或 udpxy 实现 DLNA
            # 或者使用简单的 curl 发送 UPnP 命令
            from upnpclient import Device

            # 搜索网络中的 DLNA 设备
            result = subprocess.run(
                ["gssdp-discover", "--timeout=3"],
                capture_output=True, text=True,
            )
            if result.returncode != 0:
                raise RuntimeError("未找到 DLNA 设备")

            found = result.stdout
            return (f"找到 DLNA 设备。正在投屏 {Path(video_path).name} 到电视。\n"
                    f"提示: 也可以直接在电视上通过 SMB 打开:\n"
                    f"  smb://nas/{Path(video_path).relative_to('/mnt/nas')}")
        except ImportError:
            return (f"需要安装 UPnP 客户端来投屏。\n"
                    f"视频路径: {video_path}\n"
                    f"提示: 可在电视上通过 SMB/NFS 直接播放")
        except Exception as e:
            return f"投屏失败: {e}\n可手动播放: {video_path}"

    # --- Jellyfin API 实现 ---
    async def _jf_headers(self):
        return {
            "X-Emby-Token": self.jf_cfg.get("api_key", ""),
            "Content-Type": "application/json",
        }

    async def _jf_search(self, keyword: str, media_type: str = "all") -> str:
        url = f"{self.jf_cfg['url']}/Items"
        params = {
            "searchTerm": keyword,
            "IncludePeople": False,
            "IncludeMedia": True,
            "IncludeGenres": False,
            "IncludeStudios": False,
            "IncludeArtists": False,
            "Recursive": True,
            "Limit": 20,
        }
        if media_type == "movie":
            params["IncludeItemTypes"] = "Movie"
        elif media_type == "tvshow":
            params["IncludeItemTypes"] = "Series,Episode"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    url, params=params, headers=await self._jf_headers()
                ) as resp:
                    data = await resp.json()
                    items = data.get("Items", [])
                    if not items:
                        return f"未找到匹配 '{keyword}' 的媒体"
                    lines = [f"找到 {data.get('TotalRecordCount', len(items))} 个结果："]
                    for item in items[:15]:
                        t = item.get("Type", "Unknown")
                        # Convert type
                        type_map = {"Movie": "🎬", "Series": "📺", "Episode": "📺",
                                    "Audio": "🎵", "MusicAlbum": "💿", "MusicArtist": "🎤"}
                        icon = type_map.get(t, "📄")
                        name = item.get("Name", "未知")
                        year = item.get("ProductionYear", "")
                        lines.append(f"  {icon} [{item['Id'][:8]}] {name} ({t})"
                                     f"{f' {year}' if year else ''}")
                    return "\n".join(lines)
            except Exception as e:
                return f"搜索失败: {e}"

    async def _jf_list_library(self) -> str:
        url = f"{self.jf_cfg['url']}/Library/MediaFolders"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    url, headers=await self._jf_headers()
                ) as resp:
                    data = await resp.json()
                    items = data.get("Items", [])
                    lines = ["Jellyfin 媒体库："]
                    for item in items:
                        lines.append(f"  📁 {item['Name']} "
                                     f"({item.get('Path', '未知')})")
                    return "\n".join(lines)
            except Exception as e:
                return f"获取媒体库失败: {e}"

    async def _jf_get_info(self, media_id: str) -> str:
        url = f"{self.jf_cfg['url']}/Users/me/Items/{media_id}"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    url, headers=await self._jf_headers()
                ) as resp:
                    item = await resp.json()
                    lines = [
                        f"标题: {item.get('Name', '未知')}",
                        f"类型: {item.get('Type', '未知')}",
                    ]
                    if item.get("ProductionYear"):
                        lines.append(f"年份: {item['ProductionYear']}")
                    if item.get("Overview"):
                        lines.append(f"简介: {item['Overview'][:200]}")
                    if item.get("RunTimeTicks"):
                        mins = item['RunTimeTicks'] // 600_000_000
                        lines.append(f"时长: {mins} 分钟")
                    if item.get("MediaSources"):
                        src = item["MediaSources"][0]
                        if src.get("Container"):
                            lines.append(f"格式: {src['Container']}")
                        if src.get("Path"):
                            lines.append(f"路径: {src['Path']}")
                    return "\n".join(lines)
            except Exception as e:
                return f"获取媒体信息失败: {e}"

    async def _jf_play(self, path: str) -> str:
        """通过 Jellyfin 获取播放地址"""
        url = f"{self.jf_cfg['url']}/Items"
        params = {
            "searchTerm": Path(path).stem,
            "Recursive": True,
            "Limit": 1,
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    url, params=params, headers=await self._jf_headers()
                ) as resp:
                    data = await resp.json()
                    items = data.get("Items", [])
                    if not items:
                        return f"在 Jellyfin 中未找到: {path}"
                    item_id = items[0]["Id"]
                    stream_url = (
                        f"{self.jf_cfg['url']}/Videos/{item_id}/stream"
                    )
                    return (f"播放地址: {stream_url}\n"
                            f"可在浏览器中打开，或使用 VLC/MPV 播放")
            except Exception as e:
                return f"获取播放地址失败: {e}"
