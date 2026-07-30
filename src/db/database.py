# -*- coding: utf-8 -*-
"""
Database module for Uni-Resource Agent.

Tables (v5.3):
  - organization: 组织 (个人/家庭/公司/等) + funds, reputation
  - person: 人员 (纯个人信息)
  - account: 认证凭据 (login, password, salt, status, system_role)
  - membership: 人员↔组织 (多对多, 带角色)
  - resource: 资源 (单表, type 区分 physical/financial/human/knowledge)
  - warehouse: 仓库
  - resource_warehouse: 资源-仓库明细 (location_path + quantity + unit)
  - transaction: 交易事务 (纯事件)
  - party: 交易参与方 (同生同死于 transaction, 记录 funds_change, reputation_change)

Naming:
- puid, ouid: business identifiers (VARCHAR), unique strings (e.g. "zhangsan", "wei")
- person_id, organization_id: database primary keys (SERIAL), internal integers
- JWT payload: uses puid, ouid, system_role, role; NOT person_id, organization_id
"""

from typing import Optional, List, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from src.logging_config import get_logger

logger = get_logger("db")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "unires"),
    "user": os.getenv("DB_USER", "unires"),
    "password": os.getenv("DB_PASSWORD", "demo123"),
    "port": os.getenv("DB_PORT", "5432"),
}


def get_db_connection():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        raise Exception(f"Database connection failed: {e}")


# ---------------------------------------------------------------------------
# Schema DDL
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
-- Organization: 组织 (个人/家庭/公司/等) + 资金, 名望
CREATE TABLE IF NOT EXISTS organization (
    id          SERIAL PRIMARY KEY,
    ouid        VARCHAR(100) UNIQUE NOT NULL CHECK (ouid ~ '^[A-Za-z0-9_-]+$'),
    name        VARCHAR(255) NOT NULL,
    type        VARCHAR(100) NOT NULL,
    description TEXT,
    funds       DECIMAL(15,2) DEFAULT 0,
    reputation  INTEGER DEFAULT 0,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Person: 人员 (纯个人信息, 无 ouid)
CREATE TABLE IF NOT EXISTS person (
    id               SERIAL PRIMARY KEY,
    puid             VARCHAR(100) UNIQUE NOT NULL CHECK (puid ~ '^[A-Za-z0-9_-]+$'),
    name             VARCHAR(255) NOT NULL,
    birth_date       DATE,
    health_reminders JSONB,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Account: 认证凭据 (password stores the password hash)
CREATE TABLE IF NOT EXISTS account (
    id          SERIAL PRIMARY KEY,
    person_id   INTEGER NOT NULL REFERENCES person(id) ON DELETE CASCADE,
    login       VARCHAR(150) UNIQUE NOT NULL,
    password    TEXT NOT NULL,
    salt        TEXT,
    status      VARCHAR(30) NOT NULL DEFAULT 'active',
    system_role VARCHAR(30) NOT NULL DEFAULT 'user',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Membership: 人员↔组织 (多对多, 带角色)
CREATE TABLE IF NOT EXISTS membership (
    id              SERIAL PRIMARY KEY,
    person_id       INTEGER NOT NULL REFERENCES person(id) ON DELETE CASCADE,
    organization_id INTEGER NOT NULL REFERENCES organization(id) ON DELETE CASCADE,
    role            VARCHAR(100),
    joined_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(person_id, organization_id)
);

-- Resource: 资源 (单表设计, type 区分 physical/financial/human/knowledge)
CREATE TABLE IF NOT EXISTS resource (
    id              SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organization(id) ON DELETE CASCADE,
    name            VARCHAR(255) NOT NULL,
    type            VARCHAR(100) NOT NULL,
    status          VARCHAR(50) DEFAULT 'active',
    unit            VARCHAR(50),
    amount          DECIMAL(15,2),
    currency        VARCHAR(20),
    person_id       INTEGER REFERENCES person(id),
    content         TEXT,
    embedding       TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_resource_org_name UNIQUE (organization_id, name)
);

-- Warehouse: 仓库
CREATE TABLE IF NOT EXISTS warehouse (
    id              SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organization(id) ON DELETE CASCADE,
    name            VARCHAR(255) NOT NULL,
    code            VARCHAR(50) NOT NULL,
    location        VARCHAR(255),
    description     TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(organization_id, code)
);

-- ResourceWarehouse: 资源-仓库明细
CREATE TABLE IF NOT EXISTS resource_warehouse (
    id              SERIAL PRIMARY KEY,
    resource_id     INTEGER NOT NULL REFERENCES resource(id) ON DELETE CASCADE,
    location_path   VARCHAR(255) NOT NULL,
    quantity        DECIMAL(15,2) NOT NULL DEFAULT 0,
    unit            VARCHAR(50),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(resource_id, location_path)
);

-- Transaction: 交易事务
CREATE TABLE IF NOT EXISTS transaction (
    id              SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organization(id) ON DELETE CASCADE,
    amount          DECIMAL(15,2) NOT NULL,
    category        VARCHAR(100) NOT NULL,
    description     TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Party: 交易参与方
CREATE TABLE IF NOT EXISTS party (
    id                  SERIAL PRIMARY KEY,
    person_id           INTEGER NOT NULL REFERENCES person(id),
    organization_id     INTEGER NOT NULL REFERENCES organization(id),
    transaction_id      INTEGER NOT NULL REFERENCES transaction(id) ON DELETE CASCADE,
    role                VARCHAR(100) NOT NULL,
    description         TEXT,
    funds_change        DECIMAL(15,2) DEFAULT 0,
    reputation_change   INTEGER DEFAULT 0,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Campaign import batch metadata
CREATE TABLE IF NOT EXISTS campaign_import (
    id              SERIAL PRIMARY KEY,
    campaign_code   VARCHAR(100) NOT NULL,
    campaign_name   VARCHAR(255) NOT NULL,
    source_file     VARCHAR(255),
    imported_by_puid VARCHAR(100) NOT NULL,
    status          VARCHAR(30) NOT NULL DEFAULT 'active',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at      TIMESTAMP
);

CREATE TABLE IF NOT EXISTS campaign_import_org (
    id                  SERIAL PRIMARY KEY,
    campaign_import_id  INTEGER NOT NULL REFERENCES campaign_import(id) ON DELETE CASCADE,
    organization_id     INTEGER NOT NULL REFERENCES organization(id) ON DELETE CASCADE,
    created_by_import   BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE(campaign_import_id, organization_id)
);

CREATE TABLE IF NOT EXISTS campaign_event (
    id                  SERIAL PRIMARY KEY,
    campaign_import_id  INTEGER NOT NULL REFERENCES campaign_import(id) ON DELETE CASCADE,
    organization_id     INTEGER NOT NULL REFERENCES organization(id) ON DELETE CASCADE,
    seq                 INTEGER NOT NULL,
    title               VARCHAR(255) NOT NULL,
    description         TEXT,
    payload             JSONB,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(campaign_import_id, organization_id, seq)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_membership_person ON membership(person_id);
CREATE INDEX IF NOT EXISTS idx_membership_org ON membership(organization_id);
CREATE INDEX IF NOT EXISTS idx_account_person ON account(person_id);
CREATE INDEX IF NOT EXISTS idx_account_login ON account(login);
CREATE INDEX IF NOT EXISTS idx_account_system_role ON account(system_role);
CREATE INDEX IF NOT EXISTS idx_campaign_import_status ON campaign_import(status);
CREATE INDEX IF NOT EXISTS idx_campaign_event_import ON campaign_event(campaign_import_id);
CREATE INDEX IF NOT EXISTS idx_campaign_event_org ON campaign_event(organization_id);
CREATE INDEX IF NOT EXISTS idx_resource_org ON resource(organization_id);
CREATE INDEX IF NOT EXISTS idx_resource_type ON resource(type);
CREATE INDEX IF NOT EXISTS idx_warehouse_org ON warehouse(organization_id);
CREATE INDEX IF NOT EXISTS idx_rw_resource ON resource_warehouse(resource_id);
CREATE INDEX IF NOT EXISTS idx_rw_location ON resource_warehouse(location_path);
CREATE INDEX IF NOT EXISTS idx_party_person ON party(person_id);
CREATE INDEX IF NOT EXISTS idx_party_org ON party(organization_id);
CREATE INDEX IF NOT EXISTS idx_party_transaction ON party(transaction_id);
"""


def init_database(drop_all: bool = False):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        if drop_all:
            cur.execute("""
                DROP TABLE IF EXISTS campaign_event CASCADE;
                DROP TABLE IF EXISTS campaign_import_org CASCADE;
                DROP TABLE IF EXISTS campaign_import CASCADE;
                DROP TABLE IF EXISTS party CASCADE;
                DROP TABLE IF EXISTS transaction CASCADE;
                DROP TABLE IF EXISTS resource_warehouse CASCADE;
                DROP TABLE IF EXISTS warehouse CASCADE;
                DROP TABLE IF EXISTS resource CASCADE;
                DROP TABLE IF EXISTS membership CASCADE;
                DROP TABLE IF EXISTS account CASCADE;
                DROP TABLE IF EXISTS person CASCADE;
                DROP TABLE IF EXISTS organization CASCADE;
                DROP TABLE IF EXISTS virtual_assets CASCADE;
                DROP TABLE IF EXISTS physical_assets CASCADE;
                DROP TABLE IF EXISTS assets CASCADE;
                DROP TABLE IF EXISTS transactions CASCADE;
                DROP TABLE IF EXISTS personnel CASCADE;
                DROP TABLE IF EXISTS person_org CASCADE;
                DROP TABLE IF EXISTS party_member CASCADE;
            """)
        cur.execute(SCHEMA_SQL)
        conn.commit()
        logger.info("Database initialized successfully")
    except Exception as e:
        conn.rollback()
        logger.error("Database init failed: %s", e)
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# CRUD helpers
# ---------------------------------------------------------------------------

def _fetch(sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def _execute(sql: str, params: tuple = (), fetch_returning: bool = False) -> Any:
    conn = get_db_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(sql, params)
        if fetch_returning:
            result = [dict(row) for row in cur.fetchall()]
            conn.commit()
            return result
        conn.commit()
        return cur.rowcount
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


# --- Organization ---

def create_organization(name: str, org_type: str,
                        description: str = None, funds: float = 0,
                        reputation: int = 0, ouid: str = None) -> Dict[str, Any]:
    import secrets as _secrets
    import re as _re
    if ouid is None:
        safe_name = _re.sub(r'[^a-zA-Z0-9]', '_', name).strip('_').lower()
        ouid = f"org_{safe_name}_{_secrets.token_hex(4)}"
    sql = """
        INSERT INTO organization (ouid, name, type, description, funds, reputation)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING *
    """
    return dict(_execute(sql, (ouid, name, org_type, description, funds, reputation),
                         fetch_returning=True)[0])


def query_organization(org_id: int = None, name: str = None,
                       org_type: str = None) -> List[Dict]:
    sql = "SELECT * FROM organization WHERE 1=1"
    params: list = []
    if org_id:
        sql += " AND id = %s"
        params.append(org_id)
    if name:
        sql += " AND name ILIKE %s"
        params.append(f"%{name}%")
    if org_type:
        sql += " AND type = %s"
        params.append(org_type)
    return _fetch(sql, tuple(params))


# --- Person ---

def create_person(name: str, birth_date: str = None, puid: str = None) -> Dict[str, Any]:
    import secrets as _secrets
    import re as _re
    if puid is None:
        safe_name = _re.sub(r'[^a-zA-Z0-9]', '_', name).strip('_').lower()
        puid = f"person_{safe_name}_{_secrets.token_hex(4)}"
    sql = """
        INSERT INTO person (puid, name, birth_date)
        VALUES (%s, %s, %s)
        RETURNING *
    """
    return dict(_execute(sql, (puid, name, birth_date),
                         fetch_returning=True)[0])


def query_person_by_name(name: str) -> List[Dict]:
    """Find person by name (global, not org-scoped)."""
    sql = "SELECT * FROM person WHERE name ILIKE %s"
    return _fetch(sql, (f"%{name}%",))


def query_person_by_puid(puid: str) -> List[Dict]:
    """Find person by puid (unique identifier)."""
    sql = "SELECT * FROM person WHERE puid = %s"
    return _fetch(sql, (puid,))


# --- Account ---

def create_account(person_id: int, login: str, password: str,
                   salt: str = None, system_role: str = "user") -> Dict[str, Any]:
    sql = """
        INSERT INTO account (person_id, login, password, salt, system_role)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING *
    """
    return dict(_execute(sql, (person_id, login, password, salt, system_role),
                         fetch_returning=True)[0])


def query_account_by_login(login: str) -> List[Dict]:
    """Find account by login name."""
    sql = "SELECT * FROM account WHERE login = %s"
    return _fetch(sql, (login,))


def query_accounts_by_person_id(person_id: int) -> List[Dict]:
    """Find all accounts for a person."""
    sql = "SELECT * FROM account WHERE person_id = %s ORDER BY id"
    return _fetch(sql, (person_id,))


def update_account_password(person_id: int, password: str,
                            salt: str = None) -> int:
    sql = "UPDATE account SET password = %s, salt = %s, updated_at = CURRENT_TIMESTAMP WHERE person_id = %s"
    return _execute(sql, (password, salt, person_id))


def query_organization_by_ouid(ouid: str) -> List[Dict]:
    """Find organization by ouid (unique identifier)."""
    sql = "SELECT * FROM organization WHERE ouid = %s"
    return _fetch(sql, (ouid,))


def resolve_organization_id(ouid: Any) -> int:
    """Resolve API-facing organization ouid to internal organization.id."""
    if ouid is None:
        raise ValueError("ouid is required")
    orgs = query_organization_by_ouid(str(ouid))
    if orgs:
        return orgs[0]["id"]
    raise ValueError(f"Organization not found: {ouid}")


def query_membership(person_id: int, org_id: int) -> List[Dict]:
    """Find membership by person_id and org_id."""
    sql = "SELECT * FROM membership WHERE person_id = %s AND organization_id = %s"
    return _fetch(sql, (person_id, org_id))


def query_person(organization_id: int, name: str = None) -> List[Dict]:
    """Find people in an org via membership."""
    sql = """
        SELECT p.*, m.role AS membership_role
        FROM person p
        JOIN membership m ON m.person_id = p.id
        WHERE m.organization_id = %s
    """
    params: list = [organization_id]
    if name:
        sql += " AND p.name ILIKE %s"
        params.append(f"%{name}%")
    sql += " ORDER BY p.name"
    return _fetch(sql, tuple(params))


# --- Membership ---

def add_membership(person_id: int, organization_id: int, role: str = None) -> Dict[str, Any]:
    sql = """
        INSERT INTO membership (person_id, organization_id, role)
        VALUES (%s, %s, %s)
        RETURNING *
    """
    return dict(_execute(sql, (person_id, organization_id, role), fetch_returning=True)[0])


def get_org_members(organization_id: int) -> List[Dict]:
    sql = """
        SELECT m.id, m.role, p.name, p.puid
        FROM membership m
        JOIN person p ON p.id = m.person_id
        WHERE m.organization_id = %s
    """
    return _fetch(sql, (organization_id,))


def get_person_memberships(person_id: int) -> List[Dict]:
    sql = """
        SELECT m.id, m.role, o.name, o.ouid, o.type AS org_type
        FROM membership m
        JOIN organization o ON o.id = m.organization_id
        WHERE m.person_id = %s
    """
    return _fetch(sql, (person_id,))


# --- Resource ---

def create_resource(organization_id: int, name: str, resource_type: str,
                    unit: str = None, amount: float = None,
                    currency: str = None, person_id: int = None,
                    content: str = None) -> Dict[str, Any]:
    sql = """
        INSERT INTO resource (organization_id, name, type, unit, amount, currency, person_id, content)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *
    """
    return dict(_execute(sql, (organization_id, name, resource_type, unit, amount, currency, person_id, content),
                           fetch_returning=True)[0])


def query_resource(organization_id: int, name: str = None,
                   resource_type: str = None) -> List[Dict]:
    sql = """
        SELECT r.*, p.name AS person_name
        FROM resource r
        LEFT JOIN person p ON p.id = r.person_id
        WHERE r.organization_id = %s AND r.status = 'active'
    """
    params: list = [organization_id]
    if name:
        sql += " AND r.name ILIKE %s"
        params.append(f"%{name}%")
    if resource_type:
        sql += " AND r.type = %s"
        params.append(resource_type)
    return _fetch(sql, tuple(params))


def resolve_product_uid(org_id: int, product_uid: str) -> int:
    """Resolve seller product business UID to internal resource.id within an org."""
    rows = _fetch(
        """
        SELECT id FROM resource
        WHERE organization_id = %s AND name = %s AND status = 'active'
        """,
        (org_id, product_uid),
    )
    if not rows:
        raise ValueError(f"Product not found: {product_uid}")
    return rows[0]["id"]


def verify_org_owns_resource(resource_id: int, org_id: int):
    rows = _fetch(
        "SELECT id FROM resource WHERE id = %s AND organization_id = %s",
        (resource_id, org_id),
    )
    if not rows:
        from fastapi import HTTPException
        raise HTTPException(403, "Resource does not belong to this organization")


# --- Warehouse ---

def create_warehouse(organization_id: int, name: str, code: str,
                     location: str = None, description: str = None) -> Dict[str, Any]:
    sql = """
        INSERT INTO warehouse (organization_id, name, code, location, description)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING *
    """
    return dict(_execute(sql, (organization_id, name, code, location, description),
                         fetch_returning=True)[0])


def query_warehouse(organization_id: int, name: str = None) -> List[Dict]:
    sql = "SELECT * FROM warehouse WHERE organization_id = %s"
    params: list = [organization_id]
    if name:
        sql += " AND name ILIKE %s"
        params.append(f"%{name}%")
    return _fetch(sql, tuple(params))


# --- ResourceWarehouse ---

def create_resource_warehouse(resource_id: int, location_path: str,
                              quantity: float, unit: str = None) -> Dict[str, Any]:
    sql = """
        INSERT INTO resource_warehouse (resource_id, location_path, quantity, unit)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (resource_id, location_path)
        DO UPDATE SET quantity = EXCLUDED.quantity, unit = EXCLUDED.unit,
                      updated_at = CURRENT_TIMESTAMP
        RETURNING *
    """
    return dict(_execute(sql, (resource_id, location_path, quantity, unit),
                         fetch_returning=True)[0])


def query_resource_warehouse(resource_id: int, location_path: str = None) -> List[Dict]:
    sql = "SELECT * FROM resource_warehouse WHERE resource_id = %s"
    params: list = [resource_id]
    if location_path:
        sql += " AND location_path LIKE %s"
        params.append(f"{location_path}%")
    return _fetch(sql, tuple(params))


def get_resource_total(resource_id: int) -> Dict[str, Any]:
    """Get total quantity for a resource. Priority: 'total' row > SUM."""
    rows = _fetch(
        "SELECT quantity FROM resource_warehouse "
        "WHERE resource_id = %s AND location_path = 'total' LIMIT 1",
        (resource_id,)
    )
    if rows:
        total_qty = float(rows[0]["quantity"])
    else:
        rows = _fetch(
            "SELECT COALESCE(SUM(quantity), 0) AS total_qty "
            "FROM resource_warehouse WHERE resource_id = %s",
            (resource_id,)
        )
        total_qty = float(rows[0]["total_qty"])
    return {"resource_id": resource_id, "total_qty": total_qty}


# --- Transaction ---

def create_transaction(amount: float, category: str,
                        description: str = None,
                        organization_id: int = 1) -> Dict[str, Any]:
    sql = """
        INSERT INTO transaction (amount, category, description, organization_id)
        VALUES (%s, %s, %s, %s)
        RETURNING *
    """
    return dict(_execute(sql, (amount, category, description, organization_id),
                         fetch_returning=True)[0])


def get_transactions(organization_id: int, limit: int = 20) -> List[Dict]:
    """Get transactions for an org."""
    sql = """
        SELECT t.*,
               (SELECT json_agg(json_build_object(
                   'person_id', p.person_id,
                   'person_name', per.name,
                   'role', p.role,
                   'funds_change', p.funds_change,
                   'reputation_change', p.reputation_change
               )) FROM party p
               JOIN person per ON per.id = p.person_id
               WHERE p.transaction_id = t.id) AS parties
        FROM transaction t
        WHERE t.organization_id = %s
        ORDER BY t.created_at DESC
        LIMIT %s
    """
    return _fetch(sql, (organization_id, limit))


# --- Party ---

def create_party(person_id: int, organization_id: int, transaction_id: int,
                 role: str, description: str = None,
                 funds_change: float = 0, reputation_change: int = 0) -> Dict[str, Any]:
    sql = """
        INSERT INTO party (person_id, organization_id, transaction_id, role, description,
                          funds_change, reputation_change)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING *
    """
    result = dict(_execute(sql, (person_id, organization_id, transaction_id, role, description,
                                 funds_change, reputation_change),
                           fetch_returning=True)[0])
    # Auto-update organization funds and reputation
    if funds_change != 0 or reputation_change != 0:
        _execute(
            "UPDATE organization SET funds = funds + %s, reputation = reputation + %s WHERE id = %s",
            (funds_change, reputation_change, organization_id)
        )
    return result


def query_party_by_transaction(transaction_id: int) -> List[Dict]:
    sql = """
        SELECT p.*, per.puid AS puid, per.name AS person_name, org.ouid AS ouid
        FROM party p
        JOIN person per ON per.id = p.person_id
        JOIN organization org ON org.id = p.organization_id
        WHERE p.transaction_id = %s
    """
    return _fetch(sql, (transaction_id,))


def query_party(organization_id: int, person_id: int = None,
                name: str = None, puid: str = None) -> List[Dict]:
    sql = """
        SELECT p.*, per.puid AS puid, per.name AS person_name, org.ouid AS ouid
        FROM party p
        JOIN person per ON per.id = p.person_id
        JOIN organization org ON org.id = p.organization_id
        WHERE p.organization_id = %s
    """
    params: list = [organization_id]
    if person_id:
        sql += " AND p.person_id = %s"
        params.append(person_id)
    if puid:
        sql += " AND per.puid = %s"
        params.append(puid)
    if name:
        sql += " AND per.name ILIKE %s"
        params.append(f"%{name}%")
    return _fetch(sql, tuple(params))


# --- Campaign ---

def create_campaign_import(campaign_code: str, campaign_name: str,
                           source_file: str, imported_by_puid: str) -> Dict[str, Any]:
    sql = """
        INSERT INTO campaign_import (campaign_code, campaign_name, source_file, imported_by_puid)
        VALUES (%s, %s, %s, %s)
        RETURNING *
    """
    return dict(_execute(sql, (campaign_code, campaign_name, source_file, imported_by_puid),
                         fetch_returning=True)[0])


def add_campaign_import_org(campaign_import_id: int, organization_id: int,
                            created_by_import: bool) -> Dict[str, Any]:
    sql = """
        INSERT INTO campaign_import_org (campaign_import_id, organization_id, created_by_import)
        VALUES (%s, %s, %s)
        ON CONFLICT (campaign_import_id, organization_id)
        DO UPDATE SET created_by_import = campaign_import_org.created_by_import OR EXCLUDED.created_by_import
        RETURNING *
    """
    return dict(_execute(sql, (campaign_import_id, organization_id, created_by_import),
                         fetch_returning=True)[0])


def create_campaign_event(campaign_import_id: int, organization_id: int, seq: int,
                          title: str, description: str = None,
                          payload: Dict[str, Any] = None) -> Dict[str, Any]:
    import json
    sql = """
        INSERT INTO campaign_event (campaign_import_id, organization_id, seq, title, description, payload)
        VALUES (%s, %s, %s, %s, %s, %s::jsonb)
        RETURNING *
    """
    return dict(_execute(sql, (
        campaign_import_id, organization_id, seq, title, description,
        json.dumps(payload or {}, ensure_ascii=False),
    ), fetch_returning=True)[0])


def list_campaign_imports_for_orgs(organization_ids: List[int] = None,
                                   include_all: bool = False) -> List[Dict[str, Any]]:
    if include_all:
        sql = """
            SELECT ci.*,
               COALESCE(json_agg(DISTINCT jsonb_build_object(
                   'id', o.id, 'ouid', o.ouid, 'name', o.name, 'type', o.type
               )) FILTER (WHERE o.id IS NOT NULL), '[]') AS organizations
        FROM campaign_import ci
        LEFT JOIN campaign_import_org cio ON cio.campaign_import_id = ci.id
        LEFT JOIN organization o ON o.id = cio.organization_id
        WHERE ci.status = 'active'
            GROUP BY ci.id
            ORDER BY ci.created_at DESC, ci.id DESC
        """
        return _fetch(sql)

    if not organization_ids:
        return []
    sql = """
        SELECT ci.*,
               COALESCE(json_agg(DISTINCT jsonb_build_object(
                   'id', o.id, 'ouid', o.ouid, 'name', o.name, 'type', o.type
               )) FILTER (WHERE o.id IS NOT NULL), '[]') AS organizations
        FROM campaign_import ci
        JOIN campaign_import_org cio_filter ON cio_filter.campaign_import_id = ci.id
        LEFT JOIN campaign_import_org cio ON cio.campaign_import_id = ci.id
        LEFT JOIN organization o ON o.id = cio.organization_id
        WHERE ci.status = 'active'
          AND cio_filter.organization_id = ANY(%s)
        GROUP BY ci.id
        ORDER BY ci.created_at DESC, ci.id DESC
    """
    return _fetch(sql, (organization_ids,))


def get_campaign_import(campaign_import_id: int) -> List[Dict[str, Any]]:
    return _fetch("SELECT * FROM campaign_import WHERE id = %s", (campaign_import_id,))


def get_active_campaign_import_by_code(campaign_code: str) -> List[Dict[str, Any]]:
    sql = """
        SELECT *
        FROM campaign_import
        WHERE campaign_code = %s AND status = 'active'
        ORDER BY created_at DESC, id DESC
        LIMIT 1
    """
    return _fetch(sql, (campaign_code,))


def get_campaign_import_org_ids(campaign_import_id: int) -> List[int]:
    rows = _fetch(
        "SELECT organization_id FROM campaign_import_org WHERE campaign_import_id = %s",
        (campaign_import_id,)
    )
    return [row["organization_id"] for row in rows]


def get_campaign_replay(campaign_import_id: int, organization_ids: List[int] = None,
                        include_all: bool = False) -> List[Dict[str, Any]]:
    sql = """
        SELECT ce.id, ce.seq, ce.title, ce.description, ce.payload,
               o.ouid, o.name AS organization_name, o.type AS organization_type
        FROM campaign_event ce
        JOIN organization o ON o.id = ce.organization_id
        WHERE ce.campaign_import_id = %s
    """
    params: list = [campaign_import_id]
    if not include_all:
        if not organization_ids:
            return []
        sql += " AND ce.organization_id = ANY(%s)"
        params.append(organization_ids)
    sql += " ORDER BY ce.seq, ce.id"
    return _fetch(sql, tuple(params))


def delete_campaign_import(campaign_import_id: int) -> Dict[str, Any]:
    conn = get_db_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM campaign_import WHERE id = %s", (campaign_import_id,))
        campaign = cur.fetchone()
        if not campaign:
            conn.rollback()
            return {"deleted": False, "reason": "not_found"}

        cur.execute(
            "SELECT organization_id FROM campaign_import_org WHERE campaign_import_id = %s AND created_by_import = TRUE",
            (campaign_import_id,)
        )
        org_ids = [row["organization_id"] for row in cur.fetchall()]

        cur.execute("DELETE FROM campaign_event WHERE campaign_import_id = %s", (campaign_import_id,))
        deleted_events = cur.rowcount

        deleted = {
            "events": deleted_events,
            "parties": 0,
            "transactions": 0,
            "resource_warehouse": 0,
            "resources": 0,
            "warehouses": 0,
            "memberships": 0,
            "organizations": 0,
        }

        if org_ids:
            cur.execute("DELETE FROM party WHERE organization_id = ANY(%s)", (org_ids,))
            deleted["parties"] = cur.rowcount
            cur.execute("DELETE FROM transaction WHERE organization_id = ANY(%s)", (org_ids,))
            deleted["transactions"] = cur.rowcount
            cur.execute("""
                DELETE FROM resource_warehouse rw
                USING resource r
                WHERE rw.resource_id = r.id AND r.organization_id = ANY(%s)
            """, (org_ids,))
            deleted["resource_warehouse"] = cur.rowcount
            cur.execute("DELETE FROM resource WHERE organization_id = ANY(%s)", (org_ids,))
            deleted["resources"] = cur.rowcount
            cur.execute("DELETE FROM warehouse WHERE organization_id = ANY(%s)", (org_ids,))
            deleted["warehouses"] = cur.rowcount
            cur.execute("DELETE FROM membership WHERE organization_id = ANY(%s)", (org_ids,))
            deleted["memberships"] = cur.rowcount
            cur.execute("DELETE FROM organization WHERE id = ANY(%s)", (org_ids,))
            deleted["organizations"] = cur.rowcount

        cur.execute(
            "UPDATE campaign_import SET status = 'deleted', deleted_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING *",
            (campaign_import_id,)
        )
        updated = dict(cur.fetchone())
        conn.commit()
        return {"deleted": True, "campaign_import": updated, "counts": deleted}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
