# 📘 初始化POD环境

> **适用环境**：Kubernetes Pod（Ubuntu 基础镜像）  
> **目的**：完成开发环境的基础配置，包括工作目录软链接、SSH 服务安装与启动，为后续开发调试做准备。

## 1. 比赛简介
这是 AMD Radeon-hackathon-2026-07 比赛项目。
- **运行约束**：Pod 内无 Docker/Podman，数据持久化通过 PVC 挂载，PostgreSQL 由自定义脚本管理  
- **关键路径**：持久化目录 `/workspace/persistent`，需映射至 `/data` 供服务统一访问

## 2. 创建目录软链接

将持久化存储卷挂载点 `/workspace/persistent` 软链接到 `/data`，确保所有服务（PostgreSQL、模型文件、向量库等）使用统一的 `/data` 路径。

```python
%%bash
#!/bin/bash

# 1. 检查源路径是否存在
if [ ! -e /workspace/persistent ]; then
    echo "❌ 错误: /workspace/persistent 不存在，无法创建软链接"
    exit 1
fi

# 2. 检查 /data 状态
if [ -L /data ]; then
    echo "/data 已是软链接，指向 $(readlink /data)，跳过创建"
    exit 0
elif [ -d /data ] && [ ! -L /data ]; then
    echo "/data 是普通目录，跳过创建"
    exit 0
elif [ -e /data ] && [ ! -L /data ] && [ ! -d /data ]; then
    # 处理其他类型（如文件、socket 等）
    echo "/data 已存在，但不是目录也不是软链接，跳过创建"
    exit 0
fi

# 3. 创建软链接
echo "🔗 正在创建软链接 /data -> /workspace/persistent"
ln -s /workspace/persistent /data

# 4. 验证创建结果
if [ -L /data ]; then
    echo "✅ 创建成功"
    ls -la /data
else
    echo "❌ 创建失败，请检查权限"
    exit 1
fi
```

## 3. 安装并启动 SSH 服务

为了方便远程调试和文件传输，安装 OpenSSH 服务端并启动。  
**注意**：若 Pod 已内置 SSH，可跳过安装，但通常基础镜像不包含。

```python
%%bash
#!/bin/bash
set -euo pipefail

SSHD_BIN="/usr/sbin/sshd"
SSHD_DIR="/run/sshd"

# 1. 检查 sshd 是否已安装
if command -v sshd &> /dev/null || [ -x "$SSHD_BIN" ]; then
    echo "✅ sshd 已安装: $(which sshd 2>/dev/null || echo $SSHD_BIN)"
else
    echo "🔧 sshd 未安装，开始安装..."
    sudo apt update -qq
    sudo apt install -y openssh-server
    echo "✅ 安装完成"
fi

# 2. 创建运行时目录（某些发行版需要）
if [ ! -d "$SSHD_DIR" ]; then
    sudo mkdir -p "$SSHD_DIR"
    echo "📁 创建目录 $SSHD_DIR"
fi

# 3. 检查 sshd 是否已在运行
if pgrep -x "sshd" > /dev/null; then
    echo "✅ sshd 服务已在运行"
else
    echo "🚀 正在启动 sshd..."
    sudo "$SSHD_BIN"
    # 验证启动
    sleep 2
    if pgrep -x "sshd" > /dev/null; then
        echo "✅ sshd 启动成功"
    else
        echo "❌ sshd 启动失败，请检查日志"
        exit 1
    fi
fi

# 4. 显示当前状态
echo "📊 SSH 服务状态："
ps aux | grep sshd | grep -v grep || echo "⚠️ 未找到 sshd 进程"
```

## 4. 其他

其他辅助性工具

```python
%%bash
# tree
apt -y install tree
```

## 5. 后续建议

- **设置 SSH 密码/密钥**：如需远程访问，请配置 `~/.ssh/authorized_keys` 或修改 `sshd_config`。  
- **配置 PostgreSQL 环境变量**：参考 `/data/service/pg-unires/README.md` 设置 `PGUSER`、`PGPASSWORD` 等。  
- **下载模型文件**：执行 `/scripts/download_models.py` 拉取 Qwen 量化模型至 `/data/models`。  

---

> ✅ 至此，系统基础初始化完成，可继续部署 Uni-Resource Agent 其他组件。

