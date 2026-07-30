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
JWT_EXPIRATION_HOURS = 72


# ── Login name parsing ───────────────────────────────────────────────────────

LOGIN_PATTERN = re.compile(r'^([a-zA-Z0-9_-]+)@([a-zA-Z0-9_-]+)(?:\.[a-zA-Z0-9_-]+)?$')


def parse_login_name(login: str) -> Optional[Tuple[str, str]]:
    """
    Parse login name format: {puid}@{ouid} or {puid}@{ouid}.{suffix}.
    Returns (puid, ouid) or None if invalid.
    """
    match = LOGIN_PATTERN.match(login)
    if match:
        return match.group(1), match.group(2)
    return None


def validate_puid(puid: str) -> bool:
    """Validate person puid: only letters, numbers, underscores, hyphens."""
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', puid))


def validate_ouid(ouid: str) -> bool:
    """Validate organization ouid: only letters, numbers, underscores, hyphens."""
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', ouid))


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
        return ph.verify(stored_password, password + (salt or ""))
    except VerifyMismatchError:
        return False


# ── JWT token management ─────────────────────────────────────────────────────

JWT_FORBIDDEN_ID_KEYS = {"id", "person_id", "organization_id", "person_db_id", "organization_db_id"}


def _canonicalize_token_data(data: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in data.items() if k not in JWT_FORBIDDEN_ID_KEYS}


def create_access_token(data: Dict[str, Any]) -> str:
    """
    Create JWT access token.
    """
    to_encode = _canonicalize_token_data(data)
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode JWT access token.
    Returns payload dict or None if invalid.
    """
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None


# ── User context management ──────────────────────────────────────────────────

class ContextManager:
    """上下文管理器
    
    context 是运行时概念，由 ouid 和 puid 组成
    context = {ouid, puid} 表示 "person@organization" 上下文
    """
    
    def __init__(self):
        self.current_ouid = None
        self.current_puid = None
    
    def set_context(self, ouid: str, puid: str):
        """设置当前上下文 (ouid, puid)"""
        self.current_ouid = ouid
        self.current_puid = puid
    
    def get_context(self) -> Optional[Tuple[str, str]]:
        """获取当前上下文 (ouid, puid)"""
        return (self.current_ouid, self.current_puid)
    
    def get_ouid(self) -> Optional[str]:
        """获取当前组织 ouid"""
        return self.current_ouid
    
    def get_puid(self) -> Optional[str]:
        """获取当前人员 puid"""
        return self.current_puid
    
    def validate_context(self, org_id: int, person_id: int) -> bool:
        """Validate that the given person has an active membership in the organization."""
        from src.db.database import query_membership
        memberships = query_membership(person_id, org_id)
        return len(memberships) > 0


# 全局上下文管理器实例
context_manager = ContextManager()
