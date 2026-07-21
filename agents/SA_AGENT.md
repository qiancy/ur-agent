# System Analyst Agent - SA规范文档

> **审核状态**: ✅ 已审核  
> **最后更新**: 2026-07-21  
> **版本**: 1.0

## 📋 目录
1. [SA角色定位](#sa角色定位)
2. [建模工作规范](#建模工作规范)
3. [需求分析流程](#需求分析流程)
4. [UML建模规范](#uml建模规范)
5. [架构设计规范](#架构设计规范)
6. [SA与PM协作](#sa与pm协作)

---

## SA角色定位

### 角色职责
SA（System Analyst）负责系统的建模、分析和架构设计工作，基于 `/agents/pm/ai-modeling.md` 的规范开展工作：

| 职责 | 描述 |
|------|------|
| **需求分析** | 分析用户需求、业务流程、功能规格 |
| **系统建模** | 创建UML模型、类图、序列图、状态图 |
| **架构设计** | 设计系统架构、技术方案、数据模型 |
| **文档编写** | 编写需求文档、设计文档、架构文档 |
| **技术评审** | 参与代码评审、方案评审、质量评审 |

### SA工作范围

```
┌─────────────────────────────────────────────────────────────┐
│                    SA工作范围                                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌─────────────────────────────────────────────────────┐    │
│   │                  需求分析阶段                          │    │
│   │   • 用户需求调研                                       │    │
│   │   • 业务流程分析                                       │    │
│   │   • 功能规格定义                                       │    │
│   │   • 需求文档编写                                       │    │
│   └─────────────────────────────────────────────────────┘    │
│                              │                               │
│                              ▼                               │
│   ┌─────────────────────────────────────────────────────┐    │
│   │                  系统建模阶段                          │    │
│   │   • UML建模（用例图、类图、序列图）                   │    │
│   │   • 业务流程建模                                       │    │
│   │   • 数据建模                                           │    │
│   │   • 状态机建模                                         │    │
│   └─────────────────────────────────────────────────────┘    │
│                              │                               │
│                              ▼                               │
│   ┌─────────────────────────────────────────────────────┐    │
│   │                架构设计阶段                            │    │
│   │   • 系统架构设计                                       │    │
│   │   • 技术方案制定                                       │    │
│   │   • 数据库设计                                         │    │
│   │   • API接口设计                                        │    │
│   └─────────────────────────────────────────────────────┘    │
│                              │                               │
│                              ▼                               │
│   ┌─────────────────────────────────────────────────────┐    │
│   │                实施支持阶段                            │    │
│   │   • 技术方案讲解                                       │    │
│   │   • 代码评审参与                                       │    │
│   │   • 问题答疑                                           │    │
│   └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 建模工作规范

### 建模原则

#### 1. 一致性原则
```
所有建模文档必须遵循以下规范：
- 统一的术语定义（见术语表）
- 统一的符号表示（符合UML标准）
- 统一的文档格式（PlantUML模板）
```

#### 2. 完整性原则
```
建模必须覆盖：
- 所有核心业务流程
- 所有数据实体
- 所有系统交互
- 所有约束条件
```

#### 3. 可验证性原则
```
建模结果必须可验证：
- 有明确的验证标准
- 有可执行的测试用例
- 有可追溯的需求链接
```

### PlantUML建模规范

#### 1. 用例图规范

```plantuml
@startuml
' 项目：Uni-Resource Agent
' 模块：业务用例图
' 版本：1.0
' 日期：2026-07-21

title 系统用例图 - Uni-Resource Agent

actor 用户 as User
actor 系统 as System

rectangle "系统边界" {
    usecase "查询资产" as UC1
    usecase "转移资产" as UC2
    usecase "记录交易" as UC3
    usecase "管理提醒" as UC4
    usecase "知识搜索" as UC5
    usecase "切换上下文" as UC6
}

User --> UC1
User --> UC2
User --> UC3
User --> UC4
User --> UC5
User --> UC6

System .> UC1
System .> UC2
System .> UC3
System .> UC4
System .> UC5
System .> UC6

@enduml
```

#### 2. 类图规范

```plantuml
@startuml
' 项目：Uni-Resource Agent
' 模块：核心类图
' 版本：1.0
' 日期：2026-07-21

title 核心类图 - Uni-Resource Agent

' 实体类
class Organization {
    +id: Integer
    +name: String
    +type: String
    +description: String
    +context_id: String
    +create(): void
    +update(): void
    +delete(): void
}

class Personnel {
    +id: Integer
    +name: String
    +birth_date: Date
    +health_reminders: Text
    +add_reminder(reminder: String): void
    +check_health(): HealthStatus
}

class Asset {
    +id: Integer
    +org_id: Integer
    +name: String
    +type: String
    +status: String
    +quantity: Integer
    +register(): void
    +transfer(target_org: Integer, quantity: Integer): void
}

class PhysicalAsset {
    +warehouse: String
    +location: String
    +store(location: String): void
    +retrieve(location: String): void
}

class VirtualAsset {
    +content: String
    +embedding: Vector
    +store_content(content: String): void
    +search_embedding(query: String): List<Asset>
}

class Transaction {
    +id: Integer
    +from_party_id: Integer
    +to_party_id: Integer
    +amount: Decimal
    +category: String
    +description: String
    +timestamp: DateTime
    +record(): void
    +query(date_start: DateTime, date_end: DateTime): List<Transaction>
}

class Party {
    +id: Integer
    +org_id: Integer
    +name: String
    +role: String
    +description: String
    +register(): void
}

class User {
    +id: Integer
    +name: String
    +email: String
    +context_id: String
    +login(): Boolean
    +logout(): void
}

class Context {
    +id: String
    +name: String
    +user_id: Integer
    +type: String
    +create(): void
    +switch(context_id: String): void
}

' 关系
Organization "1" *-- "0..*" Personnel : owns >
Organization "1" *-- "0..*" Asset : manages >
Organization "1" *-- "0..*" Transaction : records >
Organization "1" *-- "0..*" Party : has >

Personnel --> Membership : "is member of"
Asset --> PhysicalAsset : "is a"
Asset --> VirtualAsset : "is a"
Transaction --> Party : "from"
Transaction --> Party : "to"

User "1" *-- "0..*" Context : "uses"

@enduml
```

#### 3. 序列图规范

```plantuml
@startuml
' 项目：Uni-Resource Agent
' 模块：资产转移序列图
' 版本：1.0
' 日期：2026-07-21

title 资产转移序列图

actor 用户
participant "UI" as UI
participant "Agent" as Agent
participant "AuthService" as Auth
participant "AssetService" as Asset
participant "DB" as Database

用户 -> UI: 输入资产转移请求
UI -> Agent: transfer_asset(asset_id, from_org, to_org, quantity)
Agent -> Auth: validate_user(context_id)
Auth --> Agent: user_id, is_valid=true
Agent -> Asset: check_asset_permission(asset_id, user_id)
Asset --> Agent: has_permission=true
Agent -> Asset: query_asset(asset_id)
Asset --> Agent: asset_info
Agent -> Asset: update_asset(asset_id, from_org, to_org, quantity)
Asset -> Database: UPDATE assets SET org_id=to_org WHERE id=asset_id
Database --> Asset: success
Asset --> Agent: transfer_result=success
Agent --> UI: transfer_result=success
UI --> 用户: 显示转移成功

@enduml
```

#### 4. 状态机图规范

```plantuml
@startuml
' 项目：Uni-Resource Agent
' 模块：订单状态机
' 版本：1.0
' 日期：2026-07-21

title 订单状态机

[*] --> Pending : 创建订单
Pending --> Processing : 验证通过
Processing --> Packed : 准备完成
Packed --> Shipping : 发货确认
Shipping --> Delivered : 签收确认
Delivered --> Completed : 确认完成

Pending --> Cancelled : 用户取消
Processing --> Cancelled : 用户取消
Packed --> Cancelled : 用户取消
Shipping --> Cancelled : 用户取消

Processing --> Pending : 验证失败
Packed --> Processing : 准备未完成

Completed --> [*]
Cancelled --> [*]

@enduml
```

### 建模模板

#### 用例规约模板

```markdown
## 用例规约

### 用例名称
查询资产

### 用例编号
UC-ASSET-001

### 优先级
高

### 执行者
用户

### 前置条件
- 用户已登录系统
- 用户拥有查询权限

### 后置条件
- 系统返回符合条件的资产列表
- 若无结果，返回空列表

### 基本路径
1. 用户进入资产查询界面
2. 用户输入查询条件（名称、类型、仓库等）
3. 系统验证查询条件
4. 系统执行查询
5. 系统返回查询结果
6. 用户查看查询结果

### 扩展路径
1a. 用户未登录
   - 系统提示用户登录
   - 返回路径1

1b. 用户无查询权限
   - 系统提示权限不足
   - 返回路径1

2a. 查询条件无效
   - 系统提示无效条件
   - 返回路径2

2b. 查询无结果
   - 系统提示无结果
   - 返回路径5

### 异常路径
1. 数据库连接失败
   - 系统提示连接错误
   - 记录错误日志
   - 返回路径5

2. 查询超时
   - 系统提示超时
   - 记录错误日志
   - 返回路径5

### 业务规则
- 查询结果按创建时间倒序排列
- 默认显示最近100条记录
- 支持分页查询
- 查询条件支持模糊匹配

### 限制
- 单次查询结果不超过1000条
- 查询条件不能为空

### 关联用例
- 创建资产（UC-ASSET-002）
- 转移资产（UC-ASSET-003）
- 删除资产（UC-ASSET-004）

### 修改记录
| 版本 | 日期 | 修改内容 | 修改人 |
|------|------|---------|--------|
| 1.0 | 2026-07-21 | 初始版本 | SA |
```

#### 类图规范

```plantuml
@startuml
' 项目：Uni-Resource Agent
' 模块：数据模型类图
' 版本：1.0
' 日期：2026-07-21

title 数据模型类图

' 基类
class Base {
    +id: Integer
    +created_at: DateTime
    +updated_at: DateTime
    +save(): void
    +delete(): void
}

' 实体类
class Organization {
    +name: String
    +type: String
    +description: String
    +context_id: String
}

class Personnel {
    +name: String
    +birth_date: Date
    +health_reminders: Text
}

class Asset {
    +name: String
    +type: String
    +status: String
    +quantity: Integer
}

class PhysicalAsset {
    +warehouse: String
    +location: String
}

class VirtualAsset {
    +content: String
    +embedding: Vector
}

class Transaction {
    +from_party_id: Integer
    +to_party_id: Integer
    +amount: Decimal
    +category: String
    +description: String
}

class Party {
    +name: String
    +role: String
    +description: String
}

class Context {
    +name: String
    +type: String
}

' 关系
Organization "1" *-- "0..*" Personnel : "has"
Organization "1" *-- "0..*" Asset : "manages"
Organization "1" *-- "0..*" Transaction : "records"
Organization "1" *-- "0..*" Party : "has"

Personnel "m" -- "1" Membership : "belongs to"
Asset "1" -- "1" PhysicalAsset : "is a"
Asset "1" -- "1" VirtualAsset : "is a"
Transaction "1" --> "1" Party : "from"
Transaction "1" --> "1" Party : "to"

User "1" *-- "0..*" Context : "uses"

@enduml
```

---

## 需求分析流程

### 需求获取流程

```
┌─────────────────────────────────────────────────────────────┐
│                    需求获取流程                                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌─────────────┐                                           │
│   │ 需求收集     │                                           │
│   │ • 用户访谈  │                                           │
│   │ • 问卷调查  │                                           │
│   │ • 文档分析  │                                           │
│   └──────┬──────┘                                           │
│          ▼                                                   │
│   ┌─────────────┐                                           │
│   │ 需求整理     │                                           │
│   │ • 分类汇总  │                                           │
│   │ • 去重合并  │                                           │
│   │ • 补充完善  │                                           │
│   └──────┬──────┘                                           │
│          ▼                                                   │
│   ┌─────────────┐     ┌─────────────┐                      │
│   │  初步分析    │────▶│   项目经理   │                      │
│   └─────────────┘     │   评审      │                      │
│                       └──────┬──────┘                      │
│                              ▼                              │
│                 ┌─────────────┐                            │
│                 │  通过评审？   │                            │
│                 └──────┬──────┘                            │
│                        │                                     │
│              ┌─────────┴─────────┐                          │
│              ▼                   ▼                          │
│        ┌─────────────┐     ┌─────────────┐                  │
│        │    是        │     │    否        │                  │
│        └──────┬──────┘     └──────┬──────┘                  │
│               │                   │                         │
│               ▼                   ▼                         │
│      ┌─────────────┐     ┌─────────────┐                  │
│      │  业务建模   │     │  补充调研    │                  │
│      │  (流程图)   │     │  (补充访谈)   │                  │
│      └──────┬──────┘     └──────┬──────┘                  │
│             │                   │                           │
│             └─────────┬─────────┘                           │
│                       ▼                                     │
│              ┌─────────────┐                                │
│              │  需求规格说明书 │                                │
│              │  (SRS)       │                                │
│              └─────────────┘                                │
└─────────────────────────────────────────────────────────────┘
```

### 需求确认流程

```markdown
## 需求确认清单

### 功能需求确认
- [ ] 用户能创建/修改/删除组织
- [ ] 用户能添加/修改/删除人员
- [ ] 用户能查询/转移/记录资产
- [ ] 用户能记录/查询交易
- [ ] 用户能设置/查询提醒
- [ ] 用户能搜索知识
- [ ] 系统支持多上下文切换

### 性能需求确认
- [ ] API响应时间 < 500ms
- [ ] 并发支持 > 100用户
- [ ] 数据查询 < 10秒

### 安全需求确认
- [ ] 用户身份验证
- [ ] 权限控制
- [ ] 数据隔离
- [ ] 敏感信息加密

### 业务流程确认
- [ ] 资产查询流程
- [ ] 资产转移流程
- [ ] 交易记录流程
- [ ] 多上下文切换流程

### 确认方式
1. 评审会议
2. 原型演示
3. 用户确认签字
```

---

## UML建模规范

### UML图类型及使用场景

| 图类型 | 用途 | 使用阶段 |
|--------|------|---------|
| 用例图 | 功能需求分析 | 需求分析 |
| 类图 | 系统静态结构 | 架构设计 |
| 序列图 | 对象交互流程 | 详细设计 |
| 状态机图 | 对象状态变化 | 详细设计 |
| 活动图 | 业务流程 | 需求分析 |
| 组件图 | 系统组件关系 | 架构设计 |
| 部署图 | 系统部署结构 | 架构设计 |

### UML建模指南

#### 1. 用例图建模指南

```plantuml
@startuml
' 用例图建模指南

' 执行者
actor 用户
actor 管理员
actor 系统

' 用例
usecase "登录系统" as UC1
usecase "创建组织" as UC2
usecase "查询资产" as UC3
usecase "转移资产" as UC4
usecase "记录交易" as UC5
usecase "管理提醒" as UC6
usecase "知识搜索" as UC7
usecase "切换上下文" as UC8

' 关系
用户 --> UC1
用户 --> UC2
用户 --> UC3
用户 --> UC4
用户 --> UC5
用户 --> UC6
用户 --> UC7
用户 --> UC8

管理员 .> 用户 : includes
系统 .> UC1
系统 .> UC2

@enduml
```

#### 2. 类图建模指南

```plantuml
@startuml
' 类图建模指南

' 类定义
class User {
    +id: Integer
    +name: String
    +email: String
    +context_id: String
    +login(): Boolean
    +logout(): void
}

class Organization {
    +id: Integer
    +name: String
    +type: String
    +context_id: String
    +create(): void
    +update(): void
}

class Asset {
    +id: Integer
    +org_id: Integer
    +name: String
    +type: String
    +status: String
    +quantity: Integer
    +register(): void
    +transfer(): void
}

class Transaction {
    +id: Integer
    +from_party_id: Integer
    +to_party_id: Integer
    +amount: Decimal
    +category: String
    +description: String
    +record(): void
    +query(): List<Transaction>
}

' 关系定义
' 聚合关系
Organization "1" *-- "0..*" Asset : owns >

' 关联关系
Transaction "1" --> "1" Party : from_party
Transaction "1" --> "1" Party : to_party

' 继承关系
class PhysicalAsset extends Asset {
    +warehouse: String
    +location: String
}

class VirtualAsset extends Asset {
    +content: String
    +embedding: Vector
}

' 依赖关系
class AssetService {
    +query_assets(org_id: Integer): List<Asset>
    +transfer_asset(asset_id: Integer, to_org: Integer): void
}

AssetService --> Asset : uses

@enduml
```

#### 3. 序列图建模指南

```plantuml
@startuml
' 序列图建模指南

' 激活条
actor 用户
participant "Web" as Web
participant "Agent" as Agent
participant "AuthService" as Auth
participant "AssetService" as Asset
participant "DB" as Database

' 交互流程
用户 -> Web: 输入资产查询请求
activate Web
Web -> Agent: query_assets(org_id, name, warehouse)
activate Agent
Agent -> Auth: validate_user(context_id)
activate Auth
Auth --> Agent: user_id, is_valid=true
deactivate Auth
Agent -> Asset: check_permission(asset_id, user_id)
activate Asset
Asset -> Database: SELECT * FROM assets WHERE org_id = ?
activate Database
Database --> Asset: asset_list
deactivate Database
Asset --> Agent: has_permission=true
deactivate Asset
Agent --> Web: asset_list
deactivate Agent
Web --> 用户: 返回查询结果
deactivate Web

@enduml
```

#### 4. 状态机图建模指南

```plantuml
@startuml
' 状态机图建模指南

[*] --> Pending : 创建
Pending --> Processing : 验证通过
Processing --> Completed : 处理完成
Completed --> [*]

Pending --> Failed : 验证失败
Processing --> Failed : 处理失败
Failed --> [*]

Processing --> Pending : 重新处理

@enduml
```

---

## 架构设计规范

### 系统架构图

```plantuml
@startuml
' 项目：Uni-Resource Agent
' 模块：系统架构图
' 版本：1.0
' 日期：2026-07-21

title 系统架构图

' 用户层
rectangle "用户层" {
    rectangle "Web UI (Gradio)" as UI
    rectangle "Mobile App" as Mobile
}

' 应用层
rectangle "应用层" {
    rectangle "FastAPI Backend" as Backend
    rectangle "Agent (LangChain)" as Agent
    rectangle "Auth Service" as Auth
}

' 数据层
rectangle "数据层" {
    rectangle "PostgreSQL" as DB
    rectangle "ChromaDB" as VectorDB
}

' AI层
rectangle "AI层" {
    rectangle "Qwen3-Coder (AMD)" as LLM
    rectangle "BGE Embedding" as Embedding
}

' 外部服务
rectangle "外部服务" {
    rectangle "ModelScope" as ModelScope
}

' 关系
UI --> Backend : HTTP/REST
Mobile --> Backend : HTTP/REST
Backend --> Agent : 调用
Backend --> Auth : 调用
Agent --> LLM : 推理
Agent --> Embedding : 嵌入
Backend --> DB : JDBC
Backend --> VectorDB : API
LLM --> ModelScope : 模型下载

@enduml
```

### 数据库设计规范

#### 1. 数据库表设计

```sql
-- 组织表
CREATE TABLE organization (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    description TEXT,
    context_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_context_id (context_id),
    INDEX idx_type (type)
);

-- 人员表
CREATE TABLE personnel (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    birth_date DATE,
    health_reminders TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 成员关系表
CREATE TABLE membership (
    id SERIAL PRIMARY KEY,
    person_id INTEGER NOT NULL,
    org_id INTEGER NOT NULL,
    role VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (person_id) REFERENCES personnel(id),
    FOREIGN KEY (org_id) REFERENCES organization(id),
    INDEX idx_org_person (org_id, person_id)
);

-- 资产基表
CREATE TABLE asset (
    id SERIAL PRIMARY KEY,
    org_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'available',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (org_id) REFERENCES organization(id),
    INDEX idx_org_type (org_id, type)
);

-- 物理资产表
CREATE TABLE physical_asset (
    id INTEGER PRIMARY KEY,
    quantity INTEGER NOT NULL DEFAULT 1,
    warehouse VARCHAR(100),
    location VARCHAR(100),
    FOREIGN KEY (id) REFERENCES asset(id) ON DELETE CASCADE
);

-- 虚拟资产表
CREATE TABLE virtual_asset (
    id INTEGER PRIMARY KEY,
    content TEXT,
    embedding VECTOR(768),
    FOREIGN KEY (id) REFERENCES asset(id) ON DELETE CASCADE
);

-- 参与方表
CREATE TABLE party (
    id SERIAL PRIMARY KEY,
    org_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (org_id) REFERENCES organization(id)
);

-- 交易表
CREATE TABLE transaction (
    id SERIAL PRIMARY KEY,
    from_party_id INTEGER NOT NULL,
    to_party_id INTEGER NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    category VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_party_id) REFERENCES party(id),
    FOREIGN KEY (to_party_id) REFERENCES party(id)
);
```

#### 2. 数据库索引设计

```sql
-- 组织相关索引
CREATE INDEX idx_organization_context ON organization(context_id);
CREATE INDEX idx_organization_type ON organization(type);
CREATE INDEX idx_organization_name ON organization(name);

-- 资产相关索引
CREATE INDEX idx_asset_org_type ON asset(org_id, type);
CREATE INDEX idx_asset_status ON asset(status);
CREATE INDEX idx_asset_name ON asset(name);

-- 交易相关索引
CREATE INDEX idx_transaction_from ON transaction(from_party_id);
CREATE INDEX idx_transaction_to ON transaction(to_party_id);
CREATE INDEX idx_transaction_category ON transaction(category);
CREATE INDEX idx_transaction_date ON transaction(created_at);

-- 成员相关索引
CREATE INDEX idx_membership_org ON membership(org_id);
CREATE INDEX idx_membership_person ON membership(person_id);
```

---

## SA与PM协作

### 协作流程

```
┌─────────────────────────────────────────────────────────────┐
│                  SA与PM协作流程                                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   PM负责：                   SA负责：                          │
│   ──────────               ──────────                        │
│   • 项目计划制定           • 需求分析                         │
│   • 进度跟踪               • 系统建模                         │
│   • 质量检查               • UML建模                          │
│   • 团队协调               • 架构设计                         │
│   • 交付管理               • 技术方案制定                     │
│                                                              │
│   └─────► 协作点 ◄─────┘                                     │
│           │                                                  │
│           ▼                                                  │
│   ┌─────────────────────────────────────────┐                │
│   │         协作成果                          │                │
│   │   • 需求规格说明书 (SRS)                │                │
│   │   • UML模型 (PlantUML)                  │                │
│   │   • 架构设计文档                        │                │
│   │   • 技术方案文档                        │                │
│   └─────────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

### 协作检查点

| 检查点 | PM职责 | SA职责 | 交付物 |
|--------|--------|--------|--------|
| 需求评审 | 组织评审会 | 提供需求分析 | 需求规格说明书 |
| 架构评审 | 评估可行性 | 提供架构设计 | 架构设计文档 |
| 方案评审 | 评估技术方案 | 提供详细方案 | 技术方案文档 |
| 质量检查 | 组织检查 | 提供检查结果 | 质量报告 |

### 沟通机制

```markdown
## SA与PM沟通机制

### 1. 每日站会
- 时间：每天上午10:00
- 时长：15分钟
- 内容：
  - 昨日完成工作
  - 今日计划工作
  - 遇到的问题

### 2. 评审会议
- 需求评审：每周一次
- 架构评审：每个阶段一次
- 技术评审：每月一次

### 3. 邮件/消息通知
- 项目更新：每周一次
- 里程碑完成：及时通知
- 重大问题：立即通知

### 4. 文档共享
- 共享文档：项目文档库
- 版本管理：Git仓库
- 最新文档：项目首页
```

---

## 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| 1.0 | 2026-07-21 | 初始版本，定义SA规范 |

---

## 附录

### A. 相关文档
- [`AGENTS.md`](AGENTS.md) - 项目核心文档
- [`PM_AGENT.md`](PM_AGENT.md) - 项目管理规范
- [`TDD_AGENT.md`](TDD_AGENT.md) - 测试驱动开发规范
- [`DBA_AGENT.md`](DBA_AGENT.md) - 数据库管理规范

### B. 工具推荐
- PlantUML：UML建模
- Draw.io：架构图绘制
- Git：版本控制
- Notion：文档协作

### C. 联系方式
- 项目邮箱：agent@unires.com
- 技术支持：tech@unires.com
- 项目管理：pm@unires.com
