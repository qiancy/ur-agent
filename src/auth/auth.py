"""
Authentication module for Uni-Resource Agent.

Provides password hashing (argon2) and JWT token management.
"""
import os
import re
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt

# Password hasher using argon2
ph = PasswordHasher()

# JWT configuration — JWT_SECRET must be set via environment variable
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET environment variable is required. "
                       "Set it before starting the server.")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


# ── Login name parsing ───────────────────────────────────────────────────────

LOGIN_PATTERN = re.compile(r'^([a-zA-Z0-9_-]+)@([a-zA-Z0-9_-]+)(?:\.[a-zA-Z0-9_-]+)?$')


def parse_login_name(login: str) -> Optional[Tuple[str, str]]:
    """
    Parse login name format: {pid}@{oid} or {pid}@{oid}.{suffix}.
    Returns (pid, oid) or None if invalid.
    """
    match = LOGIN_PATTERN.match(login)
    if match:
        return match.group(1), match.group(2)
    return None


def validate_pid(pid: str) -> bool:
    """Validate person pid: only letters, numbers, underscores, hyphens."""
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', pid))


def validate_oid(oid: str) -> bool:
    """Validate organization oid: only letters, numbers, underscores, hyphens."""
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', oid))


# ── Password hashing ─────────────────────────────────────────────────────────

def hash_password(password: str) -> Tuple[str, str]:
    """
    Hash password using argon2.
    Returns (hashed_password, salt).
    """
    salt = secrets.token_hex(16)
    hashed_password = ph.hash(password + salt)
    return hashed_password, salt


def verify_password(password: str, stored_password: str, salt: str) -> bool:
    """
    Verify password against hash.
    Returns True if password matches, False otherwise.
    """
    try:
        return ph.verify(stored_password, password + salt)
    except VerifyMismatchError:
        return False


# ── JWT token management ─────────────────────────────────────────────────────

def create_access_token(data: Dict[str, Any]) -> str:
    """
    Create JWT access token.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode JWT access token.
    Returns payload dict or None if invalid.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


# ── User context management ──────────────────────────────────────────────────

class ContextManager:
    """上下文管理器
    
    context 是运行时概念，由 oid 和 pid 组成
    context = {oid, pid} 表示 "person@organization" 上下文
    """
    
    def __init__(self):
        self.current_oid = None
        self.current_pid = None
    
    def set_context(self, oid: str, pid: str):
        """设置当前上下文 (oid, pid)"""
        self.current_oid = oid
        self.current_pid = pid
    
    def get_context(self) -> Optional[Tuple[str, str]]:
        """获取当前上下文 (oid, pid)"""
        return (self.current_oid, self.current_pid)
    
    def get_oid(self) -> Optional[str]:
        """获取当前组织 oid"""
        return self.current_oid
    
    def get_pid(self) -> Optional[str]:
        """获取当前人员 pid"""
        return self.current_pid
    
    def validate_context(self, org_id: int, person_id: int) -> bool:
        """Validate that the given person has an active membership in the organization."""
        from src.db.database import query_membership
        memberships = query_membership(person_id, org_id)
        return len(memberships) > 0


# 全局上下文管理器实例
context_manager = ContextManager()
