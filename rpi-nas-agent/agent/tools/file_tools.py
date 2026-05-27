"""
文件归类与整理工具集
操作 NAS 挂载目录中的文件
"""
import asyncio
import logging
import os
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# 文件类型分类规则
CATEGORY_RULES = {
    "视频": [
        ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm",
        ".m4v", ".mpeg", ".mpg", ".rmvb", ".ts", ".iso",
    ],
    "电视剧": [
        # 按文件名模式匹配：包含 S01E01, 第01集 等
    ],
    "音乐": [
        ".mp3", ".flac", ".wav", ".aac", ".ogg", ".wma", ".ape",
        ".m4a", ".opus",
    ],
    "图片": [
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff",
        ".raw", ".heic",
    ],
    "文档": [
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
        ".txt", ".md", ".csv", ".epub",
    ],
    "压缩包": [
        ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz",
    ],
    "软件": [
        ".exe", ".msi", ".deb", ".rpm", ".AppImage", ".dmg",
        ".iso", ".img",
    ],
    "字幕": [
        ".srt", ".ass", ".ssa", ".vtt", ".sub",
    ],
}

TV_SHOW_PATTERNS = [
    re.compile(r"[Ss](\d{2})[Ee](\d{2})"),       # S01E01
    re.compile(r"第(\d+)集"),                       # 第01集
    re.compile(r"[\.\s]E(\d{2})[\.\s]"),            # .E01.
    re.compile(r"(\d{3,4})[\s.]*话"),               # 001话
]

MOVIE_PATTERNS = [
    re.compile(r"(720p|1080p|2160p|4k|BluRay|WEB-DL|HDTV|HDRip)"),
    re.compile(r"(19|20)\d{2}"),                     # 年份
]


class FileTools:
    """文件归类与搜索工具"""

    def __init__(self, config: Dict[str, Any]):
        nas_cfg = config.get("nas", {})
        self.shares = nas_cfg.get("shares", {})

    def get_tool_definitions(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "file_list",
                    "description": "列出指定目录下的文件和文件夹",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "目录路径（相对于 NAS 根目录或绝对路径）",
                            },
                            "depth": {
                                "type": "integer",
                                "description": "递归深度（默认 1，只列出当前目录）",
                            },
                        },
                        "required": ["path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "file_search",
                    "description": "在 NAS 上搜索文件（按文件名模糊匹配）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "搜索关键词（文件名包含的内容）",
                            },
                            "search_path": {
                                "type": "string",
                                "description": "搜索范围（可选，默认全 NAS）",
                            },
                            "file_type": {
                                "type": "string",
                                "enum": ["any", "video", "audio", "image",
                                         "document", "archive"],
                                "description": "文件类型筛选",
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "最大返回结果数（默认 20）",
                            },
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "file_organize",
                    "description": "自动将指定目录中的文件按类型归类到对应目录",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "要整理的目录路径",
                            },
                            "mode": {
                                "type": "string",
                                "enum": ["auto", "preview"],
                                "description": "auto=执行整理, preview=仅预览不执行",
                            },
                        },
                        "required": ["path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "file_info",
                    "description": "获取文件的详细信息（大小、类型、修改时间等）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "文件路径",
                            }
                        },
                        "required": ["path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "file_move",
                    "description": "移动或重命名文件/文件夹",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "source": {
                                "type": "string",
                                "description": "源路径",
                            },
                            "destination": {
                                "type": "string",
                                "description": "目标路径",
                            },
                        },
                        "required": ["source", "destination"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "file_delete",
                    "description": "删除文件或空目录（会先确认）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "要删除的文件/目录路径",
                            },
                            "recursive": {
                                "type": "boolean",
                                "description": "是否递归删除目录",
                            },
                        },
                        "required": ["path"],
                    },
                },
            },
        ]

    async def execute(self, tool_name: str, params: dict) -> str:
        tool_map = {
            "file_list": self._list,
            "file_search": self._search,
            "file_organize": self._organize,
            "file_info": self._info,
            "file_move": self._move,
            "file_delete": self._delete,
        }
        func = tool_map.get(tool_name)
        if not func:
            return f"错误：未知工具 {tool_name}"
        return await func(**params)

    def _resolve_path(self, path: str) -> Path:
        """解析路径，支持短路径名映射"""
        if path.startswith("/"):
            return Path(path)
        # 检查是否是共享目录别名
        for name, share_path in self.shares.items():
            if path == name or path.startswith(f"{name}/"):
                rel = path[len(name):].lstrip("/")
                return Path(share_path) / rel if rel else Path(share_path)
        return Path(path)

    def _get_category(self, file_path: Path) -> str:
        """根据文件扩展名和名称判断分类"""
        name = file_path.name
        suffix = file_path.suffix.lower()

        # 先检查是否匹配电视剧模式
        for pattern in TV_SHOW_PATTERNS:
            if pattern.search(name):
                return "电视剧"

        # 按扩展名分类
        for category, extensions in CATEGORY_RULES.items():
            if suffix in extensions:
                return category

        return "其他"

    async def _list(self, path: str, depth: int = 1) -> str:
        target = self._resolve_path(path)
        if not target.exists():
            return f"目录不存在: {path}"

        lines = [f"📁 {target.name} (" + ("目录" if target.is_dir()
                                          else "文件") + ")"]
        if target.is_dir():
            items = sorted(target.iterdir(), key=lambda x: (x.is_file(), x.name))
            for item in items:
                if item.is_dir():
                    lines.append(f"  📁 {item.name}/")
                else:
                    size = _format_size(item.stat().st_size)
                    lines.append(f"  📄 {item.name} ({size})")
                if depth > 1 and item.is_dir():
                    sub = await self._list(str(item), depth - 1)
                    # 只取子内容（去掉第一行）
                    sub_lines = sub.split("\n")[1:]
                    lines.extend(f"    {l}" for l in sub_lines)
            lines.append(f"共 {len(items)} 项")
        return "\n".join(lines)

    async def _search(self, query: str, search_path: str = "downloads",
                      file_type: str = "any", max_results: int = 20) -> str:
        target = self._resolve_path(search_path)
        if not target.exists():
            return f"搜索路径不存在: {search_path}"

        # 文件类型筛选
        type_extensions = {
            "video": CATEGORY_RULES["视频"],
            "audio": CATEGORY_RULES["音乐"],
            "image": CATEGORY_RULES["图片"],
            "document": CATEGORY_RULES["文档"],
            "archive": CATEGORY_RULES["压缩包"],
        }
        target_exts = type_extensions.get(file_type)

        results = []
        for root, dirs, files in os.walk(target):
            for f in files:
                if query.lower() in f.lower():
                    if target_exts:
                        ext = Path(f).suffix.lower()
                        if ext not in target_exts:
                            continue
                    fp = Path(root) / f
                    results.append(fp)
                    if len(results) >= max_results:
                        break
            if len(results) >= max_results:
                break

        if not results:
            return f"未找到匹配 '{query}' 的文件"

        lines = [f"找到 {len(results)} 个匹配文件："]
        for fp in results:
            try:
                size = _format_size(fp.stat().st_size)
                rel = fp.relative_to(target) if target in fp.parents else fp
                lines.append(f"  📄 {rel} ({size})")
            except OSError:
                continue
        return "\n".join(lines)

    async def _organize(self, path: str, mode: str = "preview") -> str:
        target = self._resolve_path(path)
        if not target.exists() or not target.is_dir():
            return f"目录不存在: {path}"

        # 收集文件
        files = [f for f in target.iterdir() if f.is_file()]
        if not files:
            return "该目录中没有需要整理的文件"

        organize_map: Dict[str, List[Path]] = {}
        for f in files:
            category = self._get_category(f)
            organize_map.setdefault(category, []).append(f)

        if mode == "preview":
            lines = [f"预览整理: {target.name} （共 {len(files)} 个文件）"]
            for category, items in sorted(organize_map.items()):
                target_dir = self.shares.get(
                    _category_to_share(category),
                    str(target / category),
                )
                lines.append(f"\n📁 → {target_dir}/ ({len(items)} 个文件)")
                for item in items[:5]:
                    lines.append(f"     {item.name}")
                if len(items) > 5:
                    lines.append(f"     ... 还有 {len(items)-5} 个")
            return "\n".join(lines)

        # 执行整理
        moved = 0
        errors = []
        for category, items in sorted(organize_map.items()):
            share_name = _category_to_share(category)
            dest_dir = self.shares.get(share_name, str(target / category))
            dest_path = Path(dest_dir)
            dest_path.mkdir(parents=True, exist_ok=True)

            for item in items:
                try:
                    dest = dest_path / item.name
                    # 避免重名
                    if dest.exists():
                        stem = item.stem
                        dest = dest_path / f"{stem}_{id(item)}{item.suffix}"
                    shutil.move(str(item), str(dest))
                    moved += 1
                except Exception as e:
                    errors.append(f"{item.name}: {e}")

        msg = f"整理完成: 移动了 {moved}/{len(files)} 个文件"
        if errors:
            msg += f"\n错误: {', '.join(errors[:5])}"
        return msg

    async def _info(self, path: str) -> str:
        target = self._resolve_path(path)
        if not target.exists():
            return f"路径不存在: {path}"

        stat = target.stat()
        info = [
            f"名称: {target.name}",
            f"路径: {target}",
            f"类型: {'目录' if target.is_dir() else '文件'}",
        ]
        if target.is_file():
            info.append(f"大小: {_format_size(stat.st_size)}")
            info.append(f"后缀: {target.suffix}")
        import datetime
        info.append(f"修改时间: {datetime.fromtimestamp(stat.st_mtime)}")
        info.append(f"创建时间: {datetime.fromtimestamp(stat.st_ctime)}")
        return "\n".join(info)

    async def _move(self, source: str, destination: str) -> str:
        src = self._resolve_path(source)
        dst = self._resolve_path(destination)
        if not src.exists():
            return f"源路径不存在: {source}"
        try:
            if dst.exists():
                return f"目标已存在: {destination}"
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            return f"已移动: {source} → {destination}"
        except Exception as e:
            return f"移动失败: {e}"

    async def _delete(self, path: str, recursive: bool = False) -> str:
        target = self._resolve_path(path)
        if not target.exists():
            return f"路径不存在: {path}"
        try:
            if target.is_file():
                target.unlink()
                return f"已删除文件: {path}"
            elif target.is_dir():
                if recursive:
                    shutil.rmtree(target)
                    return f"已递归删除目录: {path}"
                else:
                    target.rmdir()
                    return f"已删除空目录: {path}"
        except Exception as e:
            return f"删除失败: {e}"


def _format_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def _category_to_share(category: str) -> str:
    """文件分类名 → 共享目录名"""
    mapping = {
        "视频": "movies",
        "电视剧": "tvshows",
        "音乐": "music",
        "图片": "photos",
        "文档": "documents",
        "压缩包": "downloads",
        "软件": "software",
        "字幕": "downloads",
    }
    return mapping.get(category, "downloads")
