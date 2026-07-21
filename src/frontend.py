"""
Uni-Resource Agent — Gradio frontend.

Connects to FastAPI backend at http://localhost:8000.
"""
import requests
import gradio as gr

API = "http://localhost:8000"

# ── helpers ──────────────────────────────────────────────────────────────────

def _get(path, params=None):
    r = requests.get(f"{API}{path}", params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def _post(path, body=None):
    r = requests.post(f"{API}{path}", json=body, timeout=10)
    r.raise_for_status()
    return r.json()


# ── org selector ─────────────────────────────────────────────────────────────

ORG_OPTIONS = [
    ("蜀国 (公司)", 1),
    ("魏国 (公司)", 2),
    ("吴国 (公司)", 3),
    ("刘备 (个人)", 4),
    ("诸葛亮 (个人)", 5),
]


def org_id(label: str) -> int:
    for name, oid in ORG_OPTIONS:
        if name == label:
            return oid
    return 1


# ── Tab 1: Personnel ────────────────────────────────────────────────────────

def load_personnel(org_label):
    rows = _get("/personnel", {"org_id": org_id(org_label)})
    if not rows:
        return "暂无人员数据"
    lines = []
    for p in rows:
        lines.append(f"**{p['name']}** — {p['role'] or '-'}")
    return "\n\n".join(lines)


def add_personnel_fn(org_label, name, role):
    if not name.strip():
        return "请输入姓名"
    _post("/personnel", {
        "org_id": org_id(org_label),
        "name": name.strip(),
        "role": role.strip() or None,
    })
    return load_personnel(org_label)


# ── Tab 2: Assets ───────────────────────────────────────────────────────────

def load_assets(org_label, warehouse_filter):
    params = {"org_id": org_id(org_label)}
    if warehouse_filter.strip():
        params["warehouse"] = warehouse_filter.strip()
    rows = _get("/assets", params)
    if not rows:
        return "暂无资产数据"
    lines = []
    for a in rows:
        qty = a.get("quantity")
        wh = a.get("warehouse") or ""
        content = a.get("content") or ""
        extra = f"  x{qty} @{wh}" if qty is not None else f"  [{content}]"
        lines.append(f"**{a['name']}** ({a['type'] or '?'}){extra}")
    return "\n\n".join(lines)


def add_asset_fn(org_label, name, atype, qty, warehouse):
    if not name.strip():
        return "请输入资产名称"
    body = {
        "org_id": org_id(org_label),
        "name": name.strip(),
        "asset_type": atype.strip() or None,
        "quantity": int(qty) if qty else 0,
        "warehouse": warehouse.strip() or None,
    }
    _post("/assets", body)
    return load_assets(org_label, "")


# ── Tab 3: Party ────────────────────────────────────────────────────────────

def load_party(org_label):
    rows = _get("/party", {"org_id": org_id(org_label)})
    if not rows:
        return "暂无参与方"
    lines = []
    for p in rows:
        lines.append(f"**{p['name']}** [{p['role']}] — {p['description'] or ''}")
    return "\n\n".join(lines)


def add_party_fn(org_label, name, role, desc):
    if not name.strip():
        return "请输入参与方名称"
    _post("/party", {
        "org_id": org_id(org_label),
        "name": name.strip(),
        "role": role.strip() or None,
        "description": desc.strip() or None,
    })
    return load_party(org_label)


# ── Tab 4: Transactions ─────────────────────────────────────────────────────

def load_transactions(org_label):
    rows = _get("/transactions", {"org_id": org_id(org_label), "limit": 50})
    if not rows:
        return "暂无交易记录"
    lines = []
    for t in rows:
        fn = t.get("from_party_name") or f"#{t['from_party_id']}"
        fr = t.get("from_party_role") or ""
        tn = t.get("to_party_name") or f"#{t['to_party_id']}"
        tr = t.get("to_party_role") or ""
        lines.append(
            f"**{fn}**({fr}) → **{tn}**({tr})\n"
            f"  ¥{t['amount']}  [{t['category']}]  {t['description'] or ''}"
        )
    return "\n\n".join(lines)


def add_transaction_fn(org_label, from_name, to_name, amount, category, desc):
    if not from_name.strip() or not to_name.strip():
        return "请输入交易双方名称"
    from_parties = _get("/party", {"org_id": org_id(org_label), "name": from_name.strip()})
    to_parties = _get("/party", {"org_id": org_id(org_label), "name": to_name.strip()})
    if not from_parties:
        return f"找不到参与方: {from_name}"
    if not to_parties:
        return f"找不到参与方: {to_name}"
    _post("/transactions", {
        "from_party_id": from_parties[0]["id"],
        "to_party_id": to_parties[0]["id"],
        "amount": float(amount),
        "category": category.strip() or "其他",
        "description": desc.strip() or None,
    })
    return load_transactions(org_label)


# ── Tab 5: Summary ──────────────────────────────────────────────────────────

def load_summary(org_label):
    s = _get("/summary", {"org_id": org_id(org_label)})
    return (
        f"**{org_label} 财务摘要**\n\n"
        f"总流出: ¥{s['total_outflow']:,.2f}\n"
        f"总流入: ¥{s['total_inflow']:,.2f}\n"
        f"净余额: ¥{s['balance']:,.2f}\n"
        f"交易笔数: {s['transaction_count']}"
    )


# ── Tab 6: Chat ─────────────────────────────────────────────────────────────

def chat_fn(message, history, org_label):
    if not message.strip():
        return history, ""
    try:
        resp = _post("/chat", {"message": message, "org_id": org_id(org_label)})
        reply = resp.get("response", "No response")
    except Exception as e:
        reply = f"Error: {e}"
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": reply})
    return history, ""


# ── Build UI ─────────────────────────────────────────────────────────────────

def build_app():
    org_labels = [name for name, _ in ORG_OPTIONS]

    with gr.Blocks(title="Uni-Resource Agent") as demo:
        gr.Markdown("# Uni-Resource Agent\n**万物皆资源 — One AI. All Your Worlds.**")

        with gr.Row():
            org_selector = gr.Dropdown(
                choices=org_labels,
                value=org_labels[0],
                label="当前组织",
            )

        with gr.Tabs():
            # ── Personnel ──────────────────────────────────────────────
            with gr.TabItem("人员"):
                per_out = gr.Markdown()
                with gr.Row():
                    per_name = gr.Textbox(label="姓名", placeholder="诸葛亮")
                    per_role = gr.Textbox(label="角色", placeholder="丞相")
                    per_add = gr.Button("添加", variant="primary")
                per_add.click(load_personnel, org_selector, per_out, queue=False)
                per_add.click(
                    add_personnel_fn,
                    [org_selector, per_name, per_role],
                    per_out,
                ).then(lambda: ("", ""), outputs=[per_name, per_role])
                demo.load(load_personnel, org_selector, per_out, queue=False)

            # ── Assets ─────────────────────────────────────────────────
            with gr.TabItem("资产"):
                ast_out = gr.Markdown()
                ast_wh_filter = gr.Textbox(label="仓库筛选", placeholder="军械库（可选）")
                ast_refresh = gr.Button("刷新")
                with gr.Row():
                    ast_name = gr.Textbox(label="名称", placeholder="连弩")
                    ast_type = gr.Textbox(label="类型", placeholder="兵器")
                    ast_qty = gr.Number(label="数量", value=0)
                    ast_warehouse = gr.Textbox(label="仓库", placeholder="军械库")
                    ast_add = gr.Button("添加", variant="primary")
                ast_refresh.click(load_assets, [org_selector, ast_wh_filter], ast_out, queue=False)
                ast_add.click(
                    add_asset_fn,
                    [org_selector, ast_name, ast_type, ast_qty, ast_warehouse],
                    ast_out,
                ).then(lambda: ("", "", 0, ""), outputs=[ast_name, ast_type, ast_qty, ast_warehouse])
                demo.load(load_assets, [org_selector, gr.State("")], ast_out, queue=False)

            # ── Party ──────────────────────────────────────────────────
            with gr.TabItem("参与方"):
                party_out = gr.Markdown()
                party_refresh = gr.Button("刷新")
                with gr.Row():
                    party_name = gr.Textbox(label="名称", placeholder="蜀汉集团")
                    party_role = gr.Textbox(label="角色", placeholder="买家")
                    party_desc = gr.Textbox(label="描述", placeholder="蜀汉政权")
                    party_add = gr.Button("添加", variant="primary")
                party_refresh.click(load_party, org_selector, party_out, queue=False)
                party_add.click(
                    add_party_fn,
                    [org_selector, party_name, party_role, party_desc],
                    party_out,
                ).then(lambda: ("", "", ""), outputs=[party_name, party_role, party_desc])
                demo.load(load_party, org_selector, party_out, queue=False)

            # ── Transactions ───────────────────────────────────────────
            with gr.TabItem("交易"):
                tx_out = gr.Markdown()
                tx_refresh = gr.Button("刷新")
                with gr.Row():
                    tx_from = gr.Textbox(label="付款方", placeholder="蜀汉集团")
                    tx_to = gr.Textbox(label="收款方", placeholder="诸葛亮家")
                    tx_amt = gr.Number(label="金额", value=0)
                    tx_cat = gr.Textbox(label="类别", placeholder="军费")
                    tx_desc = gr.Textbox(label="描述", placeholder="军费支出")
                    tx_add = gr.Button("记录", variant="primary")
                tx_refresh.click(load_transactions, org_selector, tx_out, queue=False)
                tx_add.click(
                    add_transaction_fn,
                    [org_selector, tx_from, tx_to, tx_amt, tx_cat, tx_desc],
                    tx_out,
                ).then(lambda: ("", "", 0, "", ""), outputs=[tx_from, tx_to, tx_amt, tx_cat, tx_desc])
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
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False, theme=gr.themes.Soft())
