# 树莓派 NAS 智能管家

用树莓派 4B（8GB）搭建一个**完全本地运行**的智能语音管家，通过 **Ollama + Qwen2.5** 本地 AI 模型处理所有请求，数据不出家庭内网。通过 **USB 麦克风 + 外接音箱** 或 **飞书 Bot** 语音控制**黑群晖 NAS**。

## 功能

| 功能 | 说明 | 语音示例 |
|------|------|---------|
| 🖥️ **NAS 管理** | 查看存储状态、磁盘健康、系统负载、重启/关机 | "NAS 还剩多少空间？" "磁盘温度多少？" |
| ⬇️ **下载管理** | 添加/查看/管理 qBittorrent 下载任务 | "下载这个电影 magnet:?xt=..." "下载进度到哪了？" |
| 📁 **文件归类** | 自动按类型（视频/音乐/文档等）整理 NAS 文件 | "把下载目录整理一下" "帮我把这些文件归类" |
| 🎬 **媒体播放** | 搜索影视资源、本地播放或投屏到电视 | "搜索阿凡达" "播放 NAS 上的侏罗纪公园" |

## 系统架构

```
USB 麦克风 → [唤醒词] → [faster-whisper 语音识别]
                                ↓
树莓派 Agent ──→ Ollama + Qwen2.5 (本地 AI 大脑) ──→ 工具执行
          ↑              ┌──────────────────┐          ↓
          ├── 语音交互    │  🔒 完全本地运行  │    NAS 管理
          ├── 飞书 Bot    │  数据不出内网     │    下载管理
          └── CLI 终端    └──────────────────┘    文件归类
                                                  媒体播放
外接音箱  ← [edge-tts 语音合成] ← 回复文本
```

## 硬件准备

- **树莓派 4B** (8GB 版本推荐)
- **MicroSD 卡** 32GB+（推荐 64GB）
- **USB 麦克风**（即插即用）
- **外接音箱**（3.5mm 或 USB）
- **电源** 5V/3A USB-C
- **网络** 有线或 Wi-Fi

## 快速开始

### 第一步：烧录系统

推荐使用 Raspberry Pi OS Lite 64-bit（无桌面环境，省资源）：

```bash
# 下载 Raspberry Pi Imager: https://www.raspberrypi.com/software/
# 选择: Raspberry Pi OS Lite (64-bit)
# 烧录前点击 ⚙️ 设置:
#   - 启用 SSH
#   - 设置用户名/密码
#   - 配置 Wi-Fi
```

### 第二步：基础配置

```bash
# SSH 登录树莓派
ssh pi@树莓派IP

# 更新系统
sudo apt-get update && sudo apt-get upgrade -y

# 安装 git
sudo apt-get install -y git
```

### 第三步：部署本项目

```bash
# 克隆项目
git clone https://github.com/migao2009/migao2009.git
cd migao2009/rpi-nas-agent

# 一键安装（约 10-15 分钟）
sudo bash scripts/install.sh
```

### 第四步：配置

只需要配置 NAS 信息，**不需要任何 API Key**：

```bash
nano .env
```

```ini
# === 只需要填 NAS 信息 ===
NAS_HOST=192.168.1.100
NAS_USERNAME=admin
NAS_PASSWORD=your-nas-password

# 其他都是可选的，默认走本地模型
```

### 第五步：挂载 NAS

```bash
# 手动挂载
sudo bash scripts/mount_nas.sh

# 验证挂载
df -h /mnt/nas
ls /mnt/nas
```

### 第六步：启动

```bash
# 确认 Ollama 已运行且有模型
ollama ps          # 应该看到 qwen2.5:7b 已加载
ollama list        # 查看已下载的模型

# 激活虚拟环境
source venv/bin/activate

# CLI 模式测试（先打字测试，首次启动需要几秒加载模型）
python -m agent.main cli

# 语音模式（USB 麦 + 音箱）
python -m agent.main voice

# 后台服务
sudo systemctl start nas-agent
sudo systemctl enable nas-agent
```

### 本地 AI 模型说明

| 模型 | 参数量 | RAM 占用 | 树莓派 4B 速度 | 中文 | 工具调用 |
|------|--------|----------|---------------|------|---------|
| **qwen2.5:7b** (推荐) | 7B | ~4.5GB | 3-5 tok/s | 优秀 | ✅ |
| **qwen2.5:3b** (省资源) | 3B | ~2.5GB | 8-12 tok/s | 良好 | ✅ |
| **qwen2.5:1.5b** (极速) | 1.5B | ~1.5GB | 15-20 tok/s | 一般 | ✅ |

> tok/s = 每秒生成的 token 数，5 tok/s 对于日常对话已够用（类似慢速语速）

```bash
# 切换模型（编辑 config/agent.yaml 或设置环境变量）
export LLM_MODEL=qwen2.5:3b

# 拉取其他模型
ollama pull qwen2.5:3b
```

## 使用场景

### 场景 1：NAS 空间快满了

```
👤 你: NAS 还剩多少空间？
🤖 管家: 当前存储使用情况：
  - volume1: 3.2TB / 4.0TB (80%)
  - volume2: 1.1TB / 2.0TB (55%)
  建议清理下载目录里已完成的内容。
```

### 场景 2：下载电影

```
👤 你: 下载这个电影，磁力链 magnet:?xt=urn:btih:xxx...
🤖 管家: 已添加到 qBittorrent 下载队列。预计下载到 /下载/电影 目录。
```

### 场景 3：自动归类下载目录

```
👤 你: 帮我把下载目录整理一下
🤖 管家: 已整理完成，移动了 15 个文件：
  - 8 个视频 → 电影/
  - 3 个音乐 → 音乐/
  - 2 个文档 → 文档/
  - 2 个压缩包 → 软件/
```

### 场景 4：播放影片

```
👤 你: 帮我找一下阿凡达
🤖 管家: 找到阿凡达 (2009)，4K HDR 版本，时长 2h42min
  是否在电视上播放？
👤 你: 播放
🤖 管家: 正在通过 DLNA 投屏到电视，请在电视上选择输入源。
```

## 三种交互模式

| 模式 | 命令 | 适合场景 |
|------|------|---------|
| 🔉 语音 | `python -m agent.main voice` | 日常免提操作 |
| 💻 CLI | `python -m agent.main cli` | 调试/测试 |
| 🌐 API | `python -m agent.main api` | 集成到其他系统 |

## 🤖 飞书 Bot 接入

可以在飞书上给机器人发消息，远程管理 NAS。

### 前置准备

1. 打开 [飞书开放平台](https://open.feishu.cn) → 创建企业自建应用
2. 应用 → 权限管理 → 添加权限（需要勾选）:
   - `im:message:send_as_bot`（发送消息）
   - `im:message:receive`（接收消息）
3. 应用 → 事件回调 → 订阅 `im.message.receive_v1`
4. 应用 → 凭证与基础信息 → 获取 **App ID** 和 **App Secret**
5. 发布应用（需管理员审核）

### 配置

编辑 `.env`:

```ini
FEISHU_ENABLED=true
FEISHU_APP_ID=cli_xxxxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 配置回调地址

在飞书开放平台 → 事件回调 中填写:

```
请求网址 URL: http://<你的树莓派IP>:8765/webhook/feishu
```

> 飞书会发一个 `url_verification` 的 GET 请求验证地址，代码已经处理了这步。

### 启动

```bash
# 启动 API 模式（自动加载飞书通道）
python -m agent.main api --port 8765

# 验证日志
# ✅ 通道 [feishu] 已加载
# 📡 feishu: POST /webhook/feishu
```

### 使用

在飞书中找到你的 Bot，就可以发消息了：

```
👤: NAS 还剩多少空间？
Bot: 当前存储使用情况：
     - volume1: 3.2TB / 4.0TB (80%)

👤: 下一部阿凡达2
Bot: 已添加到 qBittorrent 下载队列

👤: 帮我找一下下载目录里的 mp4 文件
Bot: 找到 5 个匹配文件...
```

支持私聊和群聊（在群里需要 @你的机器人）。

## 依赖清单

| 软件 | 用途 | 安装方式 |
|------|------|---------|
| Python 3.11 | 运行环境 | apt |
| Docker | 服务容器化 | apt |
| faster-whisper | 语音识别 (STT) | pip |
| edge-tts | 语音合成 (TTS) | pip |
| **Ollama + Qwen2.5** | **AI 推理（本地运行）** | **一键安装** |
| qBittorrent | BT 下载 | Docker |
| Jellyfin | 媒体服务器 | 可选 |
| cifs-utils | SMB 挂载 NAS | apt |

## 项目结构

```
rpi-nas-agent/
├── agent/               # Agent 核心代码
│   ├── main.py         # 主入口（cli/voice/api）
│   ├── agent.py        # AI Agent 核心 + 工具调度
│   ├── voice.py        # 语音流水线（STT/TTS）
│   ├── wake_word.py    # 唤醒词 + VAD 检测
│   ├── config.py       # 配置加载
│   └── tools/          # 工具集
│       ├── nas_tools.py       # NAS 管理
│       ├── download_tools.py   # 下载管理
│       ├── file_tools.py      # 文件归类
│       └── media_tools.py     # 媒体播放
├── config/              # 配置文件
│   ├── agent.yaml      # Agent 参数
│   └── nas.yaml        # NAS 连接信息
├── scripts/             # 部署脚本
│   ├── install.sh      # 一键安装
│   └── mount_nas.sh    # NAS 挂载
├── services/            # systemd 服务
├── docker-compose.yml  # 容器编排
├── Dockerfile          # Agent 容器镜像
└── requirements.txt    # Python 依赖
```

## 维护

```bash
# 查看实时日志
sudo journalctl -u nas-agent -f

# 重启服务
sudo systemctl restart nas-agent

# 更新代码
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart nas-agent

# 重新挂载 NAS
sudo bash scripts/mount_nas.sh
```

## 故障排除

**Q: USB 麦克风不工作**
```
arecord -l           # 查看录音设备
speaker-test -t wav  # 测试音箱
```

**Q: NAS 挂载失败**
```bash
smbclient -L //192.168.1.100 -U admin  # 测试 SMB 连接
```

**Q: Ollama 启动慢或报错**
```bash
# 查看 Ollama 状态
systemctl status ollama
journalctl -u ollama -f

# 测试是否能正常推理
ollama run qwen2.5:7b "你好"
# 如果没反应，重新拉取模型:
ollama rm qwen2.5:7b && ollama pull qwen2.5:7b
```

**Q: 模型回复太慢**
```bash
# 换小模型（1-2 秒出回复）
export LLM_MODEL=qwen2.5:3b
ollama pull qwen2.5:3b

# 或使用 1.5b 极速版
ollama pull qwen2.5:1.5b
```

**Q: Agent 提示 "无法连接到 Ollama"**
```bash
# 确认 Ollama 正在运行
ollama ps

# 如果没启动
sudo systemctl start ollama
```

## 许可

MIT
