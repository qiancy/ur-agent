from typing import Optional
from datetime import datetime, timedelta
import os
import jwt
from functools import wraps
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext

# JWT配置
SECRET_KEY = os.getenv("SECRET_KEY", "uni-resource-agent-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 安全工具
security = HTTPBearer()

# JWT相关函数
def create_access_token(data: dict):
    """创建访问令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取当前用户"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="无效的认证令牌")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="无效的认证令牌")

# 用户上下文管理
class ContextManager:
    """上下文管理器"""
    
    def __init__(self):
        self.current_context = None
    
    def set_context(self, context_id: int):
        """设置当前上下文"""
        self.current_context = context_id
    
    def get_context(self) -> Optional[int]:
        """获取当前上下文"""
        return self.current_context
    
    def validate_context(self, context_id: int) -> bool:
        """验证上下文是否存在"""
        # 这里应该连接数据库检查上下文是否存在
        # 为简化实现，我们返回True
        return True

# 全局上下文管理器实例
context_manager = ContextManager()