#!/bin/bash

# Uni-Resource Agent 管理脚本
# 包含启动、停止、状态检查功能

# 配置
BACKEND_PROCESS_ID_FILE="/tmp/uni_resource_agent_backend.process_id"
BACKEND_LOG="/tmp/uni_resource_agent_backend.log"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

VERBOSE=0

get_project_root() {
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    dirname "$script_dir"
}

get_frontend_dir() {
    local project_root
    project_root="$(get_project_root)"
    if [ -d "$project_root/../frontend" ]; then
        cd "$project_root/../frontend" && pwd
    elif [ -d "$project_root/frontend" ]; then
        cd "$project_root/frontend" && pwd
    elif [ -d "$project_root/web" ]; then
        cd "$project_root/web" && pwd
    else
        return 1
    fi
}

# 优先使用项目虚拟环境；不存在则回退系统 python3/pip3
get_venv_dir() {
    local project_root
    project_root="$(get_project_root)"
    if [ -d "$project_root/../.venv/bin" ]; then
        echo "$project_root/../.venv"
    elif [ -d "$project_root/.venv/bin" ]; then
        echo "$project_root/.venv"
    fi
}

get_python() {
    local venv
    venv="$(get_venv_dir)"
    if [ -n "$venv" ]; then
        echo "$venv/bin/python"
    else
        echo "python3"
    fi
}

get_pip() {
    local venv
    venv="$(get_venv_dir)"
    if [ -n "$venv" ]; then
        echo "$venv/bin/pip"
    fi
}

# 检查依赖
check_dependencies() {
    echo -e "${YELLOW}检查依赖...${NC}"
    local venv py
    venv="$(get_venv_dir)"
    py="$(get_python)"
    if [ -n "$venv" ]; then
        echo -e "${GREEN}使用虚拟环境: $venv${NC}"
    fi
    if ! command -v "$py" &> /dev/null; then
        echo -e "${RED}错误: 请先安装 Python 3（$py 不可用）${NC}"
        exit 1
    fi

    local pip_cmd
    pip_cmd="$(get_pip)"
    if [ -z "$pip_cmd" ] && ! command -v pip3 &> /dev/null; then
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

    local pip_cmd pip_extra
    pip_cmd="$(get_pip)"
    pip_extra=""
    if [ -z "$pip_cmd" ]; then
        pip_cmd="pip3"
        pip_extra="--break-system-packages"
    fi
    "$pip_cmd" install $pip_extra -r "$REQUIREMENTS_FILE"
    if [ $? -ne 0 ]; then
        echo -e "${RED}依赖安装失败${NC}"
        exit 1
    fi
    echo -e "${GREEN}依赖安装成功${NC}"
}

# 初始化数据库（幂等保护：已初始化则跳过，避免 drop_all 清库）
init_database() {
    echo -e "${YELLOW}初始化数据库...${NC}"
    # 获取脚本所在目录的父目录（项目根目录）
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
    local py
    py="$(get_python)"

    if ! (cd "$PROJECT_ROOT" && PYTHONPATH="$PROJECT_ROOT" "$py" -c "
import sys
from src.db.database import get_db_connection
try:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT 1 FROM account LIMIT 1')
    cur.close()
    conn.close()
except Exception:
    sys.exit(1)
" 2>/dev/null); then
        echo -e "${YELLOW}数据库尚未初始化，执行 init_db.py（drop_all=True）${NC}"
        if [ -f "$PROJECT_ROOT/scripts/init_db.py" ]; then
            (cd "$PROJECT_ROOT" && PYTHONPATH="$PROJECT_ROOT" "$py" "$PROJECT_ROOT/scripts/init_db.py")
        else
            echo -e "${YELLOW}未找到数据库初始化脚本，跳过数据库初始化${NC}"
        fi
    else
        echo -e "${GREEN}数据库已初始化，跳过重建（保留现有数据）${NC}"
    fi

    echo -e "${GREEN}数据库初始化检查完成${NC}"
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
    nohup setsid "$(get_python)" -m uvicorn src.app:app --host 0.0.0.0 --port 8000 > "$BACKEND_LOG" 2>&1 < /dev/null &
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

# 前端服务使用 Vue + Vite (port 5173)
# 以下函数保留为兼容层，仅输出提示信息

hint_frontend_start() {
    FRONTEND_DIR="$(get_frontend_dir || true)"
    if [ -z "$FRONTEND_DIR" ]; then
        echo -e "${RED}未找到前端目录，期望 frontend/ 或 web/${NC}"
        return 1
    fi
    echo -e "${YELLOW}前端使用 Vue + Vite${NC}"
    echo -e "${YELLOW}请手动启动前端:${NC}"
    echo -e "  cd $FRONTEND_DIR && npm run dev -- --host 0.0.0.0 --port 5173"
    echo -e "${GREEN}前端预览: http://localhost:5173${NC}"
}

start_frontend() {
    hint_frontend_start
}

stop_frontend() {
    echo -e "${YELLOW}前端使用 Vue + Vite，请手动停止 Vite 进程${NC}"
}

restart_frontend() {
    hint_frontend_start
}

# 停止服务
stop_service() {
    echo -e "${YELLOW}停止服务...${NC}"

    # 停止后端服务
    stop_backend

    echo -e "${YELLOW}前端使用 Vue + Vite，请手动停止 Vite 进程${NC}"
    echo -e "${GREEN}后端服务已停止${NC}"
}

# 检查服务状态
check_status() {
    echo -e "${YELLOW}检查服务状态...${NC}"

    BACKEND_RUNNING=false

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

    # 前端提示
    FRONTEND_DIR="$(get_frontend_dir || true)"
    if [ -n "$FRONTEND_DIR" ]; then
        echo -e "${YELLOW}前端 (Vue + Vite): $FRONTEND_DIR，请手动确认 Vite 是否在端口 5173 运行${NC}"
    else
        echo -e "${RED}前端目录不存在，期望 frontend/ 或 web/${NC}"
    fi

    if [ "$BACKEND_RUNNING" = false ]; then
        echo -e "${RED}后端服务未运行${NC}"
        return 1
    fi

    echo -e "${GREEN}服务状态检查完成${NC}"
    return 0
}

# 显示帮助
show_help() {
    echo "Uni-Resource Agent 管理脚本"
    echo "使用方法: $0 [--verbose] <backend|service> <start|stop|status|restart>"
    echo ""
    echo "选项:"
    echo "  --verbose          显示详细输出"
    echo ""
    echo "命令:"
    echo "  backend start      启动后端服务"
    echo "  backend stop       停止后端服务"
    echo "  backend status     检查后端服务状态"
    echo "  backend restart    重启后端服务"
    echo "  service start      启动后端服务（前端请手动启动）"
    echo "  service stop       停止后端服务（前端请手动停止）"
    echo "  service status     检查后端服务状态（前端请手动确认）"
    echo "  help               显示此帮助信息"
    echo ""
    echo "服务端口:"
    echo "  后端: 8000 (FastAPI)"
    echo "  前端: 5173 (Vue + Vite, 需手动启动: cd frontend && npm run dev)"
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
                    hint_frontend_start
                    ;;
                stop)
                    stop_frontend
                    ;;
                status)
                    FRONTEND_DIR="$(get_frontend_dir || true)"
                    if [ -n "$FRONTEND_DIR" ]; then
                        echo -e "${YELLOW}前端使用 Vue + Vite: $FRONTEND_DIR，请手动确认 Vite 是否在端口 5173 运行${NC}"
                    else
                        echo -e "${RED}前端目录不存在，期望 frontend/ 或 web/${NC}"
                        return 1
                    fi
                    ;;
                restart)
                    hint_frontend_start
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
                    hint_frontend_start
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
                    hint_frontend_start
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
