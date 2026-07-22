"""
Uni-Resource Agent — FastAPI backend entry point (v5.3).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.logging_config import setup_logging
from src.db.database import (
    init_database, create_organization, create_person, create_account, add_membership,
    query_organization_by_oid, query_person_by_pid, query_account_by_login, query_membership,
)
from src.auth.auth import hash_password

logger = setup_logging("api")

from src.routers import auth, organization, person, resource, warehouse, transaction, party, summary, chat, campaign

app = FastAPI(title="Uni-Resource Agent API", version="5.3.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

app.include_router(auth.router)
app.include_router(organization.router)
app.include_router(person.router)
app.include_router(resource.router)
app.include_router(warehouse.router)
app.include_router(transaction.router)
app.include_router(party.router)
app.include_router(summary.router)
app.include_router(chat.router)
app.include_router(campaign.router)


def ensure_default_super():
    orgs = query_organization_by_oid("system")
    if orgs:
        org = orgs[0]
    else:
        org = create_organization("系统空间", "system", "系统全局管理空间", 0, 0, oid="system")

    persons = query_person_by_pid("super")
    if persons:
        person = persons[0]
    else:
        person = create_person("超级用户", pid="super")

    accounts = query_account_by_login("super@system.cn")
    if not accounts:
        password, salt = hash_password("demo123")
        create_account(person["id"], "super@system.cn", password, salt, system_role="super")

    if not query_membership(person["id"], org["id"]):
        add_membership(person["id"], org["id"], "admin")


@app.on_event("startup")
async def ensure_schema_and_super():
    init_database(drop_all=False)
    ensure_default_super()


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
