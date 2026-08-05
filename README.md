# Uni-Resource Agent

> **"One AI. All Your Worlds."**
> **Everything is a Resource.**

Uni-Resource Agent is an AI assistant for unified resource management. It helps manage physical assets, people, transactions, and knowledge through one AI Agent.

---

## Product Positioning

Uni-Resource Agent primarily targets **data-sensitive small and medium-sized organizations with scattered resources and no capacity for heavyweight ERP systems**.

Typical users include small companies, schools or laboratories, community groups, family businesses, elder-care teams, project-based teams, and small ecommerce sellers. The core buyer is not a general employee, but the resource coordinator: an administrator, finance operator, warehouse keeper, office manager, family manager, or project owner.

### Problems We Solve

1. **Scattered resources**: Items, people, knowledge documents, and income or expense records are spread across spreadsheets, chat groups, paper records, and personal memory. Search, handover, and review become expensive.
2. **Mixed contexts**: The same person may belong to a company, family, project team, or school at the same time. Data from different identities must not be mixed.
3. **Heavy systems are too costly for small organizations**: ERP, OA, asset systems, knowledge bases, and finance systems are too heavy. Small organizations need lightweight workflows for asking, searching, recording, and acting.
4. **Privacy and local deployment requirements**: Personnel, finance, assets, and internal knowledge should not be uploaded to cloud AI services. The system should support local models, a local database, and a local knowledge base.
5. **AI should do more than chat**: Users need AI connected to real business resources, reliably handling asset queries, transaction records, reminders, and knowledge retrieval.

### Why It Matters

Users get:

- One entry point for items, knowledge, people, and finance.
- Natural-language queries, records, transfers, reminders, and summaries.
- Multi-Context Space isolation across companies, families, schools, projects, and other spaces.
- Local deployment so organizational data stays inside the organization.

Value proposition:

> A local, privacy-preserving AI assistant that helps small organizations manage real resources without heavyweight IT systems.

The MVP focuses first on **lightweight warehouse management for Taobao sellers**, covering purchases, sales, stock locations, and basic income and expense tracking. The **Fire at Xinye** scenario is used for demonstrations and regression tests, showing unified modeling of timelines, factions, tasks, activities, supplies, information flow, logistics flow, and personnel flow.

---

## Architecture

```text
+-----------------------------------------------------------------+
|                    UNI-RESOURCE AGENT                           |
+-----------------------------------------------------------------+
|                                                                 |
|   Frontend (Vue+Vite)  Backend (FastAPI)    Database (PostgreSQL)|
|       port 5173           port 8000            port 5432         |
|           |                   |                    |             |
|           +---- HTTP -------->|                    |             |
|                               |  SQL Queries ----->|             |
|                               |                    |             |
|                           +---+---+                |             |
|                           v       v                |             |
|                       LangChain  pgvector          |             |
|                       (AI)       (Vector Search)   |             |
+-----------------------------------------------------------------+
```

---

## Database Schema

### Context

`context` is a runtime concept built from two business identifiers:

| Identifier | Description | Purpose |
|------------|-------------|---------|
| `ouid` | Organization business identifier | Identifies the current organization or space, such as `shu` or `wei` |
| `puid` | Person business identifier | Identifies the current person or identity, such as `liubei` or `caocao` |

**`context = {ouid, puid}` means a "person@organization" context.**

Examples:

- `Zhang San @ Company` -> `ouid=company`, `puid=zhangsan`
- `Zhang San @ Home` -> `ouid=home`, `puid=zhangsan`
- `Li Si @ School` -> `ouid=school`, `puid=lisi`

Note: `ouid` and `puid` are business identifiers. Multi-tenant isolation is implemented internally through numeric foreign keys such as `person_id` and `organization_id`. The old `context_id` API parameter has been deprecated; APIs should use `ouid` + `puid`.

| Table | Description | Key Columns |
|-------|-------------|-------------|
| `resource` | Resource | id, organization_id, ouid, puid, name, type |
| `virtual_assets` | Virtual assets inherited from assets | id(FK to assets), content, embedding |
| `personnel` | Personnel | id, ouid, puid, name, role, birth_date, health_reminders |
| `party` | Transaction party | id, ouid, puid, name, role, description |
| `party_member` | Many-to-many mapping between personnel and parties | party_id, personnel_id, role |
| `transactions` | Transaction records | id, ouid, puid, from_party_id, to_party_id, amount, category |

**ER relationships:**

```text
assets --+-- physical_assets
         +-- virtual_assets

personnel <-- party_member --> party
                                |
                                +--> transactions (from_party_id, to_party_id)
```

---

## REST API

Base URL: `http://localhost:8000`

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |

### Assets

| Method | Path | Description |
|--------|------|-------------|
| GET | `/assets?ouid=shu&name=&warehouse=` | Query assets, with optional name and warehouse filters |
| POST | `/assets` | Create an asset |
| POST | `/assets/transfer` | Transfer assets across organizations |

**POST /assets**

```json
{
  "ouid": "shu",
  "puid": "liubei",
  "name": "Repeating Crossbow",
  "asset_type": "Weapon",
  "quantity": 50,
  "warehouse": "Armory"
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
| GET | `/personnel?ouid=shu&name=` | Query personnel |
| POST | `/personnel` | Add personnel |

**POST /personnel**

```json
{
  "ouid": "shu",
  "puid": "lisi",
  "name": "Zhuge Liang",
  "role": "Chancellor",
  "birth_date": "0181-04-23"
}
```

### Party

| Method | Path | Description |
|--------|------|-------------|
| GET | `/party?ouid=shu&name=` | Query parties |
| POST | `/party` | Create a party |
| GET | `/party/{id}/members` | View party members |
| POST | `/party/members` | Add party members |

**POST /party**

```json
{
  "ouid": "shu",
  "puid": "liubei",
  "name": "Shu Han Group",
  "role": "Buyer",
  "description": "Shu Han regime"
}
```

**POST /party/members**

```json
{
  "party_id": 1,
  "personnel_id": 2,
  "ouid": "shu",
  "puid": "liubei",
  "role": "Chancellor"
}
```

### Transactions

| Method | Path | Description |
|--------|------|-------------|
| GET | `/transactions?ouid=shu&limit=50` | Transaction records, including party names |
| POST | `/transactions` | Record a transaction |

**POST /transactions**

```json
{
  "ouid": "shu",
  "puid": "liubei",
  "from_party_id": 1,
  "to_party_id": 2,
  "amount": 1000.00,
  "category": "Military Funding",
  "description": "Shu Han Group funds Zhuge Liang's household"
}
```

### Summary

| Method | Path | Description |
|--------|------|-------------|
| GET | `/summary?ouid=shu` | Financial summary: inflow, outflow, and balance |

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

### Chat

| Method | Path | Description |
|--------|------|-------------|
| POST | `/chat` | AI chat powered by the LangChain Agent |

**POST /chat**

```json
{
  "message": "Show me the asset status for Shu.",
  "ouid": "shu",
  "puid": "liubei"
}
```

---

## Tech Stack

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

## Quick Start

```bash
# 1. Install dependencies
cd backend
pip3 install --break-system-packages -r requirements.txt

# 2. Configure environment and initialize the database
cp .env.example .env
PYTHONPATH=. python scripts/init_db.py

# 3. Start the backend
PYTHONPATH=. python -m uvicorn src.app:app --host 0.0.0.0 --port 8000

# 4. Start the frontend in another terminal
cd ../frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

Open `http://localhost:5173`.

---

## Project Structure

```text
ur-agent/
|-- README.md                 # This file
|-- backend/
|   |-- src/
|   |   |-- app.py            # FastAPI backend (REST API)
|   |   |-- agents/           # LangChain Agent
|   |   |-- tools/            # Resource, finance, knowledge, and Seller tools
|   |   |-- db/               # PostgreSQL + pgvector
|   |   |-- auth/             # JWT authentication
|   |   `-- models/           # LLM client and DTOs
|   |-- scripts/              # DB init and demo data
|   |-- data/                 # Seed data, no secrets
|   |-- requirements.txt
|   |-- profile.yaml          # Non-secret config
|   `-- .env.example          # Placeholder secrets only
|-- frontend/                 # Vue + Vite frontend (port 5173)
|   |-- src/
|   |   |-- api/              # API client layer
|   |   |-- views/            # Page views
|   |   `-- ...
|   `-- package.json
|-- docs/
|   |-- API.md                # REST API reference
|   `-- ARCHITECTURE.md       # Architecture documentation
`-- tests/
    |-- backend/              # API and unit smoke tests
    `-- playwright/           # E2E recording tests
```

---

## Demo Data (Three Kingdoms)

| Context | Personnel | Party |
|---------|-----------|-------|
| Shu (1) | Liu Bei, Zhang Fei, Guan Yu, Zhao Yun, Zhuge Liang, Zhuge Zhan, Huang Yueying | Shu Han Group (buyer), Zhuge Liang Household (seller) |
| Wei (2) | Cao Cao, Sima Yi | Wei Court (buyer) |
| Wu (3) | Sun Quan, Zhou Yu | Eastern Wu Group (buyer) |

---

## Database Management

Database connection and runtime settings are configured through `backend/profile.yaml` plus local environment variables or `backend/.env`.

---

## Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture and frontend-backend separation |
| [API.md](docs/API.md) | REST API reference |

---

## Architecture Summary

```text
+-----------------------------------------------------------------+
|                    UNI-RESOURCE AGENT                           |
+-----------------------------------------------------------------+
|                                                                 |
|   Frontend (Vue+Vite)  Backend (FastAPI)    Database (PostgreSQL)|
|       port 5173           port 8000            port 5432         |
|           |                   |                    |             |
|           +---- HTTP -------->|                    |             |
|                               |  SQL Queries ----->|             |
|                               |                    |             |
|                           +---+---+                |             |
|                           v       v                |             |
|                       LangChain  pgvector          |             |
|                       (AI)       (Vector Search)   |             |
+-----------------------------------------------------------------+
```
