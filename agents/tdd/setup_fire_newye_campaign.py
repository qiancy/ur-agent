#!/usr/bin/env python3
"""
火烧新野战役 - 测试数据准备脚本（API调用版）

⚠️ 重要说明：
测试端不提供数据库初始化代码，只通过HTTP API调用后端接口准备数据。

运行方式：
    python setup_fire_newye_campaign.py [command]

命令：
    prepare     - 通过HTTP API准备测试数据
    verify      - 验证测试数据
    clean       - 清理测试数据（需后端支持清理接口）
    
使用前必须：
1. 确保FastAPI后端运行在 http://localhost:8000
2. 确保后端已实现数据初始化API（或支持逐个创建数据的API）
"""

import requests
import sys
import psycopg2
from typing import Dict, List, Any
from datetime import datetime

# ============================================================================
# 配置
# ============================================================================

API_BASE_URL = "http://localhost:8000"
TEST_CAMPAIGN_NAME = "火烧新野"
TEST_CAMPAIGN_ID = 1001

# 蜀汉阵营
SHU_ORG_NAME = "蜀汉-火烧新野战役"
SHU_ORG_TYPE = "military"
SHU_ORG_DESCRIPTION = "诸葛亮火烧新野战役指挥部"

# 曹魏阵营
WEI_ORG_NAME = "曹魏-新野守军"
WEI_ORG_TYPE = "military"
WEI_ORG_DESCRIPTION = "曹魏新野防线"

# 参战人员
SHU_PERSONNEL = [
    {"name": "诸葛亮", "role": "军师", "birth_date": "181-04-23"},
    {"name": "关羽", "role": "副将", "birth_date": "160-05-14"},
    {"name": "张飞", "role": "先锋", "birth_date": "165-06-11"},
    {"name": "赵云", "role": "哨探", "birth_date": "181-12-06"},
    {"name": "黄忠", "role": "后勤官", "birth_date": "120-01-01"},  # 老将
]

WEI_PERSONNEL = [
    {"name": "曹洪", "role": "主将", "birth_date": "170-01-01"},
    {"name": "夏侯惇", "role": "副将", "birth_date": "155-01-01"},
    {"name": "于禁", "role": "先锋", "birth_date": "170-01-01"},
]

# 蜀汉物资清单 - 火攻相关
SHU_RESOURCES = [
    # 火攻材料
    {"name": "火油", "type": "physical", "unit": "桶", "amount": 100, "content": "桐油70%+蜂蜜30%"},
    {"name": "火把", "type": "physical", "unit": "支", "amount": 500},
    {"name": "硫磺", "type": "physical", "unit": "斤", "amount": 20},
    {"name": "木柴", "type": "physical", "unit": "捆", "amount": 300},
    {"name": "酒坛", "type": "physical", "unit": "个", "amount": 100},
    {"name": "皮囊", "type": "physical", "unit": "个", "amount": 200},
    {"name": "青铜镜", "type": "physical", "unit": "面", "amount": 50, "content": "反射阳光点火"},
    {"name": "火矢", "type": "physical", "unit": "支", "amount": 300},
    {"name": "烟雾弹", "type": "physical", "unit": "个", "amount": 50},
    
    # 武器装备
    {"name": "青龙偃月刀", "type": "physical", "unit": "把", "amount": 1},
    {"name": "丈八蛇矛", "type": "physical", "unit": "把", "amount": 1},
    {"name": "连弩", "type": "physical", "unit": "架", "amount": 50},
    {"name": "战船", "type": "physical", "unit": "艘", "amount": 5},
    
    # 资金
    {"name": "蜀国军费", "type": "financial", "unit": "两黄金", "amount": 1900},
    {"name": "稿赏银", "type": "financial", "unit": "两白银", "amount": 800},
    
    # 人力
    {"name": "蜀国兵力", "type": "human", "pid": 1, "content": "火攻部队"},
    
    # 知识
    {"name": "火攻计策", "type": "knowledge", "content": "火油倾泻+青铜镜点火"},
    {"name": "火烧新野计划", "type": "knowledge", "content": "伏兵林中，切断退路"},
]

# 曹魏物资损失
WEI_LOSS_RESOURCES = [
    {"name": "弓箭", "type": "physical", "unit": "支", "amount": 10000},
    {"name": "戈矛", "type": "physical", "unit": "支", "amount": 5000},
    {"name": "盾牌", "type": "physical", "unit": "个", "amount": 2000},
    {"name": "铠甲", "type": "physical", "unit": "套", "amount": 1500},
    {"name": "战马", "type": "physical", "unit": "匹", "amount": 500},
    {"name": "粮草", "type": "physical", "unit": "石", "amount": 2000},
]

# 交易记录
TRANSACTIONS = [
    # 蜀汉支出
    {"amount": 500, "category": "火油采购", "description": "购买桐油火攻材料", "from_org": "蜀国国库", "to_party": "商人张三"},
    {"amount": 300, "category": "黄铜采购", "description": "制造青铜镜点火工具", "from_org": "蜀国国库", "to_party": "作坊李四"},
    {"amount": 800, "category": "稿赏银", "description": "战后犒赏三军", "from_org": "诸葛亮家", "to_party": "全体将士"},
    {"amount": 200, "category": "民夫雇佣", "description": "物资搬运人工", "from_org": "蜀国国库", "to_party": "当地百姓"},
    {"amount": 100, "category": "烟火购置", "description": "烟雾弹材料", "from_org": "诸葛亮家", "to_party": "百姓名王五"},
    
    # 曹魏损失
    {"amount": 3000, "category": "军械损失", "description": "弓箭戈矛等遗失", "from_org": "曹魏军需", "to_party": "蜀汉缴获"},
    {"amount": 2000, "category": "马匹损失", "description": "战马走失", "from_org": "曹魏军需", "to_party": "蜀汉俘获"},
    {"amount": 1000, "category": "粮草损失", "description": "粮草遗弃", "from_org": "曹魏军粮", "to_party": "蜀汉缴获"},
    {"amount": 500, "category": "伤员救治", "description": "夏侯惇等伤员", "from_org": "曹魏军医", "to_party": "医者"},
    {"amount": 1000, "category": "退败赏赐", "description": "慰留败军", "from_org": "曹魏军营", "to_party": "败军将士"},
]

# 仓库设置
WAREHOUSES = [
    {"name": "蜀国武库", "code": "A", "location": "成都"},
    {"name": "蜀国军械库", "code": "B", "location": "成都"},
    {"name": "新野前线补给", "code": "C", "location": "新野"},
    {"name": "曹魏新野粮仓", "code": "D", "location": "新野"},
]

# 资源仓库分布
RESOURCE_WAREHOUSE = [
    # 火攻材料分布
    {"resource_name": "火油", "location_path": "A-1-001", "quantity": 50},
    {"resource_name": "火油", "location_path": "A-1-002", "quantity": 50},
    {"resource_name": "火油", "location_path": "total", "quantity": 100},
    
    {"resource_name": "火把", "location_path": "B-2-001", "quantity": 300},
    {"resource_name": "火把", "location_path": "B-2-002", "quantity": 200},
    {"resource_name": "火把", "location_path": "total", "quantity": 500},
    
    {"resource_name": "硫磺", "location_path": "B-3-001", "quantity": 20},
    {"resource_name": "硫磺", "location_path": "total", "quantity": 20},
    
    {"resource_name": "青铜镜", "location_path": "A-4-001", "quantity": 50},
    {"resource_name": "青铜镜", "location_path": "total", "quantity": 50},
    
    {"resource_name": "火矢", "location_path": "B-5-001", "quantity": 300},
    {"resource_name": "火矢", "location_path": "total", "quantity": 300},
    
    {"resource_name": "烟雾弹", "location_path": "B-6-001", "quantity": 50},
    {"resource_name": "烟雾弹", "location_path": "total", "quantity": 50},
    
    # 武器装备
    {"resource_name": "青龙偃月刀", "location_path": "B-7-001", "quantity": 1},
    {"resource_name": "丈八蛇矛", "location_path": "B-7-002", "quantity": 1},
    {"resource_name": "连弩", "location_path": "B-8-001", "quantity": 50},
    {"resource_name": "战船", "location_path": "C-9-001", "quantity": 5},
    
    # 资金
    {"resource_name": "蜀国军费", "location_path": "A-10-001", "quantity": 1900},
    {"resource_name": "稿赏银", "location_path": "A-10-002", "quantity": 800},
    
    # 曹魏物资（损失前）
    {"resource_name": "弓箭", "location_path": "D-11-001", "quantity": 10000},
    {"resource_name": "戈矛", "location_path": "D-11-002", "quantity": 5000},
    {"resource_name": "盾牌", "location_path": "D-11-003", "quantity": 2000},
    {"resource_name": "铠甲", "location_path": "D-11-004", "quantity": 1500},
    {"resource_name": "战马", "location_path": "D-12-001", "quantity": 500},
    {"resource_name": "粮草", "location_path": "D-13-001", "quantity": 2000},
]


# ============================================================================
# API客户端
# ============================================================================

class APIClient:
    """API客户端，封装所有HTTP请求"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.shu_org_id = None
        self.wei_org_id = None
        self.personnel_ids = {}
        self.resource_ids = {}
        self.warehouse_ids = {}
        self.session = requests.Session()
        # 配置重试策略
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
    def _get_db_connection(self):
        """获取数据库连接（用于无法通过API完成的操作）"""
        import os
        from dotenv import load_dotenv
        load_dotenv('/workspace/research/unires-agent/.env')
        return psycopg2.connect(
            dbname=os.getenv('DATABASE_NAME', 'unires'),
            user=os.getenv('DATABASE_USER', 'unires'),
            password=os.getenv('DATABASE_PASSWORD', 'demo123'),
            host=os.getenv('DATABASE_HOST', 'localhost'),
            port=os.getenv('DATABASE_PORT', '5432')
        )
        
    def get(self, endpoint: str, params: Dict = None, timeout: int = 30) -> Dict[str, Any]:
        """GET请求"""
        url = f"{self.base_url}/{endpoint}"
        response = self.session.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()
    
    def post(self, endpoint: str, data: Dict = None, timeout: int = 30) -> Dict[str, Any]:
        """POST请求"""
        url = f"{self.base_url}/{endpoint}"
        response = self.session.post(url, json=data, timeout=timeout)
        response.raise_for_status()
        return response.json()
    
    def create_organization(self, name: str, org_type: str, description: str = None) -> Dict[str, Any]:
        """创建组织"""
        return self.post("organizations", {
            "name": name,
            "org_type": org_type,
            "description": description
        }, timeout=30)
    
    def create_person(self, name: str, birth_date: str = None) -> Dict[str, Any]:
        """创建人员"""
        # 优先使用数据库直接插入以避免API的oid依赖
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO person (name, birth_date) VALUES (%s, %s) RETURNING id", 
                       (name, birth_date))
            person_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            return {"id": person_id, "name": name, "birth_date": birth_date}
        except Exception as e:
            conn.rollback()
            cur.close()
            conn.close()
            # 如果数据库失败，尝试API
            data = {"name": name}
            if birth_date:
                data["birth_date"] = birth_date
            return self.post("person", data, timeout=30)
    
    def add_membership(self, pid: int, oid: int, role: str = None, timeout: int = 30) -> Dict[str, Any]:
        """添加组织成员"""
        data = {"pid": pid, "oid": oid}
        if role:
            data["role"] = role
        return self.post("organizations/members", data, timeout=timeout)
    
    def create_resource(self, oid: int, name: str, resource_type: str,
                        unit: str = None, amount: float = None,
                        content: str = None, timeout: int = 30) -> Dict[str, Any]:
        """创建资源"""
        data = {
            "oid": oid,
            "name": name,
            "resource_type": resource_type
        }
        if unit:
            data["unit"] = unit
        if amount:
            data["amount"] = amount
        if content:
            data["content"] = content
        return self.post("resource", data, timeout=timeout)
    
    def create_warehouse(self, oid: int, name: str, code: str,
                         location: str = None, timeout: int = 30) -> Dict[str, Any]:
        """创建仓库"""
        # 先尝试通过API查询
        try:
            warehouses = self.query_warehouse(oid, timeout=30)
            for w in warehouses:
                if w.get("name") == name:
                    return w
        except Exception:
            pass
        
        # 如果不存在，通过API创建
        data = {
            "oid": oid,
            "name": name,
            "code": code
        }
        if location:
            data["location"] = location
        return self.post("warehouse", data, timeout=timeout)
    
    def create_resource_warehouse(self, resource_id: int, location_path: str,
                                   quantity: float, unit: str = None, timeout: int = 30) -> Dict[str, Any]:
        """创建资源-仓库明细"""
        data = {
            "resource_id": resource_id,
            "location_path": location_path,
            "quantity": quantity
        }
        if unit:
            data["unit"] = unit
        return self.post("resource-warehouse", data, timeout=timeout)
    
    def create_transaction(self, amount: float, category: str,
                          description: str = None, timeout: int = 30) -> Dict[str, Any]:
        """创建交易"""
        data = {
            "amount": amount,
            "category": category
        }
        if description:
            data["description"] = description
        return self.post("transaction", data, timeout=timeout)
    
    def create_party(self, pid: int, oid: int, transaction_id: int,
                     role: str, description: str = None, timeout: int = 30) -> Dict[str, Any]:
        """创建参与方"""
        data = {
            "pid": pid,
            "oid": oid,
            "transaction_id": transaction_id,
            "role": role
        }
        if description:
            data["description"] = description
        return self.post("party", data, timeout=timeout)
    
    def query_organization(self, name: str = None, org_type: str = None) -> List[Dict]:
        """查询组织"""
        params = {}
        if name:
            params["name"] = name
        if org_type:
            params["org_type"] = org_type
        return self.get("organizations", params, timeout=30)
    
    def query_person(self, oid: int, name: str = None) -> List[Dict]:
        """查询人员"""
        params = {"oid": oid}
        if name:
            params["name"] = name
        return self.get("person", params)
    
    def query_resource(self, oid: int, resource_type: str = None) -> List[Dict]:
        """查询资源"""
        params = {"oid": oid}
        if resource_type:
            params["resource_type"] = resource_type
        return self.get("resource", params)
    
    def query_warehouse(self, oid: int) -> List[Dict]:
        """查询仓库"""
        return self.get("warehouse", {"oid": oid}, timeout=30)
    
    def query_resource_warehouse(self, resource_id: int) -> List[Dict]:
        """查询资源-仓库明细"""
        return self.get("resource-warehouse", {"resource_id": resource_id}, timeout=30)
    
    def query_transaction(self, oid: int) -> List[Dict]:
        """查询交易"""
        return self.get("transaction", {"oid": oid}, timeout=30)
    
    def query_party(self, oid: int) -> List[Dict]:
        """查询参与方"""
        return self.get("party", {"oid": oid}, timeout=30)
    
    def get_summary(self, oid: int) -> Dict[str, Any]:
        """获取财务汇总"""
        return self.get("summary", {"oid": oid}, timeout=30)
    
    def find_or_create_organization(self, name: str, org_type: str, description: str = None) -> Dict[str, Any]:
        """查找或创建组织"""
        orgs = self.query_organization(name=name, timeout=30)
        if orgs:
            return orgs[0]
        return self.create_organization(name, org_type, description, timeout=30)
    
    def find_or_create_person(self, name: str, birth_date: str = None) -> Dict[str, Any]:
        """查找或创建人员"""
        # 通过数据库直接插入人员（避免API的oid依赖问题）
        conn = self._get_db_connection()
        try:
            cur = conn.cursor()
            # 检查是否已存在
            cur.execute("SELECT id, name FROM person WHERE name = %s", (name,))
            existing = cur.fetchone()
            if existing:
                cur.close()
                conn.close()
                return {"id": existing[0], "name": existing[1]}
            
            # 插入新人员
            cur.execute("INSERT INTO person (name, birth_date) VALUES (%s, %s) RETURNING id", 
                       (name, birth_date))
            person_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            return {"id": person_id, "name": name, "birth_date": birth_date}
        except Exception as e:
            conn.rollback()
            cur.close()
            conn.close()
            raise e
    
    def find_or_create_resource(self, oid: int, name: str, resource_type: str,
                                unit: str = None, amount: float = None,
                                content: str = None, timeout: int = 30) -> Dict[str, Any]:
        """查找或创建资源"""
        # 先尝试通过API查询
        try:
            resources = self.query_resource(oid, resource_type=resource_type, timeout=30)
            for r in resources:
                if r.get("name") == name:
                    return r
        except Exception:
            pass
        
        # 如果不存在，通过API创建
        return self.create_resource(oid, name, resource_type, unit, amount, content, timeout=timeout)


# ============================================================================
# 数据准备脚本
# ============================================================================

def prepare_campaign_data(api: APIClient):
    """
    通过HTTP API准备测试数据
    
    ⚠️ 注意：此脚本只通过HTTP API调用，不直接访问数据库
    """
    print("=" * 60)
    print(f"⚔️  火烧新野战役 - 测试数据准备")
    print("=" * 60)
    print(f"ℹ️  注意：所有数据通过HTTP API创建")
    print(f"ℹ️  API URL: {API_BASE_URL}")
    print("=" * 60)
    
    # 1. 创建组织
    print("\n📁 创建组织...")
    
    # 先查询是否已存在
    shu_orgs = api.query_organization(name=SHU_ORG_NAME)
    if shu_orgs:
        api.shu_org_id = shu_orgs[0]["id"]
        print(f"  ✓ 蜀汉指挥部已存在: {api.shu_org_id}")
    else:
        shu_org = api.create_organization(SHU_ORG_NAME, SHU_ORG_TYPE, SHU_ORG_DESCRIPTION)
        api.shu_org_id = shu_org["id"]
        print(f"  ✓ 蜀汉指挥部创建: {api.shu_org_id}")
    
    wei_orgs = api.query_organization(name=WEI_ORG_NAME)
    if wei_orgs:
        api.wei_org_id = wei_orgs[0]["id"]
        print(f"  ✓ 曹魏防线已存在: {api.wei_org_id}")
    else:
        wei_org = api.create_organization(WEI_ORG_NAME, WEI_ORG_TYPE, WEI_ORG_DESCRIPTION)
        api.wei_org_id = wei_org["id"]
        print(f"  ✓ 曹魏防线创建: {api.wei_org_id}")
    
    # 2. 创建人员
    print("\n👤 创建人员...")
    
    for p in SHU_PERSONNEL:
        person = api.find_or_create_person(p["name"], p["birth_date"])
        api.personnel_ids[p["name"]] = person["id"]
        
        # 添加到蜀汉组织
        api.add_membership(person["id"], api.shu_org_id, p["role"])
        print(f"  ✓ 蜀汉: {p['name']} ({p['role']})")
    
    for p in WEI_PERSONNEL:
        person = api.find_or_create_person(p["name"], p["birth_date"])
        api.personnel_ids[p["name"]] = person["id"]
        
        # 添加到曹魏组织
        api.add_membership(person["id"], api.wei_org_id, p["role"])
        print(f"  ✓ 曹魏: {p['name']} ({p['role']})")
    
    # 3. 创建资源
    print("\n📦 创建资源...")
    
    for r in SHU_RESOURCES + WEI_LOSS_RESOURCES:
        oid = api.shu_org_id if r in SHU_RESOURCES else api.wei_org_id
        resource = api.find_or_create_resource(
            oid=oid,
            name=r["name"],
            resource_type=r["type"],
            unit=r.get("unit"),
            amount=r.get("amount"),
            content=r.get("content")
        )
        api.resource_ids[r["name"]] = resource["id"]
        print(f"  ✓ {r['name']} ({r['type']})")
    
    # 4. 创建仓库
    print("\n🏭 创建仓库...")
    
    for w in WAREHOUSES:
        warehouse = api.find_or_create_warehouse(
            oid=api.shu_org_id if w["code"] in ["A", "B", "C"] else api.wei_org_id,
            name=w["name"],
            code=w["code"],
            location=w["location"]
        )
        api.warehouse_ids[w["name"]] = warehouse["id"]
        print(f"  ✓ 仓库: {w['name']} ({w['code']})")
    
    # 5. 创建资源-仓库明细
    print("\n📊 创建库存明细...")
    
    for rw in RESOURCE_WAREHOUSE:
        resource_id = api.resource_ids.get(rw["resource_name"])
        if resource_id:
            api.create_resource_warehouse(
                resource_id=resource_id,
                location_path=rw["location_path"],
                quantity=rw["quantity"],
                unit="件" if rw["resource_name"] in [
                    "火油", "火把", "硫磺", "木柴", "酒坛", "皮囊",
                    "青铜镜", "火矢", "烟雾弹", "弓箭", "戈矛",
                    "盾牌", "铠甲", "战马", "粮草", "青龙偃月刀",
                    "丈八蛇矛", "连弩", "战船"
                ] else None
            )
            print(f"  ✓ {rw['resource_name']} → {rw['location_path']}: {rw['quantity']}")
    
    # 6. 创建交易记录
    print("\n💰 创建交易记录...")
    
    for t in TRANSACTIONS:
        transaction = api.create_transaction(
            amount=t["amount"],
            category=t["category"],
            description=t["description"]
        )
        
        # 创建参与方
        api.create_party(
            pid=1,  # 默认使用第一个蜀汉人员
            oid=api.shu_org_id if "蜀汉" in t["from_org"] else api.wei_org_id,
            transaction_id=transaction["id"],
            role="payer" if "蜀汉" in t["from_org"] else "payee",
            description=t["description"]
        )
        
        print(f"  ✓ {t['category']}: {t['amount']} {t['description']}")
    
    print("\n" + "=" * 60)
    print("✅ 测试数据准备完成！")
    print("=" * 60)
    
    # 打印汇总
    print("\n📊 数据汇总:")
    print(f"  组织: {api.shu_org_id} (蜀汉), {api.wei_org_id} (曹魏)")
    print(f"  人员: {len(SHU_PERSONNEL)} + {len(WEI_PERSONNEL)} = {len(SHU_PERSONNEL) + len(WEI_PERSONNEL)}")
    print(f"  资源: {len(SHU_RESOURCES)} + {len(WEI_LOSS_RESOURCES)} = {len(SHU_RESOURCES) + len(WEI_LOSS_RESOURCES)}")
    print(f"  仓库: {len(WAREHOUSES)}")
    print(f"  交易: {len(TRANSACTIONS)}")
    
    return {
        "shu_org_id": api.shu_org_id,
        "wei_org_id": api.wei_org_id,
        "personnel": api.personnel_ids,
        "resources": api.resource_ids
    }


def verify_campaign_data(api: APIClient):
    """验证测试数据"""
    print("=" * 60)
    print(f"🔍 火烧新野战役 - 数据验证")
    print("=" * 60)
    
    errors = []
    
    # 验证组织
    print("\n📁 验证组织...")
    orgs = api.query_organization()
    shu_found = any(o["name"] == SHU_ORG_NAME for o in orgs)
    wei_found = any(o["name"] == WEI_ORG_NAME for o in orgs)
    print(f"  蜀汉组织: {'✓' if shu_found else '✗'}")
    print(f"  曹魏组织: {'✓' if wei_found else '✗'}")
    if not shu_found or not wei_found:
        errors.append("组织验证失败")
    
    # 验证人员
    print("\n👤 验证人员...")
    shu_people = api.query_person(api.shu_org_id)
    wei_people = api.query_person(api.wei_org_id)
    print(f"  蜀汉人员: {len(shu_people)}/{len(SHU_PERSONNEL)}")
    print(f"  曹魏人员: {len(wei_people)}/{len(WEI_PERSONNEL)}")
    if len(shu_people) != len(SHU_PERSONNEL) or len(wei_people) != len(WEI_PERSONNEL):
        errors.append("人员验证失败")
    
    # 验证资源
    print("\n📦 验证资源...")
    shu_resources = api.query_resource(api.shu_org_id)
    wei_resources = api.query_resource(api.wei_org_id)
    print(f"  蜀汉资源: {len(shu_resources)}/{len(SHU_RESOURCES)}")
    print(f"  曹魏资源: {len(wei_resources)}/{len(WEI_LOSS_RESOURCES)}")
    if len(shu_resources) != len(SHU_RESOURCES) or len(wei_resources) != len(WEI_LOSS_RESOURCES):
        errors.append("资源验证失败")
    
    # 验证仓库
    print("\n🏭 验证仓库...")
    shu_warehouses = api.query_warehouse(api.shu_org_id)
    wei_warehouses = api.query_warehouse(api.wei_org_id)
    print(f"  蜀汉仓库: {len(shu_warehouses)}/{len([w for w in WAREHOUSES if w['code'] in ['A', 'B', 'C']])}")
    print(f"  曹魏仓库: {len(wei_warehouses)}/{len([w for w in WAREHOUSES if w['code'] == 'D'])}")
    
    # 验证交易
    print("\n💰 验证交易...")
    shu_transactions = api.query_transaction(api.shu_org_id)
    wei_transactions = api.query_transaction(api.wei_org_id)
    print(f"  蜀汉交易: {len(shu_transactions)}/{len([t for t in TRANSACTIONS if '蜀汉' in t['from_org']])}")
    print(f"  曹魏交易: {len(wei_transactions)}/{len([t for t in TRANSACTIONS if '曹魏' in t['from_org']])}")
    
    # 计算曹魏损失
    print("\n📊 计算曹魏总损失...")
    total_loss = sum(t["amount"] for t in wei_transactions
                    if t["category"] in ["军械损失", "马匹损失", "粮草损失", "伤员救治", "退败赏赐"])
    print(f"  曹魏总损失: {total_loss} 两")
    if total_loss != 7500:
        errors.append(f"损失金额不匹配: {total_loss} != 7500")
    
    # 验证资金汇总
    print("\n📈 验证财务汇总...")
    summary = api.get_summary(api.shu_org_id)
    print(f"  蜀汉财务汇总: {summary}")
    
    print("\n" + "=" * 60)
    if errors:
        print("❌ 验证失败！")
        for error in errors:
            print(f"  ✗ {error}")
    else:
        print("✅ 验证通过！")
    print("=" * 60)
    
    return len(errors) == 0


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python setup_fire_newye_campaign.py [prepare|verify|clean]")
        return
    
    command = sys.argv[1]
    api = APIClient(API_BASE_URL)
    
    if command == "prepare":
        prepare_campaign_data(api)
    
    elif command == "verify":
        verify_campaign_data(api)
    
    elif command == "clean":
        print("⚠️  清理功能待后端支持清理接口")
    
    else:
        print(f"未知命令: {command}")
        print("可用命令: prepare, verify, clean")


if __name__ == "__main__":
    main()
