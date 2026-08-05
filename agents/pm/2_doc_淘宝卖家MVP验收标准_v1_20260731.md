# 淘宝卖家 MVP 验收标准

> 角色：项目经理  
> 日期：2026-07-29  
> 对应计划：`agents/pm/淘宝卖家MVP开发计划.md`  
> 对应用例：`agents/pm/uc003_淘宝卖家仓库用例.md`

## 1. 验收结论规则

验收结果只有三种：

| 结论 | 标准 |
|------|------|
| 通过 | P0 全部通过，无 High 风险 |
| 有条件通过 | P0 只剩非安全、非数据一致性的 Medium/Low 问题，并有明确修复计划 |
| 不通过 | 任一 P0 失败，或存在权限越权、库存负数、库存交易不一致 |

## 2. P0 功能验收

| 编号 | 验收项 | 标准 | 证据 |
|------|------|------|------|
| AC-P0-01 | 创建店铺空间 | 可创建 `organization(type=ecommerce)`，`ouid` 为英文安全字符串 | API 响应和 DB 记录 |
| AC-P0-02 | 创建商品 | 当前店铺可创建 physical 商品，包含名称、单位、规格说明 | `/seller/products` 响应 |
| AC-P0-03 | 创建仓库 | 当前店铺可创建仓库和库位库存 | `/seller/warehouses` 响应 |
| AC-P0-04 | 进货入库 | 入库后指定库位库存增加，采购支出记录成功 | 库存查询 + 交易查询 |
| AC-P0-05 | 销售出库 | 出库后指定库位库存减少，销售收入记录成功 | 库存查询 + 交易查询 |
| AC-P0-06 | 库存不足保护 | 库存不足时请求失败，库存和资金均不变化 | HTTP 400/409 + 前后数据对比 |
| AC-P0-07 | 查询库存 | 可按商品名查询总库存和库位分布 | `/seller/stock` 响应 |
| AC-P0-08 | 经营摘要 | 可查询销售收入、采购支出、交易数、库存概览 | `/seller/summary` 响应 |
| AC-P0-09 | AI 入库 | 自然语言入库命令能增加库存并记录采购支出 | Chat 响应 + 库存/交易核验 |
| AC-P0-10 | AI 出库 | 自然语言出库命令能扣减库存并记录销售收入 | Chat 响应 + 库存/交易核验 |
| AC-P0-11 | AI 查库存 | 自然语言库存查询返回正确数量和库位 | Chat 响应 + API 核验 |

## 3. P0 安全和隔离验收

| 编号 | 验收项 | 标准 |
|------|------|------|
| AC-S-01 | JWT 绑定 | Seller 写接口必须要求 Bearer JWT |
| AC-S-02 | 禁止前端授权 | Seller API 不信任前端提交的 `ouid`、`organization_id`、`person_id` |
| AC-S-03 | 资源归属校验 | `resource_id` 必须属于当前 JWT `ouid` |
| AC-S-04 | 仓库归属校验 | `warehouse_id` 或库位必须属于当前 JWT `ouid` |
| AC-S-05 | 交易归属校验 | `transaction_id` 不能跨组织挂接 party |
| AC-S-06 | 店铺隔离 | 店铺 A 用户不能读写店铺 B 的商品、库存、交易、摘要 |
| AC-S-07 | JWT payload | JWT 不包含 `person_id`、`organization_id` 等数据库数字身份字段 |
| AC-S-08 | AI 上下文 | AI 工具不能使用默认 `ouid` 跨店铺查询或操作 |

任一安全隔离项失败，本轮验收不通过。

## 4. P0 数据一致性验收

| 编号 | 验收项 | 标准 |
|------|------|------|
| AC-D-01 | 原子提交 | 入库/出库的库存变化和交易记录在同一数据库事务中提交 |
| AC-D-02 | 库存非负 | 任意商品任意库位库存不得小于 0 |
| AC-D-03 | 总数一致 | 商品总库存等于各实际库位库存之和，或有明确且一致的 `total` 维护规则 |
| AC-D-04 | 失败回滚 | 交易创建失败时库存不变，库存更新失败时交易不产生 |
| AC-D-05 | 资金方向 | 采购为支出，销售为收入，摘要口径与交易流水一致 |
| AC-D-06 | 审计可追溯 | 每次入库/出库能追溯到操作者、商品、数量、库位、金额和时间 |

## 5. 自动化测试验收

必须新增并通过：

```text
agents/tdd/test_seller_inventory_api.py
```

最低测试用例：

1. `test_create_ecommerce_org_and_login`
2. `test_create_product_in_current_shop`
3. `test_create_warehouse_in_current_shop`
4. `test_purchase_in_increases_stock_and_records_outflow`
5. `test_sales_out_decreases_stock_and_records_inflow`
6. `test_sales_out_rejects_insufficient_stock`
7. `test_other_shop_cannot_read_stock_by_resource_id`
8. `test_other_shop_cannot_write_stock_by_resource_id`
9. `test_transaction_party_cannot_cross_org`
10. `test_seller_summary_matches_transactions_and_stock`
11. `test_ai_purchase_in`
12. `test_ai_sales_out`
13. `test_ai_query_stock`

基础校验命令：

```bash
python3 -m compileall src
python3 -m pytest agents/tdd/test_seller_inventory_api.py
```

如果当前环境没有 pytest，必须在验收报告中说明，并至少提供等价 HTTP 脚本输出。

## 6. 前端验收

| 编号 | 验收项 | 标准 |
|------|------|------|
| AC-FE-01 | 登录状态 | 页面明确显示当前用户、店铺和角色 |
| AC-FE-02 | 商品页面 | 可创建商品并刷新列表 |
| AC-FE-03 | 仓库页面 | 可创建仓库或库位 |
| AC-FE-04 | 入库页面 | 可完成一次采购入库 |
| AC-FE-05 | 出库页面 | 可完成一次销售出库 |
| AC-FE-06 | 库存页面 | 可查看总库存和库位分布 |
| AC-FE-07 | 摘要页面 | 可查看收入、支出、交易数、库存概览 |
| AC-FE-08 | 错误提示 | 库存不足、无权限、商品不存在时提示清楚 |

## 7. 演示验收

演示脚本必须在 3-5 分钟内完成：

1. 登录淘宝卖家店铺。
2. 创建商品“白色手机壳”。
3. 创建库位 `A-01-03`。
4. 进货 20 件，采购支出 160 元。
5. 销售 3 件，销售收入 45 元。
6. 查询库存，显示剩余 17 件和库位。
7. 查看经营摘要。
8. 用 AI 再完成一次库存查询。
9. 展示另一个店铺无法访问该商品库存。

## 8. 发布门禁

发布前必须满足：

1. P0 功能验收全部通过。
2. 安全和隔离验收全部通过。
3. 数据一致性验收全部通过。
4. `python3 -m compileall src` 通过。
5. Seller API 测试通过或有等价 HTTP 证据。
6. README 启动命令使用 `python3` 或项目脚本。
7. 演示视频使用真实淘宝卖家 MVP 流程，不只演示火烧新野。

## 9. 不接受的交付

以下情况视为不通过：

1. 只创建资源，不支持进货入库和销售出库。
2. 库存变化和交易流水需要人工分别录入。
3. 出库可以扣成负数。
4. 知道 `resource_id` 就能查看或修改其他店铺库存。
5. AI 工具默认操作 `shu` 或其他固定组织。
6. 摘要只统计交易笔数，不统计收入、支出和库存。
7. 前端只能展示历史战役，不能完成淘宝卖家流程。
