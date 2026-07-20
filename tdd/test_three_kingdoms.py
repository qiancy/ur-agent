import unittest
from src.tools.asset_tools import query_asset, transfer_asset
from src.tools.finance_tools import record_transaction, get_summary
from src.tools.human_tools import manage_reminder, check_wellness
from src.tools.knowledge_tools import rag_search
from src.db.database import init_database
import os

class TestThreeKingdomsAgents(unittest.TestCase):
    """三国角色测试用例"""
    
    def setUp(self):
        """测试前准备"""
        # 初始化数据库
        init_database()
        
        # 设置测试上下文ID
        self.context_ids = {
            'liubei': 1,    # 蜀汉
            'guanyu': 2,   # 蜀汉武将
            'zhangfei': 3,   # 蜀汉武将
            'zhugeliang': 4,  # 蜀汉军师
            'caocao': 5,     # 魏国
            'sunquan': 6,    # 吴国
            'lvbu': 7,      # 被俘武将
            'zhaoyun': 8,   # 蜀汉虎将
            'zhouyu': 9,  # 吴国谋士
            'huangzhong': 10 # 蜀汉老将
        }
    
    def test_liubei_resource_management(self):
        """刘备 - 仁德之主 - 资源管理测试"""
        # 测试库存查询
        result = query_asset("武器", self.context_ids['liubei'])
        self.assertIn("查询", result)
        
        # 测试资源转移
        result = transfer_asset("1", self.context_ids['liubei'], self.context_ids['guanyu'], 1)
        self.assertIn("转移", result)
        
        # 测试财务记录
        result = record_transaction(1000.0, "军需", "军队补给", self.context_ids['liubei'])
        self.assertIn("记录", result)
    
    def test_guanyu_weapon_management(self):
        """关羽 - 武艺超群 - 武器管理测试"""
        # 测试武器查询
        result = query_asset("青龙偃月刀", self.context_ids['guanyu'])
        self.assertIn("查询", result)
        
        # 测试装备转移
        result = transfer_asset("2", self.context_ids['guanyu'], self.context_ids['liubei'], 1)
        self.assertIn("转移", result)
        
        # 测试健康提醒
        result = manage_reminder("添加", "关羽", "检查伤口", "2026-08-01")
        self.assertIn("添加", result)
    
    def test_zhangfei_supply_management(self):
        """张飞 - 粗中有细 - 军需物资测试"""
        # 测试物资库存
        result = query_asset("粮草", self.context_ids['zhangfei'])
        self.assertIn("查询", result)
        
        # 测试物资分配
        result = transfer_asset("3", self.context_ids['zhangfei'], self.context_ids['liubei'], 50)
        self.assertIn("转移", result)
        
        # 测试支出记录
        result = record_transaction(500.0, "军需", "购买粮草", self.context_ids['zhangfei'])
        self.assertIn("记录", result)
    
    def test_zhugeliang_knowledge_management(self):
        """诸葛亮 - 智慧军师 - 知识管理测试"""
        # 测试知识搜索
        result = rag_search("战略规划", self.context_ids['zhugeliang'])
        self.assertIn("搜索", result)
        
        # 测试文档记录
        result = rag_search("出师表", self.context_ids['zhugeliang'])
        self.assertIn("搜索", result)
        
        # 测试策略建议
        result = rag_search("火烧赤壁", self.context_ids['zhugeliang'])
        self.assertIn("搜索", result)
    
    def test_caocao_resource_allocation(self):
        """曹操 - 雄才大略 - 多上下文资源测试"""
        # 测试不同身份切换
        result = query_asset("兵器", self.context_ids['caocao'])
        self.assertIn("查询", result)
        
        # 测试数据隔离
        result = query_asset("武器", self.context_ids['caocao'])
        self.assertIn("查询", result)
        
        # 测试资源分配
        result = transfer_asset("4", self.context_ids['caocao'], self.context_ids['zhangfei'], 1)
        self.assertIn("转移", result)
    
    def test_sunquan_finance_management(self):
        """孙权 - 继承基业 - 财务管理测试"""
        # 测试财务记录
        result = record_transaction(2000.0, "军费", "战船建设", self.context_ids['sunquan'])
        self.assertIn("记录", result)
        
        # 测试财务摘要
        result = get_summary(self.context_ids['sunquan'])
        self.assertIn("摘要", result)
        
        # 测试预算管理
        result = record_transaction(1000.0, "预算", "军费预算", self.context_ids['sunquan'])
        self.assertIn("记录", result)
    
    def test_lubu_special_asset(self):
        """吕布 - 人中吕布 - 特殊资源测试"""
        # 测试特殊资产查询
        result = query_asset("方天画戟", self.context_ids['lvbu'])
        self.assertIn("查询", result)
        
        # 测试资产转移
        result = transfer_asset("5", self.context_ids['lvbu'], self.context_ids['caocao'], 1)
        self.assertIn("转移", result)
        
        # 测试状态更新
        result = query_asset("吕布", self.context_ids['lvbu'])
        self.assertIn("查询", result)
    
    def test_zhaoyun_personnel_management(self):
        """赵云 - 虎将 - 人员管理测试"""
        # 测试人员信息
        result = manage_reminder("添加", "赵云", "训练", "2026-08-05")
        self.assertIn("添加", result)
        
        # 测试任务分配
        result = manage_reminder("更新", "赵云", "任务完成", "2026-08-05")
        self.assertIn("更新", result)
        
        # 测试健康提醒
        result = check_wellness("赵云")
        self.assertIn("健康", result)
    
    def test_zhouyu_strategy_planning(self):
        """周瑜 - 雄才谋士 - 战略规划测试"""
        # 测试战略文档
        result = rag_search("赤壁之战", self.context_ids['zhouyu'])
        self.assertIn("搜索", result)
        
        # 测试知识搜索
        result = rag_search("火攻策略", self.context_ids['zhouyu'])
        self.assertIn("搜索", result)
        
        # 测试策略实施
        result = rag_search("东吴战略", self.context_ids['zhouyu'])
        self.assertIn("搜索", result)
    
    def test_huangzhong_resource_inheritance(self):
        """黄忠 - 老将 - 资源传承测试"""
        # 测试资产传承
        result = transfer_asset("6", self.context_ids['huangzhong'], self.context_ids['liubei'], 1)
        self.assertIn("转移", result)
        
        # 测试资源转移
        result = transfer_asset("7", self.context_ids['huangzhong'], self.context_ids['zhangfei'], 2)
        self.assertIn("转移", result)
        
        # 测试历史记录
        result = query_asset("经验", self.context_ids['huangzhong'])
        self.assertIn("查询", result)

if __name__ == '__main__':
    unittest.main()