#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEMO 双场景种子数据（DEMO_双场景回归测试计划 §3）。

上下文 A：淘宝卖家 —— ouid=taobao_shop_a, type=ecommerce, 名称=淘宝小店 A
  人员：zhansan(张三, owner) / lisi(李四, member/仓管)
  商品：诸葛亮联名羽扇(50 件) / 木牛流马模型(12 件, 库存最低)
  流水：采购补货木牛流马、销售羽扇、销售木牛流马（正数金额）
上下文 B：火烧新野战役 —— ouid=xinye_campaign, type=campaign, 名称=火烧新野战役
  人员：liubei(刘备, 指挥官/owner) / zhugeliang(诸葛亮, 军师/member) /
        zhansan(张三, member, 录屏切换用)
  资源：军粮 1000 石 / 箭矢 5000 支

幂等性：组织/人员/membership/商品/仓库均按业务标识（ouid/puid/product_uid/
warehouse_code）检查，重复执行不产生重复行。zhansan 密码读环境变量
DEMO_ZHANSAN_PASSWORD（未设置则跳过账号创建）。

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

SHOP = {
    "ouid": "taobao_shop_a",
    "name": "淘宝小店 A",
    "type": "ecommerce",
    "description": "zhansan 的淘宝卖家工作台",
    "warehouse": {"name": "总仓", "code": "WH-MAIN", "location": "杭州"},
}
SHOP_PEOPLE = [
    {"puid": "zhansan", "name": "张三", "role": "owner"},
    {"puid": "lisi", "name": "李四", "role": "member"},
]
# (product_uid/商品名, unit, 采购 qty, 采购额, 供应商, 销售 qty, 销售额, 客户)
SHOP_PLAN = [
    ("诸葛亮联名羽扇", "件", 100, 3000.0, "诸葛扇坊", 50, 4000.0, "成都文创店"),
    ("木牛流马模型", "件", 30, 1200.0, "木牛工坊", 18, 1620.0, "荆州模型店"),
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
    {"puid": "zhugeliang", "name": "诸葛亮", "role": "member", "title": "军师"},
    {"puid": "zhansan", "name": "张三", "role": "member", "title": "军需官"},
]
# (resource 名, unit, quantity)
XINYE_SUPPLIES = [
    ("军粮", "石", 1000.0),
    ("箭矢", "支", 5000.0),
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
        print(f"[skip] 组织已存在 (id={org['id']})")
    else:
        org = db.create_organization(
            name=SHOP["name"], org_type=SHOP["type"],
            description=SHOP["description"], funds=10000.0,
            reputation=0, ouid=SHOP["ouid"],
        )
        print(f"[ok] 创建组织 (id={org['id']})")
    org_id = org["id"]

    wh = _find_warehouse(org_id, SHOP["warehouse"]["code"])
    if not wh:
        wh = db.create_warehouse(
            org_id, SHOP["warehouse"]["name"], SHOP["warehouse"]["code"],
            SHOP["warehouse"]["location"], "演示总仓")
        print(f"[ok] 创建仓库 {SHOP['warehouse']['code']}")
    else:
        print(f"[skip] 仓库已存在 {SHOP['warehouse']['code']}")

    people = {}
    for p in SHOP_PEOPLE:
        person = _person(p["puid"], p["name"])
        people[p["puid"]] = person
        _ensure_membership(person["id"], org_id, p["role"])

    operator = people["zhansan"]
    for (uid, unit, pq, pa, supplier, sq, sa, customer) in SHOP_PLAN:
        if _find_resource(org_id, uid):
            print(f"[skip] 商品已存在: {uid}")
            continue
        db.create_resource(organization_id=org_id, name=uid,
                           resource_type="physical", unit=unit,
                           content=f"演示商品：{uid}")
        db.execute_purchase_in(
            organization_id=org_id, operator_person_id=operator["id"],
            product_uid=uid, warehouse_code=SHOP["warehouse"]["code"],
            location_path=SHOP["warehouse"]["code"], quantity=pq, unit=unit,
            total_amount=pa, counterparty_name=supplier,
        )
        db.execute_sales_out(
            organization_id=org_id, operator_person_id=operator["id"],
            product_uid=uid, warehouse_code=SHOP["warehouse"]["code"],
            location_path=SHOP["warehouse"]["code"], quantity=sq, unit=unit,
            total_amount=sa, counterparty_name=customer,
        )
        print(f"[ok] 商品 {uid}: 采购 {pq}{unit}@{pa}，销售 {sq}{unit}@{sa}")

    return {"org_id": org_id, "ouid": SHOP["ouid"]}


def _seed_xinye() -> dict:
    print(f"== 上下文 B：{XINYE['name']} ({XINYE['ouid']}) ==")
    org_rows = db.query_organization_by_ouid(XINYE["ouid"])
    if org_rows:
        org = org_rows[0]
        print(f"[skip] 组织已存在 (id={org['id']})")
    else:
        org = db.create_organization(
            name=XINYE["name"], org_type=XINYE["type"],
            description=XINYE["description"], funds=0.0,
            reputation=0, ouid=XINYE["ouid"],
        )
        print(f"[ok] 创建组织 (id={org['id']})")
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

    return {"org_id": org_id, "ouid": XINYE["ouid"]}


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
        print(f"    {row['product_uid']}: {row['quantity']}{row['unit']}")
    summary = db.get_seller_summary(shop["org_id"])
    print(f"  销售收入={summary['sales_amount']} 采购支出={summary['purchase_amount']} "
          f"净现金流={summary['net_cash_flow']} 库存估值={summary['estimated_inventory_value']}")
    xinye_resources = db.query_resource(xinye["org_id"])
    print(f"  {xinye['ouid']}: 资源 {len(xinye_resources)} 个")
    for row in xinye_resources:
        print(f"    {row['name']}: {row['unit']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
