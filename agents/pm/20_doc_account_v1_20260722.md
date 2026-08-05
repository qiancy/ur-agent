# U001 Account 认证模型变更

> 角色：项目经理
> 状态：已按单账号多空间模型修订，待开发实现
> 目标：将认证凭据从 `person` 分离到 `account` 表，并支持用户注册、登录、组织空间切换。

---

## 1. 变更原则

1. `account` 是认证实体，负责 `login`、密码哈希、账号状态、系统级角色。
2. `person` 是业务人员身份，负责 `puid`、展示名、个人资料。
3. `membership` 是授权关系，负责一个 person 能进入哪些 organization，以及在组织内的角色。
4. `organization` 是业务空间和数据隔离边界；MVP 暂不新增 `workspace` 表，继续用 `organization.type` 表示业务形态。
5. `account.login` 与 `person.puid` 不做物理归并，但 MVP 演示账号允许二者相同，例如 `login=zhansan`、`puid=zhansan`。
6. 登录名不再携带 `ouid`，不得继续使用 `zhansan@zhansan_shop`、`zhansan@fire_xinye_shu` 这类多账号模拟空间切换。

---

## 2. 数据库基线

### person

```sql
CREATE TABLE person (
  id SERIAL PRIMARY KEY,
  puid VARCHAR(100) UNIQUE NOT NULL CHECK (puid ~ '^[A-Za-z0-9_-]+$'),
  name VARCHAR(255) NOT NULL,
  birth_date DATE,
  health_reminders JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### organization

```sql
CREATE TABLE organization (
  id SERIAL PRIMARY KEY,
  ouid VARCHAR(100) UNIQUE NOT NULL CHECK (ouid ~ '^[A-Za-z0-9_-]+$'),
  name VARCHAR(255) NOT NULL,
  type VARCHAR(100) NOT NULL,
  description TEXT,
  funds DECIMAL(15,2) DEFAULT 0,
  reputation INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### account

```sql
CREATE TABLE account (
  id SERIAL PRIMARY KEY,
  person_id INTEGER NOT NULL REFERENCES person(id) ON DELETE CASCADE,
  login VARCHAR(150) UNIQUE NOT NULL,
  password TEXT NOT NULL,
  salt TEXT,
  status VARCHAR(30) NOT NULL DEFAULT 'active',
  system_role VARCHAR(30) NOT NULL DEFAULT 'user',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### membership

```sql
CREATE TABLE membership (
  id SERIAL PRIMARY KEY,
  person_id INTEGER NOT NULL REFERENCES person(id) ON DELETE CASCADE,
  organization_id INTEGER NOT NULL REFERENCES organization(id) ON DELETE CASCADE,
  role VARCHAR(100),
  joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(person_id, organization_id)
);
```

说明：以上数字主键和外键仅允许服务端/数据库内部使用，业务 API、JWT、前端状态不得返回。

---

## 3. 字段命名约定

- `account.login`：登录凭据，唯一，不解析组织上下文。
- `person.puid`：业务人员标识，字符串，英文安全字符。
- `organization.ouid`：业务空间标识，字符串，英文安全字符。
- 其他表外键统一使用 `person_id` / `organization_id`。
- 对外身份字段只允许 `puid` / `ouid`；禁止旧字段 `pid` / `oid`。

---

## 4. 登录名规则

新规则：

```text
login = account.login
```

示例：

```text
zhansan
```

约束：

1. `login` 是账号凭据，不是 `puid/ouid` 上下文。
2. 登录接口不得解析 `login` 中的 `@`、`.` 或其他字符来选择组织。
3. 未来如支持邮箱/手机号登录，也只能用于定位 account。
4. 组织选择来自 `membership` 与 `/auth/switch-organization`。
5. 测试必须覆盖旧形式不会触发组织切换：`zhansan@fire_xinye_shu` 不得被解释为 `puid=zhansan, ouid=fire_xinye_shu`。

---

## 5. 用户注册

### API

```http
POST /auth/register
```

### Request

```json
{
  "login": "zhansan",
  "password": "demo-password",
  "name": "张三",
  "puid": "zhansan",
  "initial_ouid": "zhansan_shop"
}
```

### 实现流程

1. 校验 `login` 非空且唯一。
2. 决定 `puid`：
   - 请求带 `puid` 时使用请求值并校验。
   - 请求不带 `puid` 且 `login` 满足 `^[A-Za-z0-9_-]+$` 时，默认 `puid = login`。
   - 其他情况返回 422，要求补充合法 `puid`。
3. 创建或绑定 `person`。公共注册不得抢占已被其他 account 绑定的 `person.puid`。
4. 创建 `account`，密码只保存哈希。
5. 如传 `initial_ouid`，查询组织并创建 `membership`，公共注册角色固定为 `member`。
6. 如未传 `initial_ouid`，返回 `requires_organization=true`。
7. 所有响应剥离 DB 数字 ID。

---

## 6. 用户登录

### API

```http
POST /auth/login
```

### Request

```json
{
  "login": "zhansan",
  "password": "demo-password"
}
```

### 实现流程

1. 按 `account.login` 查询账号；不存在返回 401。
2. 校验账号 active；非 active 返回 403。
3. 校验密码；错误返回 401。
4. 通过 `account.person_id` 查询 person。
5. 查询 person 的 membership 列表。
6. 无 membership 时返回 `requires_organization=true`，前端展示加入/创建空间占位。
7. 有 membership 时选择默认空间，签发带 `puid/ouid` 的 JWT，并返回可切换组织列表。
8. 切换组织必须走 `/auth/switch-organization`，只提交目标 `ouid`。

### JWT payload

```json
{
  "puid": "zhansan",
  "person_name": "张三",
  "ouid": "zhansan_shop",
  "organization_name": "张三小店",
  "organization_type": "ecommerce",
  "system_role": "user",
  "role": "owner"
}
```

---

## 7. 代码修改点

### `src/models/schemas.py`

- `RegisterRequest` 增加 `puid: Optional[str]`、`initial_ouid: Optional[str]`。
- `LoginRequest.login` 注释改为账号凭据。
- Auth 请求模型启用 `extra = "forbid"`。

### `src/auth/auth.py`

- 移除认证链路对 `parse_login_name()` 的依赖。
- 保留 `validate_puid()` / `validate_ouid()`。
- 新增安全的 `derive_puid_from_login(login)`，仅用于注册缺省值。

### `src/routers/auth.py`

- `_authenticate_login()` 按 `account.login` 认证。
- 注册不解析 login；可选 `initial_ouid` 创建 membership。
- 登录响应返回 organizations 列表。
- `/seller-login` 如继续保留，应复用同一认证逻辑。

### `scripts/init_db.py`

旧三国样例可保留历史超级账号，但新增示例登录不得再使用 `puid@ouid` 表示空间。

### `scripts/seed_demo_spaces.py`

- 只创建一个演示账号：

```text
account.login = zhansan
person.puid = zhansan
```

- 建立 `zhansan` 到 4 个演示空间的 membership。
- 密码继续从 `DEMO_ZHANSAN_PASSWORD` 或未提交 `.env` 读取，不得写入源码。

### Frontend

- 登录页 placeholder 改为 `zhansan`。
- 登录成功后使用返回的 `organizations` 驱动 Header 空间切换。
- 注册页支持 `login/password/name/puid/initial_ouid`。

---

## 8. 禁止事项

1. 禁止在 `person` 表保存密码。
2. 禁止明文密码入库。
3. 禁止绕过 membership 判断组织权限。
4. 禁止用 `person.name` 或 `organization.name` 登录。
5. 禁止把 `account.login` 解析为 `puid/ouid`。
6. 禁止恢复旧 `pid/oid` 兼容。
7. 禁止对外返回 DB 数字 ID。

---

## 9. 验收标准

- `zhansan / 正确密码` 登录成功，返回默认空间和可切换组织列表。
- `zhansan / wrong` 返回 401。
- `account.status != active` 返回 403。
- 注册新用户成功创建 `account + person`。
- 注册不带 `initial_ouid` 时返回 `requires_organization=true`。
- 切换非 membership 组织返回 403。
- 认证响应和 JWT 无 DB 数字 ID。
- 旧登录形式不再作为空间上下文解析。
