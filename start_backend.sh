#!/bin/bash

# 设置环境变量
export DB_HOST="localhost"
export DB_NAME="uni_resource_agent"
export DB_USER="postgres"
export DB_PASSWORD="postgres"
export DB_PORT="5432"
export SECRET_KEY="uni-resource-agent-secret-key"

# 解析参数
DAEMON=false
if [ "$1" == "--daemon" ]; then
    DAEMON=true
fi

# 启动命令
CMD="uvicorn src.app:app --host 0.0.0.0 --port 8000"

if [ "$DAEMON" = true ]; then
    nohup $CMD > backend.log 2>&1 &
else
    $CMD
fi