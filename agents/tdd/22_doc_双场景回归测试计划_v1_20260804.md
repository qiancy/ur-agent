# Demo 双场景回归测试计划

> 角色：资深 DevOps + QA 工程师
> 目标日期：2026-08-06 比赛提交前
> 目标耗时：1 小时内完成环境重置、双场景种子、冒烟回归、录屏提词器输出
> 适用范围：测试 Demo 环境。禁止在生产库执行 Destroy & Rebuild。

---

## 0. 核心目标

将 Uni-Resource Agent 重置为“个人空间 + 火烧新野 + 淘宝卖家”多上下文完美状态，并输出可录屏的无 Bug 操作清单。

演示必须证明三件事：

1. 一个全新账号 `liuming` 登录后默认进入自己的个人空间。
2. 用户可通过 Header 切换到自己所在的淘宝卖家空间和火烧新野空间。
3. 淘宝卖家空间有真实库存、流水、摘要、Seller AI 查询闭环。
4. 火烧新野空间与淘宝卖家空间数据隔离，绝不泄漏淘宝销售收入或商品库存。

发现任何异常必须立即终止，先修复再继续。不得带着疑问进入下一阶段。

---

## 1. 执行前门禁

### 1.1 必须确认

- 当前连接的是测试数据库，不是生产数据库。
- `.env` 或终端环境变量已配置测试 DB 和 JWT secret。
- 本地没有未保存的重要数据库数据。
- 后端和前端进程可被重启。
- 当前代码分支是准备录屏的冻结分支。

### 1.2 推荐环境变量

不要把真实密码写入文档、脚本或提交文件。执行前在终端或未提交的 `.env` 中设置：

```bash
export DB_HOST=1.117.223.223
export DB_PORT=5435
export DB_USER=unires
export DB_PASSWORD='<测试数据库密码>'
export DB_NAME=unires
export JWT_SECRET='<测试 JWT secret>'
export DEMO_LIUMING_PASSWORD='<演示账号密码>'
```

### 1.3 立即停止条件

出现以下任一情况，立即停止：

- `DB_HOST/DB_PORT` 不是测试库。
- `DROP DATABASE` 操作目标不是 `unires` 测试库。
- 初始化后发现 `test_org/demo_org/tmp_*` 等开发脏组织。
- 登录响应或 JWT 出现 `id/person_id/organization_id/membership_id/pid/oid`。
- 切换空间后数据串库。
- 前端出现白屏、`NaN/null`、表格列暴露 DB ID。
- 默认测试触发真 LLM。

---

## 2. 第一阶段：数据库核爆式清理

目标：确保 Demo 环境从干净数据库开始，不受开发调试残留影响。

### 2.1 停止所有服务

```bash
pkill -f uvicorn || true
pkill -f vite || true
```

验证：

```bash
ps -ax | rg 'uvicorn|vite|npm run dev' || true
```

预期：无正在运行的后端或 Vite dev server。

### 2.2 硬重置 PostgreSQL

仅测试库执行：

```bash
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres
```

进入 psql 后执行：

```sql
DROP DATABASE IF EXISTS unires WITH (FORCE);
CREATE DATABASE unires OWNER unires;
\q
```

### 2.3 初始化表结构

```bash
PYTHONPATH=. python scripts/init_db.py
```

### 2.4 标准预置验证

执行：

```bash
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d unires \
  -c "SELECT ouid, name, type FROM organization ORDER BY ouid;"
```

验收：

- 允许存在的标准空间：
  - `shu` / 蜀
  - `wei` / 魏
  - `wu` / 吴
  - `taobao_shop_a` / 淘宝小店 A
- 不允许出现：
  - `test_org`
  - `demo_org`
  - `tmp_*`
  - 任何开发调试残留组织

---

## 3. 第二阶段：双场景种子数据

目标：录屏数据必须有故事感，不使用随机假数据。

建议新增独立脚本：

```text
scripts/seed_recording_data.py
```

不要把 Demo 数据强行塞进 `scripts/init_db.py`，除非开发团队确认 init 脚本本身就是 Demo 初始化入口。推荐流程是：

```bash
PYTHONPATH=. python scripts/init_db.py
PYTHONPATH=. python scripts/seed_recording_data.py
```

> 说明：`scripts/seed_demo_data.py`、`zhansan`、`taobao_shop_a`、`xinye_campaign` 可保留为历史回归基线；正式录屏主线必须使用 `liuming` 与全新空间。

### 3.0 默认上下文：个人空间

账号：

```text
account.login = liuming
person.puid = liuming
person.name = 刘明
password = DEMO_LIUMING_PASSWORD
```

个人空间：

```text
ouid = liuming_personal
type = personal
name = 刘明的个人空间
role = owner
```

验收：

- 登录 `liuming` 后默认进入 `liuming_personal`。
- Header 下拉可见：
  - `刘明的个人空间`
  - `明灯文创小店`
  - `新野火攻复盘空间`
- personal 空间不得调用 `/seller/*`。

### 3.1 上下文 A：淘宝卖家

组织：

```text
ouid = liuming_mingdeng_shop
type = ecommerce
name = 明灯文创小店
```

人员：

| puid | 姓名 | 角色 |
| :--- | :--- | :--- |
| liuming | 刘明 | owner |
| chenyan | 陈燕 | member/运营 |
| heqiang | 何强 | member/仓管 |

商品与库存（录屏增强版）：

| product_uid | 商品名 | 库存 | 单位 | 录屏用途 |
| :--- | :--- | ---: | :--- | :--- |
| 星火羽扇礼盒 | 星火羽扇礼盒 | 64 | 套 | 首屏库存大项 |
| 木牛流马积木套装 | 木牛流马积木套装 | 18 | 套 | 热销 SKU |
| 新野火攻桌游 | 新野火攻桌游 | 7 | 盒 | 与战役空间形成故事呼应 |
| 隆中对手账本 | 隆中对手账本 | 42 | 本 | 文具品类 |
| 孔明灯夜读灯 | 孔明灯夜读灯 | 5 | 盏 | 默认阈值 5 的临界样例 |
| 草船借箭纪念徽章 | 草船借箭纪念徽章 | 3 | 枚 | 新最低库存锚点 |

仓库/库位：

| warehouse_code | 名称 | location | 录屏用途 |
| :--- | :--- | :--- | :--- |
| MD-WH-HZ | 杭州总仓 | 杭州 | 主库存 |
| MD-WH-LIVE | 直播间备货架 | 杭州直播间 | 热销/低库存展示 |
| MD-WH-RETURN | 退货暂存区 | 杭州 | 退货待处理展示 |

最近交易：

| 类型 | 金额 | 说明 |
| :--- | ---: | :--- |
| sales_out | 正数收入 | 销售星火羽扇礼盒 |
| sales_out | 正数收入 | 销售木牛流马积木套装 |
| purchase_in | 正数支出 | 补货孔明灯夜读灯 |
| purchase_in / sales_out | 正数支出/收入 | 覆盖其余文创商品，库存流水总数不少于 12 条 |

验收：

- `/seller/stock` 能看到至少 6 个商品库存条目。
- `草船借箭纪念徽章（3枚）` 是库存最低商品。
- `/seller/summary` 的 `low_stock_items` 至少包含 `草船借箭纪念徽章` 与 `孔明灯夜读灯`。
- `/seller/summary` 能汇总销售收入、采购支出、库存金额概览。
- `/seller/chat` 回答“库存最低的商品是什么？”时指向 `草船借箭纪念徽章（3枚）`。

### 3.2 上下文 B：火烧新野

组织：

```text
ouid = liuming_xinye_review
type = campaign
name = 新野火攻复盘空间
```

人员：

| puid | 姓名 | 角色 |
| :--- | :--- | :--- |
| liuming | 刘明 | 观察员 |
| liubei_review | 刘备 | 指挥官 |
| zhugeliang_review | 诸葛亮 | 军师 |
| guanyu_review | 关羽 | 前军 |
| zhangfei_review | 张飞 | 后军 |
| zhaoyun_review | 赵云 | 护卫 |
| mizhu_review | 糜竺 | 后勤 |

资源：

| resource | 库存 | 单位 | 录屏用途 |
| :--- | ---: | :--- | :--- |
| 新野城军粮 | 1200 | 石 | 物流 |
| 南门箭矢 | 6800 | 支 | 物资 |
| 火油桶 | 160 | 桶 | 火攻关键物资 |
| 撤离辎重车 | 48 | 辆 | 人流/物流载体 |
| 斥候简报 | - | 份 | 信息流知识资源 |
| 火攻布置图 | - | 份 | 战术知识资源 |
| 百姓撤离名册 | - | 份 | 人流知识资源 |

时间线：

| seq | 标题 | 录屏用途 |
| ---: | :--- | :--- |
| 1 | 斥候确认曹军路线 | 信息流起点 |
| 2 | 军粮与火油盘点 | 物流准备 |
| 3 | 百姓撤离名册确认 | 人流展示 |
| 4 | 南门火油暗点布置 | 信息流与物流 |
| 5 | 诱敌入城信号下达 | 信息流与风险 |
| 6 | 新野点火 | 战役高潮 |
| 7 | 曹军混乱撤退 | 人流与风险 |
| 8 | 刘备军民转移复盘 | 总结与转移 |

验收：

- `liuming` 登录后 Header 下拉同时看到：
  - 刘明的个人空间
  - 明灯文创小店
  - 新野火攻复盘空间
- 切换到 `liuming_xinye_review` 后，空间数据不包含电商 SKU。
- 火烧新野 `/summary` 财务数据为 `0` 或明确军费口径，绝不能显示淘宝销售收入。
- `/spaces/current/timeline` 至少 8 个事件，每个关键事件 payload 至少能支撑 `信息流/物流/人流` 展示。

### 3.3 种子脚本红线

`scripts/seed_recording_data.py` 必须满足：

- 幂等：重复执行不会创建重复组织、重复人员、重复库存。
- 不写真实密码；`liuming` 密码从 `DEMO_LIUMING_PASSWORD` 读取。
- 录屏主线只创建一个新账号 `account.login=liuming`，不得创建 `liuming@<ouid>`。
- membership 绑定到 `person.puid=liuming`。
- 对外数据使用 `puid/ouid/product_uid/warehouse_code`，不得使用 DB 数字 ID。

---

## 4. 第三阶段：全链路冒烟测试

目标：用录屏前最小用例证明认证、切换、隔离、Seller AI 全链路可用。

测试文件：

```text
agents/tdd/test_recording_smoke.py
```

旧测试如包含 `pid/oid`，本次必须重构为 `puid/ouid`。

### 4.1 用例 1：登录鉴权

请求：

```http
POST /auth/seller-login
```

Body：

```json
{
  "login": "liuming",
  "password": "<DEMO_LIUMING_PASSWORD>"
}
```

断言：

- HTTP 200。
- 返回 `access_token`。
- JWT payload 只含业务身份字段：
  - `puid`
  - `ouid`
  - `organization_type`
  - `role`
  - 其他非 DB 身份字段
- JWT payload 不得含：
  - `id`
  - `person_id`
  - `organization_id`
  - `membership_id`
  - `pid`
  - `oid`

### 4.2 用例 2：组织列表

请求：

```http
GET /auth/me/organizations
Authorization: Bearer <token>
```

断言：

- 返回当前用户三个核心组织：
  - `liuming_personal`
  - `liuming_mingdeng_shop`
  - `liuming_xinye_review`
- 每项显示 `ouid/name/type/role`。
- 不返回 DB 数字 ID。

### 4.3 用例 3：上下文切换

请求：

```http
POST /auth/switch-organization
Authorization: Bearer <token>

{ "ouid": "liuming_mingdeng_shop" }
```

断言：

- HTTP 200。
- 返回新 JWT。
- 新 JWT 中 `ouid=liuming_mingdeng_shop`。
- 再切到战役空间：

```json
{ "ouid": "liuming_xinye_review" }
```

新 JWT 中 `ouid=liuming_xinye_review`。

### 4.4 用例 4：资产隔离

在 `liuming_mingdeng_shop` 上下文：

```text
query_asset("草船借箭纪念徽章")
```

断言：返回 `草船借箭纪念徽章`，库存 `3`。

切换至 `liuming_xinye_review` 后：

```text
query_asset("草船借箭纪念徽章")
```

断言：返回“未找到”或数量 `0`。

这是致命红线：任何淘宝库存出现在火烧新野空间，都视为 Demo 阻断。

### 4.5 用例 5：Seller AI 查询

请求：

```http
POST /seller/chat
Authorization: Bearer <liuming_mingdeng_shop token>

{ "message": "库存最低的商品是什么？" }
```

断言：

- HTTP 200。
- 回答必须包含：
  - `草船借箭纪念徽章`
  - `3`
- 不调用通用 `/chat`。
- 响应不包含 DB 数字 ID。

### 4.6 执行命令

```bash
python3 -m pytest agents/tdd/test_recording_smoke.py -v
```

验收：个人默认空间、组织切换、资产隔离、Seller AI 等核心场景全部通过。

---

## 5. 第四阶段：录屏操作提词器

目标：PM 按固定流程录屏，边演示边做 Bug 自查。

| 时间 | 操作 | 预期效果 | 检查点 |
| :--- | :--- | :--- | :--- |
| 0:00 | 启动后端和前端 | 终端无 Error，Vite 编译成功 | 若报 `ModuleNotFoundError`，立即执行 `pip install -r requirements.txt` |
| 0:30 | 访问 `http://localhost:5173` | 跳转登录页 | 登录页不提示 `puid@ouid`，只提示输入账号 |
| 1:00 | 输入 `liuming` 和演示密码登录 | Header 显示 `刘明的个人空间 (personal)` | 若默认进入店铺或战役，立即检查 personal 排序和登录默认空间选择 |
| 1:30 | 点击 Header 组织下拉 | 下拉列表含 `明灯文创小店`、`新野火攻复盘空间` | 选择后必须调用 `/auth/switch-organization`，不能前端假切换 |
| 2:00 | 切换到 `明灯文创小店` | Main 显示 Seller 经营工作台 | 只有 ecommerce 空间可调用 `/seller/*` |
| 2:30 | 点左侧 `Seller AI` | 进入 Seller AI 页面 | Network 面板只允许调用 `/seller/chat`，不得调用通用 `/chat` |
| 2:45 | 输入“算一下这个月卖了多少钱” | AI 返回销售收入/采购支出口径 | 不得回答“我不知道”；不得泄漏 DB ID |
| 3:15 | 点 `库存` 菜单 | 库存列表显示 SKU 数据 | 表格列显示 `product_uid`，绝不能显示 `asset_id/resource_id` |
| 3:45 | 点 `经营摘要` | 卡片显示收入、支出、库存概览 | 不得出现 `NaN/null`；金额必须与种子交易一致 |
| 4:15 | 切换到 `新野火攻复盘空间` | 看不到电商 SKU 和销售收入；显示时间线与信息流/物流/人流 | 证明多空间隔离 |
| 4:45 | 总结 | “同一账号，多个空间，数据和 AI 能力随空间切换” | Header、Sidebar、Main 三者上下文一致 |

---

## 6. 即时 Bug 修复策略

录屏前发现以下高频问题，按优先级立即处理。

### 6.1 切换组织后页面白屏，后端返回 422

可能原因：

- `/auth/switch-organization` 仍校验旧字段 `organization_id`。
- 前端请求体混入 DB ID。

修复：

- 检查 `src/routers/auth.py` 和 `src/models/schemas.py`。
- `SwitchOrganizationRequest` 必须只接收 `ouid: str`。
- 删除所有对 `int(id)` 或 `organization_id` 的切换逻辑。
- 前端 `web/src/api/auth.ts` 只提交 `{ ouid }`。

复测：

```bash
python3 -m pytest agents/tdd/test_auth_api.py::test_switch_organization_success_issues_new_token -q
```

### 6.2 Seller AI 回答“我不知道”

可能原因：

- Seller 工具没有拿到当前组织上下文。
- Agent 暴露了错误工具集。

修复：

- 检查 `src/routers/seller.py` 的 `/seller/chat`。
- 检查 `src/agents/agent.py` 和 Seller tools。
- 工具必须由后端从 JWT 解析后的当前组织上下文注入，不能从用户提问中推断。
- Seller AI 只允许只读安全工具，不允许暴露写工具。

复测：

```bash
python3 -m pytest agents/tdd/test_seller_chat_api.py agents/tdd/test_seller_ai_tools.py -q
```

### 6.3 前端编译 TypeError

修复：

```bash
cd web
npm run type-check
```

重点检查：

- `web/src/api/seller.ts`
- `web/src/api/auth.ts`
- `web/src/api/spaces.ts`
- `web/src/api/spaceGovernance.ts`

禁止用 `any` 逃避类型错误。API 类型必须与后端 JSON 契约一致。

### 6.4 摘要出现 `NaN/null`

可能原因：

- 交易金额为 `null`。
- 采购/销售统计口径不一致。
- 种子数据未生成 inventory movement。

修复：

- 检查 `transaction`、`inventory_movement`。
- Demo 交易金额必须为正数。
- 采购支出、销售收入、库存金额按 BE-03 已验收口径计算。

复测：

```bash
python3 -m pytest agents/tdd/test_seller_summary_api.py -q
```

---

## 7. 最终收尾命令

### 7.1 Demo 冒烟测试

```bash
python3 -m pytest agents/tdd/test_recording_smoke.py -v
```

### 7.2 安全扫描

```bash
rg -n "sk-|AKIA|password" web/src src --type py --type ts
```

说明：

- `password` 字段名可能在登录表单和认证代码中出现，允许作为字段名存在。
- 不允许出现真实密码、API key、token、secret。

进一步扫描：

```bash
rg -n 'person_id|organization_id|membership_id|account_id|resource_id|asset_id|warehouse_id|transaction_id' web/src src/routers
rg -n '"pid"|"oid"|\bpid\b|\boid\b' web/src src/routers agents/tdd
rg -n 'header-ai-entry|navigate-ai' web/src
```

### 7.3 前端构建

```bash
cd web
npm run build
```

### 7.4 录屏前状态确认

全部通过后，输出：

```text
Demo 环境已就绪，可以开始录屏
```

任一环节失败时，必须输出：

```text
Demo 环境未就绪，禁止录屏
失败阶段：
失败命令：
关键报错：
建议修复：
```

---

## 8. 最终交付物

| 交付物 | 路径/命令 | 验收 |
| :--- | :--- | :--- |
| 录屏种子脚本 | `scripts/seed_recording_data.py` | 可幂等重建个人空间 + 明灯文创小店 + 新野火攻复盘空间 |
| Demo 冒烟测试 | `agents/tdd/test_recording_smoke.py` | 个人默认空间、切换、隔离、Seller AI 场景全绿 |
| 录屏操作提词器 | 本文第 5 节 | PM 可按表逐步录屏 |
| 安全扫描结果 | 第 7.2 节命令输出 | 无真实密钥、无 DB ID 对外泄漏 |
| 前端构建结果 | `cd web && npm run build` | 构建成功 |
