"""
Uni-Resource Agent — FastAPI backend (v5.2).
"""
import asyncio
from typing import Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from src.logging_config import setup_logging

logger = setup_logging("api")

from src.db.database import (
    query_resource, create_resource,
    query_person, create_person, query_person_by_name,
    query_party, create_party, query_party_by_transaction,
    create_transaction, get_transactions,
    create_organization, query_organization,
    add_membership, get_org_members, get_person_memberships,
    create_warehouse, query_warehouse,
    create_resource_warehouse, query_resource_warehouse, get_resource_total,
)

app = FastAPI(title="Uni-Resource Agent API", version="5.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])


# ── Models ───────────────────────────────────────────────────────────────────

class OrgCreate(BaseModel):
    name: str
    org_type: str
    description: Optional[str] = None
    funds: Optional[float] = 0
    reputation: Optional[int] = 0

class ResourceCreate(BaseModel):
    oid: int
    name: str
    resource_type: str
    unit: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    pid: Optional[int] = None
    content: Optional[str] = None

class PersonCreate(BaseModel):
    name: str
    birth_date: Optional[str] = None

class MembershipAdd(BaseModel):
    pid: int
    oid: int
    role: Optional[str] = None

class WarehouseCreate(BaseModel):
    oid: int
    name: str
    code: str
    location: Optional[str] = None
    description: Optional[str] = None

class ResourceWarehouseCreate(BaseModel):
    resource_id: int
    location_path: str
    quantity: float
    unit: Optional[str] = None

class TransactionCreate(BaseModel):
    amount: float
    category: str
    description: Optional[str] = None

class PartyCreate(BaseModel):
    pid: int
    oid: int
    transaction_id: int
    role: str
    description: Optional[str] = None
    funds_change: Optional[float] = 0
    reputation_change: Optional[int] = 0

class ChatRequest(BaseModel):
    message: str
    oid: int = 1


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}


# Organization
@app.get("/organizations")
async def list_organizations(org_type: Optional[str] = None, name: Optional[str] = None):
    return query_organization(org_type=org_type, name=name)

@app.post("/organizations", status_code=201)
async def add_organization(body: OrgCreate):
    return create_organization(body.name, body.org_type, body.description,
                               body.funds, body.reputation)

@app.get("/organizations/{oid}/members")
async def list_org_members(oid: int):
    return get_org_members(oid)

@app.post("/organizations/members", status_code=201)
async def add_org_member(body: MembershipAdd):
    return add_membership(body.pid, body.oid, body.role)

@app.get("/persons/{pid}/organizations")
async def list_person_orgs(pid: int):
    return get_person_memberships(pid)


# Person
@app.get("/person")
@app.get("/personnel")
async def list_person(oid: int = Query(...), name: Optional[str] = None):
    return query_person(oid, name=name)

@app.post("/person", status_code=201)
@app.post("/personnel", status_code=201)
async def add_person(body: PersonCreate):
    return create_person(body.name, body.birth_date)


# Resource
@app.get("/resource")
@app.get("/assets")
async def list_resource(oid: int = Query(...), name: Optional[str] = None,
                        resource_type: Optional[str] = None):
    return query_resource(oid, name=name, resource_type=resource_type)

@app.post("/resource", status_code=201)
@app.post("/assets", status_code=201)
async def add_resource(body: ResourceCreate):
    return create_resource(body.oid, body.name, body.resource_type,
                           body.unit, body.amount, body.currency,
                           body.pid, body.content)


# Warehouse
@app.get("/warehouse")
@app.get("/warehouses")
async def list_warehouse(oid: int = Query(...), name: Optional[str] = None):
    return query_warehouse(oid, name=name)

@app.post("/warehouse", status_code=201)
@app.post("/warehouses", status_code=201)
async def add_warehouse(body: WarehouseCreate):
    return create_warehouse(body.oid, body.name, body.code,
                           body.location, body.description)


# ResourceWarehouse
@app.get("/resource-warehouse")
async def list_resource_warehouse(resource_id: int = Query(...),
                                   location_path: Optional[str] = None):
    return query_resource_warehouse(resource_id, location_path=location_path)

@app.post("/resource-warehouse", status_code=201)
async def add_resource_warehouse(body: ResourceWarehouseCreate):
    return create_resource_warehouse(body.resource_id, body.location_path,
                                     body.quantity, body.unit)

@app.get("/resource-warehouse/total")
async def get_total(resource_id: int = Query(...)):
    return get_resource_total(resource_id)


# Transaction
@app.get("/transaction")
@app.get("/transactions")
async def list_transaction(oid: int = Query(...), limit: int = 20):
    return get_transactions(oid, limit=limit)

@app.post("/transaction", status_code=201)
@app.post("/transactions", status_code=201)
async def add_transaction(body: TransactionCreate):
    return create_transaction(body.amount, body.category, body.description)


# Party
@app.get("/party")
async def list_party(oid: int = Query(...), pid: Optional[int] = None,
                     name: Optional[str] = None):
    return query_party(oid, pid=pid, name=name)

@app.get("/party/transaction/{transaction_id}")
async def list_party_by_transaction(transaction_id: int):
    return query_party_by_transaction(transaction_id)

@app.post("/party", status_code=201)
async def add_party(body: PartyCreate):
    return create_party(body.pid, body.oid, body.transaction_id,
                        body.role, body.description,
                        body.funds_change, body.reputation_change)


# Summary
@app.get("/summary")
async def get_summary(oid: int = Query(...)):
    from src.db.database import _fetch

    org_rows = _fetch("SELECT funds, reputation FROM organization WHERE id = %s", (oid,))
    if not org_rows:
        return {
            "oid": oid,
            "funds": 0.0,
            "reputation": 0,
            "total_outflow": 0.0,
            "transaction_count": 0,
        }
    org = org_rows[0]

    outflow_rows = _fetch(
        "SELECT COALESCE(SUM(t.amount), 0) AS total "
        "FROM transaction t "
        "JOIN party p ON p.transaction_id = t.id "
        "WHERE p.oid = %s AND p.role = 'payer'", (oid,))
    total_outflow = float(outflow_rows[0]["total"])

    count_rows = _fetch(
        "SELECT COUNT(DISTINCT t.id) AS cnt "
        "FROM transaction t "
        "JOIN party p ON p.transaction_id = t.id "
        "WHERE p.oid = %s", (oid,))

    return {
        "oid": oid,
        "funds": float(org["funds"]),
        "reputation": org["reputation"],
        "total_outflow": total_outflow,
        "transaction_count": count_rows[0]["cnt"],
    }


IDENTITY_MESSAGES = {"我是谁", "我是谁？", "我是谁?", "你是谁", "你是谁？", "你是谁?", "当前空间", "当前组织"}


def _get_org_context(oid: int) -> dict:
    rows = query_organization(oid=oid)
    if not rows:
        return {"id": oid, "name": f"组织 {oid}", "type": "unknown"}
    org = rows[0]
    return {"id": org["id"], "name": org["name"], "type": org["type"]}


# Chat
@app.post("/chat")
async def chat(body: ChatRequest):
    try:
        message = body.message.strip()
        org = _get_org_context(body.oid)
        logger.info("Chat request: oid=%s, org=%s, message=%s", body.oid, org["name"], message[:100])

        if message in IDENTITY_MESSAGES:
            response = f"你当前在{org['name']}空间，组织 ID 为 {org['id']}。我是 Uni-Resource Agent，可以帮你管理该空间的资源、人员、交易和知识。"
            logger.info("Chat fast-path response: %s", response)
            return {"response": response, "oid": body.oid}

        agent_input = (
            f"当前组织空间: {org['name']}，组织类型: {org['type']}，oid: {org['id']}。\n"
            "调用任何工具时必须使用这个 oid，不要使用默认 oid。\n"
            "如果问题是闲聊或身份确认，直接回答，不要调用工具。\n"
            f"用户问题: {message}"
        )

        def _run_agent():
            from src.agents.agent import create_uni_resource_agent
            from langchain.agents import AgentExecutor
            from src.tools import ALL_TOOLS
            agent = create_uni_resource_agent()
            agent_executor = AgentExecutor(
                agent=agent,
                tools=ALL_TOOLS,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=4,
                return_intermediate_steps=True,
            )
            return agent_executor.invoke({"input": agent_input})

        result = await asyncio.wait_for(
            asyncio.to_thread(_run_agent), timeout=30
        )
        steps = result.get("intermediate_steps", [])
        if steps:
            logger.info("Chat intermediate steps: %s", steps)
        logger.info("Chat response: %s", result.get('output', '')[:500])
        return {"response": result.get('output', ''), "oid": body.oid}
    except asyncio.TimeoutError:
        logger.error("Chat request timed out (30s)")
        raise HTTPException(504, "AI agent timed out. Is the LLM server running?")
    except Exception as e:
        logger.exception("Agent error")
        raise HTTPException(500, f"Agent error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
