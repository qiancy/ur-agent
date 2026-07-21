# Uni-Resource Agent

> **"One AI. All Your Worlds."**
> **万物皆资源**

统一资源管理 AI 助手 — 通过一个 AI Agent 管理物理资产、人员、交易和知识。

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    UNI-RESOURCE AGENT                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Frontend (Gradio)    Backend (FastAPI)    Database (PostgreSQL)│
│       port 7860           port 8000            port 5432        │
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

> `context_id` 是程序运行时概念，不作为独立表。

| Table | Description | Key Columns |
|-------|-------------|-------------|
| `assets` | 资产基表 | id, context_id, name, type, status |
| `physical_assets` | 物理资产 (继承 assets) | id(FK→assets), quantity, warehouse |
| `virtual_assets` | 虚拟资产 (继承 assets) | id(FK→assets), content, embedding |
| `personnel` | 人员 | id, context_id, name, role, birth_date, health_reminders |
| `party` | 交易参与方 | id, context_id, name, role, description |
| `party_member` | 人员↔参与方 (多对多) | party_id, personnel_id, role |
| `transactions` | 交易记录 | id, context_id, from_party_id, to_party_id, amount, category |

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
| GET | `/assets?context_id=1&name=&warehouse=` | 查询资产（支持按名称/仓库筛选） |
| POST | `/assets` | 创建资产 |
| POST | `/assets/transfer` | 跨 context 调拨资产 |

**POST /assets**
```json
{
  "context_id": 1,
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
  "from_context": 1,
  "to_context": 2,
  "quantity": 10
}
```

### Personnel

| Method | Path | Description |
|--------|------|-------------|
| GET | `/personnel?context_id=1&name=` | 查询人员 |
| POST | `/personnel` | 添加人员 |

**POST /personnel**
```json
{
  "context_id": 1,
  "name": "诸葛亮",
  "role": "丞相",
  "birth_date": "0181-04-23"
}
```

### Party (交易参与方)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/party?context_id=1&name=` | 查询参与方 |
| POST | `/party` | 创建参与方 |
| GET | `/party/{id}/members` | 查看成员 |
| POST | `/party/members` | 添加成员 |

**POST /party**
```json
{
  "context_id": 1,
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
  "role": "丞相"
}
```

### Transactions

| Method | Path | Description |
|--------|------|-------------|
| GET | `/transactions?context_id=1&limit=50` | 交易记录（含参与方名称） |
| POST | `/transactions` | 记录交易 |

**POST /transactions**
```json
{
  "context_id": 1,
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
| GET | `/summary?context_id=1` | 财务摘要（流入/流出/余额） |

**Response:**
```json
{
  "context_id": 1,
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
  "context_id": 1
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
| Frontend | Gradio |
| Database | PostgreSQL 16 |

---

## 🚀 Quick Start

```bash
# 1. 初始化数据库
PYTHONPATH=. python scripts/init_db.py

# 2. 启动后端
PYTHONPATH=. python -m uvicorn src.app:app --host 0.0.0.0 --port 8000

# 3. 启动前端
PYTHONPATH=. python src/frontend.py
```

---

## 📂 Project Structure

```
uni-resource-agent/
├── README.md                 # This file
├── AGENTS.md                 # Agent instructions
├── src/
│   ├── app.py                # FastAPI backend (REST API)
│   ├── frontend.py           # Gradio frontend
│   ├── agents/
│   │   └── agent.py          # LangChain Agent
│   ├── tools/
│   │   ├── __init__.py       # ALL_TOOLS export
│   │   ├── asset_tools.py    # query_asset, transfer_asset
│   │   ├── finance_tools.py  # record_transaction, get_summary
│   │   ├── human_tools.py    # manage_reminder, check_wellness
│   │   └── knowledge_tools.py# rag_search, store_knowledge
│   ├── db/
│   │   └── database.py       # PostgreSQL schema + CRUD
│   ├── auth/
│   │   └── auth.py           # JWT auth
│   └── models/
│       └── llm_client.py     # LLM wrapper
├── scripts/
│   └── init_db.py            # DB init + demo data
├── docs/
│   ├── DBA.md                # PostgreSQL DBA guide
│   └── ARCHITECTURE.md       # Architecture documentation
└── _pm/                      # Project management
    ├── 团队分工.md
    ├── 进度跟踪.md
    └── 质量检查.md
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

See [DBA.md](docs/DBA.md) for PostgreSQL management, pgvector setup, and service scripts.

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture, frontend-backend separation |
| [DBA.md](docs/DBA.md) | PostgreSQL database administration |
| [TDD.md](agents/tdd/TDD.md) | Test-driven development guide |

---

## 🏗️ Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    UNI-RESOURCE AGENT                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Frontend (Gradio)    Backend (FastAPI)    Database (PostgreSQL)│
│       port 7860           port 8000            port 5432        │
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
