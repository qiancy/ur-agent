"""
Uni-Resource Agent — Gradio frontend (v5.2).

Connects to FastAPI backend at http://localhost:8000.
"""
import time
import requests
import gradio as gr

from src.logging_config import setup_logging

logger = setup_logging("frontend")
API = "http://localhost:8000"

# ── Login state ──────────────────────────────────────────────────────────────

class LoginState:
    def __init__(self):
        self.access_token = None
        self.oid = None
        self.org_oid = None
        self.org_name = None
        self.person_pid = None
        self.person_name = None
        self.role = None
    
    def is_logged_in(self):
        return self.access_token is not None
    
    def set_from_response(self, resp):
        self.access_token = resp.get("access_token")
        person = resp.get("person", {})
        org = resp.get("organization", {})
        membership = resp.get("membership", {})
        self.oid = org.get("id")
        self.org_oid = org.get("oid")
        self.org_name = org.get("name")
        self.person_pid = person.get("pid")
        self.person_name = person.get("name")
        self.role = membership.get("role")
    
    def clear(self):
        self.access_token = None
        self.oid = None
        self.org_oid = None
        self.org_name = None
        self.person_pid = None
        self.person_name = None
        self.role = None

login_state = LoginState()

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


def _get(path, params=None, timeout=10):
    started = time.monotonic()
    logger.info("GET %s params=%s timeout=%s", path, params, timeout)
    headers = {}
    if login_state.access_token:
        headers["Authorization"] = f"Bearer {login_state.access_token}"
    try:
        r = requests.get(f"{API}{path}", params=params, timeout=timeout, headers=headers)
        _log_response("GET", path, started, r)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.exception("GET %s failed after %.2fs: %s", path, time.monotonic() - started, e)
        raise


def _post(path, body=None, timeout=10):
    started = time.monotonic()
    logger.info("POST %s body=%s timeout=%s", path, body, timeout)
    headers = {}
    if login_state.access_token:
        headers["Authorization"] = f"Bearer {login_state.access_token}"
    try:
        r = requests.post(f"{API}{path}", json=body, timeout=timeout, headers=headers)
        _log_response("POST", path, started, r)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.exception("POST %s failed after %.2fs: %s", path, time.monotonic() - started, e)
        raise


# ── Authentication ───────────────────────────────────────────────────────────

def login_fn(login, password):
    """Login user and update state."""
    if not login.strip() or not password.strip():
        return "请输入登录名和密码", login_state.org_name or "未登录"
    
    try:
        resp = _post("/auth/login", {"login": login.strip(), "password": password.strip()})
        login_state.set_from_response(resp)
        org_name = resp.get("organization", {}).get("name", "未知")
        person_name = resp.get("person", {}).get("name", "未知")
        return f"✅ 登录成功：{person_name} @ {org_name}", org_name
    except Exception as e:
        logger.exception("Login failed")
        return f"❌ 登录失败：{e}", login_state.org_name or "未登录"


def register_fn(login, password, name, role):
    """Register new user."""
    if not login.strip() or not password.strip() or not name.strip():
        return "请填写完整信息"
    
    try:
        resp = _post("/auth/register", {
            "login": login.strip(),
            "password": password.strip(),
            "name": name.strip(),
            "role": role.strip() or "member"
        })
        person_name = resp.get("person", {}).get("name", "未知")
        org_name = resp.get("organization", {}).get("name", "未知")
        return f"✅ 注册成功：{person_name} @ {org_name}"
    except Exception as e:
        logger.exception("Register failed")
        return f"❌ 注册失败：{e}"


def logout_fn():
    """Logout user and clear state."""
    login_state.clear()
    return "已退出登录", "未登录"


# ── org selector ─────────────────────────────────────────────────────────────

def _load_orgs():
    """动态加载组织列表"""
    try:
        orgs = _get("/organizations")
        return [(f"{o['name']} ({o['type']})", o["id"]) for o in orgs]
    except Exception:
        return []


def org_id(label: str) -> int:
    for name, oid in _load_orgs():
        if name == label:
            return oid
    return 1


# ── Tab 1: Personnel ────────────────────────────────────────────────────────

def load_personnel(org_label):
    oid = org_id(org_label)
    rows = _get("/person", {"oid": oid})
    if not rows:
        return "暂无人员数据"
    lines = []
    for p in rows:
        role = p.get("membership_role") or "-"
        lines.append(f"**{p['name']}** — {role}")
    return "\n\n".join(lines)


def add_personnel_fn(org_label, name, role):
    if not name.strip():
        return "请输入姓名"
    oid = org_id(org_label)
    person = _post("/person", {"name": name.strip()})
    if role.strip():
        _post("/organizations/members", {"pid": person["id"], "oid": oid, "role": role.strip()})
    return load_personnel(org_label)


# ── Tab 2: Assets ───────────────────────────────────────────────────────────

def load_assets(org_label):
    oid = org_id(org_label)
    rows = _get("/resource", {"oid": oid})
    if not rows:
        return "暂无资源数据"
    lines = []
    for a in rows:
        t = a.get("type") or "?"
        unit = a.get("unit") or ""
        amount = a.get("amount")
        content = a.get("content") or ""
        if amount is not None:
            extra = f"  {amount} {unit}" if unit else f"  {amount}"
        elif content:
            extra = f"  [{content[:30]}]"
        else:
            extra = ""
        lines.append(f"**{a['name']}** ({t}){extra}")
    return "\n\n".join(lines)


def add_asset_fn(org_label, name, atype, amount, unit):
    if not name.strip():
        return "请输入资源名称"
    body = {
        "oid": org_id(org_label),
        "name": name.strip(),
        "resource_type": atype.strip() or "physical",
    }
    if unit.strip():
        body["unit"] = unit.strip()
    if amount:
        body["amount"] = float(amount)
    _post("/resource", body)
    return load_assets(org_label)


# ── Tab 3: Party ────────────────────────────────────────────────────────────

def load_party(org_label):
    oid = org_id(org_label)
    rows = _get("/party", {"oid": oid})
    if not rows:
        return "暂无参与方"
    lines = []
    for p in rows:
        pname = p.get("person_name") or f"pid:{p['pid']}"
        role = p.get("role") or "-"
        desc = p.get("description") or ""
        fc = p.get("funds_change") or 0
        rc = p.get("reputation_change") or 0
        changes = []
        if fc != 0:
            changes.append(f"资金{'+'if fc>0 else ''}{fc}")
        if rc != 0:
            changes.append(f"声望{'+'if rc>0 else ''}{rc}")
        change_str = f" ({', '.join(changes)})" if changes else ""
        lines.append(f"**{pname}** [{role}] — {desc}{change_str}")
    return "\n\n".join(lines)


def add_party_fn(org_label, person_name, role, desc, funds_change, rep_change):
    if not person_name.strip():
        return "请输入人名"
    oid = org_id(org_label)
    people = _get("/person", {"oid": oid, "name": person_name.strip()})
    if not people:
        return f"找不到人员: {person_name}"
    pid = people[0]["id"]
    txns = _get("/transaction", {"oid": oid, "limit": 1})
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
    _post("/party", body)
    return load_party(org_label)


# ── Tab 4: Transactions ─────────────────────────────────────────────────────

def load_transactions(org_label):
    oid = org_id(org_label)
    rows = _get("/transaction", {"oid": oid, "limit": 50})
    if not rows:
        return "暂无交易记录"
    lines = []
    for t in rows:
        parties = t.get("parties") or []
        parts = []
        for p in parties:
            pname = p.get("person_name") or f"pid:{p['pid']}"
            role = p.get("role") or ""
            fc = p.get("funds_change") or 0
            parts.append(f"{pname}({role}, {'+'if fc>=0 else ''}{fc})")
        party_str = " ↔ ".join(parts) if parts else "无参与方"
        lines.append(
            f"**¥{t['amount']}** [{t['category']}] — {t.get('description') or ''}\n"
            f"  参与方: {party_str}"
        )
    return "\n\n".join(lines)


def add_transaction_fn(org_label, amount, category, desc):
    if not amount or float(amount) <= 0:
        return "请输入有效金额"
    body = {
        "amount": float(amount),
        "category": category.strip() or "其他",
        "description": desc.strip() or None,
    }
    _post("/transaction", body)
    return load_transactions(org_label)


# ── Tab 5: Summary ──────────────────────────────────────────────────────────

def load_summary(org_label):
    s = _get("/summary", {"oid": org_id(org_label)})
    return (
        f"**{org_label} 财务摘要**\n\n"
        f"资金: ¥{s['funds']:,.2f}\n"
        f"声望: {s['reputation']}\n"
        f"总流出: ¥{s['total_outflow']:,.2f}\n"
        f"交易笔数: {s['transaction_count']}"
    )


# ── Tab 6: Chat ─────────────────────────────────────────────────────────────

def chat_fn(message, history, org_label):
    if not message.strip():
        return history, ""
    oid = org_id(org_label)
    logger.info("CHAT input oid=%s org=%s message=%s", oid, org_label, message)
    try:
        resp = _post("/chat", {"message": message, "oid": oid}, timeout=40)
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
    org_labels = [name for name, _ in _load_orgs()] or ["蜀国 (company)"]

    with gr.Blocks(title="Uni-Resource Agent") as demo:
        gr.Markdown("# Uni-Resource Agent\n**万物皆资源 — One AI. All Your Worlds.**")

        # ── Login Section ────────────────────────────────────────────────
        with gr.Row():
            with gr.Column(scale=1):
                login_status = gr.Markdown("未登录")
                with gr.Row():
                    login_input = gr.Textbox(label="登录名", placeholder="caocao@wei.cn", scale=2)
                    login_pwd = gr.Textbox(label="密码", placeholder="密码", type="password", scale=1)
                    login_btn = gr.Button("登录", variant="primary")
                login_btn.click(
                    login_fn,
                    [login_input, login_pwd],
                    [login_status, gr.State("")]
                )
            
            with gr.Column(scale=1):
                with gr.Row():
                    reg_login = gr.Textbox(label="登录名", placeholder="newuser@wei.cn")
                    reg_pwd = gr.Textbox(label="密码", placeholder="密码", type="password")
                with gr.Row():
                    reg_name = gr.Textbox(label="姓名", placeholder="用户名")
                    reg_role = gr.Textbox(label="角色", placeholder="member")
                    reg_btn = gr.Button("注册", variant="secondary")
                reg_output = gr.Markdown()
                reg_btn.click(
                    register_fn,
                    [reg_login, reg_pwd, reg_name, reg_role],
                    reg_output
                )
        
        with gr.Row():
            org_selector = gr.Dropdown(
                choices=org_labels,
                value=org_labels[0],
                label="当前组织",
            )
            logout_btn = gr.Button("退出登录")
            logout_btn.click(logout_fn, [], [login_status, gr.State("")])

        with gr.Tabs():
            # ── Personnel ──────────────────────────────────────────────
            with gr.TabItem("人员"):
                per_out = gr.Markdown()
                with gr.Row():
                    per_name = gr.Textbox(label="姓名", placeholder="诸葛亮")
                    per_role = gr.Textbox(label="角色", placeholder="丞相")
                    per_add = gr.Button("添加", variant="primary")
                per_add.click(
                    add_personnel_fn,
                    [org_selector, per_name, per_role],
                    per_out,
                ).then(lambda: ("", ""), outputs=[per_name, per_role])
                demo.load(load_personnel, org_selector, per_out, queue=False)

            # ── Assets ─────────────────────────────────────────────────
            with gr.TabItem("资源"):
                ast_out = gr.Markdown()
                ast_refresh = gr.Button("刷新")
                with gr.Row():
                    ast_name = gr.Textbox(label="名称", placeholder="连弩")
                    ast_type = gr.Dropdown(
                        choices=["physical", "financial", "human", "knowledge"],
                        value="physical", label="类型")
                    ast_amount = gr.Number(label="数量", value=0)
                    ast_unit = gr.Textbox(label="单位", placeholder="架")
                    ast_add = gr.Button("添加", variant="primary")
                ast_refresh.click(load_assets, org_selector, ast_out, queue=False)
                ast_add.click(
                    add_asset_fn,
                    [org_selector, ast_name, ast_type, ast_amount, ast_unit],
                    ast_out,
                ).then(lambda: ("", "physical", 0, ""), outputs=[ast_name, ast_type, ast_amount, ast_unit])
                demo.load(load_assets, org_selector, ast_out, queue=False)

            # ── Party ──────────────────────────────────────────────────
            with gr.TabItem("参与方"):
                party_out = gr.Markdown()
                party_refresh = gr.Button("刷新")
                with gr.Row():
                    party_name = gr.Textbox(label="人名", placeholder="诸葛亮")
                    party_role = gr.Textbox(label="角色", placeholder="payer")
                    party_desc = gr.Textbox(label="描述", placeholder="付款方")
                with gr.Row():
                    party_fc = gr.Number(label="资金变更", value=0)
                    party_rc = gr.Number(label="声望变更", value=0)
                    party_add = gr.Button("添加", variant="primary")
                party_refresh.click(load_party, org_selector, party_out, queue=False)
                party_add.click(
                    add_party_fn,
                    [org_selector, party_name, party_role, party_desc, party_fc, party_rc],
                    party_out,
                ).then(lambda: ("", "", "", 0, 0), outputs=[party_name, party_role, party_desc, party_fc, party_rc])
                demo.load(load_party, org_selector, party_out, queue=False)

            # ── Transactions ───────────────────────────────────────────
            with gr.TabItem("交易"):
                tx_out = gr.Markdown()
                tx_refresh = gr.Button("刷新")
                with gr.Row():
                    tx_amt = gr.Number(label="金额", value=0)
                    tx_cat = gr.Textbox(label="类别", placeholder="军费")
                    tx_desc = gr.Textbox(label="描述", placeholder="军费支出")
                    tx_add = gr.Button("记录", variant="primary")
                tx_refresh.click(load_transactions, org_selector, tx_out, queue=False)
                tx_add.click(
                    add_transaction_fn,
                    [org_selector, tx_amt, tx_cat, tx_desc],
                    tx_out,
                ).then(lambda: (0, "", ""), outputs=[tx_amt, tx_cat, tx_desc])
                demo.load(load_transactions, org_selector, tx_out, queue=False)

            # ── Summary ────────────────────────────────────────────────
            with gr.TabItem("财务摘要"):
                sum_out = gr.Markdown()
                sum_refresh = gr.Button("刷新")
                sum_refresh.click(load_summary, org_selector, sum_out, queue=False)
                demo.load(load_summary, org_selector, sum_out, queue=False)

            # ── Chat ───────────────────────────────────────────────────
            with gr.TabItem("AI 助手"):
                chatbot = gr.Chatbot(height=400)
                with gr.Row():
                    chat_input = gr.Textbox(
                        label="消息",
                        placeholder="帮我查一下蜀国的资产情况",
                        scale=4,
                    )
                    chat_send = gr.Button("发送", variant="primary", scale=1)
                chat_send.click(
                    chat_fn,
                    [chat_input, chatbot, org_selector],
                    [chatbot, chat_input],
                )
                chat_input.submit(
                    chat_fn,
                    [chat_input, chatbot, org_selector],
                    [chatbot, chat_input],
                )

    return demo


if __name__ == "__main__":
    demo = build_app()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        theme=gr.themes.Soft(),
        debug=True,
        show_error=True,
    )
