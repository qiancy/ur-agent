"""
Pydantic request/response models for Uni-Resource Agent API.

API-facing identifiers: puid (person) and ouid (organization) — string business keys.
"""
from typing import Optional
from pydantic import BaseModel


# ── Organization ─────────────────────────────────────────────────────────────

class OrgCreate(BaseModel):
    name: str
    org_type: str
    ouid: Optional[str] = None
    description: Optional[str] = None
    funds: Optional[float] = 0
    reputation: Optional[int] = 0


class MembershipAdd(BaseModel):
    puid: str
    ouid: str
    role: Optional[str] = "member"


# ── Person ───────────────────────────────────────────────────────────────────

class PersonCreate(BaseModel):
    name: str
    birth_date: Optional[str] = None


# ── Resource ─────────────────────────────────────────────────────────────────

class ResourceCreate(BaseModel):
    name: str
    resource_type: str
    ouid: Optional[str] = None  # ignored, org comes from JWT/query param
    unit: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    puid: Optional[str] = None
    content: Optional[str] = None


class ResourceWarehouseCreate(BaseModel):
    resource_id: int
    location_path: str
    quantity: float
    unit: Optional[str] = None


# ── Seller MVP ───────────────────────────────────────────────────────────────

class ProductCreate(BaseModel):
    name: str
    unit: Optional[str] = None
    spec: Optional[str] = None


class WarehouseCreateSeller(BaseModel):
    name: str
    code: str
    location: Optional[str] = None


class PurchaseInRequest(BaseModel):
    product_uid: str
    quantity: float
    location_path: str
    unit: Optional[str] = None
    total_amount: float
    supplier: Optional[str] = None


class SalesOutRequest(BaseModel):
    product_uid: str
    quantity: float
    location_path: str
    unit: Optional[str] = None
    total_amount: float
    customer: Optional[str] = None


class StockQuery(BaseModel):
    product_uid: Optional[str] = None


# ── Warehouse ────────────────────────────────────────────────────────────────

class WarehouseCreate(BaseModel):
    name: str
    code: str
    ouid: Optional[str] = None  # ignored, org comes from JWT/query param
    location: Optional[str] = None
    description: Optional[str] = None


# ── Transaction ──────────────────────────────────────────────────────────────

class TransactionCreate(BaseModel):
    amount: float
    category: str
    description: Optional[str] = None


# ── Party ────────────────────────────────────────────────────────────────────

class PartyCreate(BaseModel):
    transaction_id: int
    puid: Optional[str] = None  # ignored, person comes from JWT
    ouid: Optional[str] = None  # ignored, org comes from JWT/query param
    role: str
    description: Optional[str] = None
    funds_change: Optional[float] = 0
    reputation_change: Optional[int] = 0


# ── Chat ─────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str


# ── Auth ─────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    login: str  # {puid}@{ouid}.cn
    password: str
    name: str
    role: Optional[str] = "member"


class LoginRequest(BaseModel):
    login: str  # {puid}@{ouid}.cn
    password: str


# ── Campaign ─────────────────────────────────────────────────────────────────

class CampaignImportRequest(BaseModel):
    campaign_code: str
