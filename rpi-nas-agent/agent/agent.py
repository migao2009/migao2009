"""
AI Agent 核心 - 本地私有化版本
集成 Ollama 本地 LLM + 工具调度，所有数据不出内网
"""
import json
import logging
from typing import Any, Callable, Dict, List, Optional

import aiohttp

from .config import load_config
from .tools.nas_tools import NASTools
from .tools.download_tools import DownloadTools
from .tools.file_tools import FileTools
from .tools.media_tools import MediaTools

logger = logging.getLogger(__name__)

# 系统 Prompt - 定义 AI 的角色和行为
SYSTEM_PROMPT = """你是「树莓派 NAS 管家」，一个运行在树莓派上的智能家庭服务器助手。
你通过本地 AI 模型（Ollama）理解用户意图，调用各种工具来管理黑群晖 NAS。
所有数据都在家庭内网处理，不上传任何外部服务器。

## 你的能力
1. NAS 管理 - 查看存储状态、磁盘健康、重启/关机
2. 下载管理 - 添加/查看/管理 qBittorrent 下载任务
3. 文件归类 - 自动整理 NAS 上的文件到对应分类目录
4. 媒体播放 - 搜索 NAS 上的影视资源并播放

## 使用规则
- 对于危险操作（重启/关机/删除文件），必须先明确告知用户并确认
- 回复要简洁友好，中文回答
- 每次执行完工具后，把结果用通俗的语言告诉用户
- 如果用户问问题而不是下指令，直接用知识回答

## 对话风格
你是一个能干的家庭助手，说话亲切自然，像朋友一样。
"""

# 不支持的 Tool Calling 的模型列表（手工标注）
# 这些模型将使用文本解析模式来调用工具
TEXT_TOOL_MODELS = {
    "llama2", "llama3", "llama3.1", "llama3.2:1b",
    "phi", "phi3", "phi-3", "gemma", "gemma2:2b",
    "mistral:7b", "codellama",
}


class ToolRegistry:
    """工具注册中心"""

    def __init__(self, config: Dict[str, Any]):
        self.tools: Dict[str, Any] = {}
        self._tool_map: Dict[str, Callable] = {}

        modules = [
            NASTools(config),
            DownloadTools(config),
            FileTools(config),
            MediaTools(config),
        ]

        for module in modules:
            for tool_def in module.get_tool_definitions():
                name = tool_def["function"]["name"]
                self.tools[name] = tool_def
                self._tool_map[name] = module

    def get_openai_tools(self) -> list[dict]:
        return list(self.tools.values())

    def get_tool_names(self) -> str:
        return ", ".join(sorted(self.tools.keys()))

    def get_tool_descriptions(self) -> str:
        """返回工具描述文本（用于不支持 tool calling 的模型）"""
        descs = []
        for name, tool in sorted(self.tools.items()):
            func = tool["function"]
            desc = func.get("description", "")
            params = func.get("parameters", {}).get("properties", {})
            param_desc = ", ".join(
                f"{p} ({info.get('description', '?')})"
                for p, info in params.items()
            )
            descs.append(f"- {name}: {desc}"
                         f"{f'（参数: {param_desc}）' if param_desc else ''}")
        return "\n".join(descs)

    async def execute(self, tool_name: str, params: dict) -> str:
        module = self._tool_map.get(tool_name)
        if not module:
            return f"错误：未知工具 '{tool_name}'"
        logger.info(f"执行工具: {tool_name}({params})")
        return await module.execute(tool_name, params)


class Agent:
    """AI Agent 主类"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or load_config()
        self.tool_registry = ToolRegistry(self.config)
        self.llm_cfg = self.config["agent"]["llm"]
        self.provider = self.llm_cfg.get("provider", "ollama")
        self.model_name = self.llm_cfg.get("model", "qwen2.5:7b")
        self.conversation_history: List[Dict[str, str]] = []

        # 判断是否支持 tool calling
        model_key = self.model_name.lower()
        self._supports_tools = not any(
            model_key.startswith(m) for m in TEXT_TOOL_MODELS
        )

    def add_system_prompt(self):
        tools_desc = self.tool_registry.get_tool_descriptions()

        prompt = SYSTEM_PROMPT

        # 对于不支持 tool calling 的模型，在 prompt 里嵌入工具格式说明
        if not self._supports_tools:
            prompt += f"""

## 工具调用格式（重要）
你可以调用以下工具来帮助用户。如果需要调用工具，
请输出严格的 JSON 格式（不要用 markdown 代码块包裹），格式为:
```json
{{"tool": "工具名", "params": {{"参数名": "参数值"}}}}
```

可用工具:
{tools_desc}
"""
        else:
            prompt += f"\n\n可用工具:\n{tools_desc}"

        self.conversation_history.append({
            "role": "system",
            "content": prompt,
        })

    def add_message(self, role: str, content: str):
        self.conversation_history.append({"role": role, "content": content})

    async def process_text(self, user_input: str) -> str:
        """处理用户文本输入，返回文本回复"""
        self.add_message("user", user_input)
        final_reply = await self._call_llm_with_tools()
        self.add_message("assistant", final_reply)
        return final_reply

    async def _call_llm_with_tools(self) -> str:
        """调用 LLM 并处理工具调用循环"""
        max_iterations = 8
        messages = self.conversation_history

        for iteration in range(max_iterations):
            reply = await self._llm_completion(messages)

            if reply.get("type") == "text":
                content = reply["content"]

                # -- 文本式工具调用解析（给不支持 tool calling 的模型用）--
                if not self._supports_tools and content:
                    tool_call = self._parse_text_tool_call(content)
                    if tool_call:
                        tool_name = tool_call["tool"]
                        params = tool_call.get("params", {})
                        messages.append({
                            "role": "assistant", "content": content,
                        })
                        result = await self.tool_registry.execute(
                            tool_name, params
                        )
                        messages.append({
                            "role": "tool", "tool_call_id": tool_name,
                            "content": result,
                        })
                        continue

                return content

            if reply.get("type") == "tool_calls":
                for tc in reply["tool_calls"]:
                    tool_name = tc["function"]["name"]
                    try:
                        params = json.loads(tc["function"]["arguments"])
                    except json.JSONDecodeError:
                        params = {}

                    result = await self.tool_registry.execute(tool_name, params)

                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": tc["id"],
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": tc["function"]["arguments"],
                            },
                        }],
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": result,
                    })

        return "抱歉，处理超时了，请再试一次。"

    def _parse_text_tool_call(self, text: str) -> Optional[dict]:
        """从模型回复中解析文本格式的工具调用"""
        import re

        # 尝试匹配 JSON 块
        patterns = [
            r'```(?:json)?\s*({[^}]+})\s*```',
            r'({[\s\S]*?"tool"[\s\S]*?})',
        ]
        for pat in patterns:
            match = re.search(pat, text)
            if match:
                try:
                    data = json.loads(match.group(1))
                    if "tool" in data:
                        return data
                except json.JSONDecodeError:
                    continue
        return None

    async def _llm_completion(self, messages: list) -> dict:
        """调用 LLM API（对 Ollama 做专门的兼容处理）"""
        base_url = self.llm_cfg.get("base_url", "http://localhost:11434")
        api_key = self.llm_cfg.get("api_key", "")
        timeout = self.llm_cfg.get("timeout", 120)
        model = self.llm_cfg.get("model", "qwen2.5:7b")
        temperature = self.llm_cfg.get("temperature", 0.7)
        max_tokens = self.llm_cfg.get("max_tokens", 4096)

        is_ollama = "11434" in base_url or "ollama" in base_url

        headers = {"Content-Type": "application/json"}
        if api_key and not is_ollama:
            headers["Authorization"] = f"Bearer {api_key}"

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        # Ollama 原生 API vs OpenAI 兼容 API
        if is_ollama:
            api_path = f"{base_url.rstrip('/')}/v1/chat/completions"
            # Ollama 新版本工具调用兼容性
            if self._supports_tools:
                payload["tools"] = self.tool_registry.get_openai_tools()
        else:
            api_path = f"{base_url.rstrip('/')}/v1/chat/completions"
            payload["tools"] = self.tool_registry.get_openai_tools()

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    api_path,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()

                        # 如果 tool calling 不被支持，降级为文本模式
                        if is_ollama and self._supports_tools:
                            logger.warning(
                                f"模型 {model} 不支持工具调用，降级为文本模式"
                            )
                            self._supports_tools = False
                            # 重建系统 prompt 加上工具格式说明
                            self.conversation_history = [
                                m for m in self.conversation_history
                                if m["role"] != "system"
                            ]
                            self.add_system_prompt()
                            # 重试
                            return await self._llm_completion(messages)

                        logger.error(f"API 错误 ({resp.status}): {error_text}")
                        return {
                            "type": "text",
                            "content": f"AI 服务暂时不可用（{resp.status}），"
                                       f"请检查 Ollama 是否运行: ollama ps",
                        }

                    data = await resp.json()
                    choice = data["choices"][0]
                    msg = choice["message"]

                    if msg.get("tool_calls"):
                        return {
                            "type": "tool_calls",
                            "tool_calls": msg["tool_calls"],
                        }
                    else:
                        content = msg.get("content", "") or ""
                        return {"type": "text", "content": content}

            except aiohttp.ClientConnectorError:
                return {
                    "type": "text",
                    "content": "无法连接到 Ollama。请先启动: "
                               "ollama serve（或检查 http://localhost:11434 是否可达）",
                }
            except asyncio.TimeoutError:
                return {
                    "type": "text",
                    "content": "模型响应超时。本地模型运行较慢，"
                               "如果持续超时可尝试换用小模型（如 qwen2.5:3b）",
                }
            except aiohttp.ClientError as e:
                return {"type": "text", "content": f"网络连接失败: {e}"}

    def reset_conversation(self):
        system = [m for m in self.conversation_history
                  if m["role"] == "system"]
        self.conversation_history = system
