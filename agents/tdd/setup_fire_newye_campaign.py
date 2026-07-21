#!/usr/bin/env python3
"""
火烧新野战役 - 测试数据生成脚本（修正版）
用于测试 Uni-Resource Agent 的资源管理能力
"""

from src.db.database import (
    init_database, create_organization, create_person, add_membership,
    create_resource, create_warehouse, create_resource_warehouse,
    create_transaction, create_party, get_db_connection
)

# ============================================================================
# 战役配置
# ============================================================================

CAMPAIGN_NAME = "火烧新野"
CAMPAIGN_ID = 1001  # 用于标记此次战役的所有数据

# 蜀汉阵营配置
SHU_ORG = {
    "name": "蜀汉-火烧新野战役",
    "org_type": "military",
    "description": "诸葛亮火烧新野战役指挥部"
}

# 曹魏阵营配置
WEI_ORG = {
    "name": "曹魏-新野守军",
    "org_type": "military",
    "description": "曹魏新野防线"
}

# 参战人员名单
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

# 资金流动
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
# 数据生成函数
# ============================================================================

def setup_campaign():
    """ setup the campaign data """
    print("=" * 60)
    print(f"⚔️  火烧新野战役 - 测试数据初始化")
    print("=" * 60)
    
    # 1. 创建组织
    print("\n📁 创建组织...")
    shu_org = create_organization(**SHU_ORG)
    print(f"  ✓ 蜀汉指挥部: {shu_org['id']} - {SHU_ORG['name']}")
    
    wei_org = create_organization(**WEI_ORG)
    print(f"  ✓ 曹魏防线: {wei_org['id']} - {WEI_ORG['name']}")
    
    # 2. 创建人员
    print("\n👤 创建人员...")
    shu_personnel_ids = {}
    wei_personnel_ids = {}
    
    for p in SHU_PERSONNEL:
        person = create_person(p["name"], p["birth_date"])
        shu_personnel_ids[p["name"]] = person["id"]
        add_membership(person["id"], shu_org["id"], p["role"])
        print(f"  ✓ 蜀汉: {p['name']} ({p['role']})")
    
    for p in WEI_PERSONNEL:
        person = create_person(p["name"], p["birth_date"])
        wei_personnel_ids[p["name"]] = person["id"]
        add_membership(person["id"], wei_org["id"], p["role"])
        print(f"  ✓ 曹魏: {p['name']} ({p['role']})")
    
    # 3. 创建资源
    print("\n📦 创建资源...")
    resource_ids = {}
    
    for r in SHU_RESOURCES + WEI_LOSS_RESOURCES:
        resource = create_resource(
            oid=shu_org["id"] if r in SHU_RESOURCES else wei_org["id"],
            name=r["name"],
            resource_type=r["type"],
            unit=r.get("unit"),
            amount=r.get("amount"),
            content=r.get("content"),
            pid=r.get("pid")
        )
        resource_ids[r["name"]] = resource["id"]
        print(f"  ✓ {r['type']}: {r['name']} ({r.get('unit', '')})")
    
    # 4. 创建仓库
    print("\n🏭 创建仓库...")
    warehouse_ids = {}
    
    for w in WAREHOUSES:
        warehouse = create_warehouse(
            oid=shu_org["id"] if w["code"] in ["A", "B", "C"] else wei_org["id"],
            name=w["name"],
            code=w["code"],
            location=w["location"]
        )
        warehouse_ids[w["name"]] = warehouse["id"]
        print(f"  ✓ 仓库: {w['name']} ({w['code']})")
    
    # 5. 创建资源-仓库明细
    print("\n📊 创建库存明细...")
    for rw in RESOURCE_WAREHOUSE:
        resource_id = resource_ids.get(rw["resource_name"])
        if resource_id:
            create_resource_warehouse(
                resource_id=resource_id,
                location_path=rw["location_path"],
                quantity=rw["quantity"],
                unit="件" if rw["resource_name"] in ["火油", "火把", "硫磺", "木柴", "酒坛", "皮囊", "青铜镜", "火矢", "烟雾弹", "弓箭", "戈矛", "盾牌", "铠甲", "战马", "粮草", "青龙偃月刀", "丈八蛇矛", "连弩", "战船"] else None
            )
            print(f"  ✓ {rw['resource_name']} → {rw['location_path']}: {rw['quantity']}")
    
    # 6. 创建交易记录
    print("\n💰 创建交易记录...")
    for t in TRANSACTIONS:
        transaction = create_transaction(
            amount=t["amount"],
            category=t["category"],
            description=t["description"]
        )
        
        # 创建参与方
        party = create_party(
            pid=1,  # 默认使用第一个蜀汉人员
            oid=shu_org["id"] if "蜀汉" in t["from_org"] else wei_org["id"],
            transaction_id=transaction["id"],
            role="payer" if "蜀汉" in t["from_org"] else "payee",
            description=t["description"]
        )
        
        print(f"  ✓ {t['category']}: {t['amount']} {t['description']}")
    
    print("\n" + "=" * 60)
    print("✅ 数据初始化完成！")
    print("=" * 60)
    
    # 打印汇总
    print("\n📊 数据汇总:")
    print(f"  组织: {shu_org['id']} (蜀汉), {wei_org['id']} (曹魏)")
    print(f"  人员: {len(SHU_PERSONNEL)} + {len(WEI_PERSONNEL)} = {len(SHU_PERSONNEL) + len(WEI_PERSONNEL)}")
    print(f"  资源: {len(SHU_RESOURCES)} + {len(WEI_LOSS_RESOURCES)} = {len(SHU_RESOURCES) + len(WEI_LOSS_RESOURCES)}")
    print(f"  仓库: {len(WAREHOUSES)}")
    print(f"  交易: {len(TRANSACTIONS)}")
    
    return {
        "shu_org_id": shu_org["id"],
        "wei_org_id": wei_org["id"],
        "personnel": {**shu_personnel_ids, **wei_personnel_ids},
        "resources": resource_ids
    }


if __name__ == "__main__":
    # 初始化数据库
    print("🔄 初始化数据库...")
    init_database(drop_all=False)
    
    # 运行数据生成
    result = setup_campaign()
    
    print(f"\n🎉 测试数据已创建！")
    print(f"   蜀汉组织ID: {result['shu_org_id']}")
    print(f"   曹魏组织ID: {result['wei_org_id']}")
