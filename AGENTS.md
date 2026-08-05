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
- Data isolated by `ouid` (organization) + `puid` (person) combination
- Switch spaces, Agent adapts instantly

**Context Format**: `context = {ouid, puid}`
- `ouid`: Organization ID - identifies the organization/space
- `puid`: Person ID - identifies the person/identity
- Example: `Zhang San @ Company` → `ouid=company, puid=zhangsan`

### Product Positioning

**Primary target organization**: data-sensitive small and medium organizations whose resources are scattered and who do not have the budget, time, or process maturity for heavyweight ERP/OA systems.

Typical organizations include small companies, school labs, community groups, family businesses, care teams, project-based teams, and small ecommerce sellers. The most important buyer/user is the resource coordinator: admin, finance operator, warehouse keeper, office manager, family manager, or project owner.

**Pain points addressed**:
- Physical goods, personnel, knowledge documents, and transactions are scattered across spreadsheets, chat groups, paper records, and individual memory.
- One person may act in multiple spaces, such as company, family, school, and project, and data must not leak across contexts.
- Small organizations need lightweight query, record, transfer, reminder, and summary workflows instead of a full ERP stack.
- Privacy-sensitive assets, personnel, finance, and internal knowledge should remain local.
- AI must operate on real resources, not only answer as a chatbot.

**Product promise**: a local AI resource management assistant for small organizations that protects privacy, separates contexts, and turns natural language into concrete resource operations.

**MVP priority**: satisfy a real small-business inventory scenario first, such as a Taobao seller's warehouse with purchases, sales, stock locations, and basic cash flow. The Three Kingdoms "Fire at Xinye" campaign remains the best demo/regression scenario for showing timeline, camps, tasks, activities, supplies, and information/logistics/personnel flows.

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
| Frontend | Vue 3 + Vite + TS (`web/`) — 产品主界面; Gradio (`src/app.py`) 仅作内部调试/备份入口 |
| Database | PostgreSQL (context isolation via ouid+puid) |

### Frontend (Vue SPA) Notes

- `web/` 为产品主界面（Seller MVP 工作台），Gradio 保留为内部调试/备份入口。
- 登录：`POST /auth/seller-login` → JWT 存 `localStorage`；所有请求带 `Authorization: Bearer`。
- `web/` 依赖 Vite dev server proxy 或 CORS（后端已开 `allow_origins=["*"]`）直连 `:8000`。
- 测试：Vitest + jsdom（`npm test`），构建/类型检查：`npm run build`（vue-tsc + vite）。

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
│   ├── AGENT_ASSISTANT.md    # ← 项目经理助理 Agent
│   ├── AGENT_DBA.md          # ← 数据库管理 Agent
│   ├── AGENT_DEV.md          # ← 开发运维 Agent
│   ├── AGENT_PM.md           # ← 项目管理 Agent
│   ├── AGENT_SA.md           # ← 系统分析师 Agent
│   ├── AGENT_TDD.md          # ← 测试驱动开发 Agent
│   ├── dev/                  # ← dev agent 工作目录
│   │   └── AGENT_DEV.md      # ← 仓库 git 现状 & 发布流程文档
│   ├── pm/                   # ← 项目管理文档
│   │   ├── README.md
│   │   ├── 10_doc_团队分工_v1_20260721.md
│   │   ├── 9_doc_任务拆分_v1_20260721.md
│   │   └── ...
│   ├── sa/                   # ← 软件方法建模相关文件
│   │   ├── README.md
│   │   ├── 1_doc_软件方法书_v1_20260723.md
│   │   └── 4-modeling/
│   ├── tdd/                  # ← 测试驱动开发相关文件
│   │   ├── README.md
│   │   ├── 1_doc_火烧新野战役故事文档_v1_20260721.md
│   │   └── ...
│   ├── assistant/            # ← 助理 Agent 工作目录
│   │   └── inbox/
│   └── backend/   frontend/  # ← 开发产出物
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
│   └── API.md                # API documentation
├── AI-prompt/                # ← AI建模提示词
└── tests/                    # ← 可执行测试 (pytest)
    └── backend/
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
See [AGENT_DBA.md](agents/AGENT_DBA.md) for details.

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
3. **Context Isolation** — Every DB query must include `ouid = current_ouid` and `puid = current_puid` if applicable.
4. **Quantized Model** — Must fit in <48GB VRAM (GGUF Q4_K_M, ~45GB).

### Identity Field Rules (Critical)

- `puid` and `ouid` are business identity fields, not database primary keys.
- `puid` identifies a person, for example `caocao`; `ouid` identifies an organization, for example `wei`.
- `puid` and `ouid` must be English-safe strings only: letters, numbers, underscore, and hyphen. No Chinese characters, spaces, `@`, `.`, or other special characters.
- `person.puid` and `organization.ouid` must be unique in the database.
- Frontend must treat `puid` and `ouid` as strings, never as numbers.
- `person.id` and `organization.id` are database auto-increment primary keys only. They are internal implementation details.
- JWT payload must contain only business identity fields `puid` and `ouid` for identity/context. JWT must never contain `person_id`, `org_id`, `organization_id`, `person_puid`, or other database-ID-style identity fields.
- Tables other than `person` and `organization` should use `person_id` / `organization_id` for numeric foreign keys, not `puid` / `ouid`.

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
| **FE-06 Vue SPA Spike** | ✅ Done | 8/2 |
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
2. **Context isolation** - Each test uses independent `ouid` (organization) and `puid` (person) combination
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
- [DBA指南](agents/AGENT_DBA.md)
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
| `agents/sa/modeling/场景.md` | ✅ Added | 场景文档 |
| `agents/sa/modeling/改进方案.md` | ✅ Added | 业务流程改进方案 |
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
