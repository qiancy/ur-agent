# 📘 部署应用工具

> **适用环境**：Kubernetes Pod（Ubuntu 基础镜像）  
> **目的**：安装开发调试所需的常用应用工具，包括 opencode（AI 编程助手）与 pbcopy（剪贴板传输工具）。

## 1. 比赛简介
这是 AMD Radeon-hackathon-2026-07 比赛项目。
- **运行约束**：Pod 内无 Docker/Podman，数据持久化通过 PVC 挂载，PostgreSQL 由自定义脚本管理  
- **关键路径**：持久化目录 `/workspace/persistent`，已映射至 `/data` 供服务统一访问

## 2. 安装 opencode

下载并安装 opencode AI 编程助手至 `/data/app`，并将其路径写入 `~/.profile` 以便全局使用。

```python
%%bash
#!/bin/bash
set -euo pipefail

APP_DIR="/data/app"
OPENCODE_VERSION="v1.18.9"
TARBALL="opencode-linux-x64.tar.gz"
DOWNLOAD_URL="https://github.com/anomalyco/opencode/releases/download/${OPENCODE_VERSION}/${TARBALL}"

# 1. 创建应用目录
mkdir -p "$APP_DIR"
echo "📁 应用目录: $APP_DIR"

# 2. 检查是否已安装
if [ -x "$APP_DIR/opencode" ]; then
    echo "✅ opencode 已安装: $($APP_DIR/opencode --version 2>/dev/null || echo '已就绪')"
else
    # 3. 下载 opencode 压缩包
    echo "🔧 开始下载 opencode ${OPENCODE_VERSION} ..."
    wget "$DOWNLOAD_URL" --no-check-certificate -O "/tmp/${TARBALL}"
    echo "✅ 下载完成，开始解压..."
    tar -xzf "/tmp/${TARBALL}" -C "$APP_DIR"
    rm -f "/tmp/${TARBALL}"
    echo "✅ 安装完成"
fi

# 4. 配置 PATH（~/.profile）
PROFILE_LINE='export PATH="$PATH:/data/app"'
if ! grep -qF "/data/app" "$HOME/.profile" 2>/dev/null; then
    echo "$PROFILE_LINE" >> "$HOME/.profile"
    echo "✅ 已将 /data/app 写入 ~/.profile"
else
    echo "✅ /data/app 已在 ~/.profile 中"
fi

# 5. 验证安装
if [ -x "$APP_DIR/opencode" ]; then
    echo ""
    echo "📊 验证结果："
    "$APP_DIR/opencode" --version || echo "opencode 已就绪"
    ls -la "$APP_DIR"
else
    echo "❌ opencode 安装失败，请检查网络或下载地址"
    exit 1
fi
```

## 3. 配置 pbcopy

安装 `pbcopy` 剪贴板传输工具（macOS 兼容风格），用于将内容通过终端 OSC 52 序列复制到本地剪贴板。

```python
%%bash
#!/bin/bash
set -euo pipefail

# 1. 写入 pbcopy 脚本
sudo tee /usr/local/bin/pbcopy > /dev/null << 'EOF'
#!/bin/sh
printf '\033]52;c;%s\a' "$(base64 | tr -d '\n')"
EOF

# 2. 赋予执行权限
sudo chmod +x /usr/local/bin/pbcopy

# 3. 验证安装
if [ -x /usr/local/bin/pbcopy ]; then
    echo "✅ pbcopy 安装成功: $(which pbcopy)"
    echo "--- 脚本内容 ---"
    cat /usr/local/bin/pbcopy
else
    echo "❌ pbcopy 安装失败"
    exit 1
fi
```

## 4. 使用示例

- **opencode**：执行 `source ~/.profile` 后，直接运行 `opencode` 启动 AI 编程助手。  
- **pbcopy**：`echo "hello" | pbcopy`，将内容复制到本地剪贴板（需终端支持 OSC 52）。

## 5. 后续建议

- **配置 opencode**：参考 opencode 文档设置模型 API Key 与配置文件（`~/.config/opencode/`）。  
- **配置 PostgreSQL 环境变量**：参考 `/data/service/pg-unires/README.md` 设置 `PGUSER`、`PGPASSWORD` 等。  
- **下载模型文件**：执行 `/scripts/download_models.py` 拉取 Qwen 量化模型至 `/data/models`。  

---

> ✅ 至此，应用工具部署完成，可继续部署 Uni-Resource Agent 其他组件。

