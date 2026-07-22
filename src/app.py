"""
Uni-Resource Agent — FastAPI backend entry point (v5.3).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.logging_config import setup_logging

logger = setup_logging("api")

from src.routers import auth, organization, person, resource, warehouse, transaction, party, summary, chat

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


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
