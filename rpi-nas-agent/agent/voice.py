"""
语音流水线：STT（语音转文字）+ TTS（文字转语音）
"""
import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Optional

import edge_tts
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)


class STTEngine:
    """语音转文字引擎（使用 faster-whisper）"""

    def __init__(self, model_size: str = "tiny", device: str = "cpu",
                 language: str = "zh"):
        self.language = language
        logger.info(f"加载 Whisper 模型: {model_size} (device={device})")
        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type="int8" if device == "cpu" else "float16",
            num_workers=1,
        )

    def transcribe(self, audio_path: str) -> str:
        """转写音频文件为文本"""
        segments, info = self.model.transcribe(
            audio_path,
            language=self.language,
            beam_size=5,
            vad_filter=True,
        )
        text = "".join(seg.text for seg in segments)
        return text.strip()

    async def transcribe_async(self, audio_path: str) -> str:
        """异步转写"""
        return await asyncio.to_thread(self.transcribe, audio_path)


class TTSEngine:
    """文字转语音引擎（使用 Edge-TTS）"""

    def __init__(self, voice: str = "zh-CN-XiaoxiaoNeural",
                 speed: float = 1.0):
        self.voice = voice
        self.speed = speed

    async def speak(self, text: str, output_path: Optional[str] = None) -> str:
        """
        将文字转为语音并播放
        返回音频文件路径
        """
        if output_path is None:
            tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            output_path = tmp.name
            tmp.close()

        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(output_path)
        logger.info(f"TTS 已生成: {output_path}")
        return output_path

    async def speak_and_play(self, text: str) -> None:
        """生成语音并通过默认音频设备播放"""
        audio_file = await self.speak(text)
        await _play_audio(audio_file)
        Path(audio_file).unlink(missing_ok=True)


async def _play_audio(file_path: str) -> None:
    """播放音频文件"""
    import aubio  # not used, using ffplay instead
    proc = await asyncio.create_subprocess_exec(
        "ffplay", "-nodisp", "-autoexit", file_path,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await proc.wait()


def list_audio_devices() -> None:
    """列出可用的音频输入/输出设备"""
    import sounddevice as sd
    devices = sd.query_devices()
    print("=== 音频设备列表 ===")
    for i, dev in enumerate(devices):
        print(f"  [{i}] {dev['name']} "
              f"(in:{dev['max_input_channels']}, "
              f"out:{dev['max_output_channels']})")
    default_input = sd.default.device[0]
    default_output = sd.default.device[1]
    print(f"\n默认输入设备: {default_input}")
    print(f"默认输出设备: {default_output}")
