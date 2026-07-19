# 启动脚本

#!/bin/bash

echo "正在启动 Uni-Resource Agent..."

# 检查并安装依赖
echo "检查依赖..."
if ! command -v python3 &> /dev/null; then
    echo "请先安装 Python 3"
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    echo "请先安装 pip"
    exit 1
fi

echo "安装Python依赖..."
pip3 install -r requirements.txt

# 初始化数据库
echo "初始化数据库..."
python3 scripts/init_db.py

# 启动后端服务
echo "启动后端服务..."
nohup uvicorn src.app:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &

# 等待后端启动
sleep 5

# 检查后端是否启动成功
if pgrep -f "uvicorn src.app:app" > /dev/null; then
    echo "后端服务启动成功，端口: 8000"
else
    echo "后端服务启动失败"
    exit 1
fi

# 启动前端界面
echo "启动前端界面..."
nohup python3 frontend.py > frontend.log 2>&1 &

# 等待前端启动
sleep 5

# 检查前端是否启动成功
if pgrep -f "frontend.py" > /dev/null; then
    echo "前端界面启动成功"
    echo "访问 http://localhost:7860 查看界面"
else
    echo "前端界面启动失败"
    exit 1
fi

echo "Uni-Resource Agent 启动完成!"
echo "后端服务运行在端口 8000"
echo "前端界面运行在端口 7860"