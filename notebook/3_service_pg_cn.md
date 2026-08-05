# 📘 部署 PostgreSQL + pgvector 服务

> **适用环境**：Kubernetes Pod（Ubuntu 基础镜像，无 Docker/Podman）  
> **目的**：安装并配置 PostgreSQL 16 + pgvector 0.6.0，完成数据库/用户创建、优化参数调优、向量检索验证与连接测试。
> **依赖**：先运行 `1_init_pod_env_cn.ipynb` 完成 `/data` 软链接。

## 1. 服务概述

- **版本**：PostgreSQL 16.14 (Ubuntu) + pgvector 0.6.0
- **端口/监听**：`5432` / `0.0.0.0`
- **数据目录 (PGDATA)**：`/data/data-store/pg-unires`（PVC 持久化）
- **配置目录**：`/data/service/pg-unires/config/`（`postgresql.conf` + `pg_hba.conf`）
- **时区**：`Asia/Shanghai`
- **用途**：RAG / 向量检索（pgvector HNSW / IVFFlat 索引）
- **管理方式**：`pg_ctl` 直接管理（Pod 内无 Docker，不使用容器）

## 2. 安装 PostgreSQL 与 pgvector

安装服务端、pgvector 扩展和客户端工具。**幂等**：已安装则跳过。

```python
%%bash
set -euo pipefail

if ! dpkg -s postgresql-16 >/dev/null 2>&1; then
    echo "🔧 安装 PostgreSQL 16 / pgvector / client ..."
    apt-get update -qq
    apt-get install -y -qq postgresql-16 postgresql-16-pgvector postgresql-client
    echo "✅ 安装完成"
else
    echo "✅ PostgreSQL 已安装"
fi

psql --version
dpkg -l | grep postgresql-16-pgvector | awk '{print "pgvector:", $2, $3}'
```

## 3. 初始化数据目录 (initdb)

在 PVC 上创建独立数据目录，避免使用系统默认 `/var/lib/postgresql`。  
- 编码 UTF8、locale `C.UTF-8`、开启 data checksums（数据完整性校验）。  
- **注意**：`/persistent` 默认权限 `700 root`，需放行 `postgres` 用户遍历（`chmod 711`）。

```python
%%bash
set -euo pipefail

PGDATA="/data/data-store/pg-unires"

# /persistent 默认 700 root，放行 postgres 用户遍历
chmod 711 /persistent 2>/dev/null || true

mkdir -p "$PGDATA"
chown -R postgres:postgres "$PGDATA"

if [ ! -f "$PGDATA/PG_VERSION" ]; then
    echo "🔧 初始化数据目录 (UTF8 / C.UTF-8 / checksums) ..."
    su - postgres -c "/usr/lib/postgresql/16/bin/initdb -D $PGDATA -U postgres -E UTF8 --locale=C.UTF-8 --data-checksums -A trust"
    echo "✅ initdb 完成"
else
    echo "✅ 数据目录已存在: $PGDATA"
fi
```

## 4. 优化配置 postgresql.conf

针对 128 核 / 503GB 内存主机（与 llamacpp 等共享）调优，重点面向向量检索负载：
- 内存：`shared_buffers=16GB`、`effective_cache_size=48GB`、`maintenance_work_mem=2GB`（HNSW/IVFFlat 建索引内存）
- WAL：`wal_compression=zstd`、`max_wal_size=8GB`、`checkpoint_completion_target=0.9`
- 并行：`max_parallel_workers=32`；规划器：`random_page_cost=1.1`（NVMe SSD）
- 时区/日志：`Asia/Shanghai`、`log_min_duration_statement=1000ms`

配置文件写入服务目录，并通过 PGDATA `postgresql.conf` 末尾的 `include_if_exists` 加载，实现**配置与数据分离**。

```python
%%bash
set -euo pipefail

CONF="/data/service/pg-unires/config/postgresql.conf"
PGDATA="/data/data-store/pg-unires"
mkdir -p "$(dirname "$CONF")"

cat > "$CONF" <<'EOF'
# ============================================================
# PostgreSQL 16 优化配置 — unires (pgvector / RAG)
# 机器: 128 cores / 503GB RAM (与 llamacpp 等共享)
# 通过 PGDATA/postgresql.conf include_if_exists 加载
# ============================================================

# ---------- 连接 ----------
listen_addresses = '*'
port = 5432
max_connections = 200
unix_socket_directories = '/var/run/postgresql'

# ---------- 内存 ----------
shared_buffers = 16GB
huge_pages = try
effective_cache_size = 48GB
work_mem = 64MB
temp_buffers = 64MB
maintenance_work_mem = 2GB

# ---------- 并行 ----------
max_worker_processes = 32
max_parallel_workers = 32
max_parallel_workers_per_gather = 8
max_parallel_maintenance_workers = 8
parallel_leader_participation = on
effective_io_concurrency = 200
maintenance_io_concurrency = 200

# ---------- WAL / 检查点 ----------
wal_level = replica
wal_buffers = 32MB
wal_compression = zstd
max_wal_size = 8GB
min_wal_size = 2GB
checkpoint_completion_target = 0.9
checkpoint_timeout = 15min
max_wal_senders = 10
max_replication_slots = 10

# ---------- 自动清理 ----------
autovacuum = on
autovacuum_max_workers = 8
autovacuum_naptime = 30s
autovacuum_vacuum_cost_delay = 2ms
autovacuum_vacuum_scale_factor = 0.05
autovacuum_analyze_scale_factor = 0.02

# ---------- 规划器 ----------
random_page_cost = 1.1
cpu_tuple_cost = 0.03
default_statistics_target = 200
jit = on

# ---------- 日志 ----------
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d.log'
log_rotation_age = 1d
log_min_duration_statement = 1000
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on
log_temp_files = 0
log_timezone = 'Asia/Shanghai'
log_line_prefix = '%m [%p] %q%u@%d '

# ---------- 时区 / 区域 ----------
timezone = 'Asia/Shanghai'
datestyle = 'iso, ymd'
lc_messages = 'C.UTF-8'
lc_monetary = 'C.UTF-8'
lc_numeric = 'C.UTF-8'
lc_time = 'C.UTF-8'
default_text_search_config = 'pg_catalog.english'
EOF

# 挂载到 PGDATA（include_if_exists，配置与数据分离）
if [ -f "$PGDATA/postgresql.conf" ]; then
    grep -q "service/pg-unires/config/postgresql.conf" "$PGDATA/postgresql.conf" || \
        printf "\n# 加载服务目录中的优化配置\ninclude_if_exists = '/data/service/pg-unires/config/postgresql.conf'\n" >> "$PGDATA/postgresql.conf"
    chown postgres:postgres "$PGDATA/postgresql.conf"
fi

echo "✅ 优化配置已写入: $CONF"
grep -E "^(shared_buffers|effective_cache_size|work_mem|maintenance_work_mem|max_connections|wal_compression|random_page_cost|timezone)" "$CONF"
```

## 5. 认证配置 pg_hba.conf

- `unires` 用户经 TCP 连接 → `scram-sha-256`（密码认证，任意来源地址）
- 本机/`localhost` 连接 → `trust`（免密，便于调试）

> ⚠️ 生产环境请收紧地址范围（如 `10.0.0.0/8`），并用 `pgpass` 管理密码。

```python
%%bash
set -euo pipefail

HBA="/data/service/pg-unires/config/pg_hba.conf"
PGDATA="/data/data-store/pg-unires"

cat > "$HBA" <<'EOF'
# TYPE  DATABASE        USER            ADDRESS                 METHOD
host    unires          unires          0.0.0.0/0               scram-sha-256
local   all             all                                     trust
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust
local   replication     all                                     trust
host    replication     all             127.0.0.1/32            trust
host    replication     all             ::1/128                 trust
EOF

cp "$HBA" "$PGDATA/pg_hba.conf"
chown postgres:postgres "$PGDATA/pg_hba.conf"
echo "✅ pg_hba.conf 已更新"
```

## 6. 启动服务

使用 `pg_ctl` 直接管理。若配置已修改，先 `reload`（热加载），未运行则启动。

```python
%%bash
set -euo pipefail

PGDATA="/data/data-store/pg-unires"
PG_CTL="/usr/lib/postgresql/16/bin/pg_ctl"

# 运行中则热加载配置；未运行则忽略
su - postgres -c "$PG_CTL -D $PGDATA reload" >/dev/null 2>&1 || true

if ! su - postgres -c "$PG_CTL -D $PGDATA status" >/dev/null 2>&1; then
    echo "🚀 启动 PostgreSQL ..."
    su - postgres -c "$PG_CTL -D $PGDATA -l $PGDATA/pg.log start"
fi

su - postgres -c "$PG_CTL -D $PGDATA status"
pg_isready -h 127.0.0.1 -p 5432 -U unires -d unires
```

## 7. 创建用户与数据库

- 角色 `unires`：`LOGIN` + `CREATEDB`，密码 `demo123`
- 数据库 `unires`：owner=`unires`，UTF8 / `C.UTF-8`
- 使用 `\gexec` 实现幂等（不存在才创建）。

```python
%%bash
set -euo pipefail

DB_USER="unires"; DB_PASS="demo123"; DB_NAME="unires"

su - postgres -c "psql -v ON_ERROR_STOP=1 -d postgres" <<SQL
SELECT 'CREATE ROLE $DB_USER LOGIN CREATEDB PASSWORD ''$DB_PASS'''
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname='$DB_USER')\gexec
SELECT 'CREATE DATABASE $DB_NAME OWNER $DB_USER ENCODING ''UTF8'' TEMPLATE template0 LC_COLLATE ''C.UTF-8'' LC_CTYPE ''C.UTF-8'''
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname='$DB_NAME')\gexec
SQL

echo "✅ 用户/数据库就绪"
psql -h 127.0.0.1 -U postgres -d postgres -c "\l unires"
```

## 8. 启用 pgvector 并验证

pgvector 属于**非 trusted 扩展**，需超级用户 `postgres` 创建（创建后 `unires` 可正常使用）。  
验证流程：建表（vector 列）→ HNSW 余弦索引 → 插入 → 余弦距离检索 → 清理测试表。

```python
%%bash
set -euo pipefail

DB_NAME="unires"

# 非 trusted 扩展，需超级用户创建
su - postgres -c "psql -d $DB_NAME -v ON_ERROR_STOP=1 -c 'CREATE EXTENSION IF NOT EXISTS vector;'"

# 冒烟测试（以 unires 身份连接执行）
PGPASSWORD=demo123 psql -h 127.0.0.1 -U unires -d unires -v ON_ERROR_STOP=1 <<'SQL'
CREATE TABLE IF NOT EXISTS pgvector_smoke (
    id        serial PRIMARY KEY,
    title     text,
    embedding vector(4)
);
CREATE INDEX IF NOT EXISTS idx_smoke_hnsw
    ON pgvector_smoke USING hnsw (embedding vector_cosine_ops);
TRUNCATE pgvector_smoke;
INSERT INTO pgvector_smoke (title, embedding) VALUES
    ('pgvector 教程', '[1,0,0,0]'),
    ('向量检索',      '[0,1,0,0]'),
    ('RAG 应用',      '[0,0,1,0]');
SELECT id, title, round((embedding <-> '[1,0,0,0]')::numeric, 2) AS distance
    FROM pgvector_smoke
    ORDER BY embedding <-> '[1,0,0,0]'
    LIMIT 3;
DROP TABLE pgvector_smoke;
SQL

echo "✅ pgvector 验证通过"
```

## 9. 连接信息

| 项 | 值 |
|----|----|
| Host / Port | `127.0.0.1:5432` |
| User | `unires` |
| Password | `demo123` |
| Database | `unires` |
| 连接串 | `postgresql://unires:demo123@127.0.0.1:5432/unires` |

> 应用接入（SQLAlchemy/LangChain）时若未安装驱动，先 `pip install psycopg2-binary`。

```python
%%bash
set -euo pipefail

export PGHOST=127.0.0.1 PGPORT=5432 PGUSER=unires PGPASSWORD=demo123 PGDATABASE=unires

echo "== 连接测试 =="
psql -c "SELECT current_user AS user, current_database() AS db, current_setting('timezone') AS tz;"
echo
echo "== pgvector 扩展 =="
psql -c "\dx vector"
```

## 10. 故障恢复与常用命令

- **Pod 重启恢复**（一键）：`/data/init/init-pg.sh`（重装 → initdb → 应用配置 → 启动 → 建用户/库/扩展）
- **启动/停止/状态/日志**：
  ```bash
  su - postgres -c "/data/service/pg-unires/bin/pgctl.sh start"    # 启动
  su - postgres -c "/data/service/pg-unires/bin/pgctl.sh stop"     # 停止
  su - postgres -c "/data/service/pg-unires/bin/pgctl.sh status"   # 状态
  su - postgres -c "/data/service/pg-unires/bin/pgctl.sh log"      # 跟踪日志
  ```
- **热加载配置**：`su - postgres -c "pg_ctl -D /data/data-store/pg-unires reload"`
- **日志位置**：`/data/data-store/pg-unires/pg.log`、`log/` 目录（按天轮转）

## 常见问题
- `ALTER EXTENSION ... OWNER/RENAME` 在当前 Pod 环境不可用：扩展由 `postgres` 创建，`unires` 正常使用，无需改 owner。
- `shared_preload_libraries='vector'` 会导致启动段错误：pgvector 无需预加载，**不要**设置。
- `expected 1536 dimensions`：插入向量维度须与建表 `vector(n)` 一致（如 OpenAI 嵌入为 1536）。

## 11. 后续建议

- 备份：定期 `pg_dump -Fc unires` 至 `/data/backup`。
- 索引选择：小数据量用 HNSW（内存友好、召回高），海量数据可比较 IVFFlat。
- 监控：结合 `/data/service/monitor.sh` 观察磁盘与进程。
- 模型：参考 `/data/ur-agent/2_app_cn.ipynb` 部署 llama.cpp + 应用服务。

---

> ✅ 至此 PostgreSQL + pgvector 服务部署完成，可接入 Uni-Resource Agent 应用。

