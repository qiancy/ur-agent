# DEMO 录屏模拟数据增强开发测试安排

> 角色：产品经理 / Demo Owner
> 目标：让比赛录屏画面“有数据、有故事、有对比”，同时不破坏双空间隔离和无 DB 数字 ID 红线。
> 范围：仅测试 Demo 环境；不得改生产数据，不得写真实密码或密钥。

## 1. PM 结论

当前 `scripts/seed_demo_data.py` 已能证明“淘宝卖家 + 火烧新野”双上下文，但画面偏薄：

- 淘宝卖家只有 2 个商品、3 条流水，库存表和流水表不够饱满。
- 低库存面板在默认阈值 5 下可能没有内容，产品卖点不明显。
- 火烧新野只有 2 个资源、3 个成员，没有时间线，无法充分展示“信息流、物流、人流”的多维观察能力。

因此安排开发测试团队进入 **DEMO-DATA-01：录屏模拟数据增强**。本任务只增强 Demo 数据和录屏验收脚本，原则上不改业务 API、不改 DB schema、不扩大前端功能范围。

## 2. 产品目标

录屏时必须能看到：

1. Header 中 `zhansan` 一个账号可切换 `淘宝小店 A` 与 `火烧新野战役`。
2. 淘宝卖家空间：
   - 工作台指标卡有销售收入、采购支出、净现金流、库存估值。
   - 库存表至少 6 行，有正常、临界、低库存状态。
   - 低库存处理面板至少 2 项。
   - 库存流水至少 10 条，能体现多商品采购和销售。
   - Seller AI 能回答库存最低、销售收入、采购支出、补货建议。
3. 火烧新野空间：
   - 空间观察页有人员、实物资源、知识资源、时间线。
   - 多维流向中信息流、物流、人流都有内容。
   - 不出现淘宝 SKU、淘宝销售收入或 Seller API 请求。

## 3. 数据增强口径

### 3.1 淘宝卖家空间

组织保持不变：

| 字段 | 值 |
| :--- | :--- |
| ouid | `taobao_shop_a` |
| name | `淘宝小店 A` |
| type | `ecommerce` |

人员：

| puid | 姓名 | 角色 | 录屏用途 |
| :--- | :--- | :--- | :--- |
| zhansan | 张三 | owner | 店主、登录账号 |
| lisi | 李四 | member | 仓管 |
| wangwu | 王五 | member | 运营 |

仓库/库位：

| warehouse_code | 名称 | location | 录屏用途 |
| :--- | :--- | :--- | :--- |
| WH-MAIN | 杭州总仓 | 杭州 | 主库存 |
| WH-LIVE | 直播间备货架 | 杭州直播间 | 低库存/热销展示 |
| WH-RETURN | 退货暂存区 | 杭州 | 退货待处理展示 |

商品与最终库存：

| product_uid | 单位 | 最终库存 | 状态 | 录屏用途 |
| :--- | :--- | ---: | :--- | :--- |
| 诸葛亮联名羽扇 | 件 | 50 | 充足 | 保留旧核心断言 |
| 木牛流马模型 | 件 | 12 | 正常偏低 | 保留旧商品故事 |
| 隆中对竹简礼盒 | 套 | 36 | 充足 | 提升表格行数 |
| 新野火攻纪念帆布袋 | 个 | 18 | 充足 | 文创品类扩展 |
| 孔明灯香薰套装 | 盒 | 5 | 临界 | 默认阈值 5 的临界样例 |
| 草船借箭桌游卡牌 | 盒 | 4 | 低库存 | 新的最低库存锚点 |

流水口径：

- 每个商品至少有 1 条 `purchase_in`。
- 至少 4 个商品有 `sales_out`。
- 总流水条数不少于 10 条。
- 所有金额为正数；采购进入采购支出，销售进入销售收入。
- 允许所有 `created_at` 为当前时间，不要求伪造历史日期；若团队实现日期故事线，不得直接绕过 API/事务口径修改业务结果。

AI 口径变更：

- 增强后，“库存最低的商品是什么？”的标准答案改为 `草船借箭桌游卡牌（4盒）`。
- `木牛流马模型（12件）` 继续保留，但不再作为最低库存唯一断言。
- TDD 和 Playwright 必须同步更新，不能继续断言最低库存为木牛流马。

### 3.2 火烧新野战役空间

组织保持不变：

| 字段 | 值 |
| :--- | :--- |
| ouid | `xinye_campaign` |
| name | `火烧新野战役` |
| type | `campaign` |

人员：

| puid | 姓名 | 角色 |
| :--- | :--- | :--- |
| liubei | 刘备 | 指挥官/owner |
| zhugeliang | 诸葛亮 | 军师/admin 或 member |
| guanyu | 关羽 | 前军 |
| zhangfei | 张飞 | 后军 |
| zhaoyun | 赵云 | 护卫 |
| mizhu | 糜竺 | 后勤 |
| zhansan | 张三 | 观察员/member |

资源：

| resource | type | 数量/金额 | 单位 | 录屏用途 |
| :--- | :--- | ---: | :--- | :--- |
| 军粮 | physical | 1000 | 石 | 物流 |
| 箭矢 | physical | 5000 | 支 | 物资 |
| 火油 | physical | 120 | 桶 | 火攻关键物资 |
| 草料 | physical | 800 | 捆 | 后勤 |
| 辎重车 | physical | 36 | 辆 | 物流载体 |
| 斥候情报 | knowledge | - | 份 | 信息流 |
| 新野撤退路线图 | knowledge | - | 份 | 人流/路线 |
| 火攻布置方案 | knowledge | - | 份 | 战术知识 |

时间线：

使用 `campaign_import` + `campaign_event` 写入 active 事件，`campaign_code` 建议为 `demo_xinye_recording`，事件不少于 6 条：

| seq | 标题 | info_flow | logistics_flow | people_flow | risk |
| ---: | :--- | :--- | :--- | :--- | :--- |
| 1 | 侦察曹军南下 | 斥候回报曹军行军路线 | 军粮盘点 | 百姓开始撤离登记 | 情报延迟 |
| 2 | 百姓撤离新野 | 撤离路线发布 | 辎重车集中 | 百姓向樊城方向移动 | 道路拥堵 |
| 3 | 火油布置完成 | 火攻信号确认 | 火油入城门暗点 | 伏兵进入指定位置 | 提前暴露 |
| 4 | 夜间诱敌入城 | 假败消息传递 | 箭矢转入伏击点 | 主力后撤 | 敌军识破 |
| 5 | 新野点火 | 点火令下达 | 火油消耗 | 曹军混乱撤退 | 火势失控 |
| 6 | 刘备军转移 | 战果汇总 | 剩余军粮随队转移 | 军民向江夏方向移动 | 追兵逼近 |

资金流：

- P0 可不做战役资金流水，保持资金总额为 0，用于证明不串淘宝财务。
- 如果开发团队认为 GenericSpaceView 资金流太空，可增加 1-2 条“军费/后勤支出”交易，但必须清晰分类为 `军费支出`，不得出现销售收入、采购收入等电商语义。

## 4. 开发分工

### T-DATA：种子脚本增强

负责人：数据/后端开发

改动范围：

- `scripts/seed_demo_data.py`

要求：

- 保持幂等。重复执行不得重复创建组织、人员、membership、商品、仓库、库存流水、campaign import/event。
- 继续从 `DEMO_ZHANSAN_PASSWORD` 读取演示账号密码；不写真实密码。
- 内部可以使用 DB 数字 ID 做关联，但脚本输出、API 响应、前端展示不得暴露 DB 数字 ID。
- 不修改 `scripts/init_db.py` 的标准初始化职责。

### T-TDD：后端 Demo 冒烟更新

负责人：测试开发

改动范围：

- `agents/tdd/test_demo_smoke.py`

要求：

- 保留登录、组织列表、切换、隔离、Seller AI 五类红线。
- 新增断言：
  - `/seller/stock` 至少 6 行。
  - `草船借箭桌游卡牌` 库存为 4。
  - `/seller/summary` 的 `low_stock_items` 至少包含 `草船借箭桌游卡牌` 和 `孔明灯香薰套装`。
  - `/spaces/current/timeline` 在 `xinye_campaign` 下至少 6 事件，且事件 payload 含 `info_flow/logistics_flow/people_flow`。
  - `xinye_campaign` 下 `/seller/stock` 仍为 403。

### T-E2E：Playwright 录屏专项更新

负责人：前端测试

改动范围：

- `agents/tdd/playwright/test_demo_recording.py`
- `agents/tdd/playwright/README.md`

要求：

- 更新 Seller AI 断言：接受 `草船借箭桌游卡牌` 或 `4盒`。
- 库存页断言新增 `草船借箭桌游卡牌` 与低库存标签。
- 火烧新野页断言新增：
  - `ov-events >= 6`
  - 页面可见 `侦察曹军南下`、`新野点火`
  - 可见 `信息流`、`物流`、`人流`内容
- `--headed` 录屏脚本不变。

### T-QA：录屏前验收

负责人：QA / DevOps

必须执行：

```bash
PYTHONPATH=. python scripts/init_db.py
PYTHONPATH=. python scripts/seed_demo_data.py
python3 -m pytest agents/tdd/test_demo_smoke.py -v
bash agents/tdd/playwright/run_recording.sh
cd web && npm run build
```

安全扫描：

```bash
rg -n "sk-|AKIA|password" web/src src scripts agents --type py --type ts --type md
rg -n 'person_id|organization_id|membership_id|account_id|resource_id|asset_id|warehouse_id|transaction_id' web/src src/routers agents/tdd/playwright
rg -n '"pid"|"oid"|\bpid\b|\boid\b' web/src src/routers agents/tdd/playwright
```

说明：

- `password` 作为字段名允许；真实密码不允许。
- 测试代码可以用拼接方式构造禁止字段名，避免扫描误报。

## 5. 验收标准

### P0 必过

- `zhansan` 登录成功，默认进入 `taobao_shop_a`。
- Header 可切到 `xinye_campaign`，切换请求体只含 `{ "ouid": "xinye_campaign" }`。
- 淘宝工作台库存表至少 6 行，流水至少 10 条。
- 低库存处理面板至少 2 项。
- Seller AI 回答最低库存指向 `草船借箭桌游卡牌（4盒）`。
- 火烧新野页面资源数、人员数、事件数均大于 0，时间线至少 6 条。
- 非 ecommerce 空间不得调用 `/seller/summary`、`/seller/stock`、`/seller/chat`。
- 对外响应和前端展示不得出现 DB 数字 ID。

### P1 可选

- 淘宝商品分布到多个仓库/库位，录屏时可展示库位差异。
- 战役资金流增加“军费支出”故事线。
- Playwright 产出视频文件，作为 OBS 录屏失败时的备份素材。

## 6. 不做事项

- 不新增数据库表。
- 不引入随机 Faker 数据。
- 不把真实密码、JWT secret、DB 密码写入源码。
- 不恢复 `pid/oid` 兼容。
- 不修改生产库。
- 不为了录屏绕过鉴权或上下文隔离。

## 7. PM 放行口径

开发团队完成后提交报告必须包含：

1. 新增/修改文件清单。
2. `seed_demo_data.py` 重复执行幂等证明。
3. `test_demo_smoke.py` 通过结果。
4. Playwright headed 或可录屏截图/视频结果。
5. 安全扫描结果。
6. 若最低库存锚点由 `木牛流马模型` 改为 `草船借箭桌游卡牌`，必须说明所有测试与 README 已同步。

全部通过后，PM 才允许进入正式录屏。
