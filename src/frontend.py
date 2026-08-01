"""
Uni-Resource Agent — Gradio frontend (v5.2).

Connects to FastAPI backend at http://localhost:8000.
"""
import os
import time
from typing import List

import requests
import gradio as gr

from src.logging_config import setup_logging

logger = setup_logging("frontend")
API = "http://localhost:8000"
BROWSER_STATE_SECRET = os.getenv("BROWSER_STATE_SECRET") or os.getenv("JWT_SECRET") or "unires-dev-browser-state-secret"


# ── Login state ──────────────────────────────────────────────────────────────

def _empty_login_state():
    return {
        "access_token": None,
        "org_ouid": None,
        "org_name": None,
        "org_type": None,
        "puid": None,
        "person_name": None,
        "role": None,
        "system_role": None,
    }


def _login_state_from_response(resp):
    person = resp.get("person", {})
    org = resp.get("organization", {})
    membership = resp.get("membership", {})
    return {
        "access_token": resp.get("access_token"),
        "org_ouid": org.get("ouid"),
        "org_name": org.get("name"),
        "org_type": org.get("type"),
        "puid": person.get("puid"),
        "person_name": person.get("name"),
        "role": membership.get("role"),
        "system_role": resp.get("system_role", "user"),
    }


def _is_logged_in(state):
    return bool((state or {}).get("access_token"))


# ── helpers ──────────────────────────────────────────────────────────────────

def _log_response(method, path, started, response):
    elapsed = time.monotonic() - started
    logger.info(
        "%s %s -> %s %.2fs body=%s",
        method,
        path,
        response.status_code,
        elapsed,
        response.text[:1000],
    )


def _get(path, params=None, timeout=10, state=None):
    started = time.monotonic()
    logger.info("GET %s params=%s timeout=%s", path, params, timeout)
    headers = {}
    token = (state or {}).get("access_token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = requests.get(f"{API}{path}", params=params, timeout=timeout, headers=headers)
        _log_response("GET", path, started, r)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.exception("GET %s failed after %.2fs: %s", path, time.monotonic() - started, e)
        raise


def _delete(path, params=None, timeout=10, state=None):
    started = time.monotonic()
    logger.info("DELETE %s params=%s timeout=%s", path, params, timeout)
    headers = {}
    token = (state or {}).get("access_token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = requests.delete(f"{API}{path}", params=params, timeout=timeout, headers=headers)
        _log_response("DELETE", path, started, r)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.exception("DELETE %s failed after %.2fs: %s", path, time.monotonic() - started, e)
        raise


def _post(path, body=None, params=None, timeout=10, state=None):
    started = time.monotonic()
    safe_body = dict(body or {})
    if "password" in safe_body:
        safe_body["password"] = "***"
    logger.info("POST %s params=%s body=%s timeout=%s", path, params, safe_body, timeout)
    headers = {}
    token = (state or {}).get("access_token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = requests.post(f"{API}{path}", params=params, json=body, timeout=timeout, headers=headers)
        _log_response("POST", path, started, r)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.exception("POST %s failed after %.2fs: %s", path, time.monotonic() - started, e)
        raise


def _load_orgs():
    try:
        return _get("/organizations")
    except Exception:
        return []


def _org_labels() -> List[str]:
    orgs = _load_orgs()
    labels = [f"{o['name']} ({o['type']})" for o in orgs]
    return labels or ["蜀国 (company)"]


def _label_to_ouid(label: str, state=None) -> str:
    for org in _load_orgs():
        if label == f"{org['name']} ({org['type']})":
            return org["ouid"]
    if (state or {}).get("org_ouid"):
        return state["org_ouid"]
    return "shu"


def _current_org_label(state=None) -> str:
    state = state or {}
    if _is_logged_in(state) and state.get("org_name") and state.get("org_type"):
        return f"{state['org_name']} ({state['org_type']})"
    labels = _org_labels()
    return labels[0] if labels else "蜀国 (company)"


def _auth_header(state=None) -> str:
    state = state or {}
    if _is_logged_in(state):
        system_role = state.get("system_role") or "user"
        return f"{state.get('person_name')} @ {state.get('org_name')} ({state.get('role') or 'member'}, system:{system_role})"
    return "未登录"


def _show_home():
    return (
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
    )


def _show_auth():
    return (
        gr.update(visible=False),
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(visible=False),
    )


def _show_workspace(state):
    return (
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=True),
        gr.update(visible=(state or {}).get("org_type") == "ecommerce"),
    )


def _blank_workspace():
    return "", "", "", "", "", [], "", "", "", "", [], ""


def _workspace_payload(org_label: str, state):
    ecommerce = (state or {}).get("org_type") == "ecommerce"
    return (
        load_personnel(org_label, state),
        load_assets(org_label, state),
        load_transactions(org_label, state),
        load_summary(org_label, state),
        load_campaigns(state),
        [],
        "",
        load_seller_stock(state) if ecommerce else "",
        load_seller_movements(state) if ecommerce else "",
        load_seller_summary(state) if ecommerce else "",
        [] if ecommerce else [],
        "" if ecommerce else "",
    )


# ── Authentication ───────────────────────────────────────────────────────────

def open_auth_fn():
    return "请登录或注册", *_show_auth()


def back_home_fn():
    return "未登录", *_show_home()


def login_fn(login, password, state):
    state = state or _empty_login_state()
    if not login.strip() or not password.strip():
        return (
            state,
            "请输入登录名和密码",
            _auth_header(state),
            gr.update(value=_org_labels()[0], choices=_org_labels(), interactive=True),
            *_show_auth(),
            *_blank_workspace(),
        )

    try:
        resp = _post("/auth/seller-login", {"login": login.strip(), "password": password.strip()}, state=state)
        new_state = _login_state_from_response(resp)
        org_label = _current_org_label(new_state)
        per, ast, tx, summary, campaigns, chatbot, chat_input, seller_stock, seller_mov, seller_sum, seller_chatbot, seller_chat_input = _workspace_payload(org_label, new_state)
        return (
            new_state,
            f"登录成功：{new_state.get('person_name')} @ {new_state.get('org_name')}",
            _auth_header(new_state),
            gr.update(value=org_label, choices=[org_label], interactive=False),
            *_show_workspace(new_state),
            per,
            ast,
            tx,
            summary,
            campaigns,
            chatbot,
            chat_input,
            seller_stock,
            seller_mov,
            seller_sum,
            seller_chatbot,
            seller_chat_input,
        )
    except Exception as e:
        logger.exception("Login failed")
        return (
            state,
            f"登录失败：{e}",
            _auth_header(state),
            gr.update(value=_org_labels()[0], choices=_org_labels(), interactive=True),
            *_show_auth(),
            *_blank_workspace(),
        )


def register_fn(login, password, confirm_password, name, role):
    if not login.strip() or not password.strip() or not name.strip():
        return "请填写完整信息", gr.update(value=""), gr.update(value="")
    if password.strip() != confirm_password.strip():
        return "两次密码不一致", gr.update(value=password), gr.update(value=confirm_password)

    try:
        resp = _post(
            "/auth/register",
            {
                "login": login.strip(),
                "password": password.strip(),
                "name": name.strip(),
                "role": role.strip() or "member",
            },
        )
        person_name = resp.get("person", {}).get("name", "未知")
        org_name = resp.get("organization", {}).get("name", "未知")
        return (
            f"注册成功：{person_name} @ {org_name}。请返回登录。",
            gr.update(value=""),
            gr.update(value=""),
        )
    except Exception as e:
        logger.exception("Register failed")
        return f"注册失败：{e}", gr.update(value=password), gr.update(value=confirm_password)


def logout_fn():
    state = _empty_login_state()
    return (
        state,
        "已退出登录",
        _auth_header(state),
        gr.update(value=_org_labels()[0], choices=_org_labels(), interactive=True),
        *_show_home(),
        *_blank_workspace(),
    )


def restore_login_fn(state):
    state = state or _empty_login_state()
    if not _is_logged_in(state):
        empty = _empty_login_state()
        return (
            empty,
            "未登录",
            _auth_header(empty),
            gr.update(value=_org_labels()[0], choices=_org_labels(), interactive=True),
            *_show_home(),
            *_blank_workspace(),
        )

    try:
        org_label = _current_org_label(state)
        per, ast, tx, summary, campaigns, chatbot, chat_input, seller_stock, seller_mov, seller_sum, seller_chatbot, seller_chat_input = _workspace_payload(org_label, state)
        return (
            state,
            "已恢复登录",
            _auth_header(state),
            gr.update(value=org_label, choices=[org_label], interactive=False),
            *_show_workspace(state),
            per,
            ast,
            tx,
            summary,
            campaigns,
            chatbot,
            chat_input,
            seller_stock,
            seller_mov,
            seller_sum,
            seller_chatbot,
            seller_chat_input,
        )
    except Exception:
        logger.exception("Restore login failed")
        empty = _empty_login_state()
        return (
            empty,
            "登录已失效，请重新登录",
            _auth_header(empty),
            gr.update(value=_org_labels()[0], choices=_org_labels(), interactive=True),
            *_show_home(),
            *_blank_workspace(),
        )


def restore_login_view_fn(state):
    return restore_login_fn(state)[1:]


# ── Tab 1: Personnel ────────────────────────────────────────────────────────

def load_personnel(org_label, state=None):
    ouid = _label_to_ouid(org_label, state)
    rows = _get("/person", {"ouid": ouid}, state=state)
    if not rows:
        return "暂无人员数据"
    lines = []
    for person in rows:
        role = person.get("membership_role") or "-"
        puid = person.get("puid") or "-"
        lines.append(f"**{person['name']}** — {role} (`{puid}`)")
    return "\n\n".join(lines)


def add_personnel_fn(org_label, name, role, state):
    if not name.strip():
        return "请输入姓名"
    ouid = _label_to_ouid(org_label, state)
    person = _post("/person", {"name": name.strip()}, state=state)
    if role.strip():
        _post("/organizations/members", {"puid": person["puid"], "ouid": ouid, "role": role.strip()}, state=state)
    return load_personnel(org_label, state)


# ── Tab 2: Assets ───────────────────────────────────────────────────────────

def load_assets(org_label, state=None):
    ouid = _label_to_ouid(org_label, state)
    rows = _get("/resource", {"ouid": ouid}, state=state)
    if not rows:
        return "暂无资源数据"
    lines = []
    for asset in rows:
        resource_type = asset.get("type") or "?"
        unit = asset.get("unit") or ""
        amount = asset.get("amount")
        content = asset.get("content") or ""
        if amount is not None:
            extra = f"  {amount} {unit}" if unit else f"  {amount}"
        elif content:
            extra = f"  [{content[:30]}]"
        else:
            extra = ""
        lines.append(f"**{asset['name']}** ({resource_type}){extra}")
    return "\n\n".join(lines)


def add_asset_fn(org_label, name, atype, amount, unit, state):
    if not name.strip():
        return "请输入资源名称"
    body = {
        "ouid": _label_to_ouid(org_label, state),
        "name": name.strip(),
        "resource_type": atype.strip() or "physical",
    }
    if unit.strip():
        body["unit"] = unit.strip()
    if amount:
        body["amount"] = float(amount)
    _post("/resource", body, params={"ouid": body["ouid"]}, state=state)
    return load_assets(org_label, state)


# ── Tab 3: Transactions ─────────────────────────────────────────────────────

def _format_money_direction(value):
    value = float(value or 0)
    if value > 0:
        return f"+¥{value:,.2f}"
    if value < 0:
        return f"-¥{abs(value):,.2f}"
    return "¥0.00"


def _parse_party_lines(lines_text):
    parties = []
    for line_no, raw_line in enumerate((lines_text or "").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 4:
            raise ValueError(f"参与方第 {line_no} 行格式错误：姓名,角色,+/-,金额[,说明]")
        name, role, direction, amount_text = parts[:4]
        desc = ",".join(parts[4:]).strip() if len(parts) > 4 else ""
        if direction not in {"+", "-"}:
            raise ValueError(f"参与方第 {line_no} 行方向必须是 + 或 -")
        try:
            amount = float(amount_text)
        except ValueError as exc:
            raise ValueError(f"参与方第 {line_no} 行金额无效") from exc
        if amount < 0:
            raise ValueError(f"参与方第 {line_no} 行金额应填写正数，方向用 + 或 - 表示")
        parties.append({
            "name": name,
            "role": role or "participant",
            "direction": direction,
            "amount": amount,
            "description": desc or None,
        })
    return parties


def load_transactions(org_label, state=None):
    ouid = _label_to_ouid(org_label, state)
    rows = _get("/transaction", {"ouid": ouid, "limit": 50}, state=state)
    if not rows:
        return "暂无交易记录"
    lines = []
    for txn in rows:
        parties = txn.get("parties") or []
        party_lines = []
        for party in parties:
            pname = party.get("person_name") or f"person_id:{party.get('person_id')}"
            role = party.get("role") or "participant"
            funds = _format_money_direction(party.get("funds_change") or 0)
            rep = int(party.get("reputation_change") or 0)
            rep_text = f", 声望{'+' if rep >= 0 else ''}{rep}" if rep else ""
            party_lines.append(f"  - {pname} [{role}] {funds}{rep_text}")
        party_text = "\n".join(party_lines) if party_lines else "  - 无参与方"
        lines.append(
            f"**交易 #{txn['id']} · ¥{float(txn['amount']):,.2f}** [{txn['category']}]\n"
            f"{txn.get('description') or ''}\n"
            f"参与方:\n{party_text}"
        )
    return "\n\n".join(lines)


def add_transaction_fn(org_label, amount, category, desc, party_lines, state):
    if not amount or float(amount) <= 0:
        return "请输入有效交易金额"
    ouid = _label_to_ouid(org_label, state)
    parties = _parse_party_lines(party_lines)
    if not parties:
        return "请至少填写一个参与方"

    resolved_parties = []
    for party in parties:
        people = _get("/person", {"ouid": ouid, "name": party["name"]}, state=state)
        if not people:
            raise ValueError(f"找不到参与方人员: {party['name']}")
        resolved_parties.append({**party, "puid": people[0]["puid"]})

    body = {
        "amount": float(amount),
        "category": category.strip() or "其他",
        "description": desc.strip() or None,
    }
    txn = _post("/transaction", body, params={"ouid": ouid}, state=state)
    txn_id = txn["id"]

    for party in resolved_parties:
        signed_amount = party["amount"] if party["direction"] == "+" else -party["amount"]
        _post(
            "/party",
            {
                "puid": party["puid"],
                "ouid": ouid,
                "transaction_id": txn_id,
                "role": party["role"],
                "description": party["description"],
                "funds_change": signed_amount,
                "reputation_change": 0,
            },
            params={"ouid": ouid},
            state=state,
        )
    return load_transactions(org_label, state)


# ── Tab 5: Summary ──────────────────────────────────────────────────────────

def load_summary(org_label, state=None):
    s = _get("/summary", {"ouid": _label_to_ouid(org_label, state)}, state=state)
    return (
        f"**{org_label} 财务摘要**\n\n"
        f"资金: ¥{s['funds']:,.2f}\n"
        f"声望: {s['reputation']}\n"
        f"总流出: ¥{s['total_outflow']:,.2f}\n"
        f"交易笔数: {s['transaction_count']}"
    )


# ── Tab 5: Campaigns ─────────────────────────────────────────────────────────

def _is_super(state):
    return (state or {}).get("system_role") == "super"


def load_campaigns(state=None):
    if not _is_logged_in(state):
        return "请先登录"
    rows = _get("/campaigns/imports", state=state)
    if not rows:
        return "暂无战役数据"
    lines = []
    for row in rows:
        orgs = row.get("organizations") or []
        org_text = ", ".join([f"{o.get('name')}(`{o.get('ouid')}`)" for o in orgs]) or "-"
        lines.append(
            f"**#{row['id']} {row['campaign_name']}** (`{row['campaign_code']}`)\n"
            f"组织: {org_text}\n"
            f"导入人: `{row.get('imported_by_puid')}`  状态: `{row.get('status')}`"
        )
    return "\n\n".join(lines)


def import_campaign_fn(campaign_code, state):
    if not _is_logged_in(state):
        return "请先登录", ""
    if not _is_super(state):
        return load_campaigns(state), "导入失败：需要系统超级用户账号 super@system.cn 登录。普通用户和组织级 admin 不能导入战役。"
    try:
        code = (campaign_code or "fire_xinye").strip() or "fire_xinye"
        resp = _post("/campaigns/import", {"campaign_code": code}, timeout=30, state=state)
        campaign = resp.get("campaign_import", {})
        if resp.get("already_imported"):
            return load_campaigns(state), f"已存在 active 战役：#{campaign.get('id')} {campaign.get('campaign_name')}，无需重复导入"
        return load_campaigns(state), f"导入成功：#{campaign.get('id')} {campaign.get('campaign_name')}"
    except Exception as e:
        logger.exception("Campaign import failed")
        return load_campaigns(state), f"导入失败：{e}"


def replay_campaign_fn(campaign_import_id, state):
    if not _is_logged_in(state):
        return "请先登录"
    if not campaign_import_id:
        return "请输入战役批次 ID"
    try:
        resp = _get(f"/campaigns/imports/{int(campaign_import_id)}/replay", timeout=20, state=state)
        events = resp.get("events") or []
        if not events:
            return "暂无可回放事件"
        lines = [f"# {resp.get('campaign_name')} 回放"]
        for event in events:
            org = event.get("organization") or {}
            lines.append(
                f"**{event.get('seq')}. {event.get('title')}**\n"
                f"{event.get('description') or ''}\n"
                f"组织: {org.get('name')} (`{org.get('ouid')}`)"
            )
        return "\n\n".join(lines)
    except Exception as e:
        logger.exception("Campaign replay failed")
        return f"回放失败：{e}"


def delete_campaign_fn(campaign_import_id, state):
    if not _is_logged_in(state):
        return "请先登录", ""
    if not _is_super(state):
        return load_campaigns(state), "删除失败：需要系统超级用户账号 super@system.cn 登录。普通用户和组织级 admin 不能删除战役。"
    if not campaign_import_id:
        return load_campaigns(state), "请输入战役批次 ID"
    try:
        resp = _delete(f"/campaigns/imports/{int(campaign_import_id)}", timeout=30, state=state)
        counts = resp.get("counts", {})
        return load_campaigns(state), f"删除成功：{counts}"
    except Exception as e:
        logger.exception("Campaign delete failed")
        return load_campaigns(state), f"删除失败：{e}"


# ── Tab 6: Chat ─────────────────────────────────────────────────────────────

def chat_fn(message, history, org_label, state):
    if not message.strip():
        return history, ""
    ouid = _label_to_ouid(org_label, state)
    logger.info("CHAT input ouid=%s org=%s message=%s", ouid, org_label, message)
    try:
        resp = _post("/chat", {"message": message}, params={"ouid": ouid}, timeout=40, state=state)
        reply = resp.get("response", "No response")
        logger.info("CHAT output ouid=%s response=%s", ouid, reply[:2000])
    except Exception as e:
        logger.exception("CHAT failed ouid=%s message=%s", ouid, message)
        reply = f"Error: {e}"
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": reply})
    return history, ""


# ── Seller area ──────────────────────────────────────────────────────────────

def load_seller_stock(state):
    if not _is_logged_in(state):
        return "请先登录"
    try:
        rows = _get("/seller/stock", state=state)
        if not rows:
            return "暂无库存数据"
        lines = ["| 商品 | 仓库 | 库位 | 数量 | 单位 |", "|---|---|---|---|---|"]
        for r in rows:
            lines.append(
                f"| {r.get('product_uid', '')} | {r.get('warehouse_code', '')} "
                f"| {r.get('location_path', '')} | {r.get('quantity', '')} "
                f"| {r.get('unit') or ''} |"
            )
        return "\n".join(lines)
    except Exception as e:
        logger.exception("Seller stock load failed")
        return f"加载库存失败：{e}"


def load_seller_movements(state, operation_type="", date_from="", date_to="", limit=50):
    if not _is_logged_in(state):
        return "请先登录"
    params = {}
    if operation_type:
        params["operation_type"] = operation_type
    if date_from:
        params["date_from"] = date_from
    if date_to:
        params["date_to"] = date_to
    if limit:
        params["limit"] = min(int(limit), 200)
    try:
        rows = _get("/seller/inventory-movements", params=params, state=state)
        if not rows:
            return "暂无流水数据"
        lines = [
            "| 时间 | 类型 | 商品 | 仓库 | 库位 | 变动 | 变动后 | 金额 | 单位 |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
        type_label = {"purchase_in": "入库", "sales_out": "出库"}
        for r in rows:
            lines.append(
                f"| {r.get('created_at', '')} | {type_label.get(r.get('operation_type'), r.get('operation_type', ''))} "
                f"| {r.get('product_uid', '')} | {r.get('warehouse_code', '')} "
                f"| {r.get('location_path', '')} | {r.get('quantity_delta', '')} "
                f"| {r.get('new_quantity', '')} | {r.get('total_amount', '')} "
                f"| {r.get('unit') or ''} |"
            )
        return "\n".join(lines)
    except Exception as e:
        logger.exception("Seller movements load failed")
        return f"加载流水失败：{e}"


def load_seller_summary(state):
    if not _is_logged_in(state):
        return "请先登录"
    try:
        data = _get("/seller/summary", state=state)
        lines = [
            f"### 经营摘要",
            f"- 销售收入：{data.get('sales_amount')}　采购支出：{data.get('purchase_amount')}",
            f"- 净现金流：{data.get('net_cash_flow')}　成交笔数：{data.get('movement_count')}",
            f"- 当前库存数量：{data.get('current_stock_quantity')}　商品数：{data.get('product_count')}",
            f"- 库存估值：{data.get('estimated_inventory_value')}（{data.get('valuation_method')}）",
        ]
        low = data.get("low_stock_items") or []
        if low:
            lines.append("\n**低库存商品**")
            lines.append("| 商品 | 数量 | 单位 |")
            lines.append("|---|---|---|")
            for item in low:
                lines.append(f"| {item.get('product_uid', '')} | {item.get('quantity', '')} | {item.get('unit') or ''} |")
        else:
            lines.append("\n无低库存商品。")
        top = data.get("top_products_by_sales") or []
        if top:
            lines.append("\n**热销商品（按销售额）**")
            lines.append("| 商品 | 销售额 | 销量 |")
            lines.append("|---|---|---|")
            for item in top:
                lines.append(
                    f"| {item.get('product_uid', '')} | {item.get('sales_amount', '')} "
                    f"| {item.get('sales_quantity', '')} |"
                )
        return "\n".join(lines)
    except Exception as e:
        logger.exception("Seller summary load failed")
        return f"加载摘要失败：{e}"


def seller_chat_fn(message, history, state):
    if not message.strip():
        return history, ""
    logger.info("SELLER CHAT message=%s", message)
    try:
        resp = _post("/seller/chat", {"message": message}, timeout=40, state=state)
        reply = resp.get("response", "No response")
        logger.info("SELLER CHAT response=%s", reply[:2000])
    except Exception as e:
        logger.exception("SELLER CHAT failed message=%s", message)
        reply = f"Error: {e}"
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": reply})
    return history, ""


# ── Build UI ─────────────────────────────────────────────────────────────────

def build_app():
    org_labels = _org_labels()
    default_org = org_labels[0]

    with gr.Blocks(title="Uni-Resource Agent") as demo:
        session_state = gr.BrowserState(_empty_login_state(), storage_key="unires_agent_login_state", secret=BROWSER_STATE_SECRET)
        landing_panel = gr.Group(visible=True)
        auth_panel = gr.Group(visible=False)
        workspace_panel = gr.Group(visible=False)
        seller_panel = gr.Group(visible=False)

        with landing_panel:
            gr.Markdown("# Uni-Resource Agent\n万物皆资源")
            gr.Markdown("登录后查看当前用户在当前组织的数据。")
            with gr.Row():
                enter_login_btn = gr.Button("登录", variant="primary")
                enter_reg_btn = gr.Button("注册", variant="secondary")

        with auth_panel:
            auth_status = gr.Markdown("请登录或注册")
            with gr.Row():
                back_btn = gr.Button("返回首页")
                logout_btn_top = gr.Button("退出登录")
            with gr.Tabs():
                with gr.TabItem("登录"):
                    login_info = gr.Markdown("未登录")
                    with gr.Row():
                        login_input = gr.Textbox(label="登录名", placeholder="caocao@wei.cn")
                        login_pwd = gr.Textbox(label="密码", placeholder="密码", type="password")
                    login_btn = gr.Button("登录", variant="primary")
                with gr.TabItem("注册"):
                    reg_output = gr.Markdown()
                    with gr.Row():
                        reg_login = gr.Textbox(label="登录名", placeholder="newuser@wei.cn")
                        reg_name = gr.Textbox(label="姓名", placeholder="用户名")
                    with gr.Row():
                        reg_pwd = gr.Textbox(label="密码", placeholder="密码", type="password")
                        reg_confirm = gr.Textbox(label="确认密码", placeholder="再次输入密码", type="password")
                    with gr.Row():
                        reg_role = gr.Textbox(label="角色", placeholder="member")
                        reg_btn = gr.Button("注册", variant="secondary")

        with workspace_panel:
            user_banner = gr.Markdown("未登录")
            with gr.Row():
                current_org = gr.Dropdown(choices=[default_org], value=default_org, label="当前组织", interactive=False)
                logout_btn = gr.Button("退出登录")
            with gr.Tabs():
                with gr.TabItem("战役"):
                    camp_out = gr.Markdown()
                    camp_replay = gr.Markdown()
                    with gr.Row():
                        camp_code = gr.Textbox(label="战役模板", value="fire_xinye")
                        camp_import_id = gr.Number(label="战役批次 ID", value=0, precision=0)
                    with gr.Row():
                        camp_import = gr.Button("导入战役", variant="primary")
                        camp_replay_btn = gr.Button("回放")
                        camp_delete = gr.Button("删除战役", variant="stop")
                        camp_refresh = gr.Button("刷新")
                with gr.TabItem("人员"):
                    per_out = gr.Markdown()
                    with gr.Row():
                        per_name = gr.Textbox(label="姓名", placeholder="诸葛亮")
                        per_role = gr.Textbox(label="角色", placeholder="丞相")
                        per_add = gr.Button("添加", variant="primary")
                    per_refresh = gr.Button("刷新")
                with gr.TabItem("资源"):
                    ast_out = gr.Markdown()
                    with gr.Row():
                        ast_name = gr.Textbox(label="名称", placeholder="连弩")
                        ast_type = gr.Dropdown(
                            choices=["physical", "financial", "human", "knowledge"],
                            value="physical",
                            label="类型",
                        )
                        ast_amount = gr.Number(label="数量", value=0)
                        ast_unit = gr.Textbox(label="单位", placeholder="架")
                        ast_add = gr.Button("添加", variant="primary")
                    ast_refresh = gr.Button("刷新")
                with gr.TabItem("交易"):
                    tx_out = gr.Markdown()
                    with gr.Row():
                        tx_amt = gr.Number(label="交易金额", value=0)
                        tx_cat = gr.Textbox(label="类别", placeholder="军费")
                        tx_desc = gr.Textbox(label="描述", placeholder="军费支出")
                    tx_parties = gr.Textbox(
                        label="参与方",
                        placeholder="曹操,付款方,-,5000,军费支出\n司马懿,收款方,+,5000,收到军费",
                        lines=4,
                    )
                    with gr.Row():
                        tx_add = gr.Button("记录交易", variant="primary")
                        tx_refresh = gr.Button("刷新")
                with gr.TabItem("财务摘要"):
                    sum_out = gr.Markdown()
                    sum_refresh = gr.Button("刷新")
                with gr.TabItem("AI 助手"):
                    chatbot = gr.Chatbot(height=400)
                    with gr.Row():
                        chat_input = gr.Textbox(
                            label="消息",
                            placeholder="帮我查一下蜀国的资产情况",
                            scale=4,
                        )
                        chat_send = gr.Button("发送", variant="primary", scale=1)

        with seller_panel:
            with gr.Tabs():
                with gr.TabItem("Seller 库存"):
                    seller_stock_out = gr.Markdown()
                    seller_stock_refresh = gr.Button("刷新")
                with gr.TabItem("Seller 流水"):
                    seller_mov_out = gr.Markdown()
                    with gr.Row():
                        seller_mov_op = gr.Dropdown(
                            choices=["", "purchase_in", "sales_out"],
                            value="",
                            label="操作类型",
                        )
                        seller_mov_from = gr.Textbox(label="开始日期", placeholder="YYYY-MM-DD")
                        seller_mov_to = gr.Textbox(label="结束日期", placeholder="YYYY-MM-DD")
                        seller_mov_limit = gr.Number(label="条数", value=50, precision=0)
                    seller_mov_refresh = gr.Button("刷新")
                with gr.TabItem("Seller 摘要"):
                    seller_sum_out = gr.Markdown()
                    seller_sum_refresh = gr.Button("刷新")
                with gr.TabItem("Seller AI"):
                    seller_chatbot = gr.Chatbot(height=400)
                    with gr.Row():
                        seller_chat_input = gr.Textbox(
                            label="消息",
                            placeholder="查询当前库存、低库存、销售收入",
                            scale=4,
                        )
                        seller_chat_send = gr.Button("发送", variant="primary", scale=1)

        session_state.change(
            restore_login_view_fn,
            [session_state],
            [auth_status, user_banner, current_org, landing_panel, auth_panel, workspace_panel, seller_panel, per_out, ast_out, tx_out, sum_out, camp_out, chatbot, chat_input, seller_stock_out, seller_mov_out, seller_sum_out, seller_chatbot, seller_chat_input],
            queue=False,
        )

        # ── Navigation ───────────────────────────────────────────────
        enter_login_btn.click(open_auth_fn, [], [auth_status, landing_panel, auth_panel, workspace_panel, seller_panel])
        enter_reg_btn.click(open_auth_fn, [], [auth_status, landing_panel, auth_panel, workspace_panel, seller_panel])
        back_btn.click(back_home_fn, [], [auth_status, landing_panel, auth_panel, workspace_panel, seller_panel])

        # top logout mirrors workspace logout
        logout_outputs = [session_state, auth_status, user_banner, current_org, landing_panel, auth_panel, workspace_panel, seller_panel, per_out, ast_out, tx_out, sum_out, camp_out, chatbot, chat_input, seller_stock_out, seller_mov_out, seller_sum_out, seller_chatbot, seller_chat_input]
        logout_btn_top.click(logout_fn, [], logout_outputs)
        logout_btn.click(logout_fn, [], logout_outputs)

        # ── Auth events ──────────────────────────────────────────────
        login_btn.click(
            login_fn,
            [login_input, login_pwd, session_state],
            [session_state, login_info, user_banner, current_org, landing_panel, auth_panel, workspace_panel, seller_panel, per_out, ast_out, tx_out, sum_out, camp_out, chatbot, chat_input, seller_stock_out, seller_mov_out, seller_sum_out, seller_chatbot, seller_chat_input],
        )
        reg_btn.click(
            register_fn,
            [reg_login, reg_pwd, reg_confirm, reg_name, reg_role],
            [reg_output, reg_pwd, reg_confirm],
        )

        # ── Workspace events ────────────────────────────────────────
        camp_refresh.click(load_campaigns, [session_state], camp_out, queue=False)
        camp_import.click(import_campaign_fn, [camp_code, session_state], [camp_out, camp_replay])
        camp_replay_btn.click(replay_campaign_fn, [camp_import_id, session_state], camp_replay)
        camp_delete.click(delete_campaign_fn, [camp_import_id, session_state], [camp_out, camp_replay])

        per_refresh.click(load_personnel, [current_org, session_state], per_out, queue=False)
        per_add.click(add_personnel_fn, [current_org, per_name, per_role, session_state], per_out).then(lambda: ("", ""), outputs=[per_name, per_role])

        ast_refresh.click(load_assets, [current_org, session_state], ast_out, queue=False)
        ast_add.click(add_asset_fn, [current_org, ast_name, ast_type, ast_amount, ast_unit, session_state], ast_out).then(lambda: ("", "physical", 0, ""), outputs=[ast_name, ast_type, ast_amount, ast_unit])


        tx_refresh.click(load_transactions, [current_org, session_state], tx_out, queue=False)
        tx_add.click(add_transaction_fn, [current_org, tx_amt, tx_cat, tx_desc, tx_parties, session_state], tx_out).then(lambda: (0, "", "", ""), outputs=[tx_amt, tx_cat, tx_desc, tx_parties])

        sum_refresh.click(load_summary, [current_org, session_state], sum_out, queue=False)

        chat_send.click(chat_fn, [chat_input, chatbot, current_org, session_state], [chatbot, chat_input])
        chat_input.submit(chat_fn, [chat_input, chatbot, current_org, session_state], [chatbot, chat_input])

        # ── Seller events ────────────────────────────────────────────
        seller_stock_refresh.click(load_seller_stock, [session_state], seller_stock_out, queue=False)
        seller_mov_refresh.click(
            load_seller_movements,
            [session_state, seller_mov_op, seller_mov_from, seller_mov_to, seller_mov_limit],
            seller_mov_out,
            queue=False,
        )
        seller_sum_refresh.click(load_seller_summary, [session_state], seller_sum_out, queue=False)
        seller_chat_send.click(
            seller_chat_fn,
            [seller_chat_input, seller_chatbot, session_state],
            [seller_chatbot, seller_chat_input],
        )
        seller_chat_input.submit(
            seller_chat_fn,
            [seller_chat_input, seller_chatbot, session_state],
            [seller_chatbot, seller_chat_input],
        )

    return demo


if __name__ == "__main__":
    demo = build_app()
    try:
        demo.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            theme=gr.themes.Soft(),
            debug=True,
            show_error=True,
            prevent_thread_lock=True,
        )
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        demo.close()
