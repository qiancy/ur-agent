# 初始化API实现建议

## 📋 需求说明

**用途**：为测试提供战役数据初始化能力  
**API路径**：`POST /api/init/campaign`  
**必要性**：测试脚本不应直接访问数据库，应通过API准备测试数据

---

## 🔧 API 设计

### 请求参数

```json
{
  "context_id": 10,
  "campaign_name": "火烧新野",
  "init_all_data": true
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| context_id | int | 是 | 测试上下文ID（组织ID） |
| campaign_name | string | 是 | 战役名称 |
| init_all_data | bool | 否 | 是否初始化所有数据（默认true） |

### 成功响应

```json
{
  "code": 200,
  "message": "Campaign data initialized successfully",
  "data": {
    "context_id": 10,
    "campaign_name": "火烧新野",
    "organizations": 2,
    "persons": 8,
    "resources": 24,
    "warehouses": 4,
    "transactions": 10,
    "details": {
      "shu_han": {
        "org_id": 10,
        "persons": 5,
        "resources": 17,
        "warehouses": 3,
        "transactions": 5,
        "total_funds": 1900
      },
      "cao_wei": {
        "org_id": 11,
        "persons": 3,
        "resources": 6,
        "warehouses": 1,
        "transactions": 5,
        "total_funds": 7500
      }
    }
  }
}
```

### 错误响应

```json
{
  "code": 400,
  "message": "Invalid context_id or campaign data",
  "error": "Context 10 already exists"
}
```

---

## 🔌 FastAPI 实现代码

将以下代码添加到 `src/app.py`（在现有API端点之后）：

```python
# ── 初始化API ────────────────────────────────────────────────────────────────

from typing import Dict, Any, List
from pydantic import BaseModel

class CampaignInitRequest(BaseModel):
    context_id: int
    campaign_name: str
    init_all_data: bool = True

class OrganizationData(BaseModel):
    id: int
    name: str
    org_type: str
    description: Optional[str] = None
    funds: float = 0
    reputation: int = 0

class PersonData(BaseModel):
    id: int
    name: str
    birth_date: Optional[str] = None
    org_id: int
    role: Optional[str] = None

class ResourceData(BaseModel):
    id: int
    name: str
    resource_type: str
    unit: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    org_id: int
    warehouse_id: Optional[int] = None
    quantity: Optional[float] = None

class WarehouseData(BaseModel):
    id: int
    name: str
    code: str
    location: Optional[str] = None
    org_id: int

class TransactionData(BaseModel):
    id: int
    amount: float
    category: str
    description: Optional[str] = None
    org_id: int
    from_party: str
    to_party: str

@app.post("/api/init/campaign", status_code=201)
async def init_campaign(request: CampaignInitRequest):
    """
    初始化战役数据
    为指定的 context_id 创建完整的测试数据集
    """
    from src.db.database import (
        create_organization, query_organization,
        create_person, query_person_by_name,
        create_resource, query_resource,
        create_warehouse, query_warehouse,
        create_transaction, get_transactions,
        create_party, query_party_by_transaction,
        create_resource_warehouse, query_resource_warehouse,
    )
    
    if not request.init_all_data:
        return {
            "code": 200,
            "message": "No data initialization requested",
            "data": {"context_id": request.context_id}
        }
    
    # 战役数据配置
    campaign_config = _get_campaign_config(request.campaign_name)
    
    if not campaign_config:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown campaign: {request.campaign_name}"
        )
    
    # 检查是否已存在数据
    existing_org = query_organization(oid=request.context_id)
    if existing_org:
        raise HTTPException(
            status_code=400,
            detail=f"Context {request.context_id} already has data"
        )
    
    # 开始初始化
    results = {
        "context_id": request.context_id,
        "campaign_name": request.campaign_name,
        "organizations": 0,
        "persons": 0,
        "resources": 0,
        "warehouses": 0,
        "transactions": 0,
        "details": {}
    }
    
    # 初始化组织
    for org_config in campaign_config["organizations"]:
        org_id = org_config["id"]
        if org_id == request.context_id or org_id == request.context_id + 1:
            create_organization(
                name=org_config["name"],
                org_type=org_config["type"],
                description=org_config.get("description"),
                funds=org_config.get("funds", 0),
                reputation=org_config.get("reputation", 0)
            )
            results["organizations"] += 1
    
    # 初始化人员
    for person_config in campaign_config["persons"]:
        if person_config["org_id"] in [request.context_id, request.context_id + 1]:
            create_person(
                name=person_config["name"],
                birth_date=person_config.get("birth_date")
            )
            results["persons"] += 1
    
    # 初始化仓库
    for wh_config in campaign_config["warehouses"]:
        if wh_config["org_id"] in [request.context_id, request.context_id + 1]:
            create_warehouse(
                oid=wh_config["org_id"],
                name=wh_config["name"],
                code=wh_config["code"],
                location=wh_config.get("location"),
                description=wh_config.get("description")
            )
            results["warehouses"] += 1
    
    # 初始化资源
    for res_config in campaign_config["resources"]:
        if res_config["org_id"] in [request.context_id, request.context_id + 1]:
            create_resource(
                oid=res_config["org_id"],
                name=res_config["name"],
                resource_type=res_config["type"],
                unit=res_config.get("unit"),
                amount=res_config.get("amount"),
                currency=res_config.get("currency"),
                pid=res_config.get("pid"),
                content=res_config.get("content")
            )
            results["resources"] += 1
    
    # 初始化交易
    for trans_config in campaign_config["transactions"]:
        if trans_config["org_id"] in [request.context_id, request.context_id + 1]:
            create_transaction(
                amount=trans_config["amount"],
                category=trans_config["category"],
                description=trans_config.get("description")
            )
            results["transactions"] += 1
    
    # 获取初始化后的统计
    results["details"] = {
        "shu_han": _get_org_stats(request.context_id),
        "cao_wei": _get_org_stats(request.context_id + 1)
    }
    
    return {
        "code": 201,
        "message": "Campaign data initialized successfully",
        "data": results
    }


def _get_campaign_config(campaign_name: str) -> Dict[str, Any]:
    """获取战役数据配置"""
    configs = {
        "火烧新野": {
            "organizations": [
                {"id": 10, "name": "蜀汉指挥部", "type": "military", 
                 "description": "刘备军主力指挥部", "funds": 1900, "reputation": 85},
                {"id": 11, "name": "曹魏防线", "type": "military",
                 "description": "曹洪防守部队", "funds": 7500, "reputation": 60},
            ],
            "persons": [
                {"id": 1, "name": "诸葛亮", "org_id": 10, "role": "军师", "birth_date": "181-04-14"},
                {"id": 2, "name": "刘备", "org_id": 10, "role": "主公", "birth_date": "161-06-29"},
                {"id": 3, "name": "关羽", "org_id": 10, "role": "将军", "birth_date": "160-05-01"},
                {"id": 4, "name": "张飞", "org_id": 10, "role": "将军", "birth_date": "163-03-29"},
                {"id": 5, "name": "赵云", "org_id": 10, "role": "将军", "birth_date": "182-04-11"},
                {"id": 6, "name": "黄忠", "org_id": 10, "role": "老将", "birth_date": "147-01-01"},
                {"id": 7, "name": "曹洪", "org_id": 11, "role": "将军"},
                {"id": 8, "name": "夏侯惇", "org_id": 11, "role": "将军"},
                {"id": 9, "name": "于禁", "org_id": 11, "role": "将军"},
            ],
            "warehouses": [
                {"id": 1, "name": "蜀汉火攻仓库", "code": "SH-FIRE-001", "org_id": 10, "location": "成都西郊"},
                {"id": 2, "name": "蜀汉军械仓库", "code": "SH-WEAP-001", "org_id": 10, "location": "成都南郊"},
                {"id": 3, "name": "蜀汉后勤仓库", "code": "SH-SUPP-001", "org_id": 10, "location": "成都北郊"},
                {"id": 4, "name": "曹魏前线仓库", "code": "CW-FRONT-001", "org_id": 11, "location": "新野"},
            ],
            "resources": [
                # 火攻材料
                {"id": 1, "name": "火油", "type": "fire_weapons", "unit": "桶", "amount": 100, "org_id": 10, "warehouse_id": 1},
                {"id": 2, "name": "火把", "type": "fire_weapons", "unit": "支", "amount": 500, "org_id": 10, "warehouse_id": 1},
                {"id": 3, "name": "硫磺", "type": "fire_weapons", "unit": "斤", "amount": 20, "org_id": 10, "warehouse_id": 1},
                {"id": 4, "name": "青铜镜", "type": "fire_weapons", "unit": "面", "amount": 50, "org_id": 10, "warehouse_id": 1},
                {"id": 5, "name": "火矢", "type": "fire_weapons", "unit": "支", "amount": 300, "org_id": 10, "warehouse_id": 1},
                {"id": 6, "name": "烟雾弹", "type": "fire_weapons", "unit": "个", "amount": 50, "org_id": 10, "warehouse_id": 1},
                # 武器装备
                {"id": 7, "name": "青龙偃月刀", "type": "melee_weapons", "unit": "把", "amount": 1, "org_id": 10, "warehouse_id": 2},
                {"id": 8, "name": "丈八蛇矛", "type": "melee_weapons", "unit": "把", "amount": 1, "org_id": 10, "warehouse_id": 2},
                {"id": 9, "name": "连弩", "type": "ranged_weapons", "unit": "架", "amount": 50, "org_id": 10, "warehouse_id": 2},
                {"id": 10, "name": "战船", "type": "naval", "unit": "艘", "amount": 5, "org_id": 10, "warehouse_id": 2},
                # 曹魏装备
                {"id": 11, "name": "弓箭", "type": "ranged_weapons", "unit": "支", "amount": 10000, "org_id": 11, "warehouse_id": 4},
                {"id": 12, "name": "戈矛", "type": "melee_weapons", "unit": "支", "amount": 5000, "org_id": 11, "warehouse_id": 4},
                {"id": 13, "name": "盾牌", "type": "defense", "unit": "个", "amount": 2000, "org_id": 11, "warehouse_id": 4},
                {"id": 14, "name": "铠甲", "type": "defense", "unit": "套", "amount": 1500, "org_id": 11, "warehouse_id": 4},
                {"id": 15, "name": "战马", "type": "mount", "unit": "匹", "amount": 500, "org_id": 11, "warehouse_id": 4},
                {"id": 16, "name": "粮草", "type": "supply", "unit": "石", "amount": 2000, "org_id": 11, "warehouse_id": 4},
                # 蜀汉其他物资
                {"id": 17, "name": "稿赏银", "type": "funds", "unit": "两", "amount": 800, "org_id": 10, "warehouse_id": 3},
            ],
            "transactions": [
                {"id": 1, "amount": 500, "category": "采购", "description": "购买火油", "org_id": 10, "from_party": "蜀汉", "to_party": "商人"},
                {"id": 2, "amount": 300, "category": "采购", "description": "购买黄铜", "org_id": 10, "from_party": "蜀汉", "to_party": "工匠"},
                {"id": 3, "amount": 800, "category": "赏赐", "description": "稿赏银", "org_id": 10, "from_party": "蜀汉", "to_party": "士兵"},
                {"id": 4, "amount": 200, "category": "资助", "description": "民夫资助", "org_id": 10, "from_party": "蜀汉", "to_party": "民夫"},
                {"id": 5, "amount": 100, "category": "购置", "description": "购买烟火", "org_id": 10, "from_party": "蜀汉", "to_party": "商人"},
                {"id": 6, "amount": 5000, "category": "军费", "description": "曹魏军费支出", "org_id": 11, "from_party": "曹魏", "to_party": "兵营"},
                {"id": 7, "amount": 1000, "category": "赏赐", "description": "士兵赏赐", "org_id": 11, "from_party": "曹魏", "to_party": "士兵"},
                {"id": 8, "amount": 500, "category": "采购", "description": "粮草采购", "org_id": 11, "from_party": "曹魏", "to_party": "商人"},
                {"id": 9, "amount": 300, "category": "维修", "description": "武器维修", "org_id": 11, "from_party": "曹魏", "to_party": "工匠"},
                {"id": 10, "amount": 1000, "category": "撤退", "description": "退败赏赐", "org_id": 11, "from_party": "曹魏", "to_party": "溃兵"},
            ],
        }
    }
    return configs.get(campaign_name)


def _get_org_stats(org_id: int) -> Dict[str, Any]:
    """获取组织统计数据"""
    from src.db.database import _fetch
    
    # 统计人数
    persons = _fetch(
        "SELECT COUNT(*) as cnt FROM person p "
        "JOIN membership m ON p.id = m.person_id "
        "WHERE m.org_id = %s", (org_id,))
    
    # 统计资源
    resources = _fetch(
        "SELECT COUNT(DISTINCT r.id) as cnt "
        "FROM resource r "
        "WHERE r.org_id = %s", (org_id,))
    
    # 统计仓库
    warehouses = _fetch(
        "SELECT COUNT(*) as cnt FROM warehouse WHERE org_id = %s", (org_id,))
    
    # 统计交易
    transactions = _fetch(
        "SELECT COUNT(DISTINCT t.id) as cnt "
        "FROM transaction t "
        "JOIN party p ON p.transaction_id = t.id "
        "WHERE p.oid = %s", (org_id,))
    
    # 统计资金
    funds = _fetch(
        "SELECT COALESCE(SUM(t.amount), 0) as total "
        "FROM transaction t "
        "JOIN party p ON p.transaction_id = t.id "
        "WHERE p.oid = %s", (org_id,))
    
    return {
        "org_id": org_id,
        "persons": persons[0]["cnt"],
        "resources": resources[0]["cnt"],
        "warehouses": warehouses[0]["cnt"],
        "transactions": transactions[0]["cnt"],
        "total_funds": float(transactions[0]["total"]),
    }
```

---

## 🧪 测试脚本修改

修改 `test_fire_newye_api.py` 的数据初始化部分：

```python
import requests
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

def init_campaign_data(context_id: int = 10):
    """
    通过API初始化战役数据
    """
    response = client.post(
        "/api/init/campaign",
        json={
            "context_id": context_id,
            "campaign_name": "火烧新野",
            "init_all_data": True
        }
    )
    
    if response.status_code == 201:
        print(f"✅ Campaign data initialized for context {context_id}")
        return response.json()
    else:
        raise RuntimeError(f"Failed to init campaign: {response.text}")

# 在测试前调用
init_campaign_data(context_id=10)
```

---

## 📝 使用流程

```
┌─────────────────────────────────────────────────────────────┐
│                    测试初始化流程                            │
├─────────────────────────────────────────────────────────────┤
│  1. 启动 FastAPI 服务                                       │
│     $ uvicorn src.app:app --reload                          │
│                                                             │
│  2. 调用初始化 API                                          │
│     POST /api/init/campaign                                 │
│     Body: { "context_id": 10, "campaign_name": "火烧新野" } │
│                                                             │
│  3. API 自动创建所有数据                                    │
│     - 2个组织                                               │
│     - 9名人员                                               │
│     - 4个仓库                                               │
│     - 17个资源                                              │
│     - 10笔交易                                              │
│                                                             │
│  4. 测试脚本开始执行                                        │
│     - 所有测试使用 context_id = 10                          │
│     - 数据完全隔离                                          │
│     - 不直接访问数据库                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ 完成检查清单

- [ ] API端点已添加到 `src/app.py`
- [ ] 战役数据配置已定义
- [ ] 数据初始化逻辑已实现
- [ ] 统计数据查询已实现
- [ ] 错误处理已添加
- [ ] 测试脚本已更新为使用API
- [ ] 文档已更新

---

## 📌 注意事项

1. **数据隔离**：每个测试使用独立的 `context_id`
2. **幂等性**：已存在数据时返回400错误，避免重复初始化
3. **事务性**：建议将数据初始化包装在数据库事务中
4. **清理**：测试结束后提供清理API `POST /api/cleanup/context/{id}`
