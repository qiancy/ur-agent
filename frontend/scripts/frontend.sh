#!/bin/bash

# Uni-Resource Agent 前端管理脚本
# 包含启动、停止、状态检查功能

# 配置
FRONTEND_PROCESS_ID_FILE="/tmp/uni_resource_agent_frontend.process_id"
FRONTEND_LOG="/tmp/uni_resource_agent_frontend.log"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

get_project_root() {
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    dirname "$script_dir"
}

# 检查依赖
check_dependencies() {
    echo -e "${YELLOW}检查前端依赖...${NC}"
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}错误: 请先安装 Node.js / npm${NC}"
        exit 1
    fi
    echo -e "${GREEN}前端依赖检查通过${NC}"
}

# 安装依赖
install_dependencies() {
    echo -e "${YELLOW}安装前端依赖...${NC}"
    local frontend_dir
    frontend_dir="$(get_project_root)"
    cd "$frontend_dir"
    npm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}前端依赖安装失败${NC}"
        exit 1
    fi
    echo -e "${GREEN}前端依赖安装成功${NC}"
}

# 启动前端服务
start_frontend() {
    echo -e "${YELLOW}启动前端服务...${NC}"

    # 检查是否已在运行
    if [ -f "$FRONTEND_PROCESS_ID_FILE" ]; then
        PROCESS_ID=$(cat "$FRONTEND_PROCESS_ID_FILE")
        if ps -p "$PROCESS_ID" > /dev/null; then
            echo -e "${RED}前端服务已在运行 (PROCESS_ID: $PROCESS_ID)${NC}"
            return 1
        else
            echo -e "${YELLOW}进程编号文件存在但进程不存在，清理旧的进程编号文件${NC}"
            rm -f "$FRONTEND_PROCESS_ID_FILE"
        fi
    fi

    local frontend_dir
    frontend_dir="$(get_project_root)"
    cd "$frontend_dir"

    nohup npm run dev -- --host 0.0.0.0 --port 5173 > "$FRONTEND_LOG" 2>&1 &
    FRONTEND_PROCESS_ID=$!

    # 保存进程编号
    echo "$FRONTEND_PROCESS_ID" > "$FRONTEND_PROCESS_ID_FILE"

    # 等待服务启动
    sleep 5

    # 检查前端是否启动成功
    if ps -p "$FRONTEND_PROCESS_ID" > /dev/null; then
        echo -e "${GREEN}前端服务启动成功 (PROCESS_ID: $FRONTEND_PROCESS_ID)${NC}"
        echo -e "${GREEN}前端服务运行在端口 5173${NC}"
    else
        echo -e "${RED}前端服务启动失败${NC}"
        rm -f "$FRONTEND_PROCESS_ID_FILE"
        exit 1
    fi
}

# 停止前端服务
stop_frontend() {
    if [ -f "$FRONTEND_PROCESS_ID_FILE" ]; then
        PROCESS_ID=$(cat "$FRONTEND_PROCESS_ID_FILE")
        if ps -p "$PROCESS_ID" > /dev/null; then
            echo -e "${YELLOW}停止前端服务 (PROCESS_ID: $PROCESS_ID)${NC}"
            kill "$PROCESS_ID"
            sleep 2
            if ps -p "$PROCESS_ID" > /dev/null; then
                echo -e "${YELLOW}进程未退出，强制终止...${NC}"
                kill -9 "$PROCESS_ID"
            fi
        else
            echo -e "${YELLOW}前端服务进程编号文件存在但进程不存在${NC}"
        fi
        rm -f "$FRONTEND_PROCESS_ID_FILE"
    else
        echo -e "${YELLOW}未找到前端服务进程编号文件${NC}"
    fi
}

# 检查服务状态
check_status() {
    echo -e "${YELLOW}检查前端服务状态...${NC}"

    if [ -f "$FRONTEND_PROCESS_ID_FILE" ]; then
        PROCESS_ID=$(cat "$FRONTEND_PROCESS_ID_FILE")
        if ps -p "$PROCESS_ID" > /dev/null; then
            echo -e "${GREEN}前端服务运行中 (PROCESS_ID: $PROCESS_ID)${NC}"
            echo -e "${GREEN}前端预览: http://localhost:5173${NC}"
        else
            echo -e "${RED}前端服务进程编号文件存在但进程不存在${NC}"
            rm -f "$FRONTEND_PROCESS_ID_FILE"
            return 1
        fi
    else
        echo -e "${YELLOW}前端服务未运行${NC}"
        return 1
    fi
}

# 重启前端服务
restart_frontend() {
    stop_frontend
    sleep 2
    start_frontend
}

# 显示帮助
show_help() {
    echo "Uni-Resource Agent 前端管理脚本"
    echo "使用方法: $0 [--verbose] <start|stop|status|restart>"
    echo ""
    echo "选项:"
    echo "  --verbose          显示详细输出"
    echo ""
    echo "命令:"
    echo "  start       启动前端服务"
    echo "  stop        停止前端服务"
    echo "  status      检查前端服务状态"
    echo "  restart     重启前端服务"
    echo ""
    echo "服务端口:"
    echo "  前端: 5173 (Vue + Vite)"
}

# 主程序
main() {
    local args=()
    for arg in "$@"; do
        case "$arg" in
            --verbose)
                VERBOSE=1
                ;;
            *)
                args+=("$arg")
                ;;
        esac
    done
    set -- "${args[@]}"

    case "$1" in
        start)
            check_dependencies
            install_dependencies
            start_frontend
            ;;
        stop)
            stop_frontend
            ;;
        status)
            check_status
            ;;
        restart)
            stop_frontend
            sleep 2
            check_dependencies
            install_dependencies
            start_frontend
            ;;
        help|--help|-h|"")
            show_help
            ;;
        *)
            echo -e "${RED}未知命令: $1${NC}"
            show_help
            exit 1
            ;;
    esac
}

# 执行主程序
main "$@"
