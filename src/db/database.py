"""
Database module for Uni-Resource Agent.

Tables (v5.2):
  - organization: 组织 (个人/家庭/公司/等) + funds, reputation
  - person: 人员 (纯个人信息)
  - membership: 人员↔组织 (多对多, 带角色)
  - resource: 资源 (单表, type 区分 physical/financial/human/knowledge)
  - warehouse: 仓库
  - resource_warehouse: 资源-仓库明细 (location_path + quantity + unit)
  - transaction: 交易事务 (纯事件)
  - party: 交易参与方 (同生同死于 transaction, 记录 funds_change, reputation_change)

Naming: pid = person_id, oid = org_id (统一使用短形式)
"""

from typing import Optional, List, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from src.logging_config import get_logger

logger = get_logger("db")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
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
    name        VARCHAR(255) NOT NULL,
    type        VARCHAR(100) NOT NULL,
    description TEXT,
    funds       DECIMAL(15,2) DEFAULT 0,
    reputation  INTEGER DEFAULT 0,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Person: 人员 (纯个人信息, 无 oid)
CREATE TABLE IF NOT EXISTS person (
    id               SERIAL PRIMARY KEY,
    name             VARCHAR(255) NOT NULL,
    birth_date       DATE,
    health_reminders JSONB,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Membership: 人员↔组织 (多对多, 带角色)
CREATE TABLE IF NOT EXISTS membership (
    id          SERIAL PRIMARY KEY,
    pid         INTEGER NOT NULL REFERENCES person(id) ON DELETE CASCADE,
    oid         INTEGER NOT NULL REFERENCES organization(id) ON DELETE CASCADE,
    role        VARCHAR(100),
    joined_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(pid, oid)
);

-- Resource: 资源 (单表设计, type 区分 physical/financial/human/knowledge)
CREATE TABLE IF NOT EXISTS resource (
    id          SERIAL PRIMARY KEY,
    oid         INTEGER NOT NULL REFERENCES organization(id) ON DELETE CASCADE,
    name        VARCHAR(255) NOT NULL,
    type        VARCHAR(100) NOT NULL,
    status      VARCHAR(50) DEFAULT 'active',
    unit        VARCHAR(50),
    -- financial fields (nullable)
    amount      DECIMAL(15,2),
    currency    VARCHAR(20),
    -- human fields (nullable)
    pid         INTEGER REFERENCES person(id),
    -- knowledge fields (nullable)
    content     TEXT,
    embedding   VECTOR(1024),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Warehouse: 仓库
CREATE TABLE IF NOT EXISTS warehouse (
    id          SERIAL PRIMARY KEY,
    oid         INTEGER NOT NULL REFERENCES organization(id) ON DELETE CASCADE,
    name        VARCHAR(255) NOT NULL,
    code        VARCHAR(50) NOT NULL,
    location    VARCHAR(255),
    description TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(oid, code)
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

-- Transaction: 交易事务 (纯事件, 组织上下文来自 party)
CREATE TABLE IF NOT EXISTS transaction (
    id              SERIAL PRIMARY KEY,
    oid             INTEGER NOT NULL REFERENCES organization(id) ON DELETE CASCADE,
    amount          DECIMAL(15,2) NOT NULL,
    category        VARCHAR(100) NOT NULL,
    description     TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Party: 交易参与方 (同生同死于 transaction, 记录对组织的影响)
CREATE TABLE IF NOT EXISTS party (
    id                  SERIAL PRIMARY KEY,
    pid                 INTEGER NOT NULL REFERENCES person(id),
    oid                 INTEGER NOT NULL REFERENCES organization(id),
    transaction_id      INTEGER NOT NULL REFERENCES transaction(id) ON DELETE CASCADE,
    role                VARCHAR(100) NOT NULL,
    description         TEXT,
    funds_change        DECIMAL(15,2) DEFAULT 0,
    reputation_change   INTEGER DEFAULT 0,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_membership_pid ON membership(pid);
CREATE INDEX IF NOT EXISTS idx_membership_oid ON membership(oid);
CREATE INDEX IF NOT EXISTS idx_resource_oid ON resource(oid);
CREATE INDEX IF NOT EXISTS idx_resource_type ON resource(type);
CREATE INDEX IF NOT EXISTS idx_warehouse_oid ON warehouse(oid);
CREATE INDEX IF NOT EXISTS idx_rw_resource ON resource_warehouse(resource_id);
CREATE INDEX IF NOT EXISTS idx_rw_location ON resource_warehouse(location_path);
CREATE INDEX IF NOT EXISTS idx_party_pid ON party(pid);
CREATE INDEX IF NOT EXISTS idx_party_oid ON party(oid);
CREATE INDEX IF NOT EXISTS idx_party_transaction ON party(transaction_id);
"""


def init_database(drop_all: bool = False):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        if drop_all:
            cur.execute("""
                DROP TABLE IF EXISTS party CASCADE;
                DROP TABLE IF EXISTS transaction CASCADE;
                DROP TABLE IF EXISTS resource_warehouse CASCADE;
                DROP TABLE IF EXISTS warehouse CASCADE;
                DROP TABLE IF EXISTS resource CASCADE;
                DROP TABLE IF EXISTS membership CASCADE;
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
        return cur.fetchall()
    finally:
        conn.close()


def _execute(sql: str, params: tuple = (), fetch_returning: bool = False) -> Any:
    conn = get_db_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(sql, params)
        if fetch_returning:
            result = cur.fetchall()
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
                        reputation: int = 0) -> Dict[str, Any]:
    sql = """
        INSERT INTO organization (name, type, description, funds, reputation)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING *
    """
    return dict(_execute(sql, (name, org_type, description, funds, reputation),
                         fetch_returning=True)[0])


def query_organization(oid: int = None, name: str = None,
                       org_type: str = None) -> List[Dict]:
    sql = "SELECT * FROM organization WHERE 1=1"
    params: list = []
    if oid:
        sql += " AND id = %s"
        params.append(oid)
    if name:
        sql += " AND name ILIKE %s"
        params.append(f"%{name}%")
    if org_type:
        sql += " AND type = %s"
        params.append(org_type)
    return _fetch(sql, tuple(params))


# --- Person ---

def create_person(name: str, birth_date: str = None) -> Dict[str, Any]:
    sql = """
        INSERT INTO person (name, birth_date)
        VALUES (%s, %s)
        RETURNING *
    """
    return dict(_execute(sql, (name, birth_date), fetch_returning=True)[0])


def query_person_by_name(name: str) -> List[Dict]:
    """Find person by name (global, not org-scoped)."""
    sql = "SELECT * FROM person WHERE name ILIKE %s"
    return _fetch(sql, (f"%{name}%",))


def query_person(oid: int, name: str = None) -> List[Dict]:
    """Find people in an org via membership."""
    sql = """
        SELECT p.*, m.role AS membership_role
        FROM person p
        JOIN membership m ON m.pid = p.id
        WHERE m.oid = %s
    """
    params: list = [oid]
    if name:
        sql += " AND p.name ILIKE %s"
        params.append(f"%{name}%")
    sql += " ORDER BY p.name"
    return _fetch(sql, tuple(params))


# --- Membership ---

def add_membership(pid: int, oid: int, role: str = None) -> Dict[str, Any]:
    sql = """
        INSERT INTO membership (pid, oid, role)
        VALUES (%s, %s, %s)
        RETURNING *
    """
    return dict(_execute(sql, (pid, oid, role), fetch_returning=True)[0])


def get_org_members(oid: int) -> List[Dict]:
    sql = """
        SELECT m.id, m.role, p.name, p.id AS pid
        FROM membership m
        JOIN person p ON p.id = m.pid
        WHERE m.oid = %s
    """
    return _fetch(sql, (oid,))


def get_person_memberships(pid: int) -> List[Dict]:
    sql = """
        SELECT m.id, m.role, o.name, o.id AS oid, o.type AS org_type
        FROM membership m
        JOIN organization o ON o.id = m.oid
        WHERE m.pid = %s
    """
    return _fetch(sql, (pid,))


# --- Resource ---

def create_resource(oid: int, name: str, resource_type: str,
                    unit: str = None, amount: float = None,
                    currency: str = None, pid: int = None,
                    content: str = None) -> Dict[str, Any]:
    sql = """
        INSERT INTO resource (oid, name, type, unit, amount, currency, pid, content)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *
    """
    return dict(_execute(sql, (oid, name, resource_type, unit, amount, currency, pid, content),
                           fetch_returning=True)[0])


def query_resource(oid: int, name: str = None,
                   resource_type: str = None) -> List[Dict]:
    sql = """
        SELECT r.*, p.name AS person_name
        FROM resource r
        LEFT JOIN person p ON p.id = r.pid
        WHERE r.oid = %s AND r.status = 'active'
    """
    params: list = [oid]
    if name:
        sql += " AND r.name ILIKE %s"
        params.append(f"%{name}%")
    if resource_type:
        sql += " AND r.type = %s"
        params.append(resource_type)
    return _fetch(sql, tuple(params))


# --- Warehouse ---

def create_warehouse(oid: int, name: str, code: str,
                     location: str = None, description: str = None) -> Dict[str, Any]:
    sql = """
        INSERT INTO warehouse (oid, name, code, location, description)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING *
    """
    return dict(_execute(sql, (oid, name, code, location, description),
                         fetch_returning=True)[0])


def query_warehouse(oid: int, name: str = None) -> List[Dict]:
    sql = "SELECT * FROM warehouse WHERE oid = %s"
    params: list = [oid]
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


def query_resource_warehouse(resource_id: int, location_path: str = None, oid: int = 1) -> List[Dict]:
    sql = "SELECT * FROM resource_warehouse WHERE resource_id = %s AND oid = %s"
    params: list = [resource_id, oid]
    if location_path:
        sql += " AND location_path LIKE %s"
        params.append(f"{location_path}%")
    return _fetch(sql, tuple(params))


def get_resource_total(resource_id: int, oid: int = 1) -> Dict[str, Any]:
    """Get total quantity for a resource. Priority: 'total' row > SUM."""
    rows = _fetch(
        "SELECT quantity FROM resource_warehouse "
        "WHERE resource_id = %s AND oid = %s AND location_path = 'total' LIMIT 1",
        (resource_id, oid)
    )
    if rows:
        total_qty = float(rows[0]["quantity"])
    else:
        rows = _fetch(
            "SELECT COALESCE(SUM(quantity), 0) AS total_qty "
            "FROM resource_warehouse WHERE resource_id = %s AND oid = %s",
            (resource_id, oid)
        )
        total_qty = float(rows[0]["total_qty"])
    return {"resource_id": resource_id, "oid": oid, "total_qty": total_qty}


# --- Transaction ---

def create_transaction(amount: float, category: str,
                        description: str = None,
                        oid: int = 1) -> Dict[str, Any]:
    sql = """
        INSERT INTO transaction (amount, category, description, oid)
        VALUES (%s, %s, %s, %s)
        RETURNING *
    """
    return dict(_execute(sql, (amount, category, description, oid),
                         fetch_returning=True)[0])


def get_transactions(oid: int, limit: int = 20) -> List[Dict]:
    """Get transactions for an org (via party join)."""
    sql = """
        SELECT t.*,
               (SELECT json_agg(json_build_object(
                   'pid', p.pid,
                   'person_name', per.name,
                   'role', p.role,
                   'funds_change', p.funds_change,
                   'reputation_change', p.reputation_change
               )) FROM party p
               JOIN person per ON per.id = p.pid
               WHERE p.transaction_id = t.id) AS parties
        FROM transaction t
        WHERE t.id IN (
            SELECT transaction_id FROM party WHERE oid = %s
        )
        ORDER BY t.created_at DESC
        LIMIT %s
    """
    return _fetch(sql, (oid, limit))


# --- Party ---

def create_party(pid: int, oid: int, transaction_id: int,
                 role: str, description: str = None,
                 funds_change: float = 0, reputation_change: int = 0) -> Dict[str, Any]:
    sql = """
        INSERT INTO party (pid, oid, transaction_id, role, description,
                          funds_change, reputation_change)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING *
    """
    result = dict(_execute(sql, (pid, oid, transaction_id, role, description,
                                 funds_change, reputation_change),
                           fetch_returning=True)[0])
    # Auto-update organization funds and reputation
    if funds_change != 0 or reputation_change != 0:
        _execute(
            "UPDATE organization SET funds = funds + %s, reputation = reputation + %s WHERE id = %s",
            (funds_change, reputation_change, oid)
        )
    return result


def query_party_by_transaction(transaction_id: int) -> List[Dict]:
    sql = """
        SELECT p.*, per.name AS person_name
        FROM party p
        JOIN person per ON per.id = p.pid
        WHERE p.transaction_id = %s
    """
    return _fetch(sql, (transaction_id,))


def query_party(oid: int, pid: int = None, name: str = None) -> List[Dict]:
    sql = """
        SELECT p.*, per.name AS person_name
        FROM party p
        JOIN person per ON per.id = p.pid
        WHERE p.oid = %s
    """
    params: list = [oid]
    if pid:
        sql += " AND p.pid = %s"
        params.append(pid)
    if name:
        sql += " AND per.name ILIKE %s"
        params.append(f"%{name}%")
    return _fetch(sql, tuple(params))
