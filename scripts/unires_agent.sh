#!/bin/bash

# Uni-Resource Agent 管理脚本
# 包含启动、停止、状态检查功能

# 配置
BACKEND_PROCESS_ID_FILE="/tmp/uni_resource_agent_backend.process_id"
FRONTEND_PROCESS_ID_FILE="/tmp/uni_resource_agent_frontend.process_id"
BACKEND_LOG="/tmp/uni_resource_agent_backend.log"
FRONTEND_LOG="/tmp/uni_resource_agent_frontend.log"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

VERBOSE=0

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
        # 初始化时 drop_all=True 以应用新的 schema
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
    if [ -f "$BACKEND_PROCESS_ID_FILE" ]; then
        PROCESS_ID=$(cat "$BACKEND_PROCESS_ID_FILE")
        if ps -p "$PROCESS_ID" > /dev/null; then
            echo -e "${RED}后端服务已在运行 (PROCESS_ID: $PROCESS_ID)${NC}"
            return 1
        else
            echo -e "${YELLOW}进程编号文件存在但进程不存在，清理旧的进程编号文件${NC}"
            rm -f "$BACKEND_PROCESS_ID_FILE"
        fi
    fi
    
    # 切换到项目根目录
    cd "$PROJECT_ROOT"
    
    # 启动后端服务
    cd "$PROJECT_ROOT"
    export PYTHONPATH="$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"
    export PYTHONUNBUFFERED=1
    nohup setsid python3 -m uvicorn src.app:app --host 0.0.0.0 --port 8000 > "$BACKEND_LOG" 2>&1 < /dev/null &
    BACKEND_PROCESS_ID=$!
    
    # 保存进程编号
    echo "$BACKEND_PROCESS_ID" > "$BACKEND_PROCESS_ID_FILE"
    
    # 等待服务启动
    sleep 8
    
    # 检查后端是否启动成功
    if ps -p "$BACKEND_PROCESS_ID" > /dev/null; then
        echo -e "${GREEN}后端服务启动成功 (PROCESS_ID: $BACKEND_PROCESS_ID)${NC}"
        echo -e "${GREEN}后端服务运行在端口 8000${NC}"
    else
        echo -e "${RED}后端服务启动失败${NC}"
        rm -f "$BACKEND_PROCESS_ID_FILE"
        exit 1
    fi
}

# 停止后端服务
stop_backend() {
    if [ -f "$BACKEND_PROCESS_ID_FILE" ]; then
        PROCESS_ID=$(cat "$BACKEND_PROCESS_ID_FILE")
        if ps -p "$PROCESS_ID" > /dev/null; then
            echo -e "${YELLOW}停止后端服务 (PROCESS_ID: $PROCESS_ID)${NC}"
            kill "$PROCESS_ID"
        fi
        rm -f "$BACKEND_PROCESS_ID_FILE"
    else
        echo -e "${YELLOW}未找到后端服务进程编号文件${NC}"
    fi
}

# 重启后端服务
restart_backend() {
    stop_backend
    sleep 2
    check_dependencies
    install_dependencies
    start_backend
}

find_project_frontend_process_ids() {
    local PROJECT_ROOT="$1"
    local REAL_ROOT
    REAL_ROOT="$(cd "$PROJECT_ROOT" && pwd -P)"
    ps -eo p"id=,comm=,args=" | awk \
        -v script="$PROJECT_ROOT/src/frontend.py" \
        -v real_script="$REAL_ROOT/src/frontend.py" \
        '$2 ~ /^python/ && (index($0, script) || index($0, real_script)) {print $1}'
}

is_port_listening() {
    local PORT="$1"
    ss -ltn | awk '{print $4}' | grep -Eq "(^|:)${PORT}$"
}

stop_process_gracefully() {
    local PROCESS_ID="$1"
    local LABEL="$2"
    if ! ps -p "$PROCESS_ID" > /dev/null; then
        return 0
    fi
    echo -e "${YELLOW}停止${LABEL} (PROCESS_ID: $PROCESS_ID)${NC}"
    kill "$PROCESS_ID" 2>/dev/null || true
    for _ in 1 2 3 4 5; do
        if ! ps -p "$PROCESS_ID" > /dev/null; then
            return 0
        fi
        sleep 1
    done
    if ps -p "$PROCESS_ID" > /dev/null; then
        echo -e "${YELLOW}${LABEL}未正常退出，强制停止 (PROCESS_ID: $PROCESS_ID)${NC}"
        kill -KILL "$PROCESS_ID" 2>/dev/null || true
    fi
}

# 启动前端服务
start_frontend() {
    echo -e "${YELLOW}启动前端服务...${NC}"
    
    # 获取脚本所在目录的父目录（项目根目录）
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
    
    # 检查是否已在运行
    if [ -f "$FRONTEND_PROCESS_ID_FILE" ]; then
        PROCESS_ID=$(cat "$FRONTEND_PROCESS_ID_FILE")
        if ps -p "$PROCESS_ID" > /dev/null; then
            echo -e "${RED}前端服务已在运行 (PROCESS_ID: $PROCESS_ID)${NC}"
            echo -e "${YELLOW}如需重启，请执行: $0 frontend restart${NC}"
            return 1
        else
            echo -e "${YELLOW}进程编号文件存在但进程不存在，清理旧的进程编号文件${NC}"
            rm -f "$FRONTEND_PROCESS_ID_FILE"
        fi
    fi

    EXISTING_PROCESS_IDS=$(find_project_frontend_process_ids "$PROJECT_ROOT")
    if [ -n "$EXISTING_PROCESS_IDS" ]; then
        FIRST_PROCESS_ID=$(echo "$EXISTING_PROCESS_IDS" | head -n 1)
        echo "$FIRST_PROCESS_ID" > "$FRONTEND_PROCESS_ID_FILE"
        echo -e "${RED}前端服务已在运行 (PROCESS_ID: $FIRST_PROCESS_ID)${NC}"
        echo -e "${YELLOW}如需重启，请执行: $0 frontend restart${NC}"
        return 1
    fi

    if is_port_listening 7860; then
        echo -e "${RED}端口 7860 已被占用，前端无法启动${NC}"
        echo -e "${YELLOW}请先释放端口，或检查占用进程: ss -ltnp | grep ':7860'${NC}"
        return 1
    fi
    
    # 切换到项目根目录
    cd "$PROJECT_ROOT"
    
    if [ "$VERBOSE" -eq 1 ]; then
        echo -e "${YELLOW}前端以 verbose 模式前台启动，日志将输出到当前终端${NC}"
        echo -e "${YELLOW}停止前端请按 Ctrl+C${NC}"
        PYTHONPATH="$PROJECT_ROOT" PYTHONUNBUFFERED=1 python3 -u "$PROJECT_ROOT/src/frontend.py"
        return $?
    fi

    # 启动前端服务（调试模式在 src/frontend.py 的 demo.launch 中开启）
    PYTHONPATH="$PROJECT_ROOT" PYTHONUNBUFFERED=1 nohup setsid python3 -u "$PROJECT_ROOT/src/frontend.py" > "$FRONTEND_LOG" 2>&1 < /dev/null &
    FRONTEND_PROCESS_ID=$!
    
    # 保存进程编号
    echo "$FRONTEND_PROCESS_ID" > "$FRONTEND_PROCESS_ID_FILE"
    
    # 等待服务启动
    sleep 8
    
    # 检查前端是否启动成功
    if ps -p "$FRONTEND_PROCESS_ID" > /dev/null; then
        echo -e "${GREEN}前端服务启动成功 (PROCESS_ID: $FRONTEND_PROCESS_ID)${NC}"
        echo -e "${GREEN}前端服务运行在端口 7860${NC}"
        echo -e "${YELLOW}前端调试日志: $FRONTEND_LOG${NC}"
    else
        echo -e "${RED}前端服务启动失败${NC}"
        rm -f "$FRONTEND_PROCESS_ID_FILE"
        exit 1
    fi
}

# 停止前端服务
stop_frontend() {
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
    STOPPED=false

    if [ -f "$FRONTEND_PROCESS_ID_FILE" ]; then
        PROCESS_ID=$(cat "$FRONTEND_PROCESS_ID_FILE")
        if ps -p "$PROCESS_ID" > /dev/null; then
            stop_process_gracefully "$PROCESS_ID" "前端服务"
            STOPPED=true
        fi
        rm -f "$FRONTEND_PROCESS_ID_FILE"
    fi

    PROCESS_IDS=$(find_project_frontend_process_ids "$PROJECT_ROOT")
    if [ -n "$PROCESS_IDS" ]; then
        for PROCESS_ID in $PROCESS_IDS; do
            if ps -p "$PROCESS_ID" > /dev/null; then
                stop_process_gracefully "$PROCESS_ID" "前端服务"
                STOPPED=true
            fi
        done
    fi

    if [ "$STOPPED" = false ]; then
        echo -e "${YELLOW}前端服务未运行${NC}"
    fi
}

# 重启前端服务
restart_frontend() {
    stop_frontend
    sleep 2
    check_dependencies
    install_dependencies
    start_frontend
}

# 停止服务
stop_service() {
    echo -e "${YELLOW}停止服务...${NC}"
    
    # 停止后端服务
    stop_backend
    
    # 停止前端服务
    stop_frontend
    
    echo -e "${GREEN}服务已停止${NC}"
}

# 检查服务状态
check_status() {
    echo -e "${YELLOW}检查服务状态...${NC}"
    
    BACKEND_RUNNING=false
    FRONTEND_RUNNING=false
    
    # 检查后端服务
    if [ -f "$BACKEND_PROCESS_ID_FILE" ]; then
        PROCESS_ID=$(cat "$BACKEND_PROCESS_ID_FILE")
        if ps -p "$PROCESS_ID" > /dev/null; then
            echo -e "${GREEN}后端服务运行中 (PROCESS_ID: $PROCESS_ID)${NC}"
            BACKEND_RUNNING=true
        else
            echo -e "${RED}后端服务进程编号文件存在但进程不存在${NC}"
            rm -f "$BACKEND_PROCESS_ID_FILE"
        fi
    else
        echo -e "${YELLOW}后端服务未运行${NC}"
    fi
    
    # 检查前端服务
    if [ -f "$FRONTEND_PROCESS_ID_FILE" ]; then
        PROCESS_ID=$(cat "$FRONTEND_PROCESS_ID_FILE")
        if ps -p "$PROCESS_ID" > /dev/null; then
            echo -e "${GREEN}前端服务运行中 (PROCESS_ID: $PROCESS_ID)${NC}"
            FRONTEND_RUNNING=true
        else
            echo -e "${RED}前端服务进程编号文件存在但进程不存在${NC}"
            rm -f "$FRONTEND_PROCESS_ID_FILE"
        fi
    fi
    if [ "$FRONTEND_RUNNING" = false ]; then
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
        EXISTING_PROCESS_IDS=$(find_project_frontend_process_ids "$PROJECT_ROOT")
        if [ -n "$EXISTING_PROCESS_IDS" ]; then
            FIRST_PROCESS_ID=$(echo "$EXISTING_PROCESS_IDS" | head -n 1)
            echo "$FIRST_PROCESS_ID" > "$FRONTEND_PROCESS_ID_FILE"
            echo -e "${GREEN}前端服务运行中 (PROCESS_ID: $FIRST_PROCESS_ID)${NC}"
            FRONTEND_RUNNING=true
        else
            echo -e "${YELLOW}前端服务未运行${NC}"
        fi
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
    echo "使用方法: $0 [--verbose] <backend|frontend|service> <start|stop|status|restart>"
    echo ""
    echo "选项:"
    echo "  --verbose          frontend start 时以前台模式启动，并输出日志到当前终端"
    echo ""
    echo "命令:"
    echo "  backend start      启动后端服务"
    echo "  backend stop       停止后端服务"
    echo "  backend status     检查后端服务状态"
    echo "  backend restart    重启后端服务"
    echo "  frontend start     启动前端服务"
    echo "  frontend stop      停止前端服务"
    echo "  frontend status    检查前端服务状态"
    echo "  frontend restart   重启前端服务"
    echo "  service start      启动后端和前端"
    echo "  service stop       停止后端和前端"
    echo "  service status     检查后端和前端状态"
    echo "  help               显示此帮助信息"
    echo ""
    echo "服务端口:"
    echo "  后端: 8000"
    echo "  前端: 7860"
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
        backend)
            case "$2" in
                start)
                    check_dependencies
                    install_dependencies
                    init_database
                    start_backend
                    ;;
                stop)
                    stop_backend
                    ;;
                status)
                    if [ -f "$BACKEND_PROCESS_ID_FILE" ]; then
                        PROCESS_ID=$(cat "$BACKEND_PROCESS_ID_FILE")
                        if ps -p "$PROCESS_ID" > /dev/null; then
                            echo -e "${GREEN}后端服务运行中 (PROCESS_ID: $PROCESS_ID)${NC}"
                        else
                            echo -e "${RED}后端服务进程编号文件存在但进程不存在${NC}"
                            rm -f "$BACKEND_PROCESS_ID_FILE"
                            return 1
                        fi
                    else
                        echo -e "${YELLOW}后端服务未运行${NC}"
                        return 1
                    fi
                    ;;
                restart)
                    restart_backend
                    ;;
                *)
                    echo -e "${RED}未知 backend 子命令: $2${NC}"
                    echo -e "${YELLOW}可用: backend start|stop|status|restart${NC}"
                    exit 1
                    ;;
            esac
            ;;
        frontend)
            case "$2" in
                start)
                    check_dependencies
                    install_dependencies
                    start_frontend
                    ;;
                stop)
                    stop_frontend
                    ;;
                status)
                    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
                    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
                    if [ -f "$FRONTEND_PROCESS_ID_FILE" ]; then
                        PROCESS_ID=$(cat "$FRONTEND_PROCESS_ID_FILE")
                        if ps -p "$PROCESS_ID" > /dev/null; then
                            echo -e "${GREEN}前端服务运行中 (PROCESS_ID: $PROCESS_ID)${NC}"
                            return 0
                        else
                            echo -e "${RED}前端服务进程编号文件存在但进程不存在${NC}"
                            rm -f "$FRONTEND_PROCESS_ID_FILE"
                        fi
                    fi
                    EXISTING_PROCESS_IDS=$(find_project_frontend_process_ids "$PROJECT_ROOT")
                    if [ -n "$EXISTING_PROCESS_IDS" ]; then
                        FIRST_PROCESS_ID=$(echo "$EXISTING_PROCESS_IDS" | head -n 1)
                        echo "$FIRST_PROCESS_ID" > "$FRONTEND_PROCESS_ID_FILE"
                        echo -e "${GREEN}前端服务运行中 (PROCESS_ID: $FIRST_PROCESS_ID)${NC}"
                    else
                        echo -e "${YELLOW}前端服务未运行${NC}"
                        return 1
                    fi
                    ;;
                restart)
                    restart_frontend
                    ;;
                *)
                    echo -e "${RED}未知 frontend 子命令: $2${NC}"
                    echo -e "${YELLOW}可用: frontend start|stop|status|restart${NC}"
                    exit 1
                    ;;
            esac
            ;;
        service)
            case "$2" in
                start)
                    check_dependencies
                    install_dependencies
                    init_database
                    start_backend
                    start_frontend
                    echo -e "${GREEN}Uni-Resource Agent 启动完成!${NC}"
                    echo -e "${GREEN}访问 http://localhost:7860 查看前端界面${NC}"
                    ;;
                stop)
                    stop_service
                    ;;
                status)
                    check_status
                    ;;
                restart)
                    stop_service
                    sleep 2
                    check_dependencies
                    install_dependencies
                    start_backend
                    start_frontend
                    ;;
                *)
                    echo -e "${RED}未知 service 子命令: $2${NC}"
                    echo -e "${YELLOW}可用: service start|stop|status|restart${NC}"
                    exit 1
                    ;;
            esac
            ;;
        help|--help|-h|"")
            show_help
            ;;
        *)
            echo -e "${RED}未知命令: $1${NC}"
            echo -e "${YELLOW}使用 '$0 help' 查看帮助信息${NC}"
            exit 1
            ;;
    esac
}

# 执行主程序
main "$@"
