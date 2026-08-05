# FE-08 开发计划：全局 Header 与组织切换

> 日期：2026-08-03  
> 角色：PM / 产品负责人  
> 状态：下达给开发团队，TDD 先行  
> 结论：PM 选择「写开发计划后让开发团队完成」，不由 PM 直接实现。

## 1. 背景与目标

当前 Vue 工作台已经达到可用的 Seller MVP，但登录后只呈现单一店铺后台，未充分体现 Uni-Resource Agent 的核心差异：一个用户可以在多个组织/业务形态之间切换。

FE-08 目标是在现有 Style A 工作台基础上新增全局 Header，并接通组织切换。用户 `zhansan` 登录后，应能看见当前用户、当前组织、业务形态，并可切换到自己所属的其他组织。切换必须更新 JWT 上下文，不能只做前端假切换。

参考设计：`docs/frontend-demos/be05-style-b-command.html` 的 header 部分，仅吸收结构和信息密度，不改变当前 Vue 工作台主风格。

## 2. PM 决策

| 决策 | 结论 |
| :--- | :--- |
| 是否再做静态 demo | 不需要。当前 Style A 已选定，本轮只补 Header 和组织切换 |
| 是否 PM 直接实现 | 不直接实现。交给开发团队按 TDD 执行 |
| 是否只做前端切换 | 禁止。组织切换必须由后端签发新 JWT |
| 是否接通非 ecommerce 工作台 | 本轮不接通。非 ecommerce 组织只显示空间身份和暂未接入状态 |
| 是否调用通用 `/chat` | 禁止。Header AI 在 ecommerce 下仍只调用 `/seller/chat` |

## 3. 产品形态

登录后的布局调整为：

```text
┌ Sidebar 236 ┬ Header: UA 当前组织/业务形态 | AI 查询框 | 用户/角色 | 切换组织 | 退出 ┐
│ 经营工作台   │                                                                      │
│ 库存         │ main 当前视图                                                         │
│ 库存流水     │                                                                      │
│ 经营摘要     │                                                                      │
│ Seller AI    │                                                                      │
└─────────────┴──────────────────────────────────────────────────────────────────────┘
```

Header 必须显示：

1. 当前组织名称、`ouid`、组织类型。
2. 当前用户名称、`puid`、组织内角色。
3. 组织切换下拉：列出当前用户所属组织。
4. 全局 AI 查询框：文案示例为「查询当前空间的库存、低库存、销售收入、采购支出」。
5. 退出登录按钮。

Sidebar 保留视图导航，但移除底部重复的当前店铺和退出登录信息。

## 4. 后端任务

### 4.1 新增 `GET /auth/me/organizations`

基于当前 Bearer JWT 返回当前用户所属组织列表。

响应只允许业务字段：

```json
[
  {
    "ouid": "taobao_shop_a",
    "name": "淘宝小店 A",
    "type": "ecommerce",
    "role": "owner"
  }
]
```

红线：

1. 不接受 `puid`、`ouid` 查询参数。
2. 不返回 `id`、`person_id`、`organization_id`、`membership_id`、`pid`、`oid`。
3. 不复用会泄漏 `m.id` 的原始 `get_person_memberships()` 响应；必须显式 DTO 收口。

### 4.2 新增 `POST /auth/switch-organization`

请求体：

```json
{
  "ouid": "taobao_shop_a"
}
```

行为：

1. 从当前 JWT 读取 `puid`。
2. 校验当前用户存在。
3. 校验目标组织存在。
4. 校验当前用户是目标组织成员。
5. 成功后签发目标组织上下文的新 JWT。
6. 响应结构复用登录结果，仍不暴露 DB 数字 ID。

非成员切换返回 403；目标组织不存在返回 404；无 JWT 返回 401。

## 5. 前端任务

### 5.1 API 层

在 `web/src/api/seller.ts` 或新增 `web/src/api/auth.ts` 中补充：

```ts
interface UserOrganization {
  ouid: string
  name: string
  type: string
  role: string
}

function myOrganizations(): Promise<UserOrganization[]>
function switchOrganization(ouid: string): Promise<SellerLoginResult>
```

要求：

1. `switchOrganization()` 请求体只能包含 `ouid`。
2. 成功后更新 token。
3. API 测试必须断言请求和响应类型无 DB ID 字段。

### 5.2 Header 组件

新增 `AppHeader.vue`。

Props：

```ts
{
  personName: string
  puid: string
  organizationName: string
  ouid: string
  orgType: string
  role: string
  organizations: UserOrganization[]
}
```

Events：

```ts
switch-organization(ouid: string)
logout()
ask(message: string)
```

交互：

1. 下拉选中当前 `ouid`。
2. 选择其他组织后触发 `switch-organization`。
3. AI 查询框 Enter 或按钮触发 `ask`。
4. 宽度小于 980px 时 Header 允许换行，不得横向溢出。

### 5.3 App 接线

`App.vue` 登录态从单一 `ctx` 扩展为：

```ts
{
  personName: string
  puid: string
  organizationName: string
  ouid: string
  orgType: string
  role: string
}
```

行为：

1. 登录成功后保存完整上下文到 `unires_ctx`。
2. 登录后拉取 `myOrganizations()`。
3. 切换组织成功后替换 token 和 `unires_ctx`，`currentView` 回到 `workbench`。
4. 如果新组织 `type !== "ecommerce"`，主区域显示「该业务形态暂未接入经营工作台」，不调用任何 `/seller/*` API。
5. ecommerce 组织继续显示现有 Seller 工作台。

### 5.4 Header AI

Header AI 查询只在 `orgType === "ecommerce"` 时可用，调用 `/seller/chat`。

默认行为：发送成功后切换到 `ChatView`，并把问题和回答展示在独立 AI 页。若实现复杂度较大，本轮可退化为在 Header 下方显示一次性回答，但仍必须只调用 `/seller/chat`。

## 6. TDD 与验收标准

### 6.1 后端测试

新增或扩展 auth TDD：

1. `GET /auth/me/organizations` 无 JWT 返回 401。
2. 当前用户只能看到自己的组织。
3. 响应不包含 DB 数字 ID 和旧 `pid/oid`。
4. `POST /auth/switch-organization` 成员组织成功返回新 token 和目标组织上下文。
5. 切换到非成员组织返回 403。
6. 请求体带 `organization_id`、`person_id`、`id`、`pid`、`oid` 应返回 422 或被拒绝。

### 6.2 前端测试

新增或扩展 `web/src` 测试：

1. Header 渲染当前用户、组织、业务形态、角色。
2. 登录后拉取组织列表。
3. 切换组织只提交 `ouid`，成功后更新 token 和上下文。
4. 非 ecommerce 组织不调用 `/seller/summary`、`/seller/stock`、`/seller/inventory-movements`。
5. Header AI 只调用 `/seller/chat`，不得调用 `/chat`。
6. 401 仍统一清 token 回登录。

### 6.3 命令验收

```bash
python3 -m compileall src agents/tdd
python3 -m pytest agents/tdd/test_auth_api.py -q
python3 -m pytest agents/tdd/test_seller_chat_api.py agents/tdd/test_seller_ai_tools.py -q
cd web && npm test && npm run build
git diff --check
```

安全扫描：

```bash
rg -n '"pid"|"oid"|\\bpid\\b|\\boid\\b' src web/src agents/tdd docs/API.md
rg -n 'person_id|organization_id|membership_id|resource_id|warehouse_id|transaction_id|campaign_import_id' web/src
rg -n 'sk-[A-Za-z0-9]|AKIA[0-9A-Z]{16}|api[_-]?key|secret|password|token' web/dist
```

上述扫描允许测试中的禁止字段断言和登录密码字段；不允许真实密钥、旧身份字段或业务界面暴露 DB ID。

## 7. 红线

以下任一情况出现，FE-08 不允许合并：

1. 组织切换只是前端状态切换，没有刷新 JWT。
2. 前端或后端响应出现 DB 数字 ID。
3. 前端重新引入 `pid/oid`。
4. ecommerce 组织通过 Header AI 调用了通用 `/chat`。
5. 切到非 ecommerce 组织后仍调用 `/seller/*`。
6. 提交 `node_modules`、`dist`、`tsconfig.tsbuildinfo`。
7. 为兼容旧字段增加 `pid/oid` fallback。

## 8. 实施顺序

1. TDD 写红灯：后端 auth 组织列表/切换 + 前端 Header/切换。
2. 后端实现 `/auth/me/organizations` 和 `/auth/switch-organization`。
3. 前端实现 API 类型和 `AppHeader.vue`。
4. `App.vue` 接入 Header、组织列表、切换逻辑、非 ecommerce 空状态。
5. Header AI 接入 `/seller/chat`。
6. 跑测试、构建、安全扫描、截图验收。

## 9. 视觉验收截图

开发团队完成后必须提供：

1. 1440px：ecommerce 工作台 + Header。
2. 1440px：组织下拉展开。
3. 1440px：切换到非 ecommerce 后的空状态。
4. 1280px：工作台无横向溢出。
5. 移动/窄屏：Header 换行后无遮挡。
