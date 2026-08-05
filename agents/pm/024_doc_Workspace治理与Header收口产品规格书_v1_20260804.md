# ORG-01 产品开发规格书：Workspace 治理与 Header 收口

> 日期：2026-08-04
> 角色：PM / 产品负责人
> 状态：下达开发团队，作为 AUTH-03/ORG-01 实施依据
> 关联：`AUTH-03_默认个人空间与组织治理开发计划.md`、`CR-01_多业务空间参赛版开发规格书.md`

---

## 1. 产品目标

把 Uni-Resource Agent 从“能切换演示空间”升级为“用户可自主管理业务空间”的产品。

核心闭环：

```text
account -> person -> membership -> organization(workspace)
```

用户注册后立即拥有自己的 `personal` workspace；随后可以创建家庭、店铺、项目、舰队等 workspace，也可以通过邀请或申请加入别人的 workspace。Header 只承担身份、当前空间、切换和治理入口，不再放 AI 快捷按钮。

---

## 2. 产品原则

1. `account` 只负责登录凭据。
2. `person` 是业务用户身份。
3. `membership` 是 person 与 workspace 的授权关系。
4. `organization` 就是当前阶段的 workspace 数据边界；MVP 不新增独立 `workspace` 表。
5. 注册后必须有默认 personal workspace，不能出现“暂无业务空间”死状态。
6. 加入别人的 workspace 必须有治理流程，不能凭 `ouid` 直接加入。
7. Header 不承载 AI 入口；AI 留在 Sidebar / 当前业务页面中。
8. 所有对外 API、前端状态、JWT 不暴露 DB 数字 ID。

---

## 3. 用户故事

### US-01 注册即有个人空间

作为新用户，我注册账号后应立即进入自己的个人空间，而不是看到“暂无业务空间”。

验收：

- `POST /auth/register` 成功后返回 `organization.type = personal`。
- personal `ouid` 默认 `{puid}_personal`。
- membership role 为 `owner`。
- 返回 JWT，可直接进入系统。
- 注册请求不再接受 `initial_ouid`。

### US-02 创建新的 workspace

作为用户，我可以创建新的业务空间，例如家庭、店铺、项目或舰队。

验收：

- `POST /spaces` 创建 organization。
- 创建者自动成为 `owner`。
- 成功后返回新 workspace 上下文 JWT。
- 不允许用户手工创建 `personal` 类型；personal 只由注册自动创建。

支持类型：

```text
family / ecommerce / campaign / starship / company
```

### US-03 邀请别人加入 workspace

作为 owner/admin，我可以邀请指定 `puid` 加入当前 workspace。

验收：

- owner/admin 可创建 invite。
- invite 返回 `invite_uid`，不返回 DB ID。
- 受邀人接受 invite 后创建 membership。
- invite 只能由受邀 `puid` 接受。
- personal workspace 不允许邀请成员。

### US-04 申请加入别人的 workspace

作为普通用户，我可以申请加入别人的 workspace。

验收：

- 用户对目标 `ouid` 提交 join request。
- 返回 `request_uid`，不返回 DB ID。
- owner/admin 审批通过后创建 membership。
- 已是成员时返回 409。
- personal workspace 不允许申请加入。

### US-05 退出 workspace

作为普通成员，我可以退出非 personal workspace。

验收：

- member/viewer 可退出普通 workspace。
- personal workspace 不能退出。
- 最后一个 owner 不能退出，必须先转让 owner 或解散空间。

### US-06 移除成员

作为 owner/admin，我可以移除普通成员。

验收：

- owner/admin 可移除 member/viewer。
- 不能移除 personal workspace 成员。
- 不能移除最后 owner。
- owner 只能通过 owner 转让流程处理。

### US-07 转让 owner

作为 owner，我可以把 workspace owner 转让给已有成员。

验收：

- 只有 owner 可转让。
- 新 owner 必须已经是该 workspace 成员。
- 转让后旧 owner 降为 admin。
- 响应只返回 `ouid/new_owner_puid/status` 等业务字段。

### US-08 Header 收口

作为用户，我在 Header 中只需要看清楚身份和空间上下文，不需要重复 AI 入口。

验收：

- 删除 Header 中的 AI button：`/html/body/div/div/header/div[3]/button`。
- 删除 `data-test="header-ai-entry"`。
- `AppHeader` 不再 emit `navigate-ai`。
- `App.vue` 不再监听 Header `@navigate-ai`。
- AI 仍保留在 Sidebar 的 `Seller AI` 导航和业务主区中。
- Header 只保留：品牌、当前空间、空间切换、空间菜单、用户、退出登录。

---

## 4. API 规格

### 4.1 注册

```http
POST /auth/register
```

Request:

```json
{
  "login": "account1",
  "password": "password",
  "name": "张三",
  "puid": "account1"
}
```

Response:

```json
{
  "access_token": "...",
  "token_type": "bearer",
  "person": { "puid": "account1", "name": "张三" },
  "organization": {
    "ouid": "account1_personal",
    "name": "张三的个人空间",
    "type": "personal"
  },
  "membership": { "role": "owner" },
  "organizations": [
    { "ouid": "account1_personal", "name": "张三的个人空间", "type": "personal", "role": "owner" }
  ],
  "requires_organization": false
}
```

规则：

- `login=account1` 合法。
- 不再支持或要求 `puid@ouid`。
- 传 `initial_ouid` 返回 422。
- 注册全流程必须原子化；失败不能留下半创建 account/person。

### 4.2 创建 workspace

```http
POST /spaces
```

Request:

```json
{
  "name": "张三家庭",
  "org_type": "family",
  "ouid": "zhangsan_family",
  "description": "家庭学习和生活空间"
}
```

Response：复用登录上下文 DTO，当前 JWT 切到新 workspace。

### 4.3 邀请

```http
POST /spaces/{ouid}/invites
POST /spaces/invites/accept
```

创建邀请 Request:

```json
{
  "invitee_puid": "lisi",
  "role": "member"
}
```

接受邀请 Request:

```json
{
  "invite_uid": "inv_xxxxxxxx"
}
```

### 4.4 加入申请

```http
POST /spaces/{ouid}/join-requests
POST /spaces/join-requests/approve
```

审批 Request:

```json
{
  "request_uid": "req_xxxxxxxx"
}
```

### 4.5 退出、移除、转让

```http
POST /spaces/leave
POST /spaces/kick
POST /spaces/transfer
```

退出 Request:

```json
{ "ouid": "zhangsan_family" }
```

移除 Request:

```json
{
  "ouid": "zhangsan_family",
  "member_puid": "lisi"
}
```

转让 Request:

```json
{
  "ouid": "zhangsan_family",
  "new_owner_puid": "lisi"
}
```

---

## 5. 前端规格

### 5.1 Header

Header 保留：

- 品牌。
- 当前 workspace 名称。
- workspace 类型 chip。
- `ouid`。
- workspace 切换下拉。
- 空间菜单。
- 用户名、`puid`、role。
- 退出登录。

Header 删除：

- AI button。
- `navigate-ai` emit。
- Header AI 相关测试。

### 5.2 Sidebar

AI 入口保留在 Sidebar：

- ecommerce：保留 `Seller AI`。
- non-ecommerce：不显示 AI；后续有通用 AI 再单独设计。

### 5.3 注册页

注册表单保留：

- login
- password
- name
- puid 可选

删除：

- initial_ouid 输入。
- “暂无业务空间”提示。

注册成功后直接进入 personal workspace。

---

## 6. TDD 验收

后端必须覆盖：

- `account1` 注册成功并创建 personal workspace。
- 注册传 `initial_ouid` 返回 422。
- 注册失败不产生半创建账号。
- 创建 workspace 后创建者为 owner。
- invite 接受成功。
- 非受邀人接受 invite 返回 403。
- join request 审批成功。
- personal workspace 不能邀请/申请/退出/踢人。
- 最后 owner 不能退出或被移除。
- owner 转让成功。
- 所有响应无 DB 数字 ID。

前端必须覆盖：

- Header 不存在 `header-ai-entry`。
- Header 不 emit `navigate-ai`。
- 注册表单不再提交 `initial_ouid`。
- 注册成功进入 personal workspace。
- Sidebar 仍可进入 Seller AI。

---

## 7. 安全红线

1. 不允许恢复 `pid/oid`。
2. 不允许 `account.login` 解析 `ouid`。
3. 不允许注册时凭 `initial_ouid` 加入组织。
4. 不允许 personal workspace 被退出、踢人、邀请加入。
5. 不允许 API/前端/JWT 暴露 DB 数字 ID。
6. 不允许默认测试触发真 LLM。

---

## 8. PM 验收脚本

1. 注册 `account1`。
2. 确认默认进入 `account1_personal`。
3. 创建 `zhangsan_family`。
4. 注册 `lisi`。
5. owner 邀请 `lisi` 加入家庭空间，`lisi` 接受并可切换。
6. `wangwu` 申请加入家庭空间，owner 审批后可切换。
7. member 退出家庭空间成功。
8. personal 空间退出失败。
9. 最后 owner 退出失败。
10. Header 无 AI button，Seller AI 仍在 Sidebar。
