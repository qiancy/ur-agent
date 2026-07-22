"""
Pydantic request/response models for Uni-Resource Agent API.
"""
from typing import Optional
from pydantic import BaseModel


# ── Organization ─────────────────────────────────────────────────────────────

class OrgCreate(BaseModel):
    name: str
    org_type: str
    oid: Optional[str] = None
    description: Optional[str] = None
    funds: Optional[float] = 0
    reputation: Optional[int] = 0


class MembershipAdd(BaseModel):
    pid: int
    oid: int
    role: Optional[str] = None


# ── Person ───────────────────────────────────────────────────────────────────

class PersonCreate(BaseModel):
    name: str
    birth_date: Optional[str] = None


# ── Resource ─────────────────────────────────────────────────────────────────

class ResourceCreate(BaseModel):
    oid: int
    name: str
    resource_type: str
    unit: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    pid: Optional[int] = None
    content: Optional[str] = None


class ResourceWarehouseCreate(BaseModel):
    resource_id: int
    location_path: str
    quantity: float
    unit: Optional[str] = None


# ── Warehouse ────────────────────────────────────────────────────────────────

class WarehouseCreate(BaseModel):
    oid: int
    name: str
    code: str
    location: Optional[str] = None
    description: Optional[str] = None


# ── Transaction ──────────────────────────────────────────────────────────────

class TransactionCreate(BaseModel):
    amount: float
    category: str
    description: Optional[str] = None


# ── Party ────────────────────────────────────────────────────────────────────

class PartyCreate(BaseModel):
    pid: int
    oid: int
    transaction_id: int
    role: str
    description: Optional[str] = None
    funds_change: Optional[float] = 0
    reputation_change: Optional[int] = 0


# ── Chat ─────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    oid: int = 1


# ── Auth ─────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    login: str  # {pid}@{oid}.cn
    password: str
    name: str
    role: Optional[str] = "member"


class LoginRequest(BaseModel):
    login: str  # {pid}@{oid}.cn
    password: str
