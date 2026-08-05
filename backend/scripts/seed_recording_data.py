#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEMO-DATA-02 全新录屏账号与数据（DEMO-DATA-02_全新录屏账号与数据开发测试安排）。

正式录屏基线：账号 liuming（刘明），登录默认进入个人工作空间
liuming_personal（owner），再经 membership 切换业务空间。

上下文 P：个人空间 —— ouid=liuming_personal, type=personal
  走 register_personal_space() 注册契约，与真实用户注册数据结构完全一致：
  account + person + personal organization + owner membership 原子创建。

上下文 S：电商空间 明灯文创小店 —— ouid=liuming_mingdeng_shop, type=ecommerce
  人员：liuming(owner 刘明) / chenyan(member 陈燕/运营) / heqiang(member 何强/仓管)
  仓库：MD-WH-HZ(杭州总仓) / MD-WH-LIVE(直播间备货架) / MD-WH-RETURN(退货暂存区)
  商品 6 个（库存表 6 行）：
    星火羽扇礼盒 64 套 / 木牛流马积木套装 18 套 / 新野火攻桌游 7 盒
    隆中对手账本 42 本 / 孔明灯夜读灯 5 盏(临界) / 草船借箭纪念徽章 3 枚(最低锚点)
  流水 12 条（每商品 1 purchase_in + 1 sales_out，金额为正）
  低库存 2 项（阈值 5：草船借箭纪念徽章 3 / 孔明灯夜读灯 5）
  销售收入/采购支出/净现金流/库存估值均非零。

上下文 C：战役空间 新野火攻复盘空间 —— ouid=liuming_xinye_review, type=campaign
  人员 7：liubei_review(owner 指挥官) / zhugeliang_review(admin 军师) /
          zhaoyun_review / guanyu_review / zhangfei_review / mizhu_review /
          liuming(member 观察员)
  实物资源 4：新野城军粮 1200 石 / 南门箭矢 6800 支 / 火油桶 160 桶 / 撤离辎重车 48 辆
  知识资源 3：斥候简报 / 火攻布置图 / 百姓撤离名册
  时间线 8：campaign_code=demo_liuming_review，payload 含 info_flow/logistics_flow/
            people_flow/risk；战役资金流保持 0（证明电商收入不串空间）。

幂等性：组织/人员/membership/商品/仓库/资源按业务标识（ouid/puid/product_uid/
warehouse_code/resource name）检查，campaign import 按 campaign_code 检查，
重复执行不产生重复行。liuming 密码优先读环境变量 DEMO_LIUMING_PASSWORD，
未设置时使用演示默认密码 demo123。

红线：不写真实密码；对外数据只用 puid/ouid/product_uid/warehouse_code，
不用 DB 数字 ID；不改 scripts/init_db.py 的基础职责。

用法：
  PYTHONPATH=. DEMO_LIUMING_PASSWORD=<pw> python scripts/seed_recording_data.py
"""
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv

load_dotenv(REPO_ROOT / ".env", override=False)

from src.auth.auth import hash_password, verify_password
from src.db import database as db

PASSWORD_ENV_KEY = "DEMO_LIUMING_PASSWORD"
SHARED_PASSWORD_ENV_KEY = "UNIRES_DEMO_PASSWORD"
DEFAULT_DEMO_PASSWORD = "demo123"
CAMPAIGN_CODE = "demo_liuming_review"
CAMPAIGN_NAME = "新野火攻复盘空间"

PERSONAL = {
    "puid": "liuming",
    "name": "刘明",
    "login": "liuming",
    "ouid": "liuming_personal",
}

SHOP = {
    "ouid": "liuming_mingdeng_shop",
    "name": "明灯文创小店",
    "type": "ecommerce",
    "description": "刘明的明灯文创小店（明灯文创 Seller 工作台）",
}
SHOP_WAREHOUSES = [
    {"name": "杭州总仓", "code": "MD-WH-HZ", "location": "杭州", "note": "主库存"},
    {"name": "直播间备货架", "code": "MD-WH-LIVE", "location": "杭州直播间", "note": "低库存/热销展示"},
    {"name": "退货暂存区", "code": "MD-WH-RETURN", "location": "杭州", "note": "退货待处理"},
]
SHOP_PEOPLE = [
    {"puid": "liuming", "name": "刘明", "role": "owner"},
    {"puid": "chenyan", "name": "陈燕", "role": "member"},
    {"puid": "heqiang", "name": "何强", "role": "member"},
]
# (product_uid/商品名, unit, 采购 qty, 采购额, 供应商, 销售 qty, 销售额, 客户, 仓库)
SHOP_PLAN = [
    ("星火羽扇礼盒", "套", 100, 3000.0, "明灯联名扇坊", 36, 3420.0, "直播间文创客户", "MD-WH-HZ"),
    ("木牛流马积木套装", "套", 30, 1350.0, "木牛工坊", 12, 1260.0, "积木玩家社群", "MD-WH-HZ"),
    ("新野火攻桌游", "盒", 15, 480.0, "新野桌游工坊", 8, 560.0, "樊城桌游吧", "MD-WH-HZ"),
    ("隆中对手账本", "本", 60, 720.0, "文房工坊", 18, 540.0, "襄阳书店", "MD-WH-HZ"),
    ("孔明灯夜读灯", "盏", 15, 300.0, "灯坊", 10, 450.0, "直播购物客户", "MD-WH-LIVE"),
    ("草船借箭纪念徽章", "枚", 12, 96.0, "徽章工坊", 9, 180.0, "收藏爱好者", "MD-WH-LIVE"),
]

CAMP = {
    "ouid": "liuming_xinye_review",
    "name": "新野火攻复盘空间",
    "type": "campaign",
    "description": "新野火攻复盘空间（liuming 多空间切换演示）",
    "warehouse": {"name": "新野大营", "code": "XINYE-CAMP", "location": "新野"},
}
CAMP_PEOPLE = [
    {"puid": "liubei_review", "name": "刘备", "role": "owner", "title": "指挥官"},
    {"puid": "zhugeliang_review", "name": "诸葛亮", "role": "admin", "title": "军师"},
    {"puid": "zhaoyun_review", "name": "赵云", "role": "member", "title": "护卫"},
    {"puid": "guanyu_review", "name": "关羽", "role": "member", "title": "前军"},
    {"puid": "zhangfei_review", "name": "张飞", "role": "member", "title": "后军"},
    {"puid": "mizhu_review", "name": "糜竺", "role": "member", "title": "后勤"},
    {"puid": "liuming", "name": "刘明", "role": "member", "title": "观察员"},
]
# (resource 名, unit, quantity) —— 实物资源
CAMP_SUPPLIES = [
    ("新野城军粮", "石", 1200.0),
    ("南门箭矢", "支", 6800.0),
    ("火油桶", "桶", 160.0),
    ("撤离辎重车", "辆", 48.0),
]
# (resource 名, content) —— 知识资源
CAMP_KNOWLEDGE = [
    ("斥候简报", "斥候回报曹军南下动向与新野周边行军路线"),
    ("火攻布置图", "南门火油暗点布点、点火信号与伏兵位置的战术图"),
    ("百姓撤离名册", "新野百姓向樊城、江夏方向撤离的登记名册"),
]
# (seq, title, description, info_flow, logistics_flow, people_flow, risk)
CAMP_EVENTS = [
    (1, "斥候确认曹军路线", "斥候回报曹军主力南下，确认其行军路线与到达时间。",
     "斥候回报曹军行军路线", "新野大营物资盘点", "百姓开始撤离登记", "情报延迟"),
    (2, "军粮与火油盘点", "清点新野城军粮、火油与箭矢储备，确认火攻弹药充足。",
     "盘点结果传回大营", "军粮火油入库盘点", "运输民夫整备", "物资缺口"),
    (3, "百姓撤离名册确认", "确认百姓撤离名册，安排分批向樊城方向转移。",
     "撤离名册发布", "辎重车集中装载", "百姓向樊城方向移动", "道路拥堵"),
    (4, "南门火油暗点布置", "在南门伏击位布置火油暗点，完成引火路线的铺设。",
     "火攻信号约定", "火油入城门暗点", "伏兵进入指定位置", "提前暴露"),
    (5, "诱敌入城信号下达", "诱敌部队佯装败退，按约定信号将曹军引入新野城。",
     "诱敌信号下达", "箭矢转入伏击点", "主力后撤至城外", "敌军识破"),
    (6, "新野点火", "点火令下达，火起新野，曹军前锋大乱。",
     "点火令传达", "火油桶引燃消耗", "曹军前锋混乱溃退", "火势失控"),
    (7, "曹军混乱撤退", "曹军后方不明虚实全线撤退，新野火攻成功。",
     "战果情报汇总", "城门火势封锁", "曹军后撤溃散", "追兵逼近"),
    (8, "刘备军民转移复盘", "战果汇总，刘备军民携剩余物资向江夏方向转移并复盘。",
     "战后复盘会议", "剩余军粮随队转移", "军民向江夏方向移动", "补给消耗"),
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


def _ensure_liuming_personal() -> dict:
    """Create liuming via register_personal_space (registration contract)."""
    print(f"== 个人空间：{PERSONAL['name']} ({PERSONAL['ouid']}) ==")
    password = (
        os.getenv(PASSWORD_ENV_KEY)
        or os.getenv(SHARED_PASSWORD_ENV_KEY)
        or DEFAULT_DEMO_PASSWORD
    ).strip()
    if not password:
        print(f"[error] 未设置 {PASSWORD_ENV_KEY}。")
        raise SystemExit(1)

    accounts = db.query_account_by_login(PERSONAL["login"])
    if accounts:
        account = accounts[0]
        if verify_password(password, account["password"], account["salt"]):
            print(f"[skip] account: {PERSONAL['login']} 已存在")
        else:
            hashed, salt = hash_password(password)
            db.update_account_password(account["person_id"], hashed, salt)
            print(f"[ok] account: {PERSONAL['login']} 密码已同步")
    else:
        hashed, salt = hash_password(password)
        person, account, org, membership = db.register_personal_space(
            puid=PERSONAL["puid"], name=PERSONAL["name"],
            login=PERSONAL["login"], password_hash=hashed, salt=salt,
        )
        print(f"[ok] register_personal_space: {PERSONAL['puid']} -> "
              f"{org['ouid']} (owner)")
        return {"person": person, "org": org}

    persons = db.query_person_by_puid(PERSONAL["puid"])
    if not persons:
        print(f"[error] person {PERSONAL['puid']} 不存在，请先重建数据库")
        raise SystemExit(1)
    person = persons[0]

    orgs = db.query_organization_by_ouid(PERSONAL["ouid"])
    if orgs:
        print(f"[skip] 个人空间已存在: {PERSONAL['ouid']}")
        return {"person": person, "org": orgs[0]}

    org = db.create_organization(
        name=f"{PERSONAL['name']}的个人空间", org_type="personal",
        description="个人空间", funds=0.0, reputation=0,
        ouid=PERSONAL["ouid"],
    )
    _ensure_membership(person["id"], org["id"], "owner")
    print(f"[ok] 补建个人空间 {PERSONAL['ouid']}")
    return {"person": person, "org": org}


def _seed_shop(owner_person: dict) -> dict:
    print(f"== 上下文 S：{SHOP['name']} ({SHOP['ouid']}) ==")
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

    operator = owner_person
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


def _seed_campaign() -> dict:
    print(f"== 上下文 C：{CAMP['name']} ({CAMP['ouid']}) ==")
    org_rows = db.query_organization_by_ouid(CAMP["ouid"])
    if org_rows:
        org = org_rows[0]
        print(f"[skip] 组织已存在")
    else:
        org = db.create_organization(
            name=CAMP["name"], org_type=CAMP["type"],
            description=CAMP["description"], funds=0.0,
            reputation=0, ouid=CAMP["ouid"],
        )
        print(f"[ok] 创建组织")
    org_id = org["id"]

    wh = _find_warehouse(org_id, CAMP["warehouse"]["code"])
    if not wh:
        wh = db.create_warehouse(
            org_id, CAMP["warehouse"]["name"], CAMP["warehouse"]["code"],
            CAMP["warehouse"]["location"], "战役军需仓库")
        print(f"[ok] 创建仓库 {CAMP['warehouse']['code']}")
    else:
        print(f"[skip] 仓库已存在 {CAMP['warehouse']['code']}")

    for p in CAMP_PEOPLE:
        person = _person(p["puid"], p["name"])
        _ensure_membership(person["id"], org_id, p["role"])

    for (name, unit, qty) in CAMP_SUPPLIES:
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
            location_path=CAMP["warehouse"]["code"], quantity=qty, unit=unit,
        )
        print(f"[ok] 资源 {name}: {qty}{unit}")

    for (name, content) in CAMP_KNOWLEDGE:
        if _find_resource(org_id, name):
            print(f"[skip] 知识资源已存在: {name}")
            continue
        db.create_resource(
            organization_id=org_id, name=name,
            resource_type="knowledge", unit="份", content=content,
        )
        print(f"[ok] 知识资源 {name}")

    _seed_campaign_timeline(org_id)
    return {"org_id": org_id, "ouid": CAMP["ouid"]}


def _seed_campaign_timeline(org_id: int) -> None:
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
        for (seq, title, desc, info, logistics, people, risk) in CAMP_EVENTS:
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
        CAMPAIGN_CODE, CAMPAIGN_NAME, "seed_recording_data.py", "pm")
    db.add_campaign_import_org(campaign["id"], org_id, False)
    for (seq, title, desc, info, logistics, people, risk) in CAMP_EVENTS:
        db.create_campaign_event(
            campaign["id"], org_id, seq, title, desc, {
                "info_flow": info, "logistics_flow": logistics,
                "people_flow": people, "risk": risk,
            })
        print(f"[ok] 时间线事件 #{seq} {title}")


def main() -> int:
    personal = _ensure_liuming_personal()
    shop = _seed_shop(personal["person"])
    camp = _seed_campaign()

    print("\n== 汇总 ==")
    print(f"  {PERSONAL['ouid']}: personal 空间（owner）就绪")

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

    camp_resources = db.query_resource(camp["org_id"])
    print(f"  {camp['ouid']}: 资源 {len(camp_resources)} 个")
    timeline = db.get_space_timeline(camp["org_id"])
    print(f"  {camp['ouid']}: 时间线事件 {len(timeline)} 条")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
