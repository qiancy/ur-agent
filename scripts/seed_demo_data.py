#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEMO 录屏模拟数据增强（DEMO_录屏模拟数据增强开发测试安排 §3）。

上下文 A：淘宝卖家 —— ouid=taobao_shop_a, type=ecommerce, 名称=淘宝小店 A
  人员：zhansan(张三, owner) / lisi(李四, member/仓管) / wangwu(王五, member/运营)
  仓库：WH-MAIN(杭州总仓) / WH-LIVE(直播间备货架) / WH-RETURN(退货暂存区)
  商品 6 个（库存表 6 行）：
    诸葛亮联名羽扇 50 件 / 木牛流马模型 12 件 / 隆中对竹简礼盒 36 套
    新野火攻纪念帆布袋 18 个 / 孔明灯香薰套装 5 盒(临界) / 草船借箭桌游卡牌 4 盒(最低库存锚点)
  流水 12 条（每商品 1 采购 + 1 销售，金额为正）
  低库存处理 2 项（阈值 5：草船借箭 4 / 孔明灯香薰 5）

上下文 B：火烧新野战役 —— ouid=xinye_campaign, type=campaign, 名称=火烧新野战役
  人员 7：liubei(owner 指挥官) / zhugeliang(admin 军师) / guanyu / zhangfei /
          zhaoyun / mizhu / zhansan(member 观察员)
  实物资源 5：军粮 1000 石 / 箭矢 5000 支 / 火油 120 桶 / 草料 800 捆 / 辎重车 36 辆
  知识资源 3：斥候情报 / 新野撤退路线图 / 火攻布置方案
  时间线 6：campaign_code=demo_xinye_recording，payload 含 info_flow/logistics_flow/
            people_flow/risk

幂等性：组织/人员/membership/商品/仓库/资源按业务标识（ouid/puid/product_uid/
warehouse_code/resource name）检查，campaign import 按 campaign_code 检查，
重复执行不产生重复行。zhansan 密码读环境变量 DEMO_ZHANSAN_PASSWORD
（未设置则跳过账号创建）。

红线：不写真实密码；只创建一个账号 account.login=zhansan；对外数据只用
puid/ouid/product_uid/warehouse_code，不用 DB 数字 ID。

用法：
  PYTHONPATH=. DEMO_ZHANSAN_PASSWORD=<pw> python scripts/seed_demo_data.py
"""
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv

load_dotenv(REPO_ROOT / ".env", override=False)

from src.auth.auth import hash_password
from src.db import database as db

PASSWORD_ENV_KEY = "DEMO_ZHANSAN_PASSWORD"
CAMPAIGN_CODE = "demo_xinye_recording"
CAMPAIGN_NAME = "火烧新野战役"

SHOP = {
    "ouid": "taobao_shop_a",
    "name": "淘宝小店 A",
    "type": "ecommerce",
    "description": "zhansan 的淘宝卖家工作台",
}
SHOP_WAREHOUSES = [
    {"name": "杭州总仓", "code": "WH-MAIN", "location": "杭州", "note": "主库存"},
    {"name": "直播间备货架", "code": "WH-LIVE", "location": "杭州直播间", "note": "低库存/热销展示"},
    {"name": "退货暂存区", "code": "WH-RETURN", "location": "杭州", "note": "退货待处理"},
]
SHOP_PEOPLE = [
    {"puid": "zhansan", "name": "张三", "role": "owner"},
    {"puid": "lisi", "name": "李四", "role": "member"},
    {"puid": "wangwu", "name": "王五", "role": "member"},
]
# (product_uid/商品名, unit, 采购 qty, 采购额, 供应商, 销售 qty, 销售额, 客户, 仓库)
SHOP_PLAN = [
    ("诸葛亮联名羽扇", "件", 100, 3000.0, "诸葛扇坊", 50, 4000.0, "成都文创店", "WH-MAIN"),
    ("木牛流马模型", "件", 30, 1200.0, "木牛工坊", 18, 1620.0, "荆州模型店", "WH-MAIN"),
    ("隆中对竹简礼盒", "套", 50, 2500.0, "南阳竹简坊", 14, 1232.0, "襄阳书坊", "WH-MAIN"),
    ("新野火攻纪念帆布袋", "个", 30, 600.0, "新野文创社", 12, 540.0, "樊城杂货铺", "WH-MAIN"),
    ("孔明灯香薰套装", "盒", 20, 300.0, "成都香坊", 15, 525.0, "洛阳礼品店", "WH-LIVE"),
    ("草船借箭桌游卡牌", "盒", 10, 250.0, "东吴棋牌社", 6, 270.0, "合肥桌游店", "WH-LIVE"),
]

XINYE = {
    "ouid": "xinye_campaign",
    "name": "火烧新野战役",
    "type": "campaign",
    "description": "火烧新野战役空间（zhansan 多空间切换演示）",
    "warehouse": {"name": "新野大营", "code": "XINYE-A", "location": "新野"},
}
XINYE_PEOPLE = [
    {"puid": "liubei", "name": "刘备", "role": "owner", "title": "指挥官"},
    {"puid": "zhugeliang", "name": "诸葛亮", "role": "admin", "title": "军师"},
    {"puid": "guanyu", "name": "关羽", "role": "member", "title": "前军"},
    {"puid": "zhangfei", "name": "张飞", "role": "member", "title": "后军"},
    {"puid": "zhaoyun", "name": "赵云", "role": "member", "title": "护卫"},
    {"puid": "mizhu", "name": "糜竺", "role": "member", "title": "后勤"},
    {"puid": "zhansan", "name": "张三", "role": "member", "title": "观察员"},
]
# (resource 名, unit, quantity) —— 实物资源
XINYE_SUPPLIES = [
    ("军粮", "石", 1000.0),
    ("箭矢", "支", 5000.0),
    ("火油", "桶", 120.0),
    ("草料", "捆", 800.0),
    ("辎重车", "辆", 36.0),
]
# (resource 名, content) —— 知识资源
XINYE_KNOWLEDGE = [
    ("斥候情报", "斥候回报曹军南下动向与行军路线"),
    ("新野撤退路线图", "百姓与军民向樊城、江夏方向的撤离路线"),
    ("火攻布置方案", "火油布点、点火信号与伏兵位置的战术方案"),
]
# (seq, title, description, info_flow, logistics_flow, people_flow, risk)
XINYE_EVENTS = [
    (1, "侦察曹军南下", "斥候回报曹军主力南下，刘备军决定火攻诱敌。",
     "斥候回报曹军行军路线", "军粮盘点", "百姓开始撤离登记", "情报延迟"),
    (2, "百姓撤离新野", "发布撤离路线，组织百姓有序撤离新野城。",
     "撤离路线发布", "辎重车集中", "百姓向樊城方向移动", "道路拥堵"),
    (3, "火油布置完成", "军师确认火攻信号，火油布点全部到位。",
     "火攻信号确认", "火油入城门暗点", "伏兵进入指定位置", "提前暴露"),
    (4, "夜间诱敌入城", "诱敌部队佯装败退，将曹军引入新野城。",
     "假败消息传递", "箭矢转入伏击点", "主力后撤", "敌军识破"),
    (5, "新野点火", "点火令下达，火起新野，曹军大乱。",
     "点火令下达", "火油消耗", "曹军混乱撤退", "火势失控"),
    (6, "刘备军转移", "战果汇总，军民携剩余物资向江夏方向转移。",
     "战果汇总", "剩余军粮随队转移", "军民向江夏方向移动", "追兵逼近"),
]


def _find_resource(organization_id: int, name: str):
    rows = db._fetch(
        "SELECT id, name, unit FROM resource "
        "WHERE organization_id = %s AND name = %s",
        (organization_id, name),
    )
    return rows[0] if rows else None


def _find_warehouse(organization_id: int, code: str):
    rows = db._fetch(
        "SELECT id, code FROM warehouse "
        "WHERE organization_id = %s AND code = %s",
        (organization_id, code),
    )
    return rows[0] if rows else None


def _person(puid: str, name: str):
    rows = db.query_person_by_puid(puid)
    if rows:
        return rows[0]
    return db.create_person(name=name, puid=puid)


def _ensure_membership(person_id: int, org_id: int, role: str):
    if db.query_membership(person_id, org_id):
        print(f"[skip] membership: person_id->org_id role={role}")
        return
    db.add_membership(person_id, org_id, role)
    print(f"[ok] membership role={role}")


def _seed_shop() -> dict:
    print(f"== 上下文 A：{SHOP['name']} ({SHOP['ouid']}) ==")
    org_rows = db.query_organization_by_ouid(SHOP["ouid"])
    if org_rows:
        org = org_rows[0]
        print(f"[skip] 组织已存在")
    else:
        org = db.create_organization(
            name=SHOP["name"], org_type=SHOP["type"],
            description=SHOP["description"], funds=10000.0,
            reputation=0, ouid=SHOP["ouid"],
        )
        print(f"[ok] 创建组织")
    org_id = org["id"]

    warehouses = {}
    for wh in SHOP_WAREHOUSES:
        found = _find_warehouse(org_id, wh["code"])
        if not found:
            warehouses[wh["code"]] = db.create_warehouse(
                org_id, wh["name"], wh["code"], wh["location"], wh["note"])
            print(f"[ok] 创建仓库 {wh['code']}")
        else:
            warehouses[wh["code"]] = found
            print(f"[skip] 仓库已存在 {wh['code']}")

    people = {}
    for p in SHOP_PEOPLE:
        person = _person(p["puid"], p["name"])
        people[p["puid"]] = person
        _ensure_membership(person["id"], org_id, p["role"])

    operator = people["zhansan"]
    for (uid, unit, pq, pa, supplier, sq, sa, customer, wh_code) in SHOP_PLAN:
        if _find_resource(org_id, uid):
            print(f"[skip] 商品已存在: {uid}")
            continue
        db.create_resource(organization_id=org_id, name=uid,
                           resource_type="physical", unit=unit,
                           content=f"演示商品：{uid}")
        db.execute_purchase_in(
            organization_id=org_id, operator_person_id=operator["id"],
            product_uid=uid, warehouse_code=wh_code,
            location_path=wh_code, quantity=pq, unit=unit,
            total_amount=pa, counterparty_name=supplier,
        )
        db.execute_sales_out(
            organization_id=org_id, operator_person_id=operator["id"],
            product_uid=uid, warehouse_code=wh_code,
            location_path=wh_code, quantity=sq, unit=unit,
            total_amount=sa, counterparty_name=customer,
        )
        print(f"[ok] 商品 {uid}: 采购 {pq}{unit}@{pa}，销售 {sq}{unit}@{sa}")

    return {"org_id": org_id, "ouid": SHOP["ouid"]}


def _seed_xinye() -> dict:
    print(f"== 上下文 B：{XINYE['name']} ({XINYE['ouid']}) ==")
    org_rows = db.query_organization_by_ouid(XINYE["ouid"])
    if org_rows:
        org = org_rows[0]
        print(f"[skip] 组织已存在")
    else:
        org = db.create_organization(
            name=XINYE["name"], org_type=XINYE["type"],
            description=XINYE["description"], funds=0.0,
            reputation=0, ouid=XINYE["ouid"],
        )
        print(f"[ok] 创建组织")
    org_id = org["id"]

    wh = _find_warehouse(org_id, XINYE["warehouse"]["code"])
    if not wh:
        wh = db.create_warehouse(
            org_id, XINYE["warehouse"]["name"], XINYE["warehouse"]["code"],
            XINYE["warehouse"]["location"], "战役军需仓库")
        print(f"[ok] 创建仓库 {XINYE['warehouse']['code']}")
    else:
        print(f"[skip] 仓库已存在 {XINYE['warehouse']['code']}")

    for p in XINYE_PEOPLE:
        person = _person(p["puid"], p["name"])
        _ensure_membership(person["id"], org_id, p["role"])

    for (name, unit, qty) in XINYE_SUPPLIES:
        if _find_resource(org_id, name):
            print(f"[skip] 资源已存在: {name}")
            continue
        resource = db.create_resource(
            organization_id=org_id, name=name,
            resource_type="physical", unit=unit,
            content=f"战役军需：{name}",
        )
        db.create_resource_warehouse(
            resource_id=resource["id"], warehouse_id=wh["id"],
            location_path=XINYE["warehouse"]["code"], quantity=qty, unit=unit,
        )
        print(f"[ok] 资源 {name}: {qty}{unit}")

    for (name, content) in XINYE_KNOWLEDGE:
        if _find_resource(org_id, name):
            print(f"[skip] 知识资源已存在: {name}")
            continue
        db.create_resource(
            organization_id=org_id, name=name,
            resource_type="knowledge", unit="份", content=content,
        )
        print(f"[ok] 知识资源 {name}")

    _seed_xinye_timeline(org_id)
    return {"org_id": org_id, "ouid": XINYE["ouid"]}


def _seed_xinye_timeline(org_id: int) -> None:
    imports = db.get_active_campaign_import_by_code(CAMPAIGN_CODE)
    if imports:
        import_id = imports[0]["id"]
        org_ids = db.get_campaign_import_org_ids(import_id)
        if org_id not in org_ids:
            db.add_campaign_import_org(import_id, org_id, False)
        existing = db._fetch(
            "SELECT seq FROM campaign_event "
            "WHERE campaign_import_id = %s AND organization_id = %s",
            (import_id, org_id),
        )
        existing_seqs = {row["seq"] for row in existing}
        for (seq, title, desc, info, logistics, people, risk) in XINYE_EVENTS:
            if seq in existing_seqs:
                continue
            db.create_campaign_event(
                import_id, org_id, seq, title, desc, {
                    "info_flow": info, "logistics_flow": logistics,
                    "people_flow": people, "risk": risk,
                })
            print(f"[ok] 时间线事件 #{seq} {title}")
        if existing_seqs:
            print(f"[skip] 时间线已有 {len(existing_seqs)} 事件")
        return

    campaign = db.create_campaign_import(
        CAMPAIGN_CODE, CAMPAIGN_NAME, "seed_demo_data.py", "pm")
    db.add_campaign_import_org(campaign["id"], org_id, False)
    for (seq, title, desc, info, logistics, people, risk) in XINYE_EVENTS:
        db.create_campaign_event(
            campaign["id"], org_id, seq, title, desc, {
                "info_flow": info, "logistics_flow": logistics,
                "people_flow": people, "risk": risk,
            })
        print(f"[ok] 时间线事件 #{seq} {title}")


def _ensure_zhansan_account() -> None:
    password = os.getenv(PASSWORD_ENV_KEY, "").strip()
    if not password:
        print(f"未设置 {PASSWORD_ENV_KEY}，跳过演示账号创建")
        return
    if db.query_account_by_login("zhansan"):
        print("[skip] account: zhansan 已存在")
        return
    persons = db.query_person_by_puid("zhansan")
    if not persons:
        print("[warn] person zhansan 不存在，跳过账号创建")
        return
    hashed, salt = hash_password(password)
    db.create_account(person_id=persons[0]["id"], login="zhansan",
                      password=hashed, salt=salt, system_role="user")
    print("[ok] account: zhansan")


def main() -> int:
    shop = _seed_shop()
    xinye = _seed_xinye()
    _ensure_zhansan_account()

    print("\n== 汇总 ==")
    stock = db.query_stock(shop["org_id"])
    print(f"  {shop['ouid']}: 库存 {len(stock)} 条")
    for row in stock:
        print(f"    {row['product_uid']}: {row['quantity']}{row['unit']} @{row['warehouse_code']}")
    movements = db.query_inventory_movements(shop["org_id"])
    print(f"  {shop['ouid']}: 库存流水 {len(movements)} 条")
    summary = db.get_seller_summary(shop["org_id"])
    print(f"  销售收入={summary['sales_amount']} 采购支出={summary['purchase_amount']} "
          f"净现金流={summary['net_cash_flow']} 库存估值={summary['estimated_inventory_value']}")
    low = summary["low_stock_items"]
    print(f"  低库存 {len(low)} 项: " + "、".join(
        f"{i['product_uid']}({i['quantity']}{i['unit'] or ''})" for i in low))

    xinye_resources = db.query_resource(xinye["org_id"])
    print(f"  {xinye['ouid']}: 资源 {len(xinye_resources)} 个")
    timeline = db.get_space_timeline(xinye["org_id"])
    print(f"  {xinye['ouid']}: 时间线事件 {len(timeline)} 条")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
