# FE-08 产品讨论：Header、业务空间与组织治理

> 日期：2026-08-03
> 角色：PM / 产品负责人
> 状态：产品讨论结论，供 FE-08 调整与后续 FE-09 拆分
> 背景：开发团队已将前端改为「顶部 AppHeader 通栏 + 下部 SidebarNav/Main」结构。

## 1. PM 结论

`AppHeader` 应该优先承担 **多上下文空间识别与切换**，不应该成为第二个完整 AI 聊天入口。

当前 Header 已经解决了「顶部通栏」和「组织切换」的基础结构，但产品重心还需要调整：

1. Header 的主任务是回答：**我是谁、我在哪个业务空间、我还能切到哪里、我对这个空间有什么权限**。
2. Header 可以提供「进入 AI」快捷入口，但不建议放完整 AI 输入框和「问 AI」按钮。
3. 组织治理入口应放在 Header 里，但 MVP 先做链接/占位，不一次性实现完整审批后台。
4. Seller 业务空间必须补「商品管理」。没有商品主数据管理，库存系统是不完整的。
5. 概念模型建议调整为：`account -> person -> membership -> organization(space) -> workspace(app/capability)`。
6. 登录账号不再携带组织上下文；`zhansan@taobao_shop_a` 这类多账号方式应收口为一个账号 `zhansan`，再通过 membership 切换空间。

## 2. Header 应包含的功能

### 2.1 必须包含

1. 当前用户：
   - `person.name`
   - `puid`
   - 可选：系统角色 `system_role`

2. 当前业务空间：
   - 组织名称
   - `ouid`
   - 组织类型 / 业务形态，例如 `ecommerce`、`family`、`campaign`
   - 当前用户在该组织内的角色 `membership.role`

3. 业务空间切换：
   - 下拉列出当前用户拥有 membership 的组织。
   - 每项显示：组织名 + 类型 + 角色。
   - 切换后必须调用后端重新签发 JWT，不能只改前端状态。

4. 空间治理入口：
   - 「管理空间」：当前组织设置、成员、角色。
   - 「加入空间」：输入邀请码或申请加入。
   - 「申请审核」：owner/admin 可见。
   - 「退出空间」：普通成员可见；owner 的退出需要后续定义转让或解散规则。

5. 退出登录。

### 2.2 暂不建议放在 Header 的内容

1. 大型经营指标：应留在工作台主区。
2. 入库/出库按钮：这是 Seller 业务操作，应留在 Seller 工作台。
3. 完整 AI 输入框：会和主区 AI 模块重复，分散用户注意力。
4. 长文案说明：Header 应保持紧凑。

## 3. Header AI 入口判断

当前 Header 有 AI 输入框和「问 AI」按钮，同时主区工作台右侧和独立 `Seller AI` 页也有 AI 模块。这个重复不合适。

PM 建议：

1. MVP 立即调整：移除 Header 的完整 AI 输入框和「问 AI」按钮。
2. Header 只保留一个小入口：「AI」或「打开 AI」，点击后切换到当前空间对应的 AI 页。
3. 在 ecommerce 空间下，AI 页继续调用 `/seller/chat`。
4. 在非 ecommerce 空间下，本阶段显示「该业务空间暂未接入 AI」，不要调用通用 `/chat`。

原因：

1. Header 是全局上下文层，不应承载具体业务对话。
2. Seller 工作台已有 AI 侧栏和独立 AI 页，重复输入框会让用户不知道该在哪里问。
3. 未来如果要做 Command Palette，可以再把 Header 中部升级为统一命令栏，但那是下一阶段能力，不应混入当前 MVP。

## 4. 组织治理功能分期

### 4.1 MVP 可做

1. Header 展示「管理空间」「加入空间」「审核申请」入口。
2. 暂无后端能力时，入口可进入占位页，说明功能即将开放。
3. `owner/admin` 才显示「审核申请」和完整「管理空间」。
4. 普通成员显示「申请加入其他空间」「退出当前空间」。

### 4.2 下一阶段做

1. 空间邀请链接 / 邀请码。
2. 加入申请表。
3. owner/admin 审核通过或拒绝。
4. 成员角色调整。
5. 成员退出空间。
6. owner 转让和空间解散。

### 4.3 暂不做

1. 复杂 RBAC 权限矩阵。
2. 多级组织架构。
3. 企业 SSO。
4. 跨组织数据汇总。

## 5. Seller 空间缺口：商品管理

当前 Seller 空间已经有库存、流水、摘要、入库、出库、AI 查询，但缺少商品主数据管理。

这会造成两个产品问题：

1. 用户不知道系统里有哪些商品，只能在入库/出库时手填 `product_uid`。
2. 库存系统缺少「商品档案」入口，不像可售卖产品。

建议新增 Seller「商品」视图，优先级应高于继续扩展 Header AI。

MVP 商品管理应包含：

1. 商品列表：
   - `product_uid`
   - 单位
   - 状态 active/inactive
   - 当前库存总数
   - 库位数

2. 新增商品：
   - `product_uid`
   - 单位
   - 可选描述

说明：`product_uid` 即商品业务名/编号，本版不新增独立商品 `name` 字段。

3. 停用商品：
   - 不删除历史流水。
   - 停用后不进入默认入库/出库选择。

4. 入库/出库表单优化：
   - `product_uid` 改成可搜索选择。
   - 仍允许输入新商品需另行确认，避免错别字创建脏数据。

## 6. 业务模型建议

用户提出的 `account - membership - organization - workspace` 方向是对的，但需要保留 `person` 这一层。

PM 推荐模型：

```text
account -> person -> membership -> organization(space) -> workspace(app/capability)
```

### 6.1 各层职责

| 层 | 含义 | 示例 | 说明 |
| :--- | :--- | :--- | :--- |
| `account` | 登录凭据 | `zhansan`、手机号、邮箱 | 管认证、密码、账号状态、系统级角色；不承载组织上下文 |
| `person` | 真实用户/业务人 | 张三，`puid=zhansan` | 同一个人可以加入多个组织 |
| `membership` | 人与组织的关系 | 张三是淘宝小店 A 的 owner | 管组织内角色、加入状态、权限 |
| `organization` / `space` | 数据隔离边界 | 淘宝小店 A、张三家庭、火烧新野战役 | 当前系统已有 `organization`，它就是业务空间的数据边界 |
| `workspace` / `app` | 业务应用形态 | Seller、Family、Campaign | 决定进入哪个工作台、能用哪些工具 |

### 6.2 为什么不建议 membership 直接挂 account

1. 一个自然人可能有多个登录账号。
2. 账号是认证实体，成员关系是业务授权实体，混在一起会限制扩展。
3. 当前数据库已有 `account.person_id` 和 `membership.person_id + organization_id`，继续沿用更稳。

### 6.3 organization 与 workspace 的关系

短期：继续使用 `organization.type` 表示 workspace 类型。

示例：

```text
taobao_shop_a.type = ecommerce -> Seller Workspace
zhangsan_family.type = family -> Family Workspace
fire_xinye.type = campaign -> Campaign Workspace
```

中期：如果一个组织需要挂多个业务应用，再引入 `workspace` 表或 `organization_workspace` 表。

MVP 不建议现在新增 workspace 表，避免扩大后端模型和迁移范围。

### 6.4 account.login 与 person.puid 的处理

不建议把 `account.login` 和 `person.puid` 做物理归并，也不建议继续用多账号表达空间。

PM 决策：

1. `account.login` 是登录凭据，唯一；它回答“用什么账号登录系统”。
2. `person.puid` 是业务人员标识，唯一；它回答“这个账号对应哪个业务人”。
3. `membership` 回答“这个业务人能进入哪些组织空间、在空间内是什么角色”。
4. MVP 演示用户允许二者相同：`account.login=zhansan`、`person.puid=zhansan`。
5. 不再创建 `zhansan@fire_xinye_shu`、`zhansan@zhangsan_family`、`zhansan@deep_space_fleet`、`zhansan@zhansan_shop` 四个账号。
6. 如果未来允许邮箱或手机号作为 `account.login`，仍不得从 login 中解析 `ouid`；空间切换只能调用 `/auth/switch-organization`。

用户注册的基本流程应支持：

1. 先注册 `account + person`。
2. 可选加入一个初始组织；公共注册默认角色只能是 `member`。
3. 未加入组织时进入“暂无业务空间”的占位页，引导后续创建空间或申请加入。
4. 注册、登录、组织切换响应都不得返回 DB 数字 ID。

## 7. 建议开发调整

### 7.1 FE-08 立即调整

1. Header 保留当前用户、当前空间、空间切换。
2. Header 去掉完整 AI 输入框和「问 AI」按钮。
3. Header 增加「AI」小入口，点击切到 `Seller AI` 页。
4. Header 增加「空间」菜单，包含：
   - 管理空间
   - 加入空间
   - 审核申请
   - 退出空间
5. 对未实现的空间治理能力，先跳转到占位视图，不接后端写操作。
6. 登录页占位应改为单账号示例 `zhansan`，不再提示 `puid@ouid`。

### 7.2 后续新增 FE-09

主题：Seller 商品管理。

目标：补齐商品主数据，让 Seller 工作台从「库存流水工具」变成「可售卖的经营系统」。

首批任务：

1. 新增商品视图。
2. 新增商品列表 API 或复用安全的 Seller 商品 API。
3. 新增商品创建表单。
4. 入库/出库表单使用商品选择器。
5. 商品停用不影响历史流水。

## 8. 验收标准

1. 登录后 Header 第一眼能看出：用户、当前空间、空间类型、角色。
2. 用户能从 Header 切换到其他有权限的空间。
3. Header 不出现重复 AI 输入框。
4. 点击 Header 的 AI 入口只导航，不直接发起 AI 请求。
5. 非 ecommerce 空间不调用 `/seller/*`。
6. 前端不出现 DB 数字 ID、旧 `pid/oid`。
7. 空间治理入口存在，但未实现写操作时必须明确是占位状态。

## 9. PM 最终建议

FE-08 不再继续扩展 Header AI。Header 要回到产品核心：多空间上下文、身份、权限、切换、治理入口。

下一阶段优先做 Seller 商品管理，而不是继续给 Header 加更多业务操作。
