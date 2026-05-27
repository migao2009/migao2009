"""
树莓派 NAS 智能管家 - 主入口
支持三种交互模式:
  1. voice  - 语音交互（USB 麦克风 + 外接音箱）
  2. cli    - 命令行对话
  3. api    - HTTP API 服务（Web 界面）
"""
import argparse
import asyncio
import logging
import signal
import sys
from pathlib import Path

import yaml

from .agent import Agent
from .config import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("main")


async def run_cli():
    """命令行交互模式"""
    config = load_config()
    agent = Agent(config)
    agent.add_system_prompt()
    print("\n🤖 树莓派 NAS 管家已启动（CLI 模式）")
    print("输入 'exit' 退出，输入 'reset' 重置对话\n")

    while True:
        try:
            user_input = input("👤 你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "q"):
            print("再见！")
            break
        if user_input.lower() == "reset":
            agent.reset_conversation()
            agent.add_system_prompt()
            print("对话已重置\n")
            continue

        print("🤖 思考中...", end="", flush=True)
        reply = await agent.process_text(user_input)
        print(f"\r🤖 管家: {reply}\n")


async def run_voice():
    """语音交互模式"""
    config = load_config()
    agent = Agent(config)
    agent.add_system_prompt()

    from .voice import STTEngine, TTSEngine
    from .wake_word import WakeWordDetector, VoiceActivityDetector

    voice_cfg = config["agent"]
    stt = STTEngine(
        model_size=voice_cfg["stt"]["model"],
        language=voice_cfg["stt"]["language"],
    )
    tts = TTSEngine(
        voice=voice_cfg["tts"]["voice"],
        speed=voice_cfg["tts"]["speed"],
    )
    vad = VoiceActivityDetector(
        silence_timeout=1.5,
    )

    wake_enabled = voice_cfg["wake_word"]["enabled"]
    if wake_enabled:
        detector = WakeWordDetector(
            sensitivity=voice_cfg["wake_word"]["sensitivity"],
            on_wake=lambda: logger.info("唤醒词触发"),
        )
        detector.start()
        logger.info("唤醒词监听已启动，说 'hey raspberry' 唤醒")
    else:
        logger.info("按 Enter 开始录音（唤醒词已禁用）")

    print("\n🎤 树莓派 NAS 管家已启动（语音模式）")
    print("说 'hey raspberry' 唤醒我（或按 Ctrl+C 退出）\n")

    greeting = "你好，我是你的 NAS 管家，有什么需要帮忙的吗？"
    await tts.speak_and_play(greeting)

    try:
        while True:
            if not wake_enabled:
                input("按 Enter 开始说话...")

            logger.info("等待用户说话...")
            audio_file = vad.record_until_silence()

            if not audio_file:
                if not wake_enabled:
                    print("未检测到语音，请重试")
                continue

            logger.info("正在识别语音...")
            text = await stt.transcribe_async(audio_file)
            Path(audio_file).unlink(missing_ok=True)

            if not text:
                continue

            print(f"👤 你说: {text}")

            reply = await agent.process_text(text)
            print(f"🤖 管家: {reply}")

            await tts.speak_and_play(reply)

    except KeyboardInterrupt:
        logger.info("语音服务已停止")
    finally:
        if wake_enabled and 'detector' in dir():
            detector.stop()


async def run_api():
    """HTTP API 模式（提供 Web 接口给其他服务调用）"""
    config = load_config()
    agent = Agent(config)
    agent.add_system_prompt()

    from aiohttp import web
    from .channel.manager import ChannelManager

    app = web.Application()

    # === 核心 API 路由 ===

    @app.post("/api/chat")
    async def chat_handler(request):
        body = await request.json()
        text = body.get("message", "")
        if not text:
            return web.json_response({"error": "message required"}, status=400)
        reply = await agent.process_text(text)
        return web.json_response({"reply": reply})

    @app.get("/api/health")
    async def health(request):
        return web.json_response({"status": "ok"})

    @app.post("/api/reset")
    async def reset(request):
        agent.reset_conversation()
        agent.add_system_prompt()
        return web.json_response({"status": "ok"})

    # === 加载消息通道（飞书/企业微信等） ===
    channel_mgr = ChannelManager(agent, config)
    channel_mgr.load_all()
    channel_mgr.register_routes(app)

    # === 启动 ===
    port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 8765
    logger.info(f"API 服务已启动: http://0.0.0.0:{port}")

    channel_count = len(channel_mgr.channels)
    if channel_count > 0:
        logger.info(f"已加载 {channel_count} 个消息通道: {', '.join(channel_mgr.channels.keys())}")
        await channel_mgr.start_all()

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    # 保持运行
    await asyncio.Event().wait()


def main():
    parser = argparse.ArgumentParser(
        description="树莓派 NAS 智能管家"
    )
    parser.add_argument(
        "mode", nargs="?", default="cli",
        choices=["cli", "voice", "api"],
        help="运行模式（默认: cli）",
    )
    parser.add_argument("--port", type=int, default=8765,
                        help="API 模式端口号")
    parser.add_argument("--config", type=str,
                        help="配置文件路径")

    args = parser.parse_args()

    if args.mode == "cli":
        asyncio.run(run_cli())
    elif args.mode == "voice":
        asyncio.run(run_voice())
    elif args.mode == "api":
        asyncio.run(run_api())


if __name__ == "__main__":
    main()
