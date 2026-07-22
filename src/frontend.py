"""
Uni-Resource Agent — Gradio frontend (v5.2).

Connects to FastAPI backend at http://localhost:8000.
"""
import time
from typing import List

import requests
import gradio as gr

from src.logging_config import setup_logging

logger = setup_logging("frontend")
API = "http://localhost:8000"


# ── Login state ──────────────────────────────────────────────────────────────

def _empty_login_state():
    return {
        "access_token": None,
        "org_oid": None,
        "org_name": None,
        "org_type": None,
        "pid": None,
        "person_name": None,
        "role": None,
    }


def _login_state_from_response(resp):
    person = resp.get("person", {})
    org = resp.get("organization", {})
    membership = resp.get("membership", {})
    return {
        "access_token": resp.get("access_token"),
        "org_oid": org.get("oid"),
        "org_name": org.get("name"),
        "org_type": org.get("type"),
        "pid": person.get("pid"),
        "person_name": person.get("name"),
        "role": membership.get("role"),
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


def _label_to_oid(label: str, state=None) -> str:
    for org in _load_orgs():
        if label == f"{org['name']} ({org['type']})":
            return org["oid"]
    if (state or {}).get("org_oid"):
        return state["org_oid"]
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
        return f"{state.get('person_name')} @ {state.get('org_name')} ({state.get('role') or 'member'})"
    return "未登录"


def _show_home():
    return (
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(visible=False),
    )


def _show_auth():
    return (
        gr.update(visible=False),
        gr.update(visible=True),
        gr.update(visible=False),
    )


def _show_workspace():
    return (
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=True),
    )


def _blank_workspace():
    return "", "", "", "", "", [], ""


def _workspace_payload(org_label: str, state):
    return (
        load_personnel(org_label, state),
        load_assets(org_label, state),
        load_party(org_label, state),
        load_transactions(org_label, state),
        load_summary(org_label, state),
        [],
        "",
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
        resp = _post("/auth/login", {"login": login.strip(), "password": password.strip()}, state=state)
        new_state = _login_state_from_response(resp)
        org_label = _current_org_label(new_state)
        per, ast, party, tx, summary, chatbot, chat_input = _workspace_payload(org_label, new_state)
        return (
            new_state,
            f"登录成功：{new_state.get('person_name')} @ {new_state.get('org_name')}",
            _auth_header(new_state),
            gr.update(value=org_label, choices=[org_label], interactive=False),
            *_show_workspace(),
            per,
            ast,
            party,
            tx,
            summary,
            chatbot,
            chat_input,
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


# ── Tab 1: Personnel ────────────────────────────────────────────────────────

def load_personnel(org_label, state=None):
    oid = _label_to_oid(org_label, state)
    rows = _get("/person", {"oid": oid}, state=state)
    if not rows:
        return "暂无人员数据"
    lines = []
    for person in rows:
        role = person.get("membership_role") or "-"
        pid = person.get("pid") or "-"
        lines.append(f"**{person['name']}** — {role} (`{pid}`)")
    return "\n\n".join(lines)


def add_personnel_fn(org_label, name, role, state):
    if not name.strip():
        return "请输入姓名"
    oid = _label_to_oid(org_label, state)
    person = _post("/person", {"name": name.strip()}, state=state)
    if role.strip():
        _post("/organizations/members", {"pid": person["pid"], "oid": oid, "role": role.strip()}, state=state)
    return load_personnel(org_label, state)


# ── Tab 2: Assets ───────────────────────────────────────────────────────────

def load_assets(org_label, state=None):
    oid = _label_to_oid(org_label, state)
    rows = _get("/resource", {"oid": oid}, state=state)
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
        "oid": _label_to_oid(org_label, state),
        "name": name.strip(),
        "resource_type": atype.strip() or "physical",
    }
    if unit.strip():
        body["unit"] = unit.strip()
    if amount:
        body["amount"] = float(amount)
    _post("/resource", body, params={"oid": body["oid"]}, state=state)
    return load_assets(org_label, state)


# ── Tab 3: Party ────────────────────────────────────────────────────────────

def load_party(org_label, state=None):
    oid = _label_to_oid(org_label, state)
    rows = _get("/party", {"oid": oid}, state=state)
    if not rows:
        return "暂无参与方"
    lines = []
    for party in rows:
        pname = party.get("person_name") or f"person_id:{party.get('person_id')}"
        role = party.get("role") or "-"
        desc = party.get("description") or ""
        fc = party.get("funds_change") or 0
        rc = party.get("reputation_change") or 0
        changes = []
        if fc != 0:
            changes.append(f"资金{'+'if fc>0 else ''}{fc}")
        if rc != 0:
            changes.append(f"声望{'+'if rc>0 else ''}{rc}")
        change_str = f" ({', '.join(changes)})" if changes else ""
        lines.append(f"**{pname}** [{role}] — {desc}{change_str}")
    return "\n\n".join(lines)


def add_party_fn(org_label, person_name, role, desc, funds_change, rep_change, state):
    if not person_name.strip():
        return "请输入人名"
    oid = _label_to_oid(org_label, state)
    people = _get("/person", {"oid": oid, "name": person_name.strip()}, state=state)
    if not people:
        return f"找不到人员: {person_name}"
    pid = people[0]["pid"]
    txns = _get("/transaction", {"oid": oid, "limit": 1}, state=state)
    if not txns:
        return "请先创建交易记录"
    txn_id = txns[0]["id"]
    body = {
        "pid": pid,
        "oid": oid,
        "transaction_id": txn_id,
        "role": role.strip() or "participant",
        "description": desc.strip() or None,
        "funds_change": float(funds_change) if funds_change else 0,
        "reputation_change": int(rep_change) if rep_change else 0,
    }
    _post("/party", body, params={"oid": oid}, state=state)
    return load_party(org_label, state)


# ── Tab 4: Transactions ─────────────────────────────────────────────────────

def load_transactions(org_label, state=None):
    oid = _label_to_oid(org_label, state)
    rows = _get("/transaction", {"oid": oid, "limit": 50}, state=state)
    if not rows:
        return "暂无交易记录"
    lines = []
    for txn in rows:
        parties = txn.get("parties") or []
        parts = []
        for party in parties:
            pname = party.get("person_name") or f"person_id:{party.get('person_id')}"
            role = party.get("role") or ""
            fc = party.get("funds_change") or 0
            parts.append(f"{pname}({role}, {'+'if fc>=0 else ''}{fc})")
        party_str = " ↔ ".join(parts) if parts else "无参与方"
        lines.append(
            f"**¥{txn['amount']}** [{txn['category']}] — {txn.get('description') or ''}\n"
            f"  参与方: {party_str}"
        )
    return "\n\n".join(lines)


def add_transaction_fn(org_label, amount, category, desc, state):
    if not amount or float(amount) <= 0:
        return "请输入有效金额"
    body = {
        "amount": float(amount),
        "category": category.strip() or "其他",
        "description": desc.strip() or None,
    }
    _post("/transaction", body, params={"oid": _label_to_oid(org_label, state)}, state=state)
    return load_transactions(org_label, state)


# ── Tab 5: Summary ──────────────────────────────────────────────────────────

def load_summary(org_label, state=None):
    s = _get("/summary", {"oid": _label_to_oid(org_label, state)}, state=state)
    return (
        f"**{org_label} 财务摘要**\n\n"
        f"资金: ¥{s['funds']:,.2f}\n"
        f"声望: {s['reputation']}\n"
        f"总流出: ¥{s['total_outflow']:,.2f}\n"
        f"交易笔数: {s['transaction_count']}"
    )


# ── Tab 6: Chat ─────────────────────────────────────────────────────────────

def chat_fn(message, history, org_label, state):
    if not message.strip():
        return history, ""
    oid = _label_to_oid(org_label, state)
    logger.info("CHAT input oid=%s org=%s message=%s", oid, org_label, message)
    try:
        resp = _post("/chat", {"message": message}, params={"oid": oid}, timeout=40, state=state)
        reply = resp.get("response", "No response")
        logger.info("CHAT output oid=%s response=%s", oid, reply[:2000])
    except Exception as e:
        logger.exception("CHAT failed oid=%s message=%s", oid, message)
        reply = f"Error: {e}"
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": reply})
    return history, ""


# ── Build UI ─────────────────────────────────────────────────────────────────

def build_app():
    org_labels = _org_labels()
    default_org = org_labels[0]

    with gr.Blocks(title="Uni-Resource Agent") as demo:
        session_state = gr.State(_empty_login_state())
        landing_panel = gr.Group(visible=True)
        auth_panel = gr.Group(visible=False)
        workspace_panel = gr.Group(visible=False)

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
                with gr.TabItem("参与方"):
                    party_out = gr.Markdown()
                    with gr.Row():
                        party_name = gr.Textbox(label="人名", placeholder="诸葛亮")
                        party_role = gr.Textbox(label="角色", placeholder="payer")
                        party_desc = gr.Textbox(label="描述", placeholder="付款方")
                    with gr.Row():
                        party_fc = gr.Number(label="资金变更", value=0)
                        party_rc = gr.Number(label="声望变更", value=0)
                        party_add = gr.Button("添加", variant="primary")
                    party_refresh = gr.Button("刷新")
                with gr.TabItem("交易"):
                    tx_out = gr.Markdown()
                    with gr.Row():
                        tx_amt = gr.Number(label="金额", value=0)
                        tx_cat = gr.Textbox(label="类别", placeholder="军费")
                        tx_desc = gr.Textbox(label="描述", placeholder="军费支出")
                        tx_add = gr.Button("记录", variant="primary")
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

        # ── Navigation ───────────────────────────────────────────────
        enter_login_btn.click(open_auth_fn, [], [auth_status, landing_panel, auth_panel, workspace_panel])
        enter_reg_btn.click(open_auth_fn, [], [auth_status, landing_panel, auth_panel, workspace_panel])
        back_btn.click(back_home_fn, [], [auth_status, landing_panel, auth_panel, workspace_panel])

        # top logout mirrors workspace logout
        logout_outputs = [session_state, auth_status, user_banner, current_org, landing_panel, auth_panel, workspace_panel, per_out, ast_out, party_out, tx_out, sum_out, chatbot, chat_input]
        logout_btn_top.click(logout_fn, [], logout_outputs)
        logout_btn.click(logout_fn, [], logout_outputs)

        # ── Auth events ──────────────────────────────────────────────
        login_btn.click(
            login_fn,
            [login_input, login_pwd, session_state],
            [session_state, login_info, user_banner, current_org, landing_panel, auth_panel, workspace_panel, per_out, ast_out, party_out, tx_out, sum_out, chatbot, chat_input],
        )
        reg_btn.click(
            register_fn,
            [reg_login, reg_pwd, reg_confirm, reg_name, reg_role],
            [reg_output, reg_pwd, reg_confirm],
        )

        # ── Workspace events ────────────────────────────────────────
        per_refresh.click(load_personnel, [current_org, session_state], per_out, queue=False)
        per_add.click(add_personnel_fn, [current_org, per_name, per_role, session_state], per_out).then(lambda: ("", ""), outputs=[per_name, per_role])

        ast_refresh.click(load_assets, [current_org, session_state], ast_out, queue=False)
        ast_add.click(add_asset_fn, [current_org, ast_name, ast_type, ast_amount, ast_unit, session_state], ast_out).then(lambda: ("", "physical", 0, ""), outputs=[ast_name, ast_type, ast_amount, ast_unit])

        party_refresh.click(load_party, [current_org, session_state], party_out, queue=False)
        party_add.click(add_party_fn, [current_org, party_name, party_role, party_desc, party_fc, party_rc, session_state], party_out).then(lambda: ("", "", "", 0, 0), outputs=[party_name, party_role, party_desc, party_fc, party_rc])

        tx_refresh.click(load_transactions, [current_org, session_state], tx_out, queue=False)
        tx_add.click(add_transaction_fn, [current_org, tx_amt, tx_cat, tx_desc, session_state], tx_out).then(lambda: (0, "", ""), outputs=[tx_amt, tx_cat, tx_desc])

        sum_refresh.click(load_summary, [current_org, session_state], sum_out, queue=False)

        chat_send.click(chat_fn, [chat_input, chatbot, current_org, session_state], [chatbot, chat_input])
        chat_input.submit(chat_fn, [chat_input, chatbot, current_org, session_state], [chatbot, chat_input])

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
