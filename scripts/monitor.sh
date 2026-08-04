#!/usr/bin/env bash
# ============================================================
# monitor.sh — 系统监控：unires-agent + llamacpp + AMD CPU/GPU
#
# 用法:
#   monitor.sh              # 单次输出
#   monitor.sh --loop       # 循环监控 (默认 30s 间隔)
#   monitor.sh --loop -i 10 # 每 10 秒刷新
#   monitor.sh --json       # JSON 格式输出
# ============================================================

set -euo pipefail

# ---- 配置 ----
INTERVAL=30
LOOP=false
JSON=false

LLAMACPP_PORT=8080
UNIRES_BACKEND_PORT=8000
UNIRES_FRONTEND_PORT=5173

# ---- 颜色 ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
DIM='\033[2m'
NC='\033[0m'

# ---- 参数解析 ----
while [ $# -gt 0 ]; do
    case "$1" in
        --loop) LOOP=true; shift ;;
        -i|--interval) INTERVAL="$2"; shift 2 ;;
        --json) JSON=true; shift ;;
        -h|--help|help)
            echo "用法: $0 [选项]"
            echo ""
            echo "监控 unires-agent、llama.cpp、AMD CPU/GPU 运行状态"
            echo ""
            echo "选项:"
            echo "  --loop       循环监控 (默认 30s 间隔)"
            echo "  -i SECONDS   刷新间隔 (默认 30)"
            echo "  --json       JSON 格式输出"
            echo "  -h, --help   显示此帮助"
            echo ""
            echo "示例:"
            echo "  $0                  # 单次输出"
            echo "  $0 --loop           # 每 30s 刷新"
            echo "  $0 --loop -i 10     # 每 10s 刷新"
            echo "  $0 --json           # JSON 格式"
            exit 0 ;;
        *) echo "未知参数: $1"; exit 1 ;;
    esac
done

# ============================================================
# 采集函数
# ============================================================

check_port() {
    local port=$1
    curl -s --max-time 3 "http://localhost:${port}/health" 2>/dev/null | grep -q ok && echo "up" || echo "down"
}

get_llamacpp_info() {
    local status health model vram
    status=$(check_port $LLAMACPP_PORT)
    if [ "$status" = "up" ]; then
        health="OK"
        model=$(curl -s --max-time 3 "http://localhost:${LLAMACPP_PORT}/props" 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('model_path','?').split('/')[-1])
except: print('?')
" 2>/dev/null || echo "?")
    else
        health="DOWN"
        model="-"
    fi
    echo "${status}|${health}|${model}"
}

get_unires_info() {
    local backend frontend backend_process_id frontend_process_id
    # 后端
    if [ -f /tmp/uni_resource_agent_backend.process_id ]; then
        backend_process_id=$(cat /tmp/uni_resource_agent_backend.process_id 2>/dev/null || echo "")
        if [ -n "$backend_process_id" ] && kill -0 "$backend_process_id" 2>/dev/null; then
            backend="up"
        else
            backend="down"
        fi
    else
        # 尝试按端口检测
        if curl -s --max-time 3 "http://localhost:${UNIRES_BACKEND_PORT}/" >/dev/null 2>&1; then
            backend="up"
        else
            backend="down"
        fi
    fi
    # 前端 (Vue + Vite, 手动启动)
    if curl -s --max-time 3 "http://localhost:${UNIRES_FRONTEND_PORT}/" >/dev/null 2>&1; then
        frontend="up"
    else
        frontend="down"
    fi
    echo "${backend}|${frontend}"
}

get_cpu_info() {
    local load cores usage
    cores=$(nproc)
    load=$(awk '{print $1}' /proc/loadavg)
    usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2 + $4}')
    echo "${cores}|${load}|${usage}"
}

get_gpu_info() {
    # amd-smi 获取 gfx/temp/power
    local gfx temp power
    eval "$(amd-smi metric -u -t -p --json 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    g = d['gpu_data'][0]
    gfx = g['usage']['gfx_activity']['value']
    temp = g['temperature']['edge']['value']
    power = g['power']['socket_power']['value']
    print(f'gfx={gfx};temp={temp};power={power}')
except:
    print('gfx=0;temp=0;power=0')
" 2>/dev/null)" || true

    # rocm-smi 获取 VRAM
    local vram_info
    vram_info=$(rocm-smi --showmeminfo vram 2>/dev/null | python3 -c "
import sys
used = total = 0
for line in sys.stdin:
    if 'Total Memory' in line:
        total = int(line.split('(B):')[1].strip()) // (1024*1024)
    elif 'Used Memory' in line:
        used = int(line.split('(B):')[1].strip()) // (1024*1024)
pct = round(used / total * 100, 1) if total > 0 else 0
print(f'{used}|{total}|{pct}')
" 2>/dev/null || echo "?|?|?")
    echo "${gfx:-0}|${temp:-0}|${power:-0}|${vram_info}"
}

get_gpu_processes() {
    amd-smi process --json 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    procs = d.get('gpu_data', [{}])[0].get('processes', [])
    count = len(procs)
    mem = sum(p.get('memory', {}).get('vram_usage', {}).get('value', 0) for p in procs)
    print(f'{count}|{mem}')
except:
    print('0|0')
" 2>/dev/null || echo "0|0"
}

get_vram_rocm() {
    rocm-smi --showmeminfo vram 2>/dev/null | grep -E "Total|Used" | awk '{printf "%.0f\n", $NF/1073741824}' | paste - - | awk '{print $1, $2}'
}

# ============================================================
# 格式化输出
# ============================================================

status_icon() {
    [ "$1" = "up" ] && echo -e "${GREEN}●${NC}" || echo -e "${RED}●${NC}"
}

bar() {
    local pct=$1
    local width=20
    local filled=$(echo "$pct * $width / 100" | bc 2>/dev/null || echo 0)
    local empty=$((width - filled))
    printf "["
    printf "%0.s█" $(seq 1 $filled 2>/dev/null) || true
    printf "%0.s░" $(seq 1 $empty 2>/dev/null) || true
    printf "] %s%%" "$pct"
}

print_report() {
    local ts=$(date '+%Y-%m-%d %H:%M:%S')

    # 采集数据
    IFS='|' read -r llamacpp_status llamacpp_health llamacpp_model <<< "$(get_llamacpp_info)"
    IFS='|' read -r unires_backend unires_frontend <<< "$(get_unires_info)"
    IFS='|' read -r cpu_cores cpu_load cpu_usage <<< "$(get_cpu_info)"
    IFS='|' read -r gpu_gfx gpu_temp gpu_power gpu_vram_used gpu_vram_total gpu_vram_pct <<< "$(get_gpu_info)"
    IFS='|' read -r gpu_proc_count gpu_proc_mem <<< "$(get_gpu_processes)"

    clear
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}  系统监控  ${DIM}${ts}${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    # ---- llamacpp ----
    echo -e "${CYAN}▸ llama.cpp 服务${NC}  $(status_icon $llamacpp_status)  端口 ${LLAMACPP_PORT}"
    if [ "$llamacpp_status" = "up" ]; then
        echo -e "  模型:   ${llamacpp_model}"
        echo -e "  健康:   ${GREEN}${llamacpp_health}${NC}"
    else
        echo -e "  状态:   ${RED}未运行${NC}"
    fi
    echo ""

    # ---- unires-agent ----
    echo -e "${CYAN}▸ unires-agent${NC}"
    echo -e "  后端:   $(status_icon $unires_backend)  端口 ${UNIRES_BACKEND_PORT}"
    echo -e "  前端:   $(status_icon $unires_frontend)  端口 ${UNIRES_FRONTEND_PORT}"
    echo ""

    # ---- CPU ----
    echo -e "${CYAN}▸ AMD CPU${NC}  (${cpu_cores} cores)"
    echo -e "  负载:   ${cpu_load}  用量: $(bar $cpu_usage)"
    echo ""

    # ---- GPU ----
    echo -e "${CYAN}▸ AMD GPU${NC}  (gfx1100 / Navi 31)"
    if [ "$gpu_gfx" != "?" ]; then
        echo -e "  GPU:    $(bar $gpu_gfx)  ${DIM}gfx activity${NC}"
        echo -e "  显存:   $(bar $gpu_vram_pct)  ${gpu_vram_used} MiB / ${gpu_vram_total} MiB"
        echo -e "  温度:   ${gpu_temp}°C  功耗: ${gpu_power} W"
        if [ "$gpu_proc_count" != "0" ]; then
            echo -e "  进程:   ${gpu_proc_count} 个  显存占用: ${gpu_proc_mem} MiB"
        fi
    else
        echo -e "  ${RED}无法获取 GPU 信息${NC}"
    fi
    echo ""

    echo -e "${DIM}刷新间隔: ${INTERVAL}s | Ctrl+C 退出${NC}"
}

print_json() {
    local ts=$(date -u '+%Y-%m-%dT%H:%M:%SZ')

    IFS='|' read -r llamacpp_status llamacpp_health llamacpp_model <<< "$(get_llamacpp_info)"
    IFS='|' read -r unires_backend unires_frontend <<< "$(get_unires_info)"
    IFS='|' read -r cpu_cores cpu_load cpu_usage <<< "$(get_cpu_info)"
    IFS='|' read -r gpu_gfx gpu_temp gpu_power gpu_vram_used gpu_vram_total gpu_vram_pct <<< "$(get_gpu_info)"

    cat <<EOF
{
  "timestamp": "${ts}",
  "llamacpp": {
    "status": "${llamacpp_status}",
    "health": "${llamacpp_health}",
    "model": "${llamacpp_model}",
    "port": ${LLAMACPP_PORT}
  },
  "unires_agent": {
    "backend": "${unires_backend}",
    "frontend": "${unires_frontend}",
    "backend_port": ${UNIRES_BACKEND_PORT},
    "frontend_port": ${UNIRES_FRONTEND_PORT}
  },
  "cpu": {
    "cores": ${cpu_cores:-0},
    "load": "${cpu_load:-0}",
    "usage_pct": ${cpu_usage:-0}
  },
  "gpu": {
    "gfx_activity_pct": ${gpu_gfx:-0},
    "temperature_c": ${gpu_temp:-0},
    "power_w": ${gpu_power:-0},
    "vram_used_mb": ${gpu_vram_used:-0},
    "vram_total_mb": ${gpu_vram_total:-0},
    "vram_pct": ${gpu_vram_pct:-0}
  }
}
EOF
}

# ============================================================
# 主循环
# ============================================================

if $LOOP; then
    while true; do
        if $JSON; then
            print_json
        else
            print_report
        fi
        sleep "$INTERVAL"
    done
else
    if $JSON; then
        print_json
    else
        print_report
    fi
fi
