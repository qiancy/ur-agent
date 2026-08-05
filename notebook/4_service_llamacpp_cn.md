# 📘 部署 llama.cpp 推理服务

> **适用环境**：Kubernetes Pod（Ubuntu 基础镜像，无 Docker/Podman，AMD ROCm 环境）  
> **目的**：编译 llama.cpp（HIP/ROCm 加速）、下载 GGUF 模型、启动与监控 OpenAI 兼容的推理服务。
> **依赖**：先运行 `1_init_pod_env_cn.md` 完成 `/data` 软链接；GPU 驱动与 ROCm 工具（`rocminfo` / `amd-smi` / `hipconfig`）已就绪。

## 1. 服务概述

- **源码/二进制**：`/data/app/llama.cpp`（`bin/llama-server` 等 120 个文件，含 `libggml-hip.so`）
- **配置脚本**：`/data/service/llamacpp/scripts/`（builder / download / server）
- **模型目录**：`/data/data-store/llamacpp/models/`
- **日志目录**：`/data/data-store/llamacpp/logs/`
- **调优文档**：`/data/service/llamacpp/docs/`（7B / 30B / 80B 配置与基准）

### 本机硬件（参考 docs 与实测）
| 组件 | 规格 |
|------|------|
| GPU | AMD Radeon gfx1100（RDNA3），96 CU，48 GB VRAM |
| CPU | AMD EPYC 9334，2 Socket，128 vCPU |
| RAM | ~503 GB |
| ROCm | 7.2.1 |
| llama.cpp | HIP 编译（`-DGGML_HIP=ON`） |

### 默认模型：Qwen3-Coder-30B-A3B（Q4_K_M）
- 仓库：`lucataco/Qwen3-Coder-30B-A3B-Instruct-Q4_K_M-GGUF`（约 18.6 GB）
- 配置：512K 上下文 / 6 并发 slot / KV `q4_0` / 全 GPU 层（实测约 90 tok/s，VRAM 32.3/48 GB）

---

## 2. 克隆源码

将 llama.cpp 源码克隆到持久化目录 `/data/app`（Pod 重启后仍在，无需重复克隆）。

```python
%%bash
#!/bin/bash
set -euo pipefail

SRC="/data/app/llama.cpp"

if [ -d "$SRC/.git" ]; then
    echo "✅ llama.cpp 源码已存在: $SRC"
    git -C "$SRC" log --oneline -1
else
    echo "🔧 克隆 llama.cpp ..."
    mkdir -p /data/app
    git clone https://github.com/ggml-org/llama.cpp.git "$SRC"
    echo "✅ 克隆完成: $SRC"
fi
```

---

## 3. 编译 (llamacppbuilder.sh)

使用 `/data/service/llamacpp/scripts/llamacppbuilder.sh` 编译，自动检测 GPU（`gfx1100`）并启用 HIP 加速。

**脚本要点**
- 默认 CMake：`-DGGML_HIP=ON -DGGML_HIP_ROCWMMA_FATTN=ON -DGGML_HIP_NO_VMM=ON -DGPU_TARGETS=<auto>`
- `--hackathon` 模式追加：LTO、HIP graphs、rocWMMA flash attention、原生 CPU（AVX2/FMA/BMI2）、ccache
- 输出目录：`<source>/build`（默认 `/data/app/llama.cpp/build`）

```python
%%bash
#!/bin/bash
set -euo pipefail

BUILDER="/data/service/llamacpp/scripts/llamacppbuilder.sh"

# 0) 查看参数与硬件
# bash "$BUILDER" --help

# 1) 自动检测 GPU 架构（本机应为 gfx1100）
detect_gpu() {
    rocminfo 2>/dev/null | grep -m1 'Name:.*gfx' | awk '{print $2}' || echo "gfx1100"
}
echo "GPU target: $(detect_gpu)"

# 2) 编译（hackathon 模式：最大优化，全核并行）
# 预计 10~30 分钟，请耐心等待
# bash "$BUILDER" --hackathon
```

**编译完成后**，将 `build/bin/` 移到源码根目录统一管理（当前环境已执行）：

```python
%%bash
#!/bin/bash
set -euo pipefail

cd /data/app/llama.cpp
if [ -d "build/bin" ]; then
    echo "🔧 移动 build/bin -> ./bin ..."
    mv build/bin/ .
fi
ls bin/ | grep -E "llama-server|llama-cli|llama-embedding"
```

> 💡 若二进制已存在可直接使用：`ls /data/app/llama.cpp/bin/llama-server`

---

## 4. 安装模型下载工具

`download_model.sh` 依赖 HuggingFace CLI `hf`（huggingface_hub）。国内网络建议使用镜像 `https://hf-mirror.com`（脚本默认已开启）。

```python
%%bash
#!/bin/bash
set -euo pipefail

if ! command -v hf &> /dev/null; then
    echo "🔧 安装 huggingface_hub ..."
    pip install --break-system-packages -q huggingface_hub
    echo "✅ 安装完成"
fi
hf --version
```

---

## 5. 下载模型 (download_model.sh)

```python
%%bash
#!/bin/bash
set -euo pipefail

# 30B Q4_K_M（约 18.6GB，当前部署）— 国内镜像
# bash /data/service/llamacpp/scripts/download_model_30b.sh 30b

# 80B（约 47GB，Q4_K_M）
# bash /data/service/llamacpp/scripts/download_model.sh 80b

# 强制重下 / 官方源
# bash /data/service/llamacpp/scripts/download_model_30b.sh 30b --force --no-mirror

# 查看帮助
bash /data/service/llamacpp/scripts/download_model_30b.sh --help
```

> 注意：30B Q4_K_M 使用 `download_model_30b.sh`；`download_model.sh` 的 `30b` 为 Q8_0 版本。

下载完成后模型位于：

| 模型 | 路径 |
|------|------|
| 30B Q4_K_M | `/data/data-store/llamacpp/models/Qwen3-Coder-30B-A3B-Q4_K_M/qwen3-coder-30b-a3b-instruct-q4_k_m.gguf` |
| 80B Q4_K_M | `/data/data-store/llamacpp/models/Qwen3-Coder-Next-Opus-Distilled-Q4_K_M/*.gguf` |

> ✅ 已统一：`llamaserver.sh` 默认 `BASE_MODEL_DIR=/data/data-store/llamacpp/models`，与下载脚本目录一致，无需额外设置。

---

## 6. 启动服务 (llamaserver.sh)

统一管理脚本：`start / stop / status / test`，支持 `--model 30b`、`--port`、`--verbose`、`--dry-run`。

**启动参数（30B）**：`-ngl -1`（全 GPU）、`-c 524288`（512K）、`-np 6`、KV `q4_0`、`--flash-attn on`、`--jinja`、`--numa distribute`。

```python
%%bash
#!/bin/bash
set -euo pipefail

cd /data/service/llamacpp/scripts

# 启动 30B（默认模型目录已与下载脚本一致）
bash llamaserver.sh start --model 30b

# 指定端口
# bash llamaserver.sh start --port 8081

# 仅预览将执行的命令
# bash llamaserver.sh start --dry-run

# 查看状态
bash llamaserver.sh status
```

**验证就绪**：

```python
%%bash
#!/bin/bash
set -euo pipefail

# 健康检查（返回 "ok" 即就绪）
curl -s --max-time 5 http://localhost:8080/health; echo
```

---

## 7. 推理测试

```python
%%bash
#!/bin/bash
set -euo pipefail

# 一键测试（健康检查 + OpenAI 兼容推理 + 速度/token 统计）
bash /data/service/llamacpp/scripts/llamaserver.sh test

# 或直接调用 OpenAI 兼容接口
curl -s --max-time 60 http://localhost:8080/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"model":"test","messages":[{"role":"user","content":"请用一句话介绍你自己"}],"max_tokens":50,"temperature":0.7}' \
    | python3 -m json.tool --no-ensure-ascii
```

**常用端点**

| 端点 | 说明 |
|------|------|
| `GET /health` | 健康检查 |
| `GET /v1/models` | 模型列表 |
| `POST /v1/chat/completions` | 聊天补全 |
| `POST /v1/embeddings` | 嵌入（需 `--embedding`） |
| `GET /props` | 运行参数详情 |

---

## 8. 监控 (monitor.sh)

`/data/service/monitor.sh`：每 10 秒刷新的文本监控面板，展示 llama.cpp（8080）、unires 后端（8000）、前端（7860）状态，以及 CPU / 内存 / GPU 利用率与显存。

```python
%%bash
#!/bin/bash
set -euo pipefail

# 运行监控面板（Ctrl+C 退出）
# bash /data/service/monitor.sh

# 手动快速查看
echo "== llama-server 进程 =="
pgrep -a llama-server || echo "未运行"
echo
echo "== GPU 显存 =="
amd-smi metric --mem 2>/dev/null | grep -E "TOTAL_VRAM|USED_VRAM" | head -4 || rocm-smi --showmeminfo vram 2>/dev/null
```

---

## 9. 服务管理与日志

```python
%%bash
#!/bin/bash
set -euo pipefail

# 停止（优雅 SIGTERM，超时强杀；按 PID 文件 + 端口双兜底）
# bash /data/service/llamacpp/scripts/llamaserver.sh stop

# 日志
LOG_DIR=/data/data-store/llamacpp/logs
ls -la "$LOG_DIR" 2>/dev/null || echo "（尚无日志，服务未启动过）"
```

**常见运维命令**
```bash
tail -f /data/data-store/llamacpp/logs/llamaserver-qwen3.log   # 跟踪日志
ss -tlnp | grep 8080                                          # 端口占用
rocm-smi --showmeminfo vram                                   # 显存占用
```

**Pod 重启一键恢复**（类似 PostgreSQL 的 `init-pg.sh`）：
```bash
/data/init/init-llamacpp.sh   # 装依赖 → 缺二进制则编译 → 缺模型则下载 → 启动(等待最长10分钟)
```

---

## 10. 问题排查

| 问题 | 解决方案 |
|------|----------|
| `hf` 命令找不到 | `pip install --break-system-packages huggingface_hub` |
| 下载网络不可达 | 脚本默认用 `HF_ENDPOINT=https://hf-mirror.com`，或 `--no-mirror` |
| 模型找不到 | 检查 `BASE_MODEL_DIR` 与下载目录一致（见第 5 节） |
| 启动超时/失败 | `cat /data/data-store/llamacpp/logs/llamaserver-*.log` |
| 首次启动很慢 | 模型在 PVC 网络存储上，18.6GB 读取/上显存需 5~10 分钟，属正常；`status` 显示进程存活即可等待 |
| VRAM 不足 | 减小上下文 `-c`、并发 `-np` 或 KV 量化（`q4_0`） |
| 段错误/非法指令 | 确认二进制为 HIP 构建且 `GPU_TARGETS` 正确（`gfx1100`） |
| 编译慢 | 用 `--hackathon` 或减少 `-j`；先 `cmake --build build -j 128` |

调优细节见 `/data/service/llamacpp/docs/01_7B_model_config.md` ~ `05_tuning_history.md` 与 `scripts/llama-server-params.md`。

---

## 11. 后续建议

- 嵌入：RAG 场景可用 `--embedding`（或参考 3 号文档用 pgvector 存向量）。
- 性能基准：用 `llamaserver.sh test` 记录 tok/s；对照 `docs/04_30B_tuning_benchmark.md`。
- 持久化：模型已在 PVC（`/data/data-store`），Pod 重启后无需重下，直接 `llamaserver.sh start`。
- 监控：与 PostgreSQL、unires 后端/前端统一用 `/data/service/monitor.sh` 观察。

---

> ✅ 至此 llama.cpp 推理服务部署完成，可接入 Uni-Resource Agent 应用（参考 `2_app_cn.md`）。
