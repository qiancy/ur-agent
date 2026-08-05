# FE-13 开发规格：Workspace 统一操作模型与导航修复

> 日期：2026-08-05
> 角色：PM / 产品负责人
> 状态：已按前端工程 review 修订，待下发开发团队
> 背景：测试发现 `liubei@shu.cn / demo123` 登录后侧边栏菜单点击没有明显反应，而 `liuming / demo123` 在 Seller 空间点击正常。该问题暴露出当前前端按 `organization.type` 分叉实现过重，非 ecommerce 空间和 ecommerce 空间的导航行为不一致。

---

## 1. 问题定义

当前前端的主逻辑是：

- ecommerce 空间：Sidebar 点击后切换不同视图组件，例如 `WorkbenchView`、`StockView`、`SummaryView`、`ChatView`。
- 非 ecommerce 空间：Sidebar 点击后仍然渲染同一个 `GenericSpaceView`。

这导致：

- Seller 空间点击侧边栏有明显页面变化。
- 三国/家庭/舰队/个人等通用空间点击侧边栏时，用户感知不到变化。
- 未来每新增一种 workspace 都可能要求定制页面，开发成本不可控。

P0 现象：

```text
账号：liubei@shu.cn
密码：demo123
现象：左侧导航点击后主区没有明显变化
```

结论：

这不是单个账号问题，而是 workspace 操作模型不统一。

---

## 2. 产品目标

建立统一的 workspace 操作模型：

```text
account -> person -> membership -> organization(workspace)
```

前端只认“当前 workspace 有哪些 capabilities”，而不是为每种 `orgType` 手写一套系统。

目标：

1. 所有 workspace 都拥有同一个壳体：Header + Sidebar + Main。
2. Sidebar 由 workspace capabilities 生成。
3. Main 由 view key 渲染对应模块。
4. ecommerce 只是启用了 Seller 扩展能力的 workspace，不是另一套前端系统。
5. 非 ecommerce workspace 至少有通用观察能力，点击每个菜单都必须有明确反馈。

---

## 3. 核心原则

1. **统一壳体**
   所有空间共用 `WorkspaceShell` 思路：Header 负责身份上下文，Sidebar 负责能力导航，Main 负责当前能力页面。

2. **能力驱动，不按类型硬编码页面**
   `orgType` 只用于决定 capabilities，不直接决定 UI 分叉深度。

3. **通用能力默认可用**
   每个 workspace 默认拥有：总览、资源、人员、时间线、多维观察、空间治理。

4. **业务插件可扩展**
   ecommerce 增加：商品、库存、库存流水、经营摘要、入库、出库、Seller AI。

5. **点击必须有反馈**
   任何 Sidebar 菜单点击后，Main 区域必须出现标题、内容、滚动定位或选中状态变化。

6. **不暴露 DB 数字 ID**
   所有能力模块继续只展示业务字段。

---

## 4. 短期 P0 修复

### 4.1 修复范围

先修 `liubei@shu.cn` 点击无反应，不等完整架构改造。

涉及文件：

- `frontend/src/App.vue`
- `frontend/src/views/GenericSpaceView.vue`
- `frontend/src/views/GenericSpaceView.test.ts`
- `frontend/src/App.test.ts`

### 4.2 方案

`GenericSpaceView` 必须接收并响应 `activeSection`：

```ts
defineProps<{
  ouid: string
  activeSection?: 'overview' | 'resources' | 'persons' | 'timeline' | 'flows'
}>()
```

允许两种实现方式，开发团队二选一：

#### 方案 A：单页锚点滚动

- `overview/resources/persons/timeline/flows` 都在同一页。
- 点击 Sidebar 后滚动到对应区块。
- 对应区块增加高亮或标题状态。

优点：改动小。
缺点：用户可能仍觉得“只是滚动”，商业系统感弱。

#### 方案 B：分区渲染

- `GenericSpaceView` 保留顶部概览/雷达卡片。
- 下方只渲染当前 `activeSection` 对应主区。
- 点击 `资源` 就只显示资源观察；点击 `人员` 就只显示人员观察。

优点：行为和 Seller 页面更一致。
缺点：改动略大。

PM 推荐：**方案 B**。

### 4.3 URL 状态绑定（强制）

前端开发 review 的结论采纳：`activeSection/currentView` 不能只存在内存中，必须与 URL 状态绑定，避免刷新后丢失当前页面。

PM 裁决：

- 本期允许并推荐引入 `vue-router`。
- 使用一个统一 Query 参数：`/workbench?view=resources`、`/workbench?view=stock`、`/workbench?view=seller-ai`。
- `App.vue` 初始化时从 `route.query.view` 读取当前 view。
- `SidebarNav` 点击时调用 `router.push({ query: { view } })`。
- 登录成功、组织切换成功、非法 view 降级时调用 `router.replace({ query: { view: defaultView } })`。
- 如果开发团队为了控制依赖不引入 `vue-router`，必须用 History API 实现同等行为；验收仍以 URL Query 是否保持状态为准。

不允许：

- 纯内存 `ref('overview')` 作为唯一状态源。
- URL 显示 `view=stock`，但实际渲染已被内存 clamp 到 `overview`。

### 4.4 GenericSpaceView 数据加载策略（强制）

`GenericSpaceView` 需要按 section 加载并缓存数据，避免非 ecommerce 空间首屏一次性拉取所有数据，也避免每次点击菜单重复请求。

采用现有 API，无需后端改造：

```text
overview  -> GET /spaces/current/overview
resources -> GET /spaces/current/resources
persons   -> GET /spaces/current/persons
timeline  -> GET /spaces/current/timeline
flows     -> 并行读取 resources/persons/timeline/transactions，按已缓存数据复用
```

缓存要求：

- 缓存 key 至少包含 `ouid + section`。
- 同一 `ouid` 下已加载 section 再次切回不得重复请求，除非用户点击刷新。
- 切换组织后必须清空或隔离旧 `ouid` 的页面缓存，避免串数据。
- 第一次进入某 section 时展示局部 loading，不允许整页白屏。
- 401 仍统一触发登出。

`/spaces/current/dashboard` 可以作为后续性能优化或总览聚合接口，但 FE-13 的通用空间主交互不得依赖“每次加载全量 dashboard”。

### 4.5 验收

必须覆盖：

1. `liubei@shu.cn / demo123` 登录后默认进入 `overview`。
2. 点击 `资源`，Main 显示资源观察标题和资源内容。
3. 点击 `人员`，Main 显示人员观察标题和人员内容。
4. 点击 `时间线`，Main 显示时间线标题和事件内容。
5. 点击 `多维观察`，Main 显示多维流向标题和四类流向内容。
6. 点击后 Sidebar active 状态同步。
7. 非 ecommerce 仍不得调用 `/seller/*`。
8. 访问 `/workbench?view=resources` 后刷新浏览器，仍停留在资源观察。
9. 从 ecommerce 的 `/workbench?view=stock` 切到 campaign/family 等不支持 stock 的空间后，URL 被 `router.replace` 修正为 `/workbench?view=overview`。

---

## 5. 中期统一模型：Workspace Registry

### 5.1 新增概念

前端新增 workspace registry：

```text
orgType -> capabilities -> nav items -> view modules
```

建议文件：

```text
frontend/src/workspace/registry.ts
frontend/src/workspace/types.ts
```

### 5.2 类型定义

建议类型：

```ts
import type { Component } from 'vue'

export type WorkspaceCapability =
  | 'overview'
  | 'resources'
  | 'persons'
  | 'timeline'
  | 'flows'
  | 'products'
  | 'stock'
  | 'movements'
  | 'summary'
  | 'seller-ai'
  | 'purchase-in'
  | 'sales-out'
  | 'space-manage'
  | 'space-create'
  | 'space-join'
  | 'space-review'
  | 'space-leave'

export type WorkspaceNavGroup = 'observe' | 'operate' | 'ai' | 'governance'
export type WorkspaceNavKind = 'view' | 'action'
export type GenericSection = 'overview' | 'resources' | 'persons' | 'timeline' | 'flows'
export type WorkspaceViewComponent = Component | (() => Promise<Component>)

export interface WorkspaceNavItem {
  key: WorkspaceCapability
  label: string
  icon: string
  kind: WorkspaceNavKind
  group: WorkspaceNavGroup
  requiresRole?: Array<'owner' | 'admin' | 'member' | 'viewer'>
  component?: WorkspaceViewComponent
  section?: GenericSection
}

export interface WorkspaceDefinition {
  orgType: string
  defaultView: WorkspaceCapability
  capabilities: WorkspaceCapability[]
  navItems: WorkspaceNavItem[]
}
```

组件映射必须进入 registry，不允许继续集中写在 `App.vue` 的 `switch-case` 中。对 `overview/resources/persons/timeline/flows`，可以共享 `GenericSpaceView`，但要通过 `section` 告诉组件渲染哪个区块。

### 5.3 默认能力

所有 workspace 默认拥有：

```text
overview
resources
persons
timeline
flows
space-manage
space-create
space-join
space-review(owner/admin)
space-leave(non-personal)
```

### 5.4 ecommerce 扩展能力

`orgType === "ecommerce"` 增加：

```text
products
stock
movements
summary
seller-ai
purchase-in
sales-out
```

其中 `purchase-in` / `sales-out` 仍可以表现为 modal action，不一定是 Sidebar 菜单项。

### 5.5 personal 空间能力

`orgType === "personal"` 默认能力：

```text
overview
resources
persons
timeline
flows
space-create
space-join
```

限制：

- registry 的 `personal.capabilities` 必须显式排除 `space-leave`。
- 不显示邀请成员，除非后端明确支持 personal 共享。
- 不显示 Seller 专属能力。
- 不允许在 `SidebarNav` 写 `if (orgType === 'personal')`；是否显示退出空间只能由 registry + role/capability 过滤决定。

### 5.6 campaign/family/starship/company 能力

默认全部走通用能力：

```text
overview
resources
persons
timeline
flows
space-manage
space-create
space-join
space-review
space-leave
```

后续可以按业务追加插件，但本期不为每种类型单独写页面。

---

## 6. 统一路由/渲染策略

### 6.1 当前 App.vue 问题

当前 `App.vue` 内部通过：

```ts
if (isEcommerce.value) {
  switch (view) { ... }
}
return GenericSpaceView
```

这会造成 ecommerce 和 non-ecommerce 两套路由行为。

### 6.2 目标策略

统一改成：

```text
currentWorkspaceDefinition = getWorkspaceDefinition(ctx.orgType, ctx.role)
requestedView = route.query.view
currentView = clampToAllowedView(requestedView, currentWorkspaceDefinition)
currentNavItem = currentWorkspaceDefinition.navItems.find(item => item.key === currentView)
currentComponent = currentNavItem.component
```

其中：

- `SidebarNav` 只接收 `navItems`，不直接接收 `orgType`。
- `App.vue` 不手写 ecommerce/non-ecommerce 导航列表。
- 不允许 currentView 停留在当前 workspace 不支持的 view。
- `App.vue` 内的 `if (isEcommerce.value)` 视图渲染分支必须删除，这是 FE-13 重构完成的核心标志。
- `GenericSpaceView` 不再接收 `orgType`，只接收 `ouid` 和 `activeSection`。
- `currentComponent` 来自 `WorkspaceNavItem.component`，不再由 `resolveViewComponent(view)` 的 switch-case 推导。

### 6.3 URL clamp 与组织切换

`clampToAllowedView` 不仅要返回合法 view，还必须修正 URL：

```text
if requestedView is not allowed:
  router.replace({ query: { view: definition.defaultView } })
```

组织切换流程：

1. Header 下拉调用 `POST /auth/switch-organization`，请求体只含 `{ "ouid": "target_ouid" }`。
2. 后端返回新 JWT 与新 workspace ctx。
3. 前端更新 token 与 `unires_ctx`。
4. 根据新 workspace registry clamp 当前 view。
5. 若当前 view 不支持，执行 `router.replace({ query: { view: defaultView } })`。
6. Main 重新加载新 `ouid` 对应数据。

禁止只改内存 `currentView` 而不修正 URL。

### 6.4 组件映射

registry 建议映射：

```text
overview/resources/persons/timeline/flows -> GenericSpaceView + section
products                                  -> ProductsView
stock                                     -> StockView
movements                                 -> MovementsView
summary                                   -> SummaryView
seller-ai                                -> ChatView
space-*                                   -> 对应治理页面
purchase-in/sales-out                     -> action modal
```

说明：

- 本期可以继续让 `GenericSpaceView` 承载 5 个通用 section。
- 但导航点击必须改变 URL Query、Sidebar active 状态和 Main 主标题。
- action 类能力不进入主内容区组件渲染，但仍由 registry 描述，避免在 App/Header/Sidebar 写散落逻辑。

### 6.5 Sidebar 分组展示

`SidebarNav` 必须按 `group` 分组渲染：

```text
observe    -> 观察：总览、资源、人员、时间线、多维观察
operate    -> 经营/操作：商品、库存、流水、摘要、入库、出库
ai         -> AI：Seller AI
governance -> 空间治理：管理、创建、加入、审核、退出
```

视觉要求：

- 组与组之间使用 `border-top` 或 `margin-top` 做轻量分割。
- 组标题可以小字号弱化显示。
- 不允许所有菜单平铺成一长列。
- `requiresRole` 不匹配的菜单直接隐藏。

---

## 7. AI 能力统一

本期不要求每种 workspace 都有可对话 AI。

规则：

- ecommerce：显示 `Seller AI`，调用 `/seller/chat`。
- 非 ecommerce：暂不显示可输入 AI 菜单，除非后端提供安全只读工具。
- Workbench 右侧只显示 AI 摘要，不出现输入框。
- Header 永远不显示 AI button。

后续可扩展：

```text
workspace-ai-readonly
```

但必须有后端工具隔离后再开放。

---

## 8. 测试要求

### 8.1 单元测试

新增或修改：

- `frontend/src/workspace/registry.test.ts`
- `frontend/src/components/SidebarNav.test.ts`
- `frontend/src/App.test.ts`
- `frontend/src/views/GenericSpaceView.test.ts`

必测：

1. ecommerce registry 包含 Seller 能力。
2. personal registry 不包含 Seller 能力，也不包含 `space-leave`。
3. campaign/family/starship/company registry 包含通用观察能力。
4. `SidebarNav` 根据传入 navItems 渲染，不自己判断 `orgType`。
5. 非 ecommerce 点击 `resources/persons/timeline/flows` 后 Main 内容变化。
6. ecommerce 点击 `stock/summary/seller-ai` 后 Main 组件变化。
7. 切换组织后 `currentView` 被 clamp 到目标 workspace 默认 view。
8. `registry.ts` 对 `clampToAllowedView` 做完整边界测试：未知 view、空 view、目标空间不支持 view、role 不满足、personal 不允许 `space-leave`。
9. URL Query 与 `currentView` 双向同步：点击菜单更新 URL，刷新后从 URL 恢复 view。
10. 组织切换导致 view 非法时，调用 `router.replace` 修正 URL。
11. `GenericSpaceView` 对 section 数据按需加载并缓存：重复点击同一 section 不重复请求。
12. `SidebarNav` 按 group 分区渲染，隐藏 role 不匹配菜单。

### 8.2 E2E / 录屏测试

补充 Playwright 用例：

```text
liubei@shu.cn 登录
点击 Sidebar：空间总览 -> 资源 -> 人员 -> 时间线 -> 多维观察
每次 Main 标题或 data-test 必须变化
Network 不得出现 /seller/*
刷新 /workbench?view=resources 后仍停留资源观察
```

保留 `liuming` 用例：

```text
liuming 登录
切换到 ecommerce
点击 Seller 工作台/商品/库存/流水/摘要/Seller AI
每次 Main 视图必须变化
从库存 view 切到火烧新野/家庭空间后，URL 自动降级为 view=overview
```

### 8.3 安全扫描

```bash
rg -n 'person_id|organization_id|resource_id|warehouse_id|transaction_id' frontend/src
rg -n '"pid"|"oid"|\bpid\b|\boid\b' frontend/src
rg -n '/seller/' frontend/src/views/GenericSpaceView.vue frontend/src/api/spaces.ts
```

允许：

- 测试文件中的禁止字段断言。
- 后端内部 SQL 中的 DB 外键。

不允许：

- 前端展示 DB ID。
- 非 ecommerce 视图调用 `/seller/*`。

---

## 9. 实施顺序

### Step 1：P0 修复

引入或等价实现 URL Query 状态，修复 `GenericSpaceView activeSection`，确保 `liubei@shu.cn` 侧边栏点击有反馈。

交付：

- 前端单测通过。
- 手工验证 `liubei@shu.cn / demo123`。
- 刷新 `/workbench?view=resources` 状态保持。

### Step 2：抽出 workspace registry

新增 `frontend/src/workspace/registry.ts` 和测试。

交付：

- `SidebarNav` 不再内置 `orgType` 分支。
- `App.vue` 通过 registry 获取默认 view 和 navItems。
- `WorkspaceNavItem` 直接挂载 view component 或 action 描述。
- personal registry 显式排除 `space-leave`。

### Step 3：统一 App.vue 渲染

将 current view clamp、component resolve 收口。

交付：

- 切换组织时不会保留非法 view。
- seller/non-seller 行为一致。
- 删除 `App.vue` 的 `if (isEcommerce.value)` 视图渲染分支。
- 非法 view clamp 后同步 `router.replace`。
- `GenericSpaceView` 按需加载并缓存 section 数据。

### Step 4：补 E2E

补 `liubei@shu.cn` 和 `liuming` 双账号侧边栏点击测试。

交付：

- Playwright headed 可看见每次菜单点击后的主区变化。

---

## 10. 验收命令

前端：

```bash
cd frontend
npm run test
npm run build
```

重点单测：

```bash
cd frontend
npm run test -- src/workspace/registry.test.ts src/components/SidebarNav.test.ts src/App.test.ts src/views/GenericSpaceView.test.ts
```

Playwright：

```bash
bash tests/playwright/run_recording.sh
```

扫描：

```bash
rg -n 'person_id|organization_id|resource_id|warehouse_id|transaction_id' frontend/src
rg -n '"pid"|"oid"|\bpid\b|\boid\b' frontend/src
rg -n '/seller/' frontend/src/views/GenericSpaceView.vue frontend/src/api/spaces.ts
```

---

## 11. PM 结论

不要为每一种 workspace 定制一套系统。

正确方向是：

```text
统一 workspace 壳体
+ 通用能力模块
+ 按类型启用能力包
+ Seller 深度业务插件
```

本规格先解决 `liubei@shu.cn` 导航点击无反应，再把前端从 `if ecommerce else generic` 收敛为能力驱动模型。这样后续加入家庭、战役、学校、公司、舰队等空间，不需要重新造一个前端系统。
