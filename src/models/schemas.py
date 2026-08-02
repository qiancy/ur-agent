"""
Pydantic request/response models for Uni-Resource Agent API.

API-facing identifiers: puid (person) and ouid (organization) — string business keys.
"""
from typing import Optional
from pydantic import BaseModel, Field


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
    warehouse_code: Optional[str] = None  # resolved to org's first warehouse if omitted
    location_path: str
    quantity: float
    unit: Optional[str] = None
    model_config = {"extra": "forbid"}


# ── Seller MVP ───────────────────────────────────────────────────────────────

class SellerPurchaseIn(BaseModel):
    product_uid: str
    warehouse_code: str
    location_path: str
    quantity: float = Field(gt=0)
    unit: str = "件"
    total_amount: float = Field(ge=0)
    counterparty_name: str
    model_config = {"extra": "forbid"}


class SellerSalesOut(BaseModel):
    product_uid: str
    warehouse_code: str
    location_path: str
    quantity: float = Field(gt=0)
    unit: str = "件"
    total_amount: float = Field(ge=0)
    counterparty_name: str
    model_config = {"extra": "forbid"}


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
    transaction_uid: str
    puid: Optional[str] = None  # person identity; ignored when Bearer token present
    ouid: Optional[str] = None  # org identity; ignored when Bearer token present
    role: str
    description: Optional[str] = None
    funds_change: Optional[float] = 0
    reputation_change: Optional[int] = 0


# ── Chat ─────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str


class SellerChatRequest(BaseModel):
    message: str
    model_config = {"extra": "forbid"}


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
