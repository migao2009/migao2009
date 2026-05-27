#!/bin/bash
# ===================================================
# 挂载黑群晖 NAS 共享目录到树莓派
# 依赖: sudo apt install -y cifs-utils
# 使用: sudo ./mount_nas.sh
# ===================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$PROJECT_DIR/config/nas.yaml"
ENV_FILE="$PROJECT_DIR/.env"

# 从 .env 读取配置
if [ -f "$ENV_FILE" ]; then
    source <(grep -E '^NAS_' "$ENV_FILE" | sed 's/ //g')
fi

NAS_HOST="${NAS_HOST:-192.168.1.100}"
NAS_USERNAME="${NAS_USERNAME:-admin}"
NAS_PASSWORD="${NAS_PASSWORD:-password}"
MOUNT_POINT="/mnt/nas"

echo "=========================================="
echo "  黑群晖 NAS 挂载工具"
echo "=========================================="
echo "NAS 地址:   $NAS_HOST"
echo "用户名:     $NAS_USERNAME"
echo "挂载点:     $MOUNT_POINT"
echo "=========================================="

# 检查 root
if [ "$EUID" -ne 0 ]; then
    echo "❌ 请使用 sudo 运行: sudo $0"
    exit 1
fi

# 安装依赖
if ! command -v mount.cifs &>/dev/null; then
    echo "📦 安装 cifs-utils..."
    apt-get update && apt-get install -y cifs-utils
fi

# 创建挂载点
if [ ! -d "$MOUNT_POINT" ]; then
    mkdir -p "$MOUNT_POINT"
fi

# 凭证文件（避免密码明文在进程列表）
CRED_FILE="/etc/nas-credentials"
if [ ! -f "$CRED_FILE" ]; then
    echo "创建 SMB 凭证文件: $CRED_FILE"
    cat > "$CRED_FILE" << EOF
username=$NAS_USERNAME
password=$NAS_PASSWORD
EOF
    chmod 600 "$CRED_FILE"
fi

# 探测 NAS 是否在线
echo "🔍 检测 NAS 连接中..."
if ping -c 2 -W 3 "$NAS_HOST" &>/dev/null; then
    echo "✅ NAS 在线"
else
    echo "⚠️  NAS 无法 ping 通，尝试直接挂载..."
fi

# 获取可用的 SMB 共享列表
echo "🔍 获取共享目录列表..."
SHARES=$(smbclient -L "//$NAS_HOST" -U "$NAS_USERNAME%$NAS_PASSWORD" \
    2>/dev/null | grep -E '^\s+\S+\s+Disk' | awk '{print $1}')

if [ -z "$SHARES" ]; then
    echo "⚠️  未检测到 SMB 共享，尝试默认共享名 'media'"
    SHARES="media"
fi

# 挂载每个共享
for SHARE in $SHARES; do
    SHARE_MOUNT="$MOUNT_POINT/$SHARE"
    mkdir -p "$SHARE_MOUNT"

    if mountpoint -q "$SHARE_MOUNT"; then
        echo "✅ $SHARE 已挂载"
    else
        echo "📁 挂载 $SHARE → $SHARE_MOUNT ..."
        mount -t cifs "//$NAS_HOST/$SHARE" "$SHARE_MOUNT" \
            -o "credentials=$CRED_FILE,vers=3.0,uid=1000,gid=1000,iocharset=utf8,nofail,soft" \
            2>/dev/null

        if mountpoint -q "$SHARE_MOUNT"; then
            echo "✅ $SHARE 挂载成功"
        else
            echo "⚠️  $SHARE 挂载失败（以 guest 方式重试）..."
            mount -t cifs "//$NAS_HOST/$SHARE" "$SHARE_MOUNT" \
                -o "guest,vers=3.0,uid=1000,gid=1000,iocharset=utf8,nofail,soft" \
                2>/dev/null || true
        fi
    fi
done

# 验证挂载结果
echo ""
echo "=========================================="
echo "  挂载状态"
echo "=========================================="
if mountpoint -q "$MOUNT_POINT/media" || mountpoint -q "$MOUNT_POINT/downloads"; then
    df -h "$MOUNT_POINT"/* | grep -v "Filesystem"
    echo ""
    echo "✅ NAS 已挂载到 $MOUNT_POINT"
else
    echo "❌ 所有挂载均失败"
    echo ""
    echo "排查步骤:"
    echo "  1. 确认 NAS 已开启 SMB 服务"
    echo "  2. 检查 .env 中的 NAS_HOST/NAS_USERNAME/NAS_PASSWORD 是否正确"
    echo "  3. 测试连接: smbclient -L //\$NAS_HOST -U \$NAS_USERNAME"
    echo "  4. 检查防火墙是否阻止 SMB 端口 (445)"
fi
