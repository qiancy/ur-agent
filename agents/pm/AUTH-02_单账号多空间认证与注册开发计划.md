# AUTH-02 开发计划：单账号多空间认证与注册

> 日期：2026-08-03
> 角色：PM / 产品负责人
> 状态：下达开发团队，生产参赛前必须完成
> 关联文档：`uc001_用户认证用例.md`、`u001_account.md`、`CR-01_技术规格补充.md`

---

## 1. 目标

把当前“一个空间一个登录账号”的演示方式，收口为真正的多上下文空间模型：

```text
account -> person -> membership -> organization
```

用户只登录一次 `zhansan`，系统根据 `membership` 展示并切换 `zhansan_shop`、`fire_xinye_shu`、`zhangsan_family`、`deep_space_fleet` 等业务空间。

同时，为后续真实用户开放注册打基础：注册创建 `account + person`，可选加入初始组织；没有组织时显示“暂无业务空间”占位。

---

## 2. 产品红线

1. 不再用 `zhansan@<ouid>` 多账号模拟空间切换。
2. `account.login` 不解析 `puid/ouid`。
3. `account.login` 和 `person.puid` 不物理归并；MVP 演示可同值。
4. 空间切换只走 `/auth/switch-organization`，后端校验 membership 后重新签发 JWT。
5. 认证、注册、切换组织响应和 JWT 不得含 DB 数字 ID。
6. 不恢复 `pid/oid` 兼容。
7. 公共注册不得授予 `owner/admin/super`。
8. 密码、JWT secret、DB 密码不得写入源码或可提交文档。

---

## 3. API 契约

### 3.1 POST /auth/register

请求：

```json
{
  "login": "zhansan",
  "password": "demo-password",
  "name": "张三",
  "puid": "zhansan",
  "initial_ouid": "zhansan_shop"
}
```

规则：

- `login/password/name` 必填。
- `puid` 可选；缺省时仅当 `login` 满足 `^[A-Za-z0-9_-]+$` 才默认 `puid=login`。
- `initial_ouid` 可选；存在时创建普通 `member` membership。
- 响应无 DB 数字 ID。

### 3.2 POST /auth/login

请求：

```json
{
  "login": "zhansan",
  "password": "demo-password"
}
```

规则：

- 按 `account.login` 查账号，不解析组织。
- 有 membership 时返回默认空间 JWT 和 organizations 列表。
- 无 membership 时返回 `requires_organization=true`，不调用业务空间接口。

### 3.3 GET /auth/me/organizations

返回当前 person 可进入的组织：

```json
[
  { "ouid": "zhansan_shop", "name": "张三小店", "type": "ecommerce", "role": "owner" }
]
```

### 3.4 POST /auth/switch-organization

请求：

```json
{ "ouid": "zhangsan_family" }
```

规则：

- 只接受 `ouid`。
- 禁止 `organization_id`。
- 非 membership 返回 403。
- 成功后重新签发 JWT。

---

## 4. 开发分工

### T0-BE 后端认证

负责人：后端开发

改动：

1. `src/models/schemas.py`
   - `RegisterRequest` 增加 `puid`、`initial_ouid`。
   - `LoginRequest.login` 改为账号凭据注释。
   - auth 请求模型增加 `extra="forbid"`。
2. `src/auth/auth.py`
   - 登录/注册链路移除 `parse_login_name()`。
   - 保留 `validate_puid()`、`validate_ouid()`。
   - 新增注册用 `derive_puid_from_login()`。
3. `src/routers/auth.py`
   - `/auth/register` 按 `account.login` 创建 account/person。
   - `/auth/login` 按 account 认证，返回默认组织和 organizations。
   - `/auth/seller-login` 复用同一认证逻辑。
   - `/auth/switch-organization` 保持 membership 校验。
4. `src/db/database.py`
   - 确认 account/person/membership 查询函数满足新流程。
   - 如需新增 helper，只返回服务端内部 dict；router 负责清洗 DTO。

### T0-TDD 后端测试

负责人：TDD

新增/更新：

```text
agents/tdd/test_auth_api.py
```

必测：

1. 单账号注册成功。
2. 注册不带 `initial_ouid` 返回 `requires_organization=true`。
3. 非法 `puid` 返回 422。
4. 重复 `login` 返回 409。
5. 登录单账号返回默认空间和 organizations。
6. 旧形式 `zhansan@fire_xinye_shu` 不会被解析成组织上下文。
7. 切换非 membership 组织返回 403。
8. auth 响应和 JWT 无 DB 数字 ID。

### T0-FE 前端登录/注册

负责人：前端开发

改动：

1. `web/src/views/LoginView.vue`
   - placeholder 改为 `zhansan`。
   - 登录成功读取 `organizations`。
2. 新增或扩展注册入口
   - 字段：login/password/name/puid?/initial_ouid?。
   - 无空间态显示“暂无业务空间”占位。
3. `web/src/api/auth.ts`
   - 增加 register/login 类型。
   - 组织切换继续只提交 `ouid`。
4. 前端不得拼接 `login@ouid`。

### T0-DATA 演示数据

负责人：数据/脚本开发

改动：

1. `scripts/seed_demo_spaces.py`
   - 只创建一个 `account.login=zhansan`。
   - 建立 `person.puid=zhansan` 到 4 个空间的 membership。
   - 密码从 `DEMO_ZHANSAN_PASSWORD` 或未提交 `.env` 读取。
2. `scripts/capture_qa_screenshots.py`
   - 默认登录改为 `zhansan`。
   - 不写默认密码。

---

## 5. 验收命令

后端：

```bash
python3 -m compileall src agents/tdd
python3 -m pytest agents/tdd/test_auth_api.py -q
python3 -m pytest agents/tdd/test_seller_inventory_api.py agents/tdd/test_seller_inventory_transaction_api.py agents/tdd/test_seller_summary_api.py -q
```

前端：

```bash
cd web
npm test -- LoginView auth AppHeader
npm run build
```

安全扫描：

```bash
git diff --check
rg -n '"pid"|"oid"|\\bpid\\b|\\boid\\b' src web/src agents/tdd docs/API.md agents/pm
rg -n 'person_id|organization_id|account_id|membership_id' web/src
rg -n 'zhansan@|puid@ouid|puid@\\{ouid\\}' src web/src scripts docs/API.md
rg -n 'sk-[A-Za-z0-9]|AKIA[0-9A-Z]{16}|api[_-]?key|secret|password|token' web/dist
```

允许测试中的禁止字段断言、PM 文档中的负向示例和登录密码字段；不允许真实密钥、旧身份字段、业务界面 DB ID。

---

## 6. 交付标准

1. `zhansan` 一个账号可以登录并切换 4 个演示空间。
2. `zhansan@<ouid>` 不再可用作空间登录机制。
3. 注册用户能创建 account/person。
4. 无初始组织用户有明确占位态，不触发 Seller 或 spaces 查询。
5. Header、Sidebar、Main 在组织切换后同步刷新。
6. 默认测试不调用真 LLM。
7. 所有认证响应、JWT、前端状态无 DB 数字 ID。
