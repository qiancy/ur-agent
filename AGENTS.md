# AGENTS.md

> **Audience**: All AI Agents working on Uni-Resource Agent.
> **Purpose**: One source of truth for architecture, constraints, and progress.
> **Note**: This document is primarily in Chinese for the opencode agent.


---

## 🎯 Project at a Glance

| Attribute | Value |
| :--- | :--- |
| Name | Uni-Resource Agent |
| Slogan | "One AI. All Your Worlds." |
| Event | AMD AI Developer Hackathon 2026 |
| Deadline | 2026-08-06 23:59 UTC+8 |
| Repo | `uni-resource-agent` |
| License | MIT |

---

## 🧠 Core Concept

**"Everything is a Resource."**

Four resource types. One AI Agent. Multiple isolated spaces.

| Resource Type | Examples | Tool |
| :--- | :--- | :--- |
| Physical | Inventory, equipment, furniture | `query_asset`, `transfer_asset` |
| Knowledge | SOPs, manuals, policies | `rag_search` |
| Personnel | Family, employees, care | `manage_reminder`, `check_wellness` |
| Financial | Income, expenses, budgets | `record_transaction`, `get_summary` |

**Killer Feature**: Multi-Context Space (MCS)
- One user, multiple identities: `Zhang San @ Company / Home / Family / School`
- Data isolated by `oid` (organization) + `pid` (person) combination
- Switch spaces, Agent adapts instantly

**Context Format**: `context = {oid, pid}`
- `oid`: Organization ID - identifies the organization/space
- `pid`: Person ID - identifies the person/identity
- Example: `Zhang San @ Company` → `oid=1, pid=101`

---
## 🏠 Environment

This system is running in a Kubernetes pod environment with the following constraints:
- No access to Docker or Podman commands
- Database managed through PostgreSQL service at `/data/data-store/pg-unires`
- All data persistence handled via PVC (Persistent Volume Claim)
- Service management using custom scripts in `/data/service/pg-unires/bin/pgctl.sh`
- Database connection information available in `/data/service/pg-unires/README.md`

---

## 🛠️ Tech Stack (Fixed)

| Layer | Choice |
| :--- | :--- |
| AI Framework | LangChain |
| LLM Backend | llama.cpp (AMD ROCm) |
| Embedding | BAAI/bge-large-zh-v1.5 |
| Vector DB | ChromaDB |
| Backend | FastAPI + JWT |
| Frontend | Gradio |
| Database | PostgreSQL (context isolation via oid+pid) |

### Model Strategy (Development vs Production)

| 阶段 | 模型 | 用途 | 隐私 |
| :--- | :--- | :--- | :--- |
| **开发期** | GPT-5.5 / Big Pickle (云端) | 写代码、调试、架构设计 | 仅代码，无用户数据 |
| **生产期** | Qwen 30B / 80B (本地) | 处理用户数据、业务推理 | 数据不离开机器 |

**Production Models:**

| Model | Size | VRAM | Speed | Use Case |
| :--- | :--- | :--- | :--- | :--- |
| Qwen3-Coder-30B-A3B Q4_K_M | 18.6 GB | ~20 GB | ~20-30 tok/s | 日常业务推理 (主力) |
| Qwen3-Coder-Next 80B Q5_K_M | 56.7 GB | ~48 GB | ~4 tok/s | 复杂推理任务 (备选) |

---

## 📂 Project Structure

```
uni-resource-agent/
├── CLAUDE.md                 # ← You are here (redirect)
├── AGENTS.md                 # ← This file
├── README.md                 # Human-readable
├── LICENSE
├── agents/                   # ← Agent specifications (root level)
│   ├── DBA_AGENT.md          # PostgreSQL数据库管理规范
│   ├── TDD_AGENT.md          # 测试驱动开发规范
│   ├── dba/                  # 数据库管理相关文件
│   └── tdd/                  # 测试相关文件
│       ├── README.md
│       ├── test_three_kingdoms.py
│       ├── test_three_kingdoms_http.py
│       ├── test_fire_newye_api.py
│       ├── setup_fire_newye_campaign.py
│       └── 火烧新野战役故事文档.md
├── _pm/                      # Project management (NOT YET CREATED - see note below)
│   ├── 团队分工.md
│   ├── 进度跟踪.md
│   └── 质量检查.md
├── src/
│   ├── agents/agent.py       # LangChain Agent
│   ├── tools/
│   │   ├── asset_tools.py
│   │   ├── finance_tools.py
│   │   ├── human_tools.py
│   │   └── knowledge_tools.py
│   ├── models/llm_client.py  # AMD ROCm wrapper
│   ├── db/                   # PostgreSQL + ChromaDB
│   ├── auth/auth.py          # JWT
│   └── app.py                # Gradio entry
├── scripts/
│   ├── setup_env.sh
│   ├── init_db.py
│   └── download_models.py
├── data/
│   ├── init_data/            # 4 spaces JSON
│   └── knowledge/            # RAG documents
├── docs/
│   ├── API.md                # API documentation
│   └── (removed - moved to agents/DBA_AGENT.md)
└── tdd/                      # Test scripts (root level - deprecated)
    ├── test_three_kingdoms_http.py
    └── test_three_kingdoms.py
└── agents/
    └── tdd/                  # Test scripts (moved here)
        ├── TDD.md            # TDD规范文档
        ├── test_three_kingdoms_http.py
        └── test_three_kingdoms.py
```

---

## 🔧 Tool Function Signatures

All tools use `@tool` decorator from LangChain. Exported via `src.tools.ALL_TOOLS`.

```python
@tool
def query_asset(name: str, org_id: int, warehouse: Optional[str] = None) -> str

@tool
def transfer_asset(asset_id: int, from_org: int, to_org: int, quantity: int) -> str

@tool
def record_transaction(amount: float, category: str, description: str,
                       org_id: int, from_party: str, to_party: str) -> str

@tool
def get_transaction_history(org_id: int) -> str

@tool
def get_summary(org_id: int) -> str

@tool
def manage_reminder(action: str, person_name: str, task: str,
                    org_id: int, due_date: Optional[str] = None) -> str

@tool
def check_wellness(person_name: str, org_id: int) -> str

@tool
def rag_search(query: str, org_id: int) -> str

@tool
def store_knowledge(content: str, org_id: int, title: str) -> str
```

---

## 🗄️ Database Schema

> `org_id` 是程序运行时概念，不作为独立表。所有表带 `org_id` 做多租户隔离。

| Table | Description | Key Columns |
|-------|-------------|-------------|
| `organization` | 组织 (个人/家庭/公司) | id, name, type, description |
| `personnel` | 人员 | id, name, birth_date, health_reminders |
| `membership` | 人员↔组织 (多对多, 带角色) | person_id, org_id, role |
| `assets` | 资产基表 | id, org_id, name, type, status |
| `physical_assets` | 物理资产 (继承 assets) | id(FK→assets), quantity, warehouse |
| `virtual_assets` | 虚拟资产 (继承 assets) | id(FK→assets), content, embedding |
| `party` | 交易参与方 (属于组织) | id, org_id, name, role, description |
| `transactions` | 交易记录 | id, from_party_id, to_party_id, amount, category |

**ER 关系:**

```
organization ──→ membership ←── personnel
      │
      └──→ party ──→ transactions (from_party_id, to_party_id)

assets ─┬─ physical_assets
        └─ virtual_assets
```

## 🛠️ Database Configuration

PostgreSQL 16.14 + pgvector. Database: `unires`, User: `unires`, Password: `demo123`, Port: `5432`.
See [DBA_AGENT.md](agents/DBA_AGENT.md) for details.

## 🌐 REST API

Backend: FastAPI at `http://localhost:8000`. Full API docs: `README.md`.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | 健康检查 |
| GET | `/organizations?type=&name=` | 查询组织 |
| POST | `/organizations` | 创建组织 |
| GET | `/organizations/{id}/members` | 查看组织成员 |
| POST | `/organizations/members` | 添加组织成员 |
| GET | `/persons/{id}/organizations` | 查看人员所属组织 |
| GET | `/assets?org_id=&name=&warehouse=` | 查询资产 |
| POST | `/assets` | 创建资产 |
| POST | `/assets/transfer` | 资产调拨 |
| GET | `/personnel?org_id=&name=` | 查询人员 |
| POST | `/personnel` | 添加人员 |
| GET | `/party?org_id=&name=` | 查询参与方 |
| POST | `/party` | 创建参与方 |
| GET | `/transactions?org_id=&limit=` | 交易记录 |
| POST | `/transactions` | 记录交易 |
| GET | `/summary?org_id=` | 财务摘要 |
| POST | `/chat` | AI 对话 |

---

## 🚨 Critical Constraints (Do Not Violate)

1. **Zero Cloud API (Production)** — Core inference for user data runs locally on AMD ROCm. No external model APIs for business logic.
2. **Privacy First** — No user data leaves the machine. Cloud APIs allowed for development only (code generation, no user data).
3. **Context Isolation** — Every DB query must include `oid = current_oid` and `pid = current_pid` if applicable.
4. **Quantized Model** — Must fit in <48GB VRAM (GGUF Q4_K_M, ~45GB).

### Identity Field Rules (Critical)

- `pid` and `oid` are business identity fields, not database primary keys.
- `pid` identifies a person, for example `caocao`; `oid` identifies an organization, for example `wei`.
- `pid` and `oid` must be English-safe strings only: letters, numbers, underscore, and hyphen. No Chinese characters, spaces, `@`, `.`, or other special characters.
- `person.pid` and `organization.oid` must be unique in the database.
- Frontend must treat `pid` and `oid` as strings, never as numbers.
- `person.id` and `organization.id` are database auto-increment primary keys only. They are internal implementation details.
- JWT payload must contain only business identity fields `pid` and `oid` for identity/context. JWT must never contain `person_id`, `org_id`, `organization_id`, `person_pid`, or other database-ID-style identity fields.
- Tables other than `person` and `organization` should use `person_id` / `organization_id` for numeric foreign keys, not `pid` / `oid`.

---

## 📊 Current Progress

| Phase | Status | ETA |
| :--- | :--- | :--- |
| Infrastructure scripts | ✅ Done | 7/20 |
| Tool functions | ✅ Done | 7/25 |
| Agent + Backend | ✅ Done | 7/28 |
| TDD Test Scripts | ✅ Done | 7/21 |
| TDD Documentation | ✅ Done | 7/21 |
| **初始化API实现建议** | ✅ Done | 7/21 |
| **测试脚本更新** | ✅ Done | 7/21 |
| **测试计划文档更新** | ✅ Done | 7/21 |
| AMD GPU verification | 🔴 Not started | 8/3 |
| Submission | 🔴 Not started | 8/6 |

Detailed tasks: [`_pm/进度跟踪.md`](_pm/进度跟踪.md)

---

## 🧪 Testing (TDD)

### Test Documentation
- **TDD规范**：[`TDD.md`](agents/tdd/TDD.md)
- **测试用例**：[`agents/tdd/test_three_kingdoms_http.py`](agents/tdd/test_three_kingdoms_http.py)

### Test Principles
1. **Black-box testing** - No modification to `src/` code
2. **Context isolation** - Each test uses independent `oid` (organization) and `pid` (person) combination
3. **API-only operations** - All data access via HTTP API

### Test Coverage
| Module | Status |
|--------|--------|
| Organization API | ✅ 100% |
| Person API | ✅ 100% |
| Resource API | ✅ 100% |
| Warehouse API | ✅ 100% |
| Transaction API | ✅ 100% |
| Party API | ✅ 100% |
| Summary API | ✅ 100% |
| Chat API | ⚠️ Basic |

---

## 🔗 Quick Links

- [团队分工](_pm/团队分工.md)
- [进度跟踪](_pm/进度跟踪.md)
- [质量检查](_pm/质量检查.md)
- [DBA指南](agents/DBA_AGENT.md)
- [TDD指南](agents/tdd/TDD.md)
- [回归测试计划](agents/tdd/回归测试计划.md)
- [测试执行指南](agents/tdd/测试执行指南.md)
- [初始化API建议](agents/tdd/初始化API实现建议.md)

---

## 📝 Documentation Updates

| File | Status | Description |
|------|--------|-------------|
| `agents/tdd/TDD.md` | ✅ Updated | Added test case execution flow with manager review process |
| `AGENTS.md` | ✅ Updated | Added TDD section with test coverage and principles, updated links |
| `docs/ARCHITECTURE.md` | ✅ Created | Added comprehensive architecture documentation |
| `README.md` | ✅ Updated | Added documentation links and architecture summary |
| `agents/tdd/回归测试计划.md` | ✅ Updated | 回归测试计划文档，包含API依赖说明 |
| `agents/tdd/测试执行指南.md` | ✅ Created | 测试执行指南 |
| `agents/tdd/初始化API实现建议.md` | ✅ Created | 初始化API实现建议和API调用说明 |
| `agents/tdd/test_fire_newye_api.py` | ✅ Updated | 添加init-api命令和API调用逻辑 |

---

## 📌 Note on _pm/ Directory

The `_pm/` directory does not currently exist in this project. Project management documentation files should be created under this directory when needed:

- `团队分工.md` - Team分工 (Team Division)
- `进度跟踪.md` - Progress tracking
- `质量检查.md` - Quality check guidelines

---