from typing import Optional, Tuple


# 用户上下文管理
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