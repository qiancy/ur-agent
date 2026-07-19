# AGENTS.md

> **Audience**: All AI Agents working on Uni-Resource Agent.
> **Purpose**: One source of truth for architecture, constraints, and progress.

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
- Data isolated by `context_id`
- Switch spaces, Agent adapts instantly

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
| Database | PostgreSQL (context_id isolation) |

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
├── _pm/                      # Project management
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
└── docs/
    └── 项目说明文档.md
```

---

## 🔧 Tool Function Signatures (Must Implement)

All tools use `@tool` decorator from LangChain.

```python
@tool
def query_asset(name: str, context_id: int, warehouse: Optional[str] = None) -> str

@tool
def transfer_asset(asset_id: str, from_context: int, to_context: int, quantity: int) -> str

@tool
def record_transaction(amount: float, category: str, description: str, context_id: int) -> str

@tool
def manage_reminder(action: str, person_name: str, task: str, due_date: Optional[str] = None) -> str

@tool
def rag_search(query: str, context_id: int) -> str
```

---

## 🗄️ Database Schema

All tables use `context_id` for multi-tenant isolation.

- `contexts` — id, name, type, owner_user_id
- `physical_assets` — id, context_id, name, type, quantity, status, lifecycle_log
- `virtual_assets` — id, context_id, name, content, embedding
- `personnel` — id, context_id, name, role, birth_date, health_reminders
- `transactions` — id, context_id, amount, category, description, transaction_date

## 🛠️ Database Configuration

The database is configured and running on PostgreSQL 16.14. For detailed configuration information, see the [PostgreSQL service documentation](/data/service/pg-unires/README.md).

---

## 🚨 Critical Constraints (Do Not Violate)

1. **Zero Cloud API (Production)** — Core inference for user data runs locally on AMD ROCm. No external model APIs for business logic.
2. **Privacy First** — No user data leaves the machine. Cloud APIs allowed for development only (code generation, no user data).
3. **Context Isolation** — Every DB query must include `context_id = current_context`.
4. **Quantized Model** — Must fit in <48GB VRAM (GGUF Q4_K_M, ~45GB).

---

## 📊 Current Progress

| Phase | Status | ETA |
| :--- | :--- | :--- |
| Infrastructure scripts | 🔴 Not started | 7/20 |
| Tool functions | 🔴 Not started | 7/25 |
| Agent + Backend | 🔴 Not started | 7/28 |
| AMD GPU verification | 🔴 Not started | 8/3 |
| Submission | 🔴 Not started | 8/6 |

Detailed tasks: [`_pm/进度跟踪.md`](_pm/进度跟踪.md)

---

## 🔗 Quick Links

- [Team分工](_pm/团队分工.md)
- [进度跟踪](_pm/进度跟踪.md)
- [质量检查](_pm/质量检查.md)
