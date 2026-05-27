FROM --platform=linux/arm64 python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    alsa-utils \
    pulseaudio \
    cifs-utils \
    sshpass \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY agent/ ./agent/
COPY config/ ./config/

# 默认启动命令
CMD ["python", "-m", "agent.main", "api", "--port", "8765"]
