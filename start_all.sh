#!/bin/bash
echo "正在启动 Uni-Resource Agent..."

# 先准备环境（安装依赖 + 初始化数据库）
./setup.sh

# 启动后端（后台）
echo "启动后端服务..."
nohup ./start_backend.sh --daemon > backend.log 2>&1 &

# 启动前端（后台）
echo "启动前端界面..."
nohup ./start_frontend.sh --daemon > frontend.log 2>&1 &

sleep 5

# 检查进程
if pgrep -f "uvicorn src.app:app" > /dev/null; then
    echo "后端服务启动成功，端口: 8000"
else
    echo "后端服务启动失败"
    exit 1
fi

if pgrep -f "frontend.py" > /dev/null; then
    echo "前端界面启动成功"
    echo "访问 http://localhost:7860 查看界面"
else
    echo "前端界面启动失败"
    exit 1
fi

echo "Uni-Resource Agent 启动完成!"