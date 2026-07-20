#!/bin/bash

# 设置环境变量
export DB_HOST="localhost"
export DB_NAME="uni_resource_agent"
export DB_USER="postgres"
export DB_PASSWORD="postgres"
export DB_PORT="5432"
export SECRET_KEY="uni-resource-agent-secret-key"

# 安装依赖
echo "安装Python依赖..."
pip install -r requirements.txt

# 初始化数据库
echo "初始化数据库..."
python -c "from src.db.database import init_database; init_database()"

# 启动应用
echo "启动Uni-Resource Agent..."
uvicorn src.app:app --host 0.0.0.0 --port 8000