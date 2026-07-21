"""
Uni-Resource Agent — FastAPI backend (v5.2).
"""
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
    return create_organization(body.name, body.org_type, body.description)

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
async def list_person(oid: int = Query(...), name: Optional[str] = None):
    return query_person(oid, name=name)

@app.post("/person", status_code=201)
async def add_person(body: PersonCreate):
    return create_person(body.name, body.birth_date)


# Resource
@app.get("/resource")
async def list_resource(oid: int = Query(...), name: Optional[str] = None,
                        resource_type: Optional[str] = None):
    return query_resource(oid, name=name, resource_type=resource_type)

@app.post("/resource", status_code=201)
async def add_resource(body: ResourceCreate):
    return create_resource(body.oid, body.name, body.resource_type,
                           body.unit, body.amount, body.currency,
                           body.pid, body.content)


# Warehouse
@app.get("/warehouse")
async def list_warehouse(oid: int = Query(...), name: Optional[str] = None):
    return query_warehouse(oid, name=name)

@app.post("/warehouse", status_code=201)
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
async def list_transaction(oid: int = Query(...), limit: int = Query(50, ge=1, le=200)):
    return get_transactions(oid, limit=limit)

@app.post("/transaction", status_code=201)
async def add_transaction(body: TransactionCreate):
    if body.amount <= 0:
        raise HTTPException(400, "Amount must be positive")
    return create_transaction(body.amount, body.category, body.description)


# Party
@app.get("/party")
async def list_party(oid: int = Query(...), pid: Optional[int] = None):
    return query_party(oid, pid=pid)

@app.get("/party/transaction/{transaction_id}")
async def list_party_by_transaction(transaction_id: int):
    return query_party_by_transaction(transaction_id)

@app.post("/party", status_code=201)
async def add_party(body: PartyCreate):
    return create_party(body.pid, body.oid, body.transaction_id,
                        body.role, body.description)


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


# Chat
@app.post("/chat")
async def chat(body: ChatRequest):
    try:
        from src.agents.agent import create_uni_resource_agent
        logger.info(f"Chat request: oid={body.oid}, message={body.message[:50]}...")
        agent = create_uni_resource_agent()
        result = agent.invoke({"input": body.message})
        logger.info(f"Chat response: {result['output'][:100]}...")
        return {"response": result["output"], "oid": body.oid}
    except Exception as e:
        logger.error(f"Agent error: {e}")
        raise HTTPException(500, f"Agent error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
