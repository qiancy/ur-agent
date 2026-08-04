# DEMO-DATA-02 全新录屏账号与数据开发测试安排

> 角色：产品经理 / Demo Owner
> 目标：录屏主线与正式 MVP 产品逻辑一致：用户登录默认进入个人工作空间，再通过 Header 切换到自己所在的业务空间。
> 范围：测试 Demo 环境；不改生产库；不写真实密码或密钥。

## 1. PM 结论

`zhansan` 是历史演示账号，适合做回归，但不适合作为最终录屏主线。原因是它可能由种子脚本直接创建 membership，缺少 `zhansan_personal`，登录后默认进入 `taobao_shop_a`，这会削弱 MVP 的核心卖点：

> 一个账号先拥有自己的 personal 工作空间，再通过 membership 切换到店铺、战役、家庭、舰队等业务空间。

因此安排开发测试团队进入 **DEMO-DATA-02：全新录屏账号与数据**。

本轮要求创建全新的录屏账号、全新的业务空间、全新的模拟数据。`zhansan / taobao_shop_a / xinye_campaign` 保留为旧回归数据，不作为正式录屏入口。

## 2. 新录屏主线

### 2.1 账号

| 字段 | 值 |
| :--- | :--- |
| account.login | `liuming` |
| person.puid | `liuming` |
| person.name | `刘明` |
| 密码来源 | `DEMO_LIUMING_PASSWORD` |

要求：

- 密码只从环境变量或未提交的 `.env` 读取。
- 不允许源码、文档、测试里写真实密码。
- 如未设置 `DEMO_LIUMING_PASSWORD`，种子脚本应明确报错或跳过建号并提示，不得使用硬编码默认密码。

### 2.2 默认个人工作空间

注册/种子后必须存在：

| 字段 | 值 |
| :--- | :--- |
| ouid | `liuming_personal` |
| name | `刘明的个人空间` |
| type | `personal` |
| role | `owner` |

验收：

- `POST /auth/login` 登录 `liuming` 后默认返回 `organization.ouid = liuming_personal`。
- Header 默认显示 `刘明的个人空间 (personal)`。
- personal 空间不调用 `/seller/*`。

实现建议：

- 优先走现有注册契约或复用 `register_personal_space()`，让数据结构与真实用户注册一致。
- 如果种子脚本直接写 DB，必须完全等价于注册结果：`account + person + personal organization + owner membership` 原子创建。

## 3. 新业务空间

### 3.1 电商空间：明灯文创小店

| 字段 | 值 |
| :--- | :--- |
| ouid | `liuming_mingdeng_shop` |
| name | `明灯文创小店` |
| type | `ecommerce` |
| liuming role | `owner` |

人员：

| puid | 姓名 | 角色 |
| :--- | :--- | :--- |
| liuming | 刘明 | owner |
| chenyan | 陈燕 | member/运营 |
| heqiang | 何强 | member/仓管 |

仓库：

| warehouse_code | 名称 | location |
| :--- | :--- | :--- |
| MD-WH-HZ | 杭州总仓 | 杭州 |
| MD-WH-LIVE | 直播间备货架 | 杭州直播间 |
| MD-WH-RETURN | 退货暂存区 | 杭州 |

商品与最终库存：

| product_uid | 单位 | 最终库存 | 状态 | 录屏用途 |
| :--- | :--- | ---: | :--- | :--- |
| 星火羽扇礼盒 | 套 | 64 | 充足 | 首屏库存大项 |
| 木牛流马积木套装 | 套 | 18 | 正常偏低 | 热销 SKU |
| 新野火攻桌游 | 盒 | 7 | 正常偏低 | 和战役空间形成故事呼应 |
| 隆中对手账本 | 本 | 42 | 充足 | 文具品类 |
| 孔明灯夜读灯 | 盏 | 5 | 临界 | 默认阈值 5 |
| 草船借箭纪念徽章 | 枚 | 3 | 低库存 | 新最低库存锚点 |

流水：

- 至少 12 条库存流水。
- 每个商品至少 1 条 `purchase_in`。
- 至少 5 个商品有 `sales_out`。
- 所有金额为正数。
- 采购支出、销售收入、净现金流、库存估值必须有非零值。

AI 标准回答：

- “库存最低的商品是什么？”应指向 `草船借箭纪念徽章（3枚）`。
- “这个月卖了多少钱？”应返回本空间销售收入，不得混入战役空间资金。
- “哪些商品需要补货？”至少应包含 `草船借箭纪念徽章` 与 `孔明灯夜读灯`。

### 3.2 战役空间：新野火攻复盘空间

| 字段 | 值 |
| :--- | :--- |
| ouid | `liuming_xinye_review` |
| name | `新野火攻复盘空间` |
| type | `campaign` |
| liuming role | `member` 或 `observer` |

人员：

| puid | 姓名 | 角色 |
| :--- | :--- | :--- |
| liuming | 刘明 | 观察员 |
| liubei_review | 刘备 | 指挥官 |
| zhugeliang_review | 诸葛亮 | 军师 |
| zhaoyun_review | 赵云 | 护卫 |
| guanyu_review | 关羽 | 前军 |
| zhangfei_review | 张飞 | 后军 |
| mizhu_review | 糜竺 | 后勤 |

资源：

| resource | type | 数量/金额 | 单位 | 录屏用途 |
| :--- | :--- | ---: | :--- | :--- |
| 新野城军粮 | physical | 1200 | 石 | 物流 |
| 南门箭矢 | physical | 6800 | 支 | 物资 |
| 火油桶 | physical | 160 | 桶 | 火攻核心 |
| 撤离辎重车 | physical | 48 | 辆 | 人流/物流 |
| 斥候简报 | knowledge | - | 份 | 信息流 |
| 火攻布置图 | knowledge | - | 份 | 战术知识 |
| 百姓撤离名册 | knowledge | - | 份 | 人流 |

时间线至少 8 条：

| seq | 标题 | 必含维度 |
| ---: | :--- | :--- |
| 1 | 斥候确认曹军路线 | info_flow |
| 2 | 军粮与火油盘点 | logistics_flow |
| 3 | 百姓撤离名册确认 | people_flow |
| 4 | 南门火油暗点布置 | info_flow / logistics_flow |
| 5 | 诱敌入城信号下达 | info_flow / risk |
| 6 | 新野点火 | logistics_flow / people_flow |
| 7 | 曹军混乱撤退 | people_flow / risk |
| 8 | 刘备军民转移复盘 | info_flow / logistics_flow / people_flow |

资金口径：

- P0 建议保持战役资金流为 0，用于录屏证明电商销售收入不串到战役空间。
- 若补军费数据，必须分类为 `军费支出`，不得出现“销售收入/采购收入”等电商口径。

## 4. 开发任务

### T-DATA：新种子脚本

负责人：数据/后端开发

建议新增：

```text
scripts/seed_recording_data.py
```

要求：

- 不复用 `zhansan`、`taobao_shop_a`、`xinye_campaign`。
- 创建 `liuming`、`liuming_personal`、`liuming_mingdeng_shop`、`liuming_xinye_review`。
- 保持幂等：重复执行不产生重复组织、人员、membership、商品、仓库、库存流水、campaign event。
- 可复用现有 DB helper，但对外输出不得出现 DB 数字 ID。
- 不修改 `scripts/init_db.py` 的基础职责。

### T-TDD：新冒烟测试

负责人：测试开发

建议新增：

```text
agents/tdd/test_recording_smoke.py
```

必测：

1. `liuming` 登录默认进入 `liuming_personal`。
2. `/auth/me/organizations` 至少包含 `liuming_personal`、`liuming_mingdeng_shop`、`liuming_xinye_review`。
3. Header/后端切换请求只允许 `{ "ouid": "liuming_mingdeng_shop" }` 或 `{ "ouid": "liuming_xinye_review" }`，不得含 DB ID。
4. personal 和 campaign 空间访问 `/seller/stock` 返回 403。
5. ecommerce 空间 `/seller/stock` 至少 6 行，最低库存为 `草船借箭纪念徽章` 3。
6. ecommerce 空间 `/seller/summary` 有非零销售收入、采购支出、库存估值。
7. campaign 空间 `/spaces/current/timeline` 至少 8 条事件，页面/响应含信息流、物流、人流。
8. ecommerce 商品不得出现在 campaign 资源中。
9. 所有认证、空间、seller、spaces 响应递归扫描无 DB 数字 ID。

### T-E2E：Playwright 录屏专项切新账号

负责人：前端测试

改动：

- `agents/tdd/playwright/test_demo_recording.py`
- `agents/tdd/playwright/README.md`
- `agents/tdd/playwright/run_recording.sh`

新默认环境：

```bash
export DEMO_RECORDING_LOGIN=liuming
export DEMO_LIUMING_PASSWORD='<未提交 .env 中配置>'
export DEMO_RECORDING_PERSONAL_OUID=liuming_personal
export DEMO_RECORDING_SHOP_OUID=liuming_mingdeng_shop
export DEMO_RECORDING_CAMPAIGN_OUID=liuming_xinye_review
```

录屏主流程：

1. 登录 `liuming`。
2. 验证默认进入 `刘明的个人空间 (personal)`。
3. Header 切换到 `明灯文创小店`，进入 Seller 工作台。
4. 展示库存、低库存、流水、经营摘要、Seller AI。
5. Header 切换到 `新野火攻复盘空间`，展示时间线和信息流/物流/人流。
6. 回到 personal 或 shop，总结多空间隔离。

### T-QA：录屏前门禁

执行：

```bash
PYTHONPATH=. python scripts/init_db.py
PYTHONPATH=. python scripts/seed_recording_data.py
python3 -m pytest agents/tdd/test_recording_smoke.py -v
bash agents/tdd/playwright/run_recording.sh
cd web && npm run build
```

安全扫描：

```bash
rg -n "sk-|AKIA|password" web/src src scripts agents --type py --type ts --type md
rg -n 'person_id|organization_id|membership_id|account_id|resource_id|asset_id|warehouse_id|transaction_id' web/src src/routers agents/tdd/playwright agents/tdd/test_recording_smoke.py
rg -n '"pid"|"oid"|\bpid\b|\boid\b' web/src src/routers agents/tdd/playwright agents/tdd/test_recording_smoke.py
```

## 5. 验收标准

P0 必过：

- 新账号 `liuming` 登录默认进入 `liuming_personal`。
- Header 可切换到 `liuming_mingdeng_shop` 和 `liuming_xinye_review`。
- 所有空间切换都走 `/auth/switch-organization`，前端不得假切换。
- personal / campaign 不调用 Seller API。
- ecommerce 工作台数据饱满：6+ 商品、12+ 流水、2+ 低库存、summary 非零。
- campaign 空间数据饱满：7+ 人员、7+ 资源、8+ 时间线，并展示信息流/物流/人流。
- 响应和前端不得暴露 DB 数字 ID。
- 默认测试不触发真 LLM；录屏可用 fake Seller AI 或稳定本地 LLM。

P1 可选：

- 保留 `zhansan` 旧冒烟测试，作为兼容回归。
- 新增 `family` 或 `fleet` 第三业务空间作为彩蛋，但不阻塞本轮录屏。

## 6. PM 放行口径

开发团队提交报告时必须说明：

1. 新账号、新空间、新数据清单。
2. `liuming` 登录默认 personal 的 API 证据。
3. Header 切换新空间的 Playwright 证据。
4. `test_recording_smoke.py` 结果。
5. seed 脚本幂等证明。
6. 安全扫描结果。

全部通过后，PM 才允许用新账号正式录屏。
