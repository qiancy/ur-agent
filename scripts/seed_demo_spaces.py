#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
预置示例空间种子脚本（T4 交付物）。

作用：
  1. 依次导入 3 个示例空间包（fire_xinye / family_learning / deep_space_fleet），
     已导入（status='active'）则跳过，保证幂等。
  2. 创建/复用演示用户 zhansan（puid=zhansan, name=张三），并建立 membership 到：
     - 既有 fe06_spike_* ecommerce 演示店铺（找不到则跳过并提示）
     - fire_xinye_shu / zhangsan_family / deep_space_fleet
  3. 演示账号密码不写入源码：从环境变量 DEMO_ZHANSAN_PASSWORD 读取，
     否则尝试读取项目根未提交的 .env 中的 DEMO_ZHANSAN_PASSWORD=；
     仍为空则跳过建号并在 stdout 提示。

用法：
  PYTHONPATH=. python scripts/seed_demo_spaces.py
"""
import json
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv

# 优先级：环境变量 > .env；override=False 保证 shell 环境优先
load_dotenv(REPO_ROOT / ".env", override=False)

from src.auth.auth import hash_password
from src.db import database as db
from src.db.database import get_db_connection

CAMPAIGN_DIR = REPO_ROOT / "data" / "campaigns"
CAMPAIGN_CODES = ["fire_xinye", "family_learning", "deep_space_fleet"]

MAX_RETRIES = 4
RETRY_BASE_DELAY = 2.0

DEMO_PUID = "zhansan"
DEMO_NAME = "张三"

# (ouid 或 ouid 前缀, 角色)；前缀以 '*' 结尾表示模糊匹配
DEMO_SPACES = [
    ("zhansan_shop", "owner"),
    ("fire_xinye_shu", "owner"),
    ("zhangsan_family", "owner"),
    ("deep_space_fleet", "owner"),
]

PASSWORD_ENV_KEY = "DEMO_ZHANSAN_PASSWORD"


def _find_org(target: str):
    """按 ouid 精确匹配，或按前缀模糊匹配（'*' 结尾）。"""
    if target.endswith("*"):
        prefix = target[:-1]
        rows = db.query_organization(org_type="ecommerce")
        for r in rows:
            if r["ouid"].startswith(prefix):
                return r
        return None
    rows = db.query_organization_by_ouid(target)
    return rows[0] if rows else None


def _direction_amount(direction: str, amount: float) -> float:
    if direction in {"out", "-"}:
        return -abs(float(amount))
    if direction in {"in", "+"}:
        return abs(float(amount))
    raise ValueError(f"Invalid party direction: {direction}")


def _hard_reset_campaign(campaign_code: str):
    """兜底清理：强制删除某 campaign_code 的全部导入行（含事件/组织关联），幂等。"""
    try:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM campaign_event WHERE campaign_import_id IN "
                "(SELECT id FROM campaign_import WHERE campaign_code = %s)",
                (campaign_code,))
            cur.execute(
                "DELETE FROM campaign_import_org WHERE campaign_import_id IN "
                "(SELECT id FROM campaign_import WHERE campaign_code = %s)",
                (campaign_code,))
            cur.execute("DELETE FROM campaign_import WHERE campaign_code = %s", (campaign_code,))
            conn.commit()
            cur.close()
        finally:
            conn.close()
    except Exception as exc:
        raise RuntimeError(f"清理 {campaign_code} 失败: {exc}") from exc


def _cleanup_campaign(campaign_code: str, attempt: int):
    """删除失败导入留下的 active 导入行；delete_campaign_import 优先，失败走兜底。"""
    rows = db.get_active_campaign_import_by_code(campaign_code)
    for row in rows:
        try:
            db.delete_campaign_import(row["id"])
        except Exception as exc:
            print(f"[warn] 第 {attempt} 次清理 {campaign_code} (id={row['id']}) 失败: {exc}")
    _hard_reset_campaign(campaign_code)


def _import_campaign_once(campaign_code: str) -> dict:
    """照搬 src/routers/campaign.py::import_campaign 的导入逻辑，直接调用 database 函数。"""
    path = CAMPAIGN_DIR / f"{campaign_code}.json"
    with open(path, encoding="utf-8") as fh:
        template = json.load(fh)

    campaign = db.create_campaign_import(
        campaign_code=template["campaign_code"],
        campaign_name=template["campaign_name"],
        source_file=str(path.relative_to(REPO_ROOT)),
        imported_by_puid=DEMO_PUID,
    )

    orgs: dict = {}
    people: dict = {}
    warehouses: dict = {}
    counts = {"orgs": 0, "persons": 0, "memberships": 0,
              "warehouses": 0, "resources": 0, "transactions": 0, "events": 0}

    try:
        for org_cfg in template.get("organizations", []):
            rows = db.query_organization_by_ouid(org_cfg["ouid"])
            if rows:
                org, created = rows[0], False
            else:
                org = db.create_organization(
                    name=org_cfg["name"],
                    org_type=org_cfg.get("type", "campaign"),
                    description=org_cfg.get("description"),
                    funds=org_cfg.get("funds", 0),
                    reputation=org_cfg.get("reputation", 0),
                    ouid=org_cfg["ouid"],
                )
                created = True
            orgs[org["ouid"]] = org
            db.add_campaign_import_org(campaign["id"], org["id"], created)
            counts["orgs"] += 1

        for person_cfg in template.get("persons", []):
            rows = db.query_person_by_puid(person_cfg["puid"])
            person = rows[0] if rows else db.create_person(
                name=person_cfg["name"], puid=person_cfg["puid"])
            people[person["puid"]] = person
            counts["persons"] += 1

        for member_cfg in template.get("memberships", []):
            person, org = people.get(member_cfg["puid"]), orgs.get(member_cfg["ouid"])
            if not person or not org:
                raise RuntimeError(f"Invalid membership in {campaign_code} template")
            if not db.query_membership(person["id"], org["id"]):
                db.add_membership(person["id"], org["id"], member_cfg.get("role", "member"))
                counts["memberships"] += 1

        for wh_cfg in template.get("warehouses", []):
            org = orgs.get(wh_cfg["ouid"])
            if not org:
                raise RuntimeError(f"Invalid warehouse organization in {campaign_code} template")
            wh = db.create_warehouse(
                org["id"], wh_cfg["name"], wh_cfg["code"],
                wh_cfg.get("location"), wh_cfg.get("description"))
            warehouses[(org["ouid"], wh["code"])] = wh
            counts["warehouses"] += 1

        for res_cfg in template.get("resources", []):
            org = orgs.get(res_cfg["ouid"])
            if not org:
                raise RuntimeError(f"Invalid resource organization in {campaign_code} template")
            person_id = None
            if res_cfg.get("puid"):
                person = people.get(res_cfg["puid"])
                if person:
                    person_id = person["id"]
            res = db.create_resource(
                organization_id=org["id"],
                name=res_cfg["name"],
                resource_type=res_cfg.get("type", "physical"),
                unit=res_cfg.get("unit"),
                amount=res_cfg.get("amount"),
                currency=res_cfg.get("currency"),
                person_id=person_id,
                content=res_cfg.get("content"),
            )
            if res_cfg.get("warehouse_code") and res_cfg.get("amount") is not None:
                wh = warehouses.get((org["ouid"], res_cfg["warehouse_code"]))
                if wh:
                    db.create_resource_warehouse(
                        res["id"], wh["id"], wh["code"], res_cfg["amount"], res_cfg.get("unit"))
                    db.create_resource_warehouse(
                        res["id"], wh["id"], "total", res_cfg["amount"], res_cfg.get("unit"))
            counts["resources"] += 1

        for tx_cfg in template.get("transactions", []):
            org = orgs.get(tx_cfg["ouid"])
            if not org:
                raise RuntimeError(f"Invalid transaction organization in {campaign_code} template")
            tx = db.create_transaction(
                amount=tx_cfg["amount"],
                category=tx_cfg["category"],
                description=tx_cfg.get("description"),
                organization_id=org["id"],
            )
            for party_cfg in tx_cfg.get("parties", []):
                person = people.get(party_cfg["puid"])
                if not person:
                    raise RuntimeError(f"Invalid transaction party in {campaign_code} template")
                db.create_party(
                    person_id=person["id"],
                    organization_id=org["id"],
                    transaction_id=tx["id"],
                    role=party_cfg.get("role", "participant"),
                    description=party_cfg.get("description"),
                    funds_change=_direction_amount(
                        party_cfg.get("direction", "in"), party_cfg.get("amount", 0)),
                    reputation_change=party_cfg.get("reputation_change", 0),
                )
            counts["transactions"] += 1

        for event_cfg in template.get("events", []):
            org = orgs.get(event_cfg["ouid"])
            if not org:
                raise RuntimeError(f"Invalid event organization in {campaign_code} template")
            db.create_campaign_event(
                campaign_import_id=campaign["id"],
                organization_id=org["id"],
                seq=event_cfg["seq"],
                title=event_cfg["title"],
                description=event_cfg.get("description"),
                payload=event_cfg,
            )
            counts["events"] += 1
    except Exception:
        raise

    print(f"[ok] {campaign_code}: 导入完成 {counts}")
    return {"skipped": False, "campaign_import_id": campaign["id"], "counts": counts}


def import_campaign_pack(campaign_code: str) -> dict:
    """幂等导入：已存在 active 导入则跳过；失败重试并先清理残留。"""
    existing = db.get_active_campaign_import_by_code(campaign_code)
    if existing:
        print(f"[skip] {campaign_code}: 已存在 active 导入 (id={existing[0]['id']})，跳过")
        return {"skipped": True, "campaign_import_id": existing[0]["id"]}

    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return _import_campaign_once(campaign_code)
        except Exception as exc:
            last_err = exc
            print(f"[retry] {campaign_code}: 第 {attempt} 次导入失败 ({exc})")
            if attempt < MAX_RETRIES:
                _cleanup_campaign(campaign_code, attempt)
                time.sleep(min(RETRY_BASE_DELAY * attempt, 8.0))
    raise RuntimeError(f"{campaign_code} 导入失败（已重试 {MAX_RETRIES} 次）: {last_err}") from last_err


def ensure_demo_user(password: str) -> dict:
    """创建/复用演示用户 zhansan，并建立 4 空间 membership 与单账号。

    AUTH-02: 只创建一个 account.login=zhansan；person.puid=zhansan。
    空间切换靠 membership + JWT，不再使用 zhansan@<ouid> 多账号。
    """
    rows = db.query_person_by_puid(DEMO_PUID)
    person = rows[0] if rows else db.create_person(name=DEMO_NAME, puid=DEMO_PUID)
    created_person = not rows

    created_memberships = 0
    for target, role in DEMO_SPACES:
        org = _find_org(target)
        if not org:
            print(f"[warn] 未找到组织 {target}，跳过 membership")
            continue
        if not db.query_membership(person["id"], org["id"]):
            db.add_membership(person["id"], org["id"], role)
            created_memberships += 1
            print(f"[ok] membership: {DEMO_PUID} -> {org['ouid']} (role={role})")

    created_accounts = 0
    if password:
        if db.query_account_by_login(DEMO_PUID):
            print(f"[skip] account: {DEMO_PUID} 已存在")
        else:
            hashed, salt = hash_password(password)
            db.create_account(person_id=person["id"], login=DEMO_PUID,
                              password=hashed, salt=salt, system_role="user")
            created_accounts += 1
            print(f"[ok] account: {DEMO_PUID}")

    return {
        "person_created": created_person,
        "person_id": person["id"],
        "memberships_created": created_memberships,
        "accounts_created": created_accounts,
    }


def main() -> int:
    password = os.getenv(PASSWORD_ENV_KEY, "").strip()

    print("== 导入示例空间包 ==")
    import_results = [import_campaign_pack(code) for code in CAMPAIGN_CODES]

    print("\n== 演示账号 zhansan ==")
    if not password:
        print("未设置 DEMO_ZHANSAN_PASSWORD，跳过演示账号创建")
        user_result = None
    else:
        last_err = None
        user_result = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                user_result = ensure_demo_user(password)
                break
            except Exception as exc:
                last_err = exc
                print(f"[retry] 演示账号设置第 {attempt} 次失败 ({exc})")
                if attempt < MAX_RETRIES:
                    time.sleep(min(RETRY_BASE_DELAY * attempt, 8.0))
        if user_result is None:
            raise RuntimeError(f"演示账号设置失败（已重试 {MAX_RETRIES} 次）: {last_err}") from last_err

    print("\n== 汇总 ==")
    for code, result in zip(CAMPAIGN_CODES, import_results):
        if result.get("skipped"):
            print(f"  {code}: 已导入（跳过）")
        else:
            c = result["counts"]
            print(f"  {code}: 新增导入 (orgs={c['orgs']}, persons={c['persons']}, "
                  f"memberships={c['memberships']}, warehouses={c['warehouses']}, "
                  f"resources={c['resources']}, transactions={c['transactions']}, "
                  f"events={c['events']})")
    if user_result is None:
        print(f"  {DEMO_PUID}: 未创建账号（未配置密码）")
    else:
        print(f"  {DEMO_PUID}: person_created={user_result['person_created']}, "
              f"memberships_created={user_result['memberships_created']}, "
              f"accounts_created={user_result['accounts_created']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
