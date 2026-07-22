#!/bin/bash

# Uni-Resource Agent 管理脚本
# 包含启动、停止、状态检查功能

# 配置
BACKEND_PID_FILE="/tmp/uni_resource_agent_backend.pid"
FRONTEND_PID_FILE="/tmp/uni_resource_agent_frontend.pid"
BACKEND_LOG="/tmp/uni_resource_agent_backend.log"
FRONTEND_LOG="/tmp/uni_resource_agent_frontend.log"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查依赖
check_dependencies() {
    echo -e "${YELLOW}检查依赖...${NC}"
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}错误: 请先安装 Python 3${NC}"
        exit 1
    fi
    
    if ! command -v pip3 &> /dev/null; then
        echo -e "${RED}错误: 请先安装 pip${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}依赖检查通过${NC}"
}

# 安装依赖
install_dependencies() {
    echo -e "${YELLOW}安装Python依赖...${NC}"
    # 获取脚本所在目录的父目录（项目根目录）
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
    REQUIREMENTS_FILE="$PROJECT_ROOT/requirements.txt"
    
    if [ ! -f "$REQUIREMENTS_FILE" ]; then
        echo -e "${RED}错误: 未找到 requirements.txt 文件${NC}"
        echo -e "${YELLOW}期望路径: $REQUIREMENTS_FILE${NC}"
        exit 1
    fi
    
    pip3 install --break-system-packages -r "$REQUIREMENTS_FILE"
    if [ $? -ne 0 ]; then
        echo -e "${RED}依赖安装失败${NC}"
        exit 1
    fi
    echo -e "${GREEN}依赖安装成功${NC}"
}

# 初始化数据库
init_database() {
    echo -e "${YELLOW}初始化数据库...${NC}"
    # 获取脚本所在目录的父目录（项目根目录）
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
    
    # 尝试使用项目根目录下的init_db.py文件
    if [ -f "$PROJECT_ROOT/scripts/init_db.py" ]; then
        python3 "$PROJECT_ROOT/scripts/init_db.py"
    else
        # 如果没有这个文件，创建一个简单的数据库初始化
        echo -e "${YELLOW}未找到数据库初始化脚本，跳过数据库初始化${NC}"
    fi
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}数据库初始化失败${NC}"
        echo -e "${YELLOW}这可能是因为数据库服务未启动，但我们可以继续启动应用${NC}"
        # 不退出，因为可能数据库服务是外部的
    fi
    echo -e "${GREEN}数据库初始化完成${NC}"
}

# 启动后端服务
start_backend() {
    echo -e "${YELLOW}启动后端服务...${NC}"
    
    # 获取脚本所在目录的父目录（项目根目录）
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
    
    # 检查是否已在运行
    if [ -f "$BACKEND_PID_FILE" ]; then
        PID=$(cat "$BACKEND_PID_FILE")
        if ps -p "$PID" > /dev/null; then
            echo -e "${RED}后端服务已在运行 (PID: $PID)${NC}"
            return 1
        else
            echo -e "${YELLOW}PID文件存在但进程不存在，清理旧的PID文件${NC}"
            rm -f "$BACKEND_PID_FILE"
        fi
    fi
    
    # 切换到项目根目录
    cd "$PROJECT_ROOT"
    
    # 启动后端服务
    cd "$PROJECT_ROOT"
    nohup uvicorn src.app:app --host 0.0.0.0 --port 8000 > "$BACKEND_LOG" 2>&1 &
    BACKEND_PID=$!
    
    # 保存PID
    echo "$BACKEND_PID" > "$BACKEND_PID_FILE"
    
    # 等待服务启动
    sleep 8
    
    # 检查后端是否启动成功
    if ps -p "$BACKEND_PID" > /dev/null; then
        echo -e "${GREEN}后端服务启动成功 (PID: $BACKEND_PID)${NC}"
        echo -e "${GREEN}后端服务运行在端口 8000${NC}"
    else
        echo -e "${RED}后端服务启动失败${NC}"
        rm -f "$BACKEND_PID_FILE"
        exit 1
    fi
}

# 启动前端服务
start_frontend() {
    echo -e "${YELLOW}启动前端服务...${NC}"
    
    # 获取脚本所在目录的父目录（项目根目录）
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
    
    # 检查是否已在运行
    if [ -f "$FRONTEND_PID_FILE" ]; then
        PID=$(cat "$FRONTEND_PID_FILE")
        if ps -p "$PID" > /dev/null; then
            echo -e "${RED}前端服务已在运行 (PID: $PID)${NC}"
            return 1
        fi
    fi
    
    # 切换到项目根目录
    cd "$PROJECT_ROOT"
    
    # 启动前端服务（调用独立的 frontend.py 脚本）
    nohup python3 "$PROJECT_ROOT/src/frontend.py" > "$FRONTEND_LOG" 2>&1 &
    
    FRONTEND_PID=$!
    
    # 保存PID
    echo "$FRONTEND_PID" > "$FRONTEND_PID_FILE"
    
    # 等待服务启动
    sleep 8
    
    # 检查前端是否启动成功
    if ps -p "$FRONTEND_PID" > /dev/null; then
        echo -e "${GREEN}前端服务启动成功 (PID: $FRONTEND_PID)${NC}"
        echo -e "${GREEN}前端服务运行在端口 7860${NC}"
    else
        echo -e "${RED}前端服务启动失败${NC}"
        rm -f "$FRONTEND_PID_FILE"
        exit 1
    fi
}

# 停止服务
stop_service() {
    echo -e "${YELLOW}停止服务...${NC}"
    
    # 停止后端服务
    if [ -f "$BACKEND_PID_FILE" ]; then
        PID=$(cat "$BACKEND_PID_FILE")
        if ps -p "$PID" > /dev/null; then
            echo -e "${YELLOW}停止后端服务 (PID: $PID)${NC}"
            kill "$PID"
        fi
        rm -f "$BACKEND_PID_FILE"
    else
        echo -e "${YELLOW}未找到后端服务PID文件${NC}"
    fi
    
    # 停止前端服务
    if [ -f "$FRONTEND_PID_FILE" ]; then
        PID=$(cat "$FRONTEND_PID_FILE")
        if ps -p "$PID" > /dev/null; then
            echo -e "${YELLOW}停止前端服务 (PID: $PID)${NC}"
            kill "$PID"
        fi
        rm -f "$FRONTEND_PID_FILE"
    else
        echo -e "${YELLOW}未找到前端服务PID文件${NC}"
    fi
    
    echo -e "${GREEN}服务已停止${NC}"
}

# 检查服务状态
check_status() {
    echo -e "${YELLOW}检查服务状态...${NC}"
    
    BACKEND_RUNNING=false
    FRONTEND_RUNNING=false
    
    # 检查后端服务
    if [ -f "$BACKEND_PID_FILE" ]; then
        PID=$(cat "$BACKEND_PID_FILE")
        if ps -p "$PID" > /dev/null; then
            echo -e "${GREEN}后端服务运行中 (PID: $PID)${NC}"
            BACKEND_RUNNING=true
        else
            echo -e "${RED}后端服务PID文件存在但进程不存在${NC}"
            rm -f "$BACKEND_PID_FILE"
        fi
    else
        echo -e "${YELLOW}后端服务未运行${NC}"
    fi
    
    # 检查前端服务
    if [ -f "$FRONTEND_PID_FILE" ]; then
        PID=$(cat "$FRONTEND_PID_FILE")
        if ps -p "$PID" > /dev/null; then
            echo -e "${GREEN}前端服务运行中 (PID: $PID)${NC}"
            FRONTEND_RUNNING=true
        else
            echo -e "${RED}前端服务PID文件存在但进程不存在${NC}"
            rm -f "$FRONTEND_PID_FILE"
        fi
    else
        echo -e "${YELLOW}前端服务未运行${NC}"
    fi
    
    if [ "$BACKEND_RUNNING" = false ] && [ "$FRONTEND_RUNNING" = false ]; then
        echo -e "${RED}服务未运行${NC}"
        return 1
    fi
    
    echo -e "${GREEN}服务状态检查完成${NC}"
    return 0
}

# 显示帮助
show_help() {
    echo "Uni-Resource Agent 管理脚本"
    echo "使用方法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  start       启动服务 (后端和前端)"
    echo "  start-backend  启动后端服务"
    echo "  start-frontend  启动前端服务"
    echo "  stop        停止全部服务"
    echo "  stop-backend  停止后端服务"
    echo "  stop-frontend 停止前端服务"
    echo "  status      检查服务状态"
    echo "  help        显示此帮助信息"
    echo ""
    echo "服务端口:"
    echo "  后端: 8000"
    echo "  前端: 7860"
    echo ""
    echo "注意:"
    echo "  脚本会自动从项目根目录查找 requirements.txt"
    echo "  请确保在项目根目录下运行此脚本"
}

# 主程序
main() {
    case "$1" in
        start)
            check_dependencies
            install_dependencies
            init_database
            start_backend
            start_frontend
            echo -e "${GREEN}Uni-Resource Agent 启动完成!${NC}"
            echo -e "${GREEN}访问 http://localhost:7860 查看前端界面${NC}"
            ;;
        start-backend)
            check_dependencies
            install_dependencies
            init_database
            start_backend
            ;;
        start-frontend)
            check_dependencies
            install_dependencies
            start_frontend
            ;;
        stop)
            stop_service
            ;;
        stop-backend)
            if [ -f "$BACKEND_PID_FILE" ]; then
                PID=$(cat "$BACKEND_PID_FILE")
                if ps -p "$PID" > /dev/null; then
                    echo -e "${YELLOW}停止后端服务 (PID: $PID)${NC}"
                    kill "$PID"
                fi
                rm -f "$BACKEND_PID_FILE"
            fi
            ;;
        stop-frontend)
            if [ -f "$FRONTEND_PID_FILE" ]; then
                PID=$(cat "$FRONTEND_PID_FILE")
                if ps -p "$PID" > /dev/null; then
                    echo -e "${YELLOW}停止前端服务 (PID: $PID)${NC}"
                    kill "$PID"
                fi
                rm -f "$FRONTEND_PID_FILE"
            fi
            ;;
        status)
            check_status
            ;;
        help)
            show_help
            ;;
        *)
            echo -e "${RED}未知选项: $1${NC}"
            echo -e "${YELLOW}使用 '$0 help' 查看帮助信息${NC}"
            exit 1
            ;;
    esac
}

# 执行主程序
main "$@"