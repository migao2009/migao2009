"""
配置加载模块
从 yaml 文件 + 环境变量加载配置，环境变量优先
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"


def load_config() -> Dict[str, Any]:
    """加载所有配置"""
    load_dotenv(BASE_DIR / ".env")

    config = {}

    # 加载 agent.yaml
    agent_cfg = _load_yaml(CONFIG_DIR / "agent.yaml")
    llm = agent_cfg.get("llm", {})

    # 环境变量覆盖（适配从云端切换到本地等场景）
    if os.getenv("LLM_PROVIDER"):
        llm["provider"] = os.getenv("LLM_PROVIDER")
    if os.getenv("LLM_BASE_URL"):
        llm["base_url"] = os.getenv("LLM_BASE_URL")
    if os.getenv("LLM_MODEL"):
        llm["model"] = os.getenv("LLM_MODEL")
    if os.getenv("DEEPSEEK_API_KEY"):
        llm["api_key"] = os.getenv("DEEPSEEK_API_KEY")
    if os.getenv("OPENAI_API_KEY"):
        llm["api_key"] = os.getenv("OPENAI_API_KEY")

    agent_cfg["llm"] = llm
    config["agent"] = agent_cfg

    # 加载 nas.yaml
    nas_cfg = _load_yaml(CONFIG_DIR / "nas.yaml")
    if os.getenv("NAS_HOST"):
        nas_cfg["nas"]["host"] = os.getenv("NAS_HOST")
    if os.getenv("NAS_USERNAME"):
        nas_cfg["nas"]["username"] = os.getenv("NAS_USERNAME")
    if os.getenv("NAS_PASSWORD"):
        nas_cfg["nas"]["password"] = os.getenv("NAS_PASSWORD")
    config["nas"] = nas_cfg

    # 加载外部服务配置
    config["services"] = {
        "qbittorrent": {
            "url": os.getenv("QBITTORRENT_URL", "http://localhost:8080"),
            "username": os.getenv("QBITTORRENT_USERNAME", "admin"),
            "password": os.getenv("QBITTORRENT_PASSWORD", ""),
        },
        "aria2": {
            "rpc_url": os.getenv("ARIA2_RPC_URL", "http://localhost:6800/rpc"),
            "secret": os.getenv("ARIA2_SECRET", ""),
        },
        "jellyfin": {
            "url": os.getenv("JELLYFIN_URL", "http://localhost:8096"),
            "api_key": os.getenv("JELLYFIN_API_KEY", ""),
        },
    }

    # 加载消息通道配置
    config["channels"] = {}
    for ch in ["feishu", "wecom"]:
        enabled = os.getenv(f"{ch.upper()}_ENABLED", "").lower() in ("1", "true", "yes")
        if enabled:
            config["channels"][ch] = True
            config[ch] = {
                k: os.getenv(f"{prefix}_{k}", "")
                for k in _channel_keys(ch)
            }

    return config


def _channel_keys(name: str) -> list[str]:
    """返回通道所需的配置键名列表（用于从环境变量读取）"""
    keys_map = {
        "feishu": ["FEISHU_APP_ID", "FEISHU_APP_SECRET", "FEISHU_VERIFY_TOKEN"],
        "wecom": [
            "WECOM_CORP_ID", "WECOM_AGENT_ID", "WECOM_SECRET",
            "WECOM_TOKEN", "WECOM_ENCODING_AES_KEY", "WECOM_WEBHOOK_URL",
        ],
    }
    return keys_map.get(name, [])


def _load_yaml(path: Path) -> Dict[str, Any]:
    """安全加载 YAML 文件"""
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
