"""
唤醒词检测模块
使用 openwakeword 进行本地唤醒词检测
"""
import asyncio
import logging
import tempfile
import wave
from pathlib import Path
from typing import Callable, Optional

import numpy as np
import sounddevice as sd
from openwakeword.model import Model as WakeWordModel

logger = logging.getLogger(__name__)


class WakeWordDetector:
    """
    唤醒词检测器
    持续监听 USB 麦克风，检测到唤醒词后触发回调
    """

    def __init__(
        self,
        sensitivity: float = 0.5,
        input_device: Optional[int] = None,
        sample_rate: int = 16000,
        wake_words: list = ["alexa"],  # 默认使用 openwakeword 内置唤醒词
        on_wake: Optional[Callable] = None,
    ):
        self.sensitivity = sensitivity
        self.input_device = input_device
        self.sample_rate = sample_rate
        self.wake_words = wake_words
        self.on_wake = on_wake
        self._running = False

        logger.info("加载唤醒词模型...")
        self.model = WakeWordModel(
            wake_word_models=[],  # 使用内置模型
        )

    def start(self):
        """开始监听唤醒词"""
        self._running = True
        logger.info(f"唤醒词监听已启动（灵敏度: {self.sensitivity}）")

        def audio_callback(indata, frames, time_info, status):
            if not self._running:
                return
            if status:
                logger.warning(f"音频状态: {status}")

            # 转换为 float32
            audio = np.frombuffer(indata, dtype=np.int16).astype(np.float32) / 32768.0

            # 预测唤醒词
            prediction = self.model.predict(audio)

            for wake_word in self.wake_words:
                score = prediction.get(wake_word, 0)
                if score > self.sensitivity:
                    logger.info(f"检测到唤醒词: {wake_word} (score={score:.3f})")
                    if self.on_wake:
                        self.on_wake()
                    break

        self._stream = sd.InputStream(
            device=self.input_device,
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
            callback=audio_callback,
            blocksize=1280,  # ~80ms @ 16kHz
        )
        self._stream.start()

    def stop(self):
        """停止监听"""
        self._running = False
        if hasattr(self, "_stream"):
            self._stream.stop()
            self._stream.close()
            logger.info("唤醒词监听已停止")


class VoiceActivityDetector:
    """
    语音活动检测器（VAD）
    检测到语音开始录音，静音后停止
    """

    def __init__(
        self,
        input_device: Optional[int] = None,
        sample_rate: int = 16000,
        silence_timeout: float = 1.5,  # 静音超过此秒数停止录音
        min_audio_duration: float = 0.5,  # 最短录音时长
        max_audio_duration: float = 15.0,  # 最长录音时长
    ):
        self.input_device = input_device
        self.sample_rate = sample_rate
        self.silence_timeout = silence_timeout
        self.min_audio_duration = min_audio_duration
        self.max_audio_duration = max_audio_duration

    def record_until_silence(self) -> str:
        """
        录音直到检测到静音
        返回音频文件路径（WAV 格式，16kHz，16bit）
        """
        import webrtcvad

        vad = webrtcvad.Vad(2)  # 灵敏度 0-3
        recorded_frames = []
        silent_chunks = 0
        frames_per_chunk = int(self.sample_rate * 0.03)  # 30ms 帧
        max_chunks = int(self.max_audio_duration / 0.03)
        min_chunks = int(self.min_audio_duration / 0.03)
        silence_chunks_threshold = int(self.silence_timeout / 0.03)
        is_speaking = False

        logger.info("开始录音（等待语音...）")

        def callback(indata, frames, time_info, status):
            nonlocal silent_chunks, is_speaking
            if status:
                logger.warning(f"音频状态: {status}")
            # webrtcvad 需要 16-bit PCM
            audio_bytes = np.frombuffer(indata, dtype=np.int16).tobytes()
            is_speech = vad.is_speech(audio_bytes, self.sample_rate)

            if is_speech:
                is_speaking = True
                silent_chunks = 0
                recorded_frames.append(indata.copy())
            elif is_speaking:
                silent_chunks += 1
                recorded_frames.append(indata.copy())
                if silent_chunks > silence_chunks_threshold:
                    raise sd.CallbackStop()

        try:
            with sd.InputStream(
                device=self.input_device,
                samplerate=self.sample_rate,
                channels=1,
                dtype="int16",
                callback=callback,
                blocksize=frames_per_chunk,
            ):
                sd.sleep(int(self.max_audio_duration * 1000))
        except sd.CallbackStop:
            pass

        # 检查是否录到足够内容
        if len(recorded_frames) < min_chunks:
            logger.warning("录音太短或未检测到语音")
            return ""

        # 保存为 WAV
        audio_data = np.concatenate(recorded_frames)
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        with wave.open(tmp.name, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data.tobytes())

        duration = len(audio_data) / self.sample_rate
        logger.info(f"录音完成: {duration:.1f}s -> {tmp.name}")
        return tmp.name
