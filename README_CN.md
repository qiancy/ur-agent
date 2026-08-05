# Uni-Resource Agent

> **"One AI. All Your Worlds."**
> **万物皆资源**

统一资源管理 AI 助手 — 通过一个 AI Agent 管理物理资产、人员、交易和知识。

---

## 🎯 Product Positioning

Uni-Resource Agent 的第一目标组织是：**数据敏感、资源分散、没有重型 ERP 能力的中小型组织**。

典型用户包括小公司、学校或实验室、社区机构、家庭企业、养老照护团队、项目制团队，以及电商小卖家。核心购买者不是普通员工，而是资源协调者：行政、财务、仓管、办公室主任、家庭管理者或项目负责人。

### 解决的痛点

1. **资源分散**：物品、人员、知识文档、收支记录分散在 Excel、群聊、纸质记录和个人经验里，查询、交接和复盘成本高。
2. **上下文混乱**：同一个人可能同时属于公司、家庭、项目组或学校，不同身份下的数据不能混在一起。
3. **小组织用不起复杂系统**：ERP、OA、资产系统、知识库和财务系统太重，小组织更需要能问、能查、能记、能办的轻量系统。
4. **隐私和本地化要求**：人员、财务、资产和内部知识不适合上传到云端 AI，系统应支持本地模型、本地数据库和本地知识库。
5. **AI 不能只聊天**：用户需要 AI 连接真实业务资源，可靠完成查询资产、记录交易、管理提醒和检索知识。

### 买点与卖点

买点：
- 一个入口管理物品、知识、人员和财务。
- 用自然语言查询、记录、调拨、提醒和总结。
- 通过 Multi-Context Space 隔离公司、家庭、学校、项目等不同空间。
- 本地部署，数据不出组织。

卖点：

> 给没有重型信息化能力的小组织，一个能本地运行、保护隐私、真正管资源的 AI 助手。

当前 MVP 的优先业务场景是**淘宝卖家的轻量仓库管理**，覆盖买入、卖出、库存位置和基础收支；**火烧新野**作为演示和回归测试场景，用于展示时间线、阵营、任务、活动、物资，以及信息流、物流、人流的统一建模。

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    UNI-RESOURCE AGENT                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Frontend (Vue+Vite)  Backend (FastAPI)    Database (PostgreSQL)│
│       port 5173           port 8000            port 5432        │
│           │                   │                    │            │
│           └──── HTTP ────────►│                    │            │
│                               │  SQL Queries ─────►│            │
│                               │                    │            │
│                           ┌───┴───┐               │            │
│                           ▼       ▼               │            │
│                       LangChain  pgvector        │            │
│                       (AI)       (Vector Search) │            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Database Schema

### Context (运行时概念)
`context` 是程序运行时动态组合的概念，由两个核心标识组成：

| 标识 | 说明 | 作用 |
|------|------|------|
| `ouid` | 组织业务标识 | 标识当前操作所属的组织/空间，例如 `shu`、`wei` |
| `puid` | 人员业务标识 | 标识当前操作所属的人员/身份，例如 `liubei`、`caocao` |

**`context = {ouid, puid}` 表示 "person@organization" 上下文**

例如：
- `Zhang San @ Company` → ouid=company, puid=zhangsan
- `Zhang San @ Home` → ouid=home, puid=zhangsan
- `Li Si @ School` → ouid=school, puid=lisi

> 注意：`ouid` 和 `puid` 作为业务标识，通过 `person_id` / `organization_id` 数字外键实现多租户隔离。`context_id` 参数在 API 中已被废弃，统一使用 `ouid` + `puid` 传递。

| Table | Description | Key Columns |
|-------|-------------|-------------|
| `resource` | 资源 | id, organization_id, ouid, puid, name, type |
| `virtual_assets` | 虚拟资产 (继承 assets) | id(FK→assets), content, embedding |
| `personnel` | 人员 | id, ouid, puid, name, role, birth_date, health_reminders |
| `party` | 交易参与方 | id, ouid, puid, name, role, description |
| `party_member` | 人员↔参与方 (多对多) | party_id, personnel_id, role |
| `transactions` | 交易记录 | id, ouid, puid, from_party_id, to_party_id, amount, category |

**ER 关系:**

```
assets ─┬─ physical_assets
        └─ virtual_assets

personnel ←── party_member ──→ party
                                  │
                                  └──→ transactions (from_party_id, to_party_id)
```

---

## 🔌 REST API

Base URL: `http://localhost:8000`

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | 健康检查 |

### Assets

| Method | Path | Description |
|--------|------|-------------|
| GET | `/assets?ouid=shu&name=&warehouse=` | 查询资产（支持按名称/仓库筛选） |
| POST | `/assets` | 创建资产 |
| POST | `/assets/transfer` | 跨组织调拨资产 |

**POST /assets**
```json
{
  "ouid": "shu",
  "puid": "liubei",
  "name": "连弩",
  "asset_type": "兵器",
  "quantity": 50,
  "warehouse": "军械库"
}
```

**POST /assets/transfer**
```json
{
  "asset_id": 4,
  "from_ouid": "shu",
  "from_puid": "liubei",
  "to_ouid": "wei",
  "to_puid": "caocao",
  "quantity": 10
}
```

### Personnel

| Method | Path | Description |
|--------|------|-------------|
| GET | `/personnel?ouid=shu&name=` | 查询人员 |
| POST | `/personnel` | 添加人员 |

**POST /personnel**
```json
{
  "ouid": "shu",
  "puid": "lisi",
  "name": "诸葛亮",
  "role": "丞相",
  "birth_date": "0181-04-23"
}
```

### Party (交易参与方)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/party?ouid=shu&name=` | 查询参与方 |
| POST | `/party` | 创建参与方 |
| GET | `/party/{id}/members` | 查看成员 |
| POST | `/party/members` | 添加成员 |

**POST /party**
```json
{
  "ouid": "shu",
  "puid": "liubei",
  "name": "蜀汉集团",
  "role": "买家",
  "description": "蜀汉政权"
}
```

**POST /party/members**
```json
{
  "party_id": 1,
  "personnel_id": 2,
  "ouid": "shu",
  "puid": "liubei",
  "role": "丞相"
}
```

### Transactions

| Method | Path | Description |
|--------|------|-------------|
| GET | `/transactions?ouid=shu&limit=50` | 交易记录（含参与方名称） |
| POST | `/transactions` | 记录交易 |

**POST /transactions**
```json
{
  "ouid": "shu",
  "puid": "liubei",
  "from_party_id": 1,
  "to_party_id": 2,
  "amount": 1000.00,
  "category": "军费",
  "description": "蜀汉集团资助诸葛亮家"
}
```

### Summary

| Method | Path | Description |
|--------|------|-------------|
| GET | `/summary?ouid=shu` | 财务摘要（流入/流出/余额） |

**Response:**
```json
{
  "ouid": "shu",
  "puid": "liubei",
  "total_outflow": 4500.0,
  "total_inflow": 4500.0,
  "balance": 0.0,
  "transaction_count": 3
}
```

### Chat (AI Agent)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/chat` | AI 对话（调用 LangChain Agent） |

**POST /chat**
```json
{
  "message": "帮我查一下蜀国的资产情况",
  "ouid": "shu",
  "puid": "liubei"
}
```

---

## 🛠 Tech Stack

| Layer | Choice |
|-------|--------|
| AI Framework | LangChain |
| LLM Backend | llama.cpp (AMD ROCm) |
| Embedding | BAAI/bge-large-zh-v1.5 |
| Vector DB | pgvector (PostgreSQL) |
| Backend | FastAPI |
| Frontend | Vue + Vite |
| Database | PostgreSQL 16 |

---

## 🚀 Quick Start

```bash
# 1. 安装依赖
cd backend
pip3 install --break-system-packages -r requirements.txt

# 2. 配置环境并初始化数据库
cp .env.example .env
PYTHONPATH=. python scripts/init_db.py

# 3. 启动后端
PYTHONPATH=. python -m uvicorn src.app:app --host 0.0.0.0 --port 8000

# 4. 启动前端 (另开终端)
cd ../frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

访问 `http://localhost:5173`

---

## 📂 Project Structure

```
ur-agent/
├── README.md                 # This file
├── backend/
│   ├── src/
│   │   ├── app.py            # FastAPI backend (REST API)
│   │   ├── agents/           # LangChain Agent
│   │   ├── tools/            # 资源/财务/知识/Seller 工具
│   │   ├── db/               # PostgreSQL + pgvector
│   │   ├── auth/             # JWT 认证
│   │   └── models/           # LLM 客户端与 DTO
│   ├── scripts/              # DB init + demo data
│   ├── data/                 # Seed data, no secrets
│   ├── requirements.txt
│   ├── profile.yaml          # Non-secret config
│   └── .env.example          # Placeholder secrets only
├── frontend/                 # Vue + Vite frontend (port 5173)
│   ├── src/
│   │   ├── api/              # API 调用层
│   │   ├── views/            # 页面视图
│   │   └── ...
│   └── package.json
├── docs/
│   ├── API.md                # REST API reference
│   └── ARCHITECTURE.md       # Architecture documentation
└── tests/
    ├── backend/              # API/unit smoke tests
    └── playwright/           # E2E recording tests
```

---

## 📊 Demo Data (Three Kingdoms)

| Context | Personnel | Party |
|---------|-----------|-------|
| 蜀国 (1) | 刘备、张飞、关羽、赵云、诸葛亮、诸葛瞻、黄月英 | 蜀汉集团(买家)、诸葛亮家(卖家) |
| 魏国 (2) | 曹操、司马懿 | 魏国朝廷(买家) |
| 吴国 (3) | 孙权、周瑜 | 东吴集团(买家) |

---

## 🔧 Database Management

Database connection and runtime settings are configured through `backend/profile.yaml` plus local environment variables or `backend/.env`.

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture, frontend-backend separation |
| [API.md](docs/API.md) | REST API reference |

---

## 🏗️ Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    UNI-RESOURCE AGENT                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Frontend (Vue+Vite)  Backend (FastAPI)    Database (PostgreSQL)│
│       port 5173           port 8000            port 5432        │
│           │                   │                    │            │
│           └──── HTTP ────────►│                    │            │
│                               │  SQL Queries ─────►│            │
│                               │                    │            │
│                           ┌───┴───┐               │            │
│                           ▼       ▼               │            │
│                       LangChain  pgvector        │            │
│                       (AI)       (Vector Search) │            │
└─────────────────────────────────────────────────────────────────┘
```
