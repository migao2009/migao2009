#!/bin/bash
# ===================================================
# 树莓派 NAS 管家 - 一键安装脚本
# 在树莓派 4B (8GB) 上运行:
#   curl -SL https://xxxx | bash
#   或
#   sudo ./scripts/install.sh
# ===================================================
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查架构
ARCH=$(uname -m)
if [ "$ARCH" != "aarch64" ] && [ "$ARCH" != "armv7l" ]; then
    log_warn "当前架构: $ARCH（非 ARM64），某些服务可能不兼容"
fi

log_info "=========================================="
log_info "树莓派 NAS 管家 - 一键安装"
log_info "=========================================="
echo ""

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

# ---------- 1. 系统更新 + 基础依赖 ----------
log_info "1/7 安装系统依赖..."
sudo apt-get update
sudo apt-get install -y \
    python3 python3-pip python3-venv \
    docker.io docker-compose-v2 \
    cifs-utils smbclient \
    alsa-utils pulseaudio \
    ffmpeg mpv \
    git curl wget \
    sshpass

# 启用 Docker
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker "$USER"

# ---------- 2. 配置 .env ----------
log_info "2/7 配置环境变量..."
if [ ! -f .env ]; then
    cp .env.example .env
    log_info "已创建 .env 文件，请编辑填入你的配置:"
    log_info "  nano .env"
else
    log_info ".env 已存在，跳过"
fi

# ---------- 3. 创建 Python 虚拟环境 ----------
log_info "3/7 创建 Python 虚拟环境..."
if [ ! -d venv ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    log_info "✅ 虚拟环境已创建"
else
    log_info "venv 已存在，跳过"
fi

# ---------- 4. 安装 Ollama + 拉取本地模型 ----------
log_info "4/7 安装 Ollama 本地模型..."
if ! command -v ollama &>/dev/null; then
    log_info "下载安装 Ollama（树莓派 ARM64）..."
    curl -fsSL https://ollama.com/install.sh | sh
    # 等待 Ollama 启动
    sleep 3
    if command -v ollama &>/dev/null; then
        log_info "✅ Ollama 安装成功"
    else
        log_warn "Ollama 自动安装失败，请手动安装: curl -fsSL https://ollama.com/install.sh | sh"
    fi
else
    log_info "Ollama 已安装: $(ollama --version)"
fi

# 拉取模型（默认 qwen2.5:7b，树莓派 8GB 可以运行 q4 量化版）
log_info "拉取 AI 模型（首次下载约 4-5GB，可能需要几分钟）..."
ollama pull qwen2.5:7b 2>/dev/null && log_info "✅ qwen2.5:7b 拉取完成" || {
    log_warn "qwen2.5:7b 拉取失败，尝试更小的 qwen2.5:3b..."
    ollama pull qwen2.5:3b 2>/dev/null && {
        log_info "✅ qwen2.5:3b 拉取完成"
        # 更新配置使用 3b 模型
        sed -i 's/model: qwen2.5:7b/model: qwen2.5:3b/' config/agent.yaml
    } || log_warn "模型拉取失败，请稍后手动: ollama pull qwen2.5:7b"
}

# 设为开机自启
sudo systemctl enable ollama 2>/dev/null || true

# ---------- 5. 配置音频设备 ----------
log_info "5/7 配置音频设备..."
# 添加当前用户到 audio 组
sudo usermod -aG audio "$USER"

# 检查 ALSA 设备
if command -v arecord &>/dev/null; then
    echo "检测到以下音频输入设备:"
    arecord -l 2>/dev/null || echo "  （无录音设备）"
fi
if command -v aplay &>/dev/null; then
    echo "检测到以下音频输出设备:"
    aplay -l 2>/dev/null || echo "  （无播放设备）"
fi

log_info "如果 USB 麦克风未列出，请检查连接: lsusb"

# ---------- 5. 创建 systemd 服务 ----------
log_info "6/7 注册 systemd 服务..."
SERVICE_FILE="/etc/systemd/system/nas-agent.service"
sudo tee "$SERVICE_FILE" > /dev/null << 'SERVICEEOF'
[Unit]
Description=树莓派 NAS 智能管家
After=network-online.target remote-fs.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/rpi-nas-agent
Environment=PYTHONUNBUFFERED=1
ExecStart=/home/pi/rpi-nas-agent/venv/bin/python -m agent.main cli
Restart=on-failure
RestartSec=5

# 语音模式需要音频权限
DeviceAllow=/dev/snd
SupplementaryGroups=audio

[Install]
WantedBy=multi-user.target
SERVICEEOF

sudo systemctl daemon-reload
log_info "✅ systemd 服务已注册: nas-agent.service"
log_info "   启动: sudo systemctl start nas-agent"
log_info "   开机自启: sudo systemctl enable nas-agent"
log_info "   查看日志: sudo journalctl -u nas-agent -f"

# ---------- 6. 挂载 NAS ----------
log_info "7/7 挂载 NAS..."
if [ -f .env ]; then
    source <(grep -E '^NAS_' .env | sed 's/ //g')
fi

if [ -n "$NAS_HOST" ]; then
    sudo bash scripts/mount_nas.sh || log_warn "NAS 挂载失败，可稍后手动执行: sudo ./scripts/mount_nas.sh"
else
    log_info "跳过 NAS 挂载（未配置 NAS_HOST）"
fi

echo ""
log_info "=========================================="
log_info "✅ 安装完成！"
log_info "=========================================="
echo ""
echo "下一步操作:"
echo "  1. 编辑配置: nano .env"
echo "  2. 测试运行: source venv/bin/activate && python -m agent.main cli"
echo "  3. 语音模式: python -m agent.main voice"
echo "  4. 启动服务: sudo systemctl start nas-agent"
echo ""
echo "快速测试:"
echo "  source venv/bin/activate"
echo '  python -c "from agent.main import run_cli; import asyncio; asyncio.run(run_cli())"'
echo ""
