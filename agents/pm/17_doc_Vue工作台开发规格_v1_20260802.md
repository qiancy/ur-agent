# FE-07 Vue 工作台开发规格（Style A）

> **状态**：Approved（项目经理 6 条修正条件已吸收）
> **日期**：2026-08-02
> **范围**：`web/` 前端，后端零改动，Gradio 不删除

---

## 1. 目标

在 FE-06 基础上，将 `web/` 从「登录 + 摘要」扩展为完整的 **Style A 经营工作台**（主风格锁定 `docs/frontend-demos/be05-style-a-ops.html`）。

功能范围：stock / inventory-movements / purchase-in / sales-out / seller chat。

**参考设计**：`docs/frontend-demos/be05-style-a-ops.html`
- 主风格 = Style A（Ops Desk）
- 吸收 Style B 的低库存风险优先展示
- 吸收 Style C 的快速入库/出库按钮

---

## 2. 已确认决策（用户 + PM）

| 决策 | 结论 |
| :--- | :--- |
| 导航结构 | 侧边栏多视图：经营工作台 / 库存 / 库存流水 / 经营摘要 / Seller AI |
| 入库/出库 | 弹窗表单（EntryFormModal） |
| Seller AI | 工作台右侧内嵌 ChatPanel + 侧边栏独立 ChatView 页 |
| 路由 | **无 vue-router**，App.vue 内 `currentView` 状态切换。刷新默认回工作台，不承诺独立 URL；赛后产品化再加 vue-router |
| 主风格 | 锁定 Style A，不做三套风格混搭 |

---

## 3. API 层类型契约（seller.ts 补全）

> 所有字段必须是业务字段，**不得出现** `id` / `*_id` / `pid` / `oid`。

```ts
interface SellerStockRow {
  product_uid: string
  warehouse_code: string
  location_path: string
  quantity: number
  unit: string
}

interface SellerMovement {
  movement_uid: string
  operation_type: 'purchase_in' | 'sales_out'
  product_uid: string
  warehouse_code: string
  location_path: string
  quantity_delta: number
  new_quantity: number
  unit: string
  total_amount: number
  counterparty_name: string
  created_at: string
}

interface SellerPurchaseInRequest {
  product_uid: string
  warehouse_code: string
  location_path: string
  quantity: number       // > 0
  unit: string
  total_amount: number   // >= 0
  counterparty_name: string
}

interface SellerSalesOutRequest = SellerPurchaseInRequest  // 同字段，语义不同

interface SellerChatResponse {
  response: string
  ouid: string
}
```

**新增 API 函数**（均带 Bearer；沿用 `request` 封装）：
- `sellerStock(productUid?: string): Promise<SellerStockRow[]>`
- `sellerInventoryMovements(params?): Promise<SellerMovement[]>`
  - 参数：`productUid?` / `operationType?` / `dateFrom?` / `dateTo?` / `limit?`
- `sellerPurchaseIn(req: SellerPurchaseInRequest): Promise<{status, new_quantity, ...}>`
- `sellerSalesOut(req: SellerSalesOutRequest): Promise<{status, new_quantity, ...}>`
- `sellerChat(message: string): Promise<SellerChatResponse>`

---

## 4. 组件结构

```
web/src/
├── api/
│   ├── client.ts          （FE-06 已有，零改动）
│   ├── seller.ts          （补类型 + 新增 5 函数）
├── components/
│   ├── SidebarNav.vue     侧边栏（品牌 + 5 导航 + 店铺信息 + 退出）
│   ├── MetricsRow.vue     5 指标卡（销售收入/采购支出/净现金流/库存估值/低库存数）
│   ├── StockTable.vue     库存明细表（低库存 tag：ok/warn/danger）
│   ├── MovementTable.vue  库存流水表（operation_type 标签 + 方向色）
│   ├── LowStockPanel.vue  低库存处理列表（风险优先）
│   ├── ChatPanel.vue      聊天面板（user/ai 气泡，只读查询提示，防重复发送）
│   └── EntryFormModal.vue 入库/出库弹窗
└── views/
    ├── WorkbenchView.vue  经营工作台（MetricsRow + StockTable + LowStockPanel + ChatPanel）
    ├── StockView.vue      库存页
    ├── MovementsView.vue  流水页（筛选）
    ├── SummaryView.vue    摘要页（FE-06 升级）
    └── ChatView.vue       Seller AI 独立页
```

**App.vue**：登录后进入工作台框架；`currentView` 切换；顶部 `出库/入库` 按钮开 EntryFormModal。

---

## 5. 数据流与错误处理

- 所有写操作只提交业务字段，不传/不展示 DB ID。
- 401 统一清 token 回登录（`client.ts` 已实现，视图 emit `logged-out`）。
- EntryFormModal 提交成功 → 关闭 + 刷新 stock + movements + summary（emit 刷新事件，由父级重新拉取）。
- 失败展示后端错误文本，不吞错误。
- ChatPanel 只调 `/seller/chat`；写入意图由后端 `_READ_ONLY_NOTICE` 兜底（前端不改写，直接展示后端 response）。

---

## 6. 测试策略（PM 条件 5）

避免低价值快照测试，重点覆盖：

| 场景 | 断言 |
| :--- | :--- |
| API 请求 | 请求 URL/body 不含 DB ID 字段名 |
| 401 | 清 token 并 emit logged-out |
| 入库/出库 | 提交只含业务字段；loading 防重复点击 |
| 提交成功 | 触发刷新（父级重新拉取 stock/movements/summary） |
| Seller AI | 只调 `/seller/chat` |
| 渲染 | 页面不出现 DB ID 字段名（`id`/`*_id` 字样） |

每个 API 函数 1 个单元测试（fetch mock）；每个视图/组件 mount 测试。

---

## 7. 验收（PM 条件 6）

1. `npm test` 全绿
2. `npm run build`（vue-tsc 类型检查 + vite 构建）通过
3. **视觉检查（必须）**：启动 dev server，提供 URL；桌面宽度 1280 / 1440 截图验收（Playwright 或人工）
4. 安全扫描：dist 产物无密钥/无 DB ID 字段
5. 后端零改动；Gradio 未删除

---

## 8. 红线（不变量）

- 后端零改动
- 不删除 Gradio（`src/app.py` 保留为内部调试入口）
- 不引入真实密钥
- 不提交 `node_modules`、`dist`、`tsconfig.tsbuildinfo`（已在 `web/.gitignore`）

---

## 9. 实施顺序

1. API 类型补全 + 测试
2. Layout + SidebarNav
3. MetricsRow / StockTable / MovementTable
4. EntryFormModal 入库/出库
5. ChatPanel + ChatView
6. 视图整合 + 视觉打磨 + 安全扫描 + build + commit

---

## 10. 真后端 spike 验证

临时 ecommerce 店铺（`fe06_spike_*` 模式）：
1. `/auth/seller-login` 登录 → 存 JWT
2. Bearer 调 `/seller/stock` / `/seller/inventory-movements` / `/seller/summary`
3. `/seller/purchase-in` 入库一笔 + `/seller/sales-out` 出库一笔
4. 确认 movements / summary 反映变化（数量、金额）
5. 清理：临时店铺数据保留可接受（测试用），spike 测试文件删除
