"""
初始化数据库：建表 + 插入三国示例数据。
用法: PYTHONPATH=. python scripts/init_db.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.db.database import (
    init_database, create_resource, create_person,
    create_organization, add_membership,
    create_party, create_transaction,
    create_warehouse, create_resource_warehouse,
    create_account,
    query_person, query_party, query_resource, query_organization,
)
from src.auth.auth import hash_password


def main():
    init_database(drop_all=True)

    # ── Organizations ──────────────────────────────────────────
    orgs = {}
    for name, otype, desc, funds, rep, ouid in [
        ("系统空间", "system", "系统全局管理空间", 0, 0, "system"),
        ("蜀国", "company", "蜀汉政权", 50000, 80, "shu"),
        ("魏国", "company", "曹魏政权", 80000, 90, "wei"),
        ("吴国", "company", "东吴政权", 60000, 75, "wu"),
        ("刘备", "personal", "刘备个人组织", 5000, 70, "liubei"),
        ("诸葛亮", "personal", "诸葛亮个人组织", 8000, 85, "zhugeliang"),
    ]:
        orgs[name] = create_organization(name, otype, desc, funds, rep, ouid=ouid)

    # ── Persons ───────────────────────────────────────────────
    persons = {}
    for name, puid in [
        ("超级用户", "super"),
        ("张飞", "zhangfei"),
        ("诸葛亮", "zhugeliang"),
        ("关羽", "guanyu"),
        ("赵云", "zhaoyun"),
        ("刘备", "liubei"),
        ("诸葛瞻", "zhugezhan"),
        ("黄月英", "huangyueying"),
        ("曹操", "caocao"),
        ("司马懿", "simayi"),
        ("孙权", "sunquan"),
        ("周瑜", "zhouyu"),
    ]:
        persons[name] = create_person(name=name, puid=puid)

    # ── Account (认证凭据, 仅给有密码的角色) ──────
    accounts = {}
    for person_name, login, pwd, system_role in [
        ("超级用户", "super@system.cn", "demo123", "super"),
        ("诸葛亮", "zhugeliang@shu.cn", "demo123", "user"),
        ("刘备", "liubei@shu.cn", "demo123", "user"),
        ("曹操", "caocao@wei.cn", "demo123", "user"),
        ("孙权", "sunquan@wu.cn", "demo123", "user"),
    ]:
        hashed_password, salt = hash_password(pwd)
        accounts[person_name] = create_account(
            person_id=persons[person_name]["id"],
            login=login,
            password=hashed_password,
            salt=salt,
            system_role=system_role,
        )

    # ── Membership (person ↔ org, 带 role) ──────────────────
    links = [
        ("超级用户", "系统空间", "admin"),
        ("刘备", "蜀国", "主公"),
        ("诸葛亮", "蜀国", "丞相"),
        ("张飞", "蜀国", "将军"),
        ("关羽", "蜀国", "将军"),
        ("赵云", "蜀国", "将军"),
        ("刘备", "刘备", "本人"),
        ("诸葛亮", "诸葛亮", "本人"),
        ("诸葛亮", "刘备", "军师"),
        ("诸葛瞻", "诸葛亮", "子女"),
        ("黄月英", "诸葛亮", "配偶"),
        ("曹操", "魏国", "主公"),
        ("司马懿", "魏国", "谋士"),
        ("孙权", "吴国", "主公"),
        ("周瑜", "吴国", "都督"),
    ]
    for person_name, org_name, role in links:
        add_membership(persons[person_name]["id"], orgs[org_name]["id"], role)

    # ── Warehouse ────────────────────────────────────────────
    warehouses = {}
    for org_name, name, code, loc in [
        ("蜀国", "蜀国武库", "A", "成都"),
        ("蜀国", "蜀国军械库", "B", "成都"),
        ("魏国", "魏国武库", "A", "洛阳"),
        ("吴国", "吴国水军基地", "A", "建业"),
    ]:
        warehouses[(org_name, name)] = create_warehouse(
            orgs[org_name]["id"], name, code, loc
        )

    # ── Resources (physical) ────────────────────────────────
    resources = {}
    for org_name, name, rtype, unit in [
        ("蜀国", "青龙偃月刀", "physical", "把"),
        ("蜀国", "丈八蛇矛", "physical", "把"),
        ("蜀国", "连弩", "physical", "架"),
        ("蜀国", "战船", "physical", "艘"),
        ("魏国", "长枪", "physical", "支"),
        ("吴国", "战船", "physical", "艘"),
    ]:
        resources[(org_name, name)] = create_resource(
            orgs[org_name]["id"], name, rtype, unit
        )

    # ── Resources (financial) ────────────────────────────────
    for org_name, name, amount, currency in [
        ("蜀国", "蜀国金库", 50000, "黄金"),
        ("魏国", "魏国金库", 80000, "黄金"),
        ("吴国", "吴国金库", 60000, "黄金"),
    ]:
        resources[(org_name, name)] = create_resource(
            orgs[org_name]["id"], name, "financial", unit=None,
            amount=amount, currency=currency
        )

    # ── Resources (human) ────────────────────────────────────
    for org_name, name, person_db_id in [
        ("蜀国", "蜀国兵力", persons["张飞"]["id"]),
        ("魏国", "魏国兵力", persons["曹操"]["id"]),
        ("吴国", "吴国兵力", persons["孙权"]["id"]),
    ]:
        resources[(org_name, name)] = create_resource(
            orgs[org_name]["id"], name, "human", person_id=person_db_id
        )

    # ── Resources (knowledge) ────────────────────────────────
    resources[("蜀国", "隆中对")] = create_resource(
        orgs["蜀国"]["id"], "隆中对", "knowledge",
        content="三分天下之策"
    )

    # ── ResourceWarehouse (resource quantities) ──────────────
    rw = [
        ("蜀国", "青龙偃月刀", "total", 1, "把"),
        ("蜀国", "青龙偃月刀", "A", 1, "把"),
        ("蜀国", "青龙偃月刀", "A-1-001", 1, "把"),
        ("蜀国", "丈八蛇矛", "total", 1, "把"),
        ("蜀国", "丈八蛇矛", "A", 1, "把"),
        ("蜀国", "丈八蛇矛", "A-1-002", 1, "把"),
        ("蜀国", "连弩", "total", 50, "架"),
        ("蜀国", "连弩", "A", 30, "架"),
        ("蜀国", "连弩", "A-1-003", 30, "架"),
        ("蜀国", "连弩", "B", 20, "架"),
        ("蜀国", "连弩", "B-1-001", 20, "架"),
        ("蜀国", "战船", "total", 10, "艘"),
        ("蜀国", "战船", "A", 10, "艘"),
        ("蜀国", "战船", "A-2-001", 10, "艘"),
        ("魏国", "长枪", "total", 200, "支"),
        ("魏国", "长枪", "A", 200, "支"),
        ("魏国", "长枪", "A-1-001", 200, "支"),
        ("吴国", "战船", "total", 100, "艘"),
        ("吴国", "战船", "A", 100, "艘"),
        ("吴国", "战船", "A-2-001", 100, "艘"),
    ]
    for org_name, res_name, loc_path, qty, unit in rw:
        wh_code = "B" if loc_path.startswith("B") else "A"
        wh = next(w for (o, _n), w in warehouses.items()
                  if o == org_name and w["code"] == wh_code)
        create_resource_warehouse(
            resources[(org_name, res_name)]["id"],
            wh["id"], loc_path, qty, unit
        )

    # ── Transactions (先创建 transaction, 再创建 party) ─────
    # t1: 诸葛亮资助蜀汉军费
    t1 = create_transaction(1000.00, "军费", "诸葛亮家资助蜀汉军费", organization_id=orgs["蜀国"]["id"])
    create_party(persons["刘备"]["id"], orgs["蜀国"]["id"], t1["id"],
                 "payer", "蜀汉集团支付", funds_change=-1000, reputation_change=-2)
    create_party(persons["诸葛亮"]["id"], orgs["蜀国"]["id"], t1["id"],
                 "payee", "诸葛亮家接收", funds_change=1000, reputation_change=2)

    # t2: 蜀汉发放俸禄
    t2 = create_transaction(500.00, "俸禄", "蜀汉发放俸禄", organization_id=orgs["蜀国"]["id"])
    create_party(persons["刘备"]["id"], orgs["蜀国"]["id"], t2["id"],
                 "payer", "蜀汉集团支付俸禄", funds_change=-500, reputation_change=1)
    create_party(persons["诸葛亮"]["id"], orgs["蜀国"]["id"], t2["id"],
                 "payee", "诸葛亮接收俸禄", funds_change=500, reputation_change=0)

    # t3: 东吴联合抗曹军费
    t3 = create_transaction(3000.00, "军费", "东吴联合抗曹军费", organization_id=orgs["吴国"]["id"])
    create_party(persons["孙权"]["id"], orgs["吴国"]["id"], t3["id"],
                 "payer", "东吴支付军费", funds_change=-3000, reputation_change=-5)
    create_party(persons["刘备"]["id"], orgs["蜀国"]["id"], t3["id"],
                 "payee", "蜀汉接收军费", funds_change=3000, reputation_change=5)

    # ── Verify ─────────────────────────────────────────────
    print("\n── 验证 ──")
    for org_name, label in [("蜀国", "蜀国"), ("魏国", "魏国"), ("吴国", "吴国")]:
        organization_id = orgs[org_name]["id"]
        org = query_organization(org_id=organization_id)[0]
        per = query_person(organization_id)
        pat = query_party(organization_id)
        res = query_resource(organization_id)
        print(f"\n{label} (organization_id={organization_id}, ouid={org['ouid']}):")
        print(f"  funds={org['funds']}, reputation={org['reputation']}")
        print(f"  person:  {[p['name'] for p in per]}")
        print(f"  party:   {[(p['person_name']+'('+p['role']+',funds:'+str(p['funds_change'])+')') for p in pat]}")
        print(f"  resource: {[(r['name']+'['+r['type']+']') for r in res]}")


if __name__ == "__main__":
    main()
