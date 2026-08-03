#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补建 zhansan 的 ecommerce 演示店铺（T1 集成补充，非 T4 计划内）。

背景：T4 种子脚本对 fe06_spike_* ecommerce 店铺按设计"找不到则跳过"，
但远端 DB 无该店铺，导致 zhansan 缺"公司/工作台"空间，MCS 演示不完整。
本脚本创建一个轻量 ecommerce 演示店铺并给 zhansan 加入 owner membership，
复用既有 seller 业务函数（execute_purchase_in / execute_sales_out）产生真实
商品/库存/流水/交易数据，使 Seller 工作台与多空间切换均可完整演示。

幂等性：
  - 组织 zhansan_shop 已存在 → 不重建。
  - 商品（resource.type='physical' + name）已存在 → 跳过入库/出货。
  - zhansan->zhansan_shop membership 已存在 → 跳过。
  - 账号 zhansan@zhansan_shop 已存在 → 跳过；密码同 DEMO_ZHANSAN_PASSWORD。

用法：
  PYTHONPATH=. DEMO_ZHANSAN_PASSWORD=<pw> python scripts/seed_demo_shop.py
  （密码缺省则仅建店铺/数据，不建登录账号。）
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

SHOP_OUID = "zhansan_shop"
SHOP_NAME = "张三小铺"
SHOP_TYPE = "ecommerce"
WAREHOUSE = {"name": "总仓", "code": "WH-MAIN", "location": "杭州"}
OPERATOR_PUID = "zhansan"
OPERATOR_NAME = "张三"
PASSWORD_ENV_KEY = "DEMO_ZHANSAN_PASSWORD"

# (product_uid, unit, 采购 qty, 采购额, 供应商, 销售 qty, 销售额, 客户)
PLAN = [
    ("景德镇陶瓷杯", "个", 200, 3000.0, "景德镇陶瓷厂", 80, 2400.0, "杭州文创店"),
    ("手工帆布包", "个", 100, 2500.0, "棉纺合作社", 45, 1800.0, "杭州文创店"),
    ("黄铜书签", "件", 300, 1500.0, "铜器工坊", 120, 960.0, "文房四宝商行"),
]


def _find_resource(organization_id: int, name: str):
    rows = db._fetch(
        "SELECT id, name, unit FROM resource WHERE organization_id = %s AND name = %s",
        (organization_id, name),
    )
    return rows[0] if rows else None


def _find_warehouse(organization_id: int, code: str):
    rows = db._fetch(
        "SELECT id, code FROM warehouse WHERE organization_id = %s AND code = %s",
        (organization_id, code),
    )
    return rows[0] if rows else None


def main() -> int:
    password = os.getenv(PASSWORD_ENV_KEY, "").strip()

    print(f"== 演示店铺 {SHOP_NAME} ({SHOP_OUID}) ==")
    org_rows = db.query_organization_by_ouid(SHOP_OUID)
    if org_rows:
        org = org_rows[0]
        print(f"[skip] 组织已存在 (id={org['id']})")
    else:
        org = db.create_organization(
            name=SHOP_NAME, org_type=SHOP_TYPE,
            description="zhansan 的 ecommerce 演示店铺",
            funds=10000.0, reputation=0, ouid=SHOP_OUID,
        )
        print(f"[ok] 创建组织 (id={org['id']})")
    org_id = org["id"]

    wh = _find_warehouse(org_id, WAREHOUSE["code"])
    if not wh:
        wh = db.create_warehouse(org_id, WAREHOUSE["name"], WAREHOUSE["code"],
                                 WAREHOUSE["location"], "演示总仓")
        print(f"[ok] 创建仓库 {WAREHOUSE['code']}")
    else:
        print(f"[skip] 仓库已存在 {WAREHOUSE['code']}")

    person_rows = db.query_person_by_puid(OPERATOR_PUID)
    operator = person_rows[0] if person_rows else db.create_person(
        name=OPERATOR_NAME, puid=OPERATOR_PUID)
    if not person_rows:
        print(f"[ok] 创建人员 {OPERATOR_PUID}")

    for (uid, unit, pq, pa, supplier, sq, sa, customer) in PLAN:
        if _find_resource(org_id, uid):
            print(f"[skip] 商品已存在: {uid}")
            continue
        db.create_resource(organization_id=org_id, name=uid, resource_type="physical",
                           unit=unit, content=f"演示商品：{uid}")
        db.execute_purchase_in(
            organization_id=org_id, operator_person_id=operator["id"],
            product_uid=uid, warehouse_code=WAREHOUSE["code"],
            location_path=WAREHOUSE["code"], quantity=pq, unit=unit,
            total_amount=pa, counterparty_name=supplier,
        )
        db.execute_sales_out(
            organization_id=org_id, operator_person_id=operator["id"],
            product_uid=uid, warehouse_code=WAREHOUSE["code"],
            location_path=WAREHOUSE["code"], quantity=sq, unit=unit,
            total_amount=sa, counterparty_name=customer,
        )
        print(f"[ok] 商品 {uid}: 入库 {pq}{unit}@{pa}，出库 {sq}{unit}@{sa}")

    if not db.query_membership(operator["id"], org_id):
        db.add_membership(operator["id"], org_id, "owner")
        print(f"[ok] membership: {OPERATOR_PUID} -> {SHOP_OUID} (role=owner)")
    else:
        print(f"[skip] membership 已存在: {OPERATOR_PUID} -> {SHOP_OUID}")

    if password:
        login = f"{OPERATOR_PUID}@{SHOP_OUID}"
        if db.query_account_by_login(login):
            print(f"[skip] account: {login} 已存在")
        else:
            hashed, salt = hash_password(password)
            db.create_account(person_id=operator["id"], login=login,
                              password=hashed, salt=salt, system_role="user")
            print(f"[ok] account: {login}")
    else:
        print(f"未设置 {PASSWORD_ENV_KEY}，跳过演示账号创建")

    print("\n== 汇总 ==")
    print(f"  {SHOP_OUID}: org_id={org_id}, 商品数={len(PLAN)}, warehouse={WAREHOUSE['code']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
