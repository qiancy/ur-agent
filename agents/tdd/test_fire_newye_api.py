"""
测试脚本：火烧新野战役 - 通过API创建和验证测试数据

运行方式：
    python test_fire_newye_api.py [command]

命令：
    setup     - 创建测试数据
    verify    - 验证测试数据
    clean     - 清理测试数据
    all       - 全流程（setup + verify + clean）
"""

import requests
import sys
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
    {"name": "黄忠", "role": "后勤官", "birth_date": "120-01-01"},
]

WEI_PERSONNEL = [
    {"name": "曹洪", "role": "主将", "birth_date": "170-01-01"},
    {"name": "夏侯惇", "role": "副将", "birth_date": "155-01-01"},
    {"name": "于禁", "role": "先锋", "birth_date": "170-01-01"},
]

# 物资清单
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
    {"name": "蜀国兵力", "type": "human", "puid": "liubei", "content": "火攻部队"},
    # 知识
    {"name": "火攻计策", "type": "knowledge", "content": "火油倾泻+青铜镜点火"},
    {"name": "火烧新野计划", "type": "knowledge", "content": "伏兵林中，切断退路"},
]

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
    {"name": "蜀国武库", "code": "A", "location": "成都", "ouid": "fire_xinye_shu"},
    {"name": "蜀国军械库", "code": "B", "location": "成都", "ouid": "fire_xinye_shu"},
    {"name": "新野前线补给", "code": "C", "location": "新野", "ouid": "fire_xinye_shu"},
    {"name": "曹魏新野粮仓", "code": "D", "location": "新野", "ouid": "fire_xinye_wei"},
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
        
    def get(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        """GET请求"""
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, params=params)
        return response.json()
    
    def post(self, endpoint: str, data: Dict = None, params: Dict = None) -> Dict[str, Any]:
        """POST请求"""
        url = f"{self.base_url}/{endpoint}"
        response = requests.post(url, json=data, params=params)
        return response.json()
    
    def create_organization(self, name: str, org_type: str, description: str = None) -> Dict[str, Any]:
        """创建组织"""
        return self.post("organizations", {
            "name": name,
            "org_type": org_type,
            "description": description
        })
    
    def create_person(self, name: str, birth_date: str = None) -> Dict[str, Any]:
        """创建人员"""
        data = {"name": name}
        if birth_date:
            data["birth_date"] = birth_date
        return self.post("person", data)
    
    def add_membership(self, puid: str, ouid: str, role: str = None) -> Dict[str, Any]:
        """添加组织成员"""
        data = {"puid": puid, "ouid": ouid}
        if role:
            data["role"] = role
        return self.post("organizations/members", data)
    
    def create_resource(self, ouid: str, name: str, resource_type: str,
                        unit: str = None, amount: float = None,
                        content: str = None, puid: str = None,
                        currency: str = None) -> Dict[str, Any]:
        """创建资源"""
        data = {
            "ouid": ouid,
            "name": name,
            "resource_type": resource_type
        }
        if unit:
            data["unit"] = unit
        if amount:
            data["amount"] = amount
        if content:
            data["content"] = content
        if puid:
            data["puid"] = puid
        if currency:
            data["currency"] = currency
        return self.post("resource", data)
    
    def create_warehouse(self, ouid: str, name: str, code: str,
                         location: str = None) -> Dict[str, Any]:
        """创建仓库"""
        data = {
            "ouid": ouid,
            "name": name,
            "code": code
        }
        if location:
            data["location"] = location
        return self.post("warehouse", data)
    
    def create_resource_warehouse(self, resource_id: int, location_path: str,
                                    quantity: float, unit: str = None,
                                    ouid: str = None) -> Dict[str, Any]:
        """创建资源-仓库明细"""
        data = {
            "resource_id": resource_id,
            "location_path": location_path,
            "quantity": quantity
        }
        if unit:
            data["unit"] = unit
        params = {"ouid": ouid} if ouid else None
        return self.post("resource-warehouse", data, params=params)

    def create_transaction(self, amount: float, category: str,
                           description: str = None) -> Dict[str, Any]:
        """创建交易"""
        data = {
            "amount": amount,
            "category": category
        }
        if description:
            data["description"] = description
        return self.post("transaction", data)
    
    def create_party(self, puid: str, ouid: str, transaction_uid: str,
                     role: str, description: str = None) -> Dict[str, Any]:
        """创建参与方"""
        data = {
            "puid": puid,
            "ouid": ouid,
            "transaction_uid": transaction_uid,
            "role": role
        }
        if description:
            data["description"] = description
        return self.post("party", data)
    
    def query_organization(self, name: str = None, org_type: str = None) -> List[Dict]:
        """查询组织"""
        params = {}
        if name:
            params["name"] = name
        if org_type:
            params["org_type"] = org_type
        return self.get("organizations", params)
    
    def query_person(self, ouid: str, name: str = None) -> List[Dict]:
        """查询人员"""
        params = {"ouid": ouid}
        if name:
            params["name"] = name
        return self.get("person", params)
    
    def query_resource(self, ouid: str, resource_type: str = None) -> List[Dict]:
        """查询资源"""
        params = {"ouid": ouid}
        if resource_type:
            params["resource_type"] = resource_type
        return self.get("resource", params)
    
    def query_warehouse(self, ouid: str) -> List[Dict]:
        """查询仓库"""
        return self.get("warehouse", {"ouid": ouid})
    
    def query_resource_warehouse(self, resource_id: int, ouid: str = None) -> List[Dict]:
        """查询资源-仓库明细"""
        params = {"resource_id": resource_id}
        if ouid:
            params["ouid"] = ouid
        return self.get("resource-warehouse", params)
    
    def query_transaction(self, ouid: str) -> List[Dict]:
        """查询交易"""
        return self.get("transaction", {"ouid": ouid})
    
    def query_party(self, ouid: str) -> List[Dict]:
        """查询参与方"""
        return self.get("party", {"ouid": ouid})
    
    def get_summary(self, ouid: str) -> Dict[str, Any]:
        """获取财务汇总"""
        return self.get("summary", {"ouid": ouid})


# ============================================================================
# 测试脚本
# ============================================================================

def init_campaign_via_api(ouid: str = 10, puid: str = 101, campaign_name: str = "火烧新野"):
    """
    通过初始化API准备测试数据
    
    注意：此功能依赖后端提供的初始化API。
    如果API未实现，请先运行数据库初始化脚本：
        python scripts/init_db.py --ouid={ouid} --puid={puid}
    
    API调用格式：
        POST /api/init/campaign
        Body: {
            "ouid": {ouid},
            "puid": {puid},
            "campaign_name": "{campaign_name}",
            "init_all_data": true
        }
    """
    print(f"ℹ️  初始化战役数据: ouid={ouid}, puid={puid}, campaign={campaign_name}")
    print(f"ℹ️  注意：需要后端提供 /api/init/campaign API")
    print(f"ℹ️  如API未实现，请先运行: python scripts/init_db.py --ouid={ouid} --puid={puid}")
    return {
        "ouid": ouid,
        "puid": puid,
        "campaign_name": campaign_name,
        "api_available": False,  # 待后端实现
        "note": "等待后端初始化API实现"
    }


class FireNewyeTest:
    """火烧新野战役测试脚本"""
    
    def __init__(self, api: APIClient):
        self.api = api
        self.shu_org_ouid = None
        self.wei_org_ouid = None
        self.personnel_ids = {}
        self.resource_ids = {}
        
    def setup_campaign(self):
        """设置测试战役数据"""
        print("=" * 60)
        print(f"⚔️  火烧新野战役 - 测试数据初始化")
        print("=" * 60)
        
        # 尝试通过API初始化
        print("\n🔄 尝试通过API初始化数据...")
        api_init_result = init_campaign_via_api(
            ouid="fire_xinye_shu",
            puid="liubei",
            campaign_name=SHU_ORG_NAME
        )
        
        if api_init_result.get("api_available"):
            print(f"✓ API初始化成功: {api_init_result}")
        else:
            print(f"⚠️  API初始化不可用: {api_init_result.get('note')}")
            print("ℹ️  将使用现有API逐个创建数据...")
        
        # 1. 创建组织
        print("\n📁 创建组织...")
        
        # 先获取所有组织，然后匹配
        all_orgs = self.api.query_organization()
        shu_found = False
        wei_found = False
        
        for org in all_orgs:
            if org["name"] == SHU_ORG_NAME:
                self.shu_org_ouid = org["ouid"]
                shu_found = True
                print(f"  ✓ 蜀汉指挥部已存在: {self.shu_org_ouid}")
                break
        
        if not shu_found:
            shu_org = self.api.create_organization(
                SHU_ORG_NAME, SHU_ORG_TYPE, SHU_ORG_DESCRIPTION
            )
            self.shu_org_ouid = shu_org["ouid"]
            print(f"  ✓ 蜀汉指挥部创建: {self.shu_org_ouid}")
        
        for org in all_orgs:
            if org["name"] == WEI_ORG_NAME:
                self.wei_org_ouid = org["ouid"]
                wei_found = True
                print(f"  ✓ 曹魏防线已存在: {self.wei_org_ouid}")
                break
        
        if not wei_found:
            wei_org = self.api.create_organization(
                WEI_ORG_NAME, WEI_ORG_TYPE, WEI_ORG_DESCRIPTION
            )
            self.wei_org_ouid = wei_org["ouid"]
            print(f"  ✓ 曹魏防线创建: {self.wei_org_ouid}")
        
        # 创建默认人员用于交易
        default_person = self.api.query_person(self.shu_org_ouid, name="默认人员")
        if not default_person:
            default_p = self.api.create_person("默认人员")
            self.api.add_membership(default_p["puid"], self.shu_org_ouid, "财务专员")
            self.default_person_puid = default_p["puid"]
        else:
            self.default_person_puid = default_person[0]["puid"]
        
        # 2. 创建人员
        print("\n👤 创建人员...")
        
        for p in SHU_PERSONNEL:
            # 查询是否已存在
            people = self.api.query_person(self.shu_org_ouid, name=p["name"])
            if people:
                self.personnel_ids[p["name"]] = people[0]["id"]
                print(f"  ✓ 蜀汉人员已存在: {p['name']}")
            else:
                person = self.api.create_person(p["name"], p["birth_date"])
                self.personnel_ids[p["name"]] = person["id"]
                # 添加到组织
                self.api.add_membership(person["puid"], self.shu_org_ouid, p["role"])
                print(f"  ✓ 蜀汉人员创建: {p['name']} ({p['role']})")
        
        for p in WEI_PERSONNEL:
            people = self.api.query_person(self.wei_org_ouid, name=p["name"])
            if people:
                self.personnel_ids[p["name"]] = people[0]["id"]
                print(f"  ✓ 曹魏人员已存在: {p['name']}")
            else:
                person = self.api.create_person(p["name"], p["birth_date"])
                self.personnel_ids[p["name"]] = person["id"]
                self.api.add_membership(person["puid"], self.wei_org_ouid, p["role"])
                print(f"  ✓ 曹魏人员创建: {p['name']} ({p['role']})")
        
        # 3. 创建资源
        print("\n📦 创建资源...")
        
        for r in SHU_RESOURCES + WEI_LOSS_RESOURCES:
            # 查询是否已存在
            resources = self.api.query_resource(
                self.shu_org_ouid if r in SHU_RESOURCES else self.wei_org_ouid,
                resource_type=r["type"]
            )
            existing = [res for res in resources if res["name"] == r["name"]]
            
            if existing:
                self.resource_ids[r["name"]] = existing[0]["id"]
                print(f"  ✓ 资源已存在: {r['name']}")
            else:
                resource = self.api.create_resource(
                    ouid=self.shu_org_ouid if r in SHU_RESOURCES else self.wei_org_ouid,
                    name=r["name"],
                    resource_type=r["type"],
                    unit=r.get("unit"),
                    amount=r.get("amount"),
                    content=r.get("content"),
                    puid=r.get("puid")
                )
                self.resource_ids[r["name"]] = resource["id"]
                print(f"  ✓ 资源创建: {r['name']} ({r['type']})")
        
        # 4. 创建仓库
        print("\n🏭 创建仓库...")
        
        for w in WAREHOUSES:
            warehouses = self.api.query_warehouse(w["ouid"])
            existing = [wh for wh in warehouses if wh["name"] == w["name"]]
            
            if existing:
                print(f"  ✓ 仓库已存在: {w['name']}")
            else:
                try:
                    response = self.api.create_warehouse(
                        w["ouid"], w["name"], w["code"], w["location"]
                    )
                    print(f"  ✓ 仓库创建: {w['name']} ({w['code']})")
                except Exception as e:
                    print(f"  ✗ 仓库创建失败 {w['name']}: {e}")
        
        # 5. 创建资源-仓库明细
        print("\n📊 创建库存明细...")
        
        for rw in RESOURCE_WAREHOUSE:
            try:
                self.api.create_resource_warehouse(
                    resource_id=self.resource_ids.get(rw["resource_name"]),
                    location_path=rw["location_path"],
                    quantity=rw["quantity"],
                    ouid=self.shu_org_ouid if rw["resource_name"] in SHU_RESOURCES else self.wei_org_ouid,
                    unit="件" if rw["resource_name"] in [
                        "火油", "火把", "硫磺", "木柴", "酒坛", "皮囊", 
                        "青铜镜", "火矢", "烟雾弹", "弓箭", "戈矛", 
                        "盾牌", "铠甲", "战马", "粮草", "青龙偃月刀", 
                        "丈八蛇矛", "连弩", "战船"
                    ] else None
                )
                print(f"  ✓ {rw['resource_name']} → {rw['location_path']}: {rw['quantity']}")
            except Exception as e:
                print(f"  ✗ {rw['resource_name']} 创建失败: {e}")
        
        # 6. 创建交易记录
        print("\n💰 创建交易记录...")
        
        for t in TRANSACTIONS:
            try:
                transaction = self.api.create_transaction(
                    amount=t["amount"],
                    category=t["category"],
                    description=t["description"]
                )
                
                self.api.create_party(
                    puid=self.default_person_puid,
                    ouid=self.shu_org_ouid if "蜀汉" in t["from_org"] else self.wei_org_ouid,
                    transaction_uid=transaction["transaction_uid"],
                    role="payer" if "蜀汉" in t["from_org"] else "payee",
                    description=t["description"]
                )
                
                print(f"  ✓ {t['category']}: {t['amount']} {t['description']}")
            except Exception as e:
                print(f"  ✗ {t['category']} 创建失败: {e}")
        
        print("\n" + "=" * 60)
        print("✅ 数据初始化完成！")
        print("=" * 60)
        
        return {
            "shu_org_ouid": self.shu_org_ouid,
            "wei_org_ouid": self.wei_org_ouid,
            "personnel": self.personnel_ids,
            "resources": self.resource_ids
        }
    
    def verify_campaign(self):
        """验证测试数据"""
        print("=" * 60)
        print(f"🔍 火烧新野战役 - 数据验证")
        print("=" * 60)
        
        errors = []
        
        # 验证组织
        print("\n📁 验证组织...")
        orgs = self.api.query_organization()
        shu_found = any(o["name"] == SHU_ORG_NAME for o in orgs)
        wei_found = any(o["name"] == WEI_ORG_NAME for o in orgs)
        print(f"  蜀汉组织: {'✓' if shu_found else '✗'}")
        print(f"  曹魏组织: {'✓' if wei_found else '✗'}")
        if not shu_found or not wei_found:
            errors.append("组织验证失败")
        
        # 验证人员
        print("\n👤 验证人员...")
        shu_people = self.api.query_person(self.shu_org_ouid)
        wei_people = self.api.query_person(self.wei_org_ouid)
        shu_count = len(shu_people)
        wei_count = len(wei_people)
        print(f"  蜀汉人员: {shu_count}/{len(SHU_PERSONNEL)}")
        print(f"  曹魏人员: {wei_count}/{len(WEI_PERSONNEL)}")
        # 只验证蜀汉人员完整
        if shu_count != len(SHU_PERSONNEL):
            errors.append("蜀汉人员验证失败")
        
        # 验证资源
        print("\n📦 验证资源...")
        shu_resources = self.api.query_resource(self.shu_org_ouid)
        shu_resource_count = len(shu_resources)
        print(f"  蜀汉资源: {shu_resource_count}/{len(SHU_RESOURCES)}")
        if shu_resource_count != len(SHU_RESOURCES):
            errors.append("蜀汉资源验证失败")
        
        # 验证仓库
        print("\n🏭 验证仓库...")
        shu_warehouses = self.api.query_warehouse(self.shu_org_ouid)
        wei_warehouses = self.api.query_warehouse(self.wei_org_ouid)
        print(f"  蜀汉仓库: {len(shu_warehouses)}/{len([w for w in WAREHOUSES if w['ouid'] == self.shu_org_ouid])}")
        print(f"  曹魏仓库: {len(wei_warehouses)}/{len([w for w in WAREHOUSES if w['ouid'] == self.wei_org_ouid])}")
        
        # 验证交易
        print("\n💰 验证交易...")
        shu_transactions = self.api.query_transaction(self.shu_org_ouid)
        wei_transactions = self.api.query_transaction(self.wei_org_ouid)
        
        # 解析交易数据
        shu_trans_count = len(shu_transactions)
        wei_trans_count = len(wei_transactions)
        
        # 从party信息中计算损失
        wei_loss_amount = 0.0
        for t in wei_transactions:
            if isinstance(t, dict):
                parties = t.get("parties", [])
                for p in parties:
                    if isinstance(p, dict):
                        role = p.get("role", "")
                        # 曹魏的损失交易中，party角色是payer，funds_change为负值
                        if role == "payer":
                            funds_change = float(p.get("funds_change", 0))
                            wei_loss_amount += abs(funds_change)
        
        print(f"  蜀汉交易: {shu_trans_count}/{len([t for t in TRANSACTIONS if '蜀汉' in t['from_org']])}")
        print(f"  曹魏交易: {wei_trans_count}/{len([t for t in TRANSACTIONS if '曹魏' in t['from_org']])}")
        print(f"  曹魏总损失: {wei_loss_amount} 两")
        if wei_loss_amount != 7500:
            errors.append(f"损失金额不匹配: {wei_loss_amount} != 7500")
        
        # 验证资金汇总
        print("\n📈 验证财务汇总...")
        try:
            summary = self.api.get_summary(self.shu_org_ouid)
            print(f"  蜀汉财务汇总: {summary}")
        except Exception as e:
            print(f"  财务汇总获取失败: {e}")
        
        print("\n" + "=" * 60)
        if errors:
            print("❌ 验证失败！")
            for error in errors:
                print(f"  ✗ {error}")
        else:
            print("✅ 验证通过！")
        print("=" * 60)
        
        return len(errors) == 0
    
    def clean_campaign(self):
        """清理测试数据"""
        print("=" * 60)
        print(f"🗑️  清理测试数据")
        print("=" * 60)
        
        # 这里可以添加清理逻辑
        print("⚠️  清理功能待实现...")
        
        print("=" * 60)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python test_fire_newye_api.py [setup|verify|clean|all|init-api]")
        return
    
    command = sys.argv[1]
    
    if command == "init-api":
        # 单独调用初始化API
        result = init_campaign_via_api()
        print(f"初始化结果: {result}")
        return
    
    api = APIClient(API_BASE_URL)
    test = FireNewyeTest(api)
    
    if command == "setup":
        test.setup_campaign()
    
    elif command == "verify":
        test.verify_campaign()
    
    elif command == "clean":
        test.clean_campaign()
    
    elif command == "all":
        test.setup_campaign()
        test.verify_campaign()
        test.clean_campaign()
    
    else:
        print(f"未知命令: {command}")
        print("可用命令: setup, verify, clean, all")


if __name__ == "__main__":
    main()
