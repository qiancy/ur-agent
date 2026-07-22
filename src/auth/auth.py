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

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET", secrets.token_hex(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


# ── Login name parsing ───────────────────────────────────────────────────────

LOGIN_PATTERN = re.compile(r'^([a-zA-Z0-9_-]+)@([a-zA-Z0-9_-]+)\.cn$')


def parse_login_name(login: str) -> Optional[Tuple[str, str]]:
    """
    Parse login name format: {pid}@{oid}.cn
    Returns (person_pid, org_oid) or None if invalid.
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
    Returns (password_hash, salt).
    """
    salt = secrets.token_hex(16)
    password_hash = ph.hash(password + salt)
    return password_hash, salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """
    Verify password against hash.
    Returns True if password matches, False otherwise.
    """
    try:
        return ph.verify(password_hash, password + salt)
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
    
    def set_context(self, oid: int, pid: int):
        """设置当前上下文 (oid, pid)"""
        self.current_oid = oid
        self.current_pid = pid
    
    def get_context(self) -> Optional[Tuple[int, int]]:
        """获取当前上下文 (oid, pid)"""
        return (self.current_oid, self.current_pid)
    
    def get_oid(self) -> Optional[int]:
        """获取当前组织ID"""
        return self.current_oid
    
    def get_pid(self) -> Optional[int]:
        """获取当前人员ID"""
        return self.current_pid
    
    def validate_context(self, oid: int, pid: int) -> bool:
        """验证上下文是否存在"""
        # 这里应该连接数据库检查上下文是否存在
        # 为简化实现，我们返回True
        return True


# 全局上下文管理器实例
context_manager = ContextManager()
