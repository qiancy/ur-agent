# PostgreSQL 数据库管理文档

## 基本信息
- 版本: PostgreSQL 16.14 (Ubuntu)
- 端口: 5432
- 监听: 0.0.0.0 (所有接口)
- 时区: Asia/Shanghai

## 存储
- PVC 挂载: `/workspace`
- 软链接: `/data` → `/workspace/`
- 数据和配置均在 PVC 上持久化

## 目录结构
```
/workspace/                          # PVC 挂载点
├── data-store/
│   └── pg-unires/                   # 数据目录 (PGDATA)
│       ├── base/
│       ├── pg_wal/
│       ├── postgresql.conf
│       └── ...
├── service/
│   └── pg-unires/
│       ├── config/
│       │   └── pg_hba.conf          # 认证配置
│       ├── bin/
│       │   ├── pgctl.sh             # pg_ctl 方式管理
│       │   └── pg_podman.sh         # podman 方式 (备用)
│       ├── docker-compose.yaml
│       └── README.md                # 本文档
└── init/
    └── init-pg.sh                   # Pod 重启恢复脚本
```

## 用户
| 用户 | Superuser | 可登录 | 可创建DB |
|------|-----------|--------|----------|
| postgres | ✓ | ✓ | ✓ |
| unires | - | ✓ | ✓ |

## 数据库
| 数据库 | 所有者 |
|--------|--------|
| postgres | postgres |
| unires | unires |

## 连接信息
- Host: 127.0.0.1:5432
- User: unires
- Password: demo123
- Database: unires

## 认证 (pg_hba.conf)
- `unires` 用户通过 TCP 连接 → scram-sha-256 (密码认证)
- 本地/localhost 连接 → trust (免密)

## 常用命令
```bash
# 启动
su - postgres -c "/data/service/pg-unires/bin/pgctl.sh start"

# 停止
su - postgres -c "/data/service/pg-unires/bin/pgctl.sh stop"

# 状态
su - postgres -c "/data/service/pg-unires/bin/pgctl.sh status"

# 日志
su - postgres -c "/data/service/pg-unires/bin/pgctl.sh log"
```

## K8s Pod 重启
数据在 PVC 上持久化，Pod 重启后只需重装 PostgreSQL 并启动:
```bash
/data/init/init-pg.sh
```