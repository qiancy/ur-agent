# 🏗️ Uni-Resource Agent - 架构文档

> **版本**: 5.4  
> **更新日期**: 2026-08-05  
> **说明**: 退役 Gradio 前端，产品唯一前端入口为 web/ (Vue + Vite)

---

## 📋 目录

1. [架构概览](#架构概览)
2. [前后端分离设计](#前后端分离设计)
3. [组件职责划分](#组件职责划分)
4. [数据流向](#数据流向)
5. [端口与服务](#端口与服务)
6. [安全与认证](#安全与认证)

---

## 🏗️ 架构概览

### 三层架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    UNI-RESOURCE AGENT ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ╔═══════════════════════════════════════════════════════════════════╗  │
│   ║                    LAYER 3: PRESENTATION                          ║  │
│   ╠═══════════════════════════════════════════════════════════════════╣  │
│   ║   ┌────────────────────────────────────────────────────────────┐ ║  │
│   ║   │              VUE + VITE (Frontend)                         │ ║  │
│   ║   │   File: web/src/                                           │ ║  │
│   ║   │   Port: 5173                                               │ ║  │
│   ║   │   Role: User Interface Only                                │ ║  │
│   ║   │   Database: ❌ No direct access                             │ ║  │
│   ║   └────────────────────────────────────────────────────────────┘ ║  │
│   ╠═══════════════════════════════════════════════════════════════════╣  │
│   ║   HTTP/REST API (requests library)                               ║  │
│   ╠═══════════════════════════════════════════════════════════════════╣  │
│   ║   ┌────────────────────────────────────────────────────────────┐ ║  │
│   ║   │                 FASTAPI (Backend)                          │ ║  │
│   ║   │   File: src/app.py                                         │ ║  │
│   ║   │   Port: 8000                                               │ ║  │
│   ║   │   Role: Business Logic + API Layer                         │ ║  │
│   ║   │   Database: ✅ Direct access via src/db/database.py       │ ║  │
│   ║   └────────────────────────────────────────────────────────────┘ ║  │
│   ╠═══════════════════════════════════════════════════════════════════╣  │
│   ║   SQL Queries + LangChain Agent                                  ║  │
│   ╠═══════════════════════════════════════════════════════════════════╣  │
│   ║   ┌────────────────────────────────────────────────────────────┐ ║  │
│   ║   │              POSTGRESQL + pgvector (Database)              │ ║  │
│   ║   │   File: src/db/database.py                                 │ ║  │
│   ║   │   Port: 5432                                               │ ║  │
│   ║   │   Role: Data Persistence + Vector Search                   │ ║  │
│   ║   └────────────────────────────────────────────────────────────┘ ║  │
│   ╚═══════════════════════════════════════════════════════════════════╝  │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                    LangChain Agent (in Backend)                 │  │
│   │   File: src/agents/agent.py                                     │  │
│   │   Integration: llama.cpp (AMD ROCm)                             │  │
│   │   Purpose: AI reasoning with tool calls                         │  │
│   └─────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔀 前后端分离设计

### 为什么需要前后端分离？

| 优势 | 说明 |
|------|------|
| **安全隔离** | 数据库不直接暴露给前端用户 |
| **独立扩展** | 可以单独扩展前端或后端服务 |
| **API复用** | Backend可同时服务Web前端、移动端、脚本等 |
| **开发效率** | 前端和后端可以并行开发 |
| **技术栈灵活** | 可以独立选择和升级各层技术 |

### 前端实现细节

```typescript
// web/src/api/seller.ts - 前端 API 调用层 (Vue + TypeScript)
// 关键特点：
// 1. 使用 fetch 调用后端 API
// 2. 不包含任何数据库连接代码
// 3. 仅负责 UI 渲染和用户输入

const API_BASE = '/api'

export async function sellerSummary(token: string): Promise<SellerSummary> {
  const res = await fetch(`${API_BASE}/seller/summary`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error(res.statusText)
  return res.json()
}
```

**前端代码示例：**
```typescript
// web/src/views/GenericSpaceView.vue
// 从后端API获取空间数据，通过聚合接口一次加载
import { getSpaceDashboard } from '../api/spaces'

const load = async () => {
  const dashboard = await getSpaceDashboard()
  overview.value = dashboard.overview
  grouped.value = dashboard.resources
  persons.value = dashboard.persons
}
```

### 后端实现细节

```python
# src/app.py - FastAPI后端
# 关键特点：
# 1. 直接导入数据库操作函数
# 2. 提供REST API供前端调用
# 3. 处理业务逻辑和数据验证

from src.db.database import (
    query_resource, create_resource,
    query_person, create_person,
    query_party, create_party,
    create_transaction, get_transactions,
)

app = FastAPI(title="Uni-Resource Agent API", version="5.2.0")

@app.get("/personnel")
async def list_personnel(org_id: int = Query(...)):
    """REST API endpoint - 调用数据库函数"""
    return query_person(org_id)
```

---

## 📊 组件职责划分

### 完整组件列表

| 组件 | 文件路径 | 端口 | 职责 | 数据库访问 |
|------|----------|------|------|-----------|
| **Vue + Vite** | `web/src/` | 5173 | 用户界面、表单、交互 | ❌ 仅调用API |
| **FastAPI** | `src/app.py` | 8000 | REST API、业务逻辑 | ✅ 直接访问 |
| **Database** | `src/db/database.py` | 5432 | 数据持久化、ORM | ✅ 原生连接 |
| **LangChain Agent** | `src/agents/agent.py` | - | AI推理、工具调用 | ✅ 通过数据库 |
| **LLM Client** | `src/models/llm_client.py` | - | LLM接口封装 | - |
| **JWT Auth** | `src/auth/auth.py` | - | 身份验证 | ✅ 查询用户 |

### 职责矩阵

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        职责划分矩阵                                      │
├──────────────────────┬────────────────┬─────────────────┬───────────────┤
│ 功能                 │ Frontend       │ Backend         │ Database      │
├──────────────────────┼────────────────┼─────────────────┼───────────────┤
│ UI渲染               │ ✅ 主要负责     │ ❌              │ ❌            │
│ 用户输入处理         │ ✅ 主要负责     │ ✅ 验证         │ ❌            │
│ 业务逻辑             │ ❌              │ ✅ 主要负责      │ ❌            │
│ API接口              │ ✅ 调用        │ ✅ 提供        │ ❌            │
│ 数据验证             │ ✅ 基础验证    │ ✅ 严格验证     │ ❌            │
│ 数据持久化           │ ❌              │ ✅ 调用         │ ✅ 主要负责    │
│ 查询优化             │ ❌              │ ✅ SQL优化      │ ✅ 索引优化    │
│ 安全认证             │ ✅ Token管理   │ ✅ JWT验证      │ ✅ 用户验证    │
│ AI推理               │ ❌              │ ✅ Agent调用    │ ✅ 查询存储    │
└──────────────────────┴────────────────┴─────────────────┴───────────────┘
```

---

## 🔄 数据流向

### 完整请求流程

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         REQUEST FLOW                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   1. 用户操作UI                                                        │
│      └─► 用户点击按钮、填写表单                                         │
│                                                                         │
│   2. Frontend处理                                                      │
│      └─► web/src/                                                      │
│          • 验证用户输入                                                │
│          • 组织请求参数                                                │
│          • 调用后端API                                                 │
│                                                                         │
│   3. HTTP请求                                                          │
│      └─► requests.get/post("http://localhost:8000/api/endpoint")      │
│                                                                         │
│   4. Backend接收                                                       │
│      └─► src/app.py                                                    │
│          • FastAPI路由匹配                                             │
│          • Pydantic模型验证                                            │
│          • 调用数据库函数                                              │
│                                                                         │
│   5. Database执行                                                      │
│      └─► src/db/database.py                                            │
│          • psycopg2连接池                                              │
│          • SQL查询执行                                                 │
│          • 结果返回                                                    │
│                                                                         │
│   6. Backend响应                                                       │
│      └─► src/app.py                                                    │
│          • 格式化响应                                                  │
│          • JSON序列化                                                  │
│                                                                         │
│   7. Frontend接收                                                      │
│      └─► web/src/                                                      │
│          • fetch 接收响应                                              │
│          • JSON解析                                                    │
│          • UI更新                                                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 数据流图示

```
用户浏览器
    │
    │ ① 用户操作 (点击、输入)
    ▼
┌─────────────────┐
│  Vue + Vite     │  ← Frontend (port 5173)
│  (无数据库连接) │
└────────┬────────┘
         │ ② HTTP请求
         │    - URL: http://localhost:8000/api/endpoint
         │    - Method: GET/POST
         │    - Headers: JWT Token (if auth required)
         ▼
┌─────────────────┐
│  FastAPI        │  ← Backend (port 8000)
│  + LangChain    │
│  + Auth(JWT)    │
└────────┬────────┘
         │ ③ SQL查询
         │    - psycopg2连接
         │    - 参数化查询
         │    - 事务管理
         ▼
┌─────────────────┐
│  PostgreSQL     │  ← Database (port 5432)
│  + pgvector     │
└─────────────────┘
```

---

## 🔌 端口与服务

### 端口分配表

| 服务 | 端口 | 协议 | 启动命令 | 说明 |
|------|------|------|----------|------|
| **Vue + Vite** | 5173 | HTTP | `cd web && npm run dev -- --host 0.0.0.0 --port 5173` | 用户界面 |
| **FastAPI** | 8000 | HTTP | `uvicorn src.app:app --host 0.0.0.0 --port 8000` | API服务 |
| **PostgreSQL** | 5432 | TCP | `pg_ctl start` | 数据库 |
| **llama.cpp** | 8000 (default) | HTTP | `./main -m model.gguf` | LLM服务 |

### 启动脚本

```bash
# 启动后端
cd /workspace/research/unires-agent
PYTHONPATH=. uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload

# 启动前端 (另开终端)
cd /workspace/research/unires-agent/web
npm run dev -- --host 0.0.0.0 --port 5173

# 健康检查
curl http://localhost:8000/health
```

> 注意：前端已从 Gradio (port 7860) 迁移到 Vue + Vite (port 5173)。

---

## 🔐 安全与认证

### 安全架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           SECURITY LAYER                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                    Authentication Flow                          │  │
│   ├─────────────────────────────────────────────────────────────────┤  │
│   │   1. User Login                                                 │  │
│   │      → POST /login with username/password                      │  │
│   │                                                                  │  │
│   │   2. JWT Token Generated                                        │  │
│   │      → expires in 30 minutes                                    │  │
│   │                                                                  │  │
│   │   3. Token in Authorization Header                              │  │
│   │      → Authorization: Bearer <token>                            │  │
│   │                                                                  │  │
│   │   4. Backend Validates                                          │  │
│   │      → verify_token()                                           │  │
│   │                                                                  │  │
│   │   5. Request Proceeds                                           │  │
│   │      → User context available                                   │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                    Context Isolation                            │  │
│   ├─────────────────────────────────────────────────────────────────┤  │
│   │   • 每个组织数据独立隔离                                          │  │
│   │   • 数据库表带 ouid 字段                                           │  │
│   │   • 所有查询必须包含 ouid 过滤                                   │  │
│   │                                                                  │  │
│   │   SQL: SELECT * FROM organization WHERE id = $ouid              │  │
│   │   SQL: SELECT * FROM resource WHERE ouid = $ouid                 │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                    CORS Configuration                           │  │
│   ├─────────────────────────────────────────────────────────────────┤  │
│   │   # src/app.py:24-25                                            │  │
│   │   app.add_middleware(CORSMiddleware,                             │  │
│   │       allow_origins=["*"],  # 可配置为特定域名                  │  │
│   │       allow_credentials=True,                                    │  │
│   │       allow_methods=["*"],                                       │  │
│   │       allow_headers=["*"])                                       │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 认证代码示例

```python
# src/auth/auth.py
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta

# JWT配置
SECRET_KEY = os.getenv("SECRET_KEY", "uni-resource-agent-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def verify_token(token: str) -> dict:
    """验证JWT Token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="无效的认证令牌")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取当前用户"""
    token = credentials.credentials
    payload = verify_token(token)
    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    return user_id
```

---

## 📂 项目结构完整版

```
uni-resource-agent/
├── src/
│   ├── app.py                      # FastAPI Backend (port 8000)
│   ├── agents/
│   │   └── agent.py                # LangChain Agent
│   ├── tools/
│   │   ├── __init__.py             # ALL_TOOLS export
│   │   ├── resource_tools.py       # 资源查询/创建
│   │   ├── finance_tools.py        # 交易/摘要
│   │   ├── human_tools.py          # 人员/提醒
│   │   └── knowledge_tools.py      # RAG搜索
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py             # PostgreSQL操作
│   │   └── chroma_client.py        # ChromaDB向量搜索
│   ├── auth/
│   │   ├── __init__.py
│   │   └── auth.py                 # JWT认证
│   └── models/
│       ├── __init__.py
│       └── llm_client.py           # LLM客户端
├── web/                            # Vue + Vite 前端 (port 5173)
│   ├── src/
│   │   ├── api/                    # API 调用层
│   │   ├── views/                  # 页面视图
│   │   └── ...
│   └── package.json
├── scripts/
│   └── init_db.py                  # 数据库初始化
├── docs/
│   ├── API.md                      # REST API 文档
│   └── ARCHITECTURE.md             # 本文档
├── tests/                          # API 与 E2E 冒烟测试
└── README.md                       # 项目说明
```

---

## 📌 关键要点总结

### ✅ 正确实现的架构特点

| 特点 | 说明 |
|------|------|
| **清晰的层划分** | UI、API、DB各司其职 |
| **API优先设计** | FastAPI提供完整的REST API |
| **数据库隔离** | Frontend无法直接访问DB |
| **安全认证** | JWT + CORS配置 |
| **上下文隔离** | 通过ouid实现多租户 |
| **AI集成** | LangChain Agent在Backend层 |

### ⚠️ 注意事项

1. **CORS配置**: 当前允许所有源(`allow_origins=["*"]`)，生产环境应限制为特定域名
2. **Token过期**: JWT过期时间为30分钟，需实现刷新机制
3. **连接池**: 建议在`src/db/database.py`中实现连接池优化

---

## 🔗 相关文档

- [API文档](docs/API.md)
