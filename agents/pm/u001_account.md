# U001 Account 认证模型变更

> 角色：项目经理  
> 状态：待开发实现  
> 目标：将认证凭据从 `person` 分离到 `account` 表，完成用户注册和登录。

---

## 1. 变更原则

- `person` 是业务人员身份，不保存密码。
- `account` 是登录凭据，保存 login、password、salt、status。
- `organization` 是组织空间。
- `membership` 负责人员和组织的授权关系。
- 登录和注册必须通过 `membership` 校验组织权限。

---

## 2. 数据库修改

### person

```sql
CREATE TABLE person (
  id SERIAL PRIMARY KEY,
  puid VARCHAR(100) UNIQUE NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_person_puid
ON person(puid)
;
```

### organization

```sql
CREATE TABLE organization (
  id SERIAL PRIMARY KEY,
  ouid VARCHAR(100) UNIQUE NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_organization_ouid
ON organization(ouid)
;
```

### account

```sql
CREATE TABLE IF NOT EXISTS account (
    id SERIAL PRIMARY KEY,
    person_id INTEGER NOT NULL REFERENCES person(id) ON DELETE CASCADE,
    login VARCHAR(150) NOT NULL UNIQUE,
    password TEXT NOT NULL,
    salt TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 3. 字段命名约定

- `person.id`：人员数字主键。
- `person.puid`：人员业务标识，英文非特殊字符，例如 `caocao`。
- `organization.id`：组织数字主键。
- `organization.ouid`：组织业务标识，规则同 `puid`，例如 `wei`。
- 除 `person` / `organization` 两张主表外，其他表的外键统一使用 `person_id` / `organization_id`，不得再使用 `puid` / `ouid` 表示数字外键。

需要调整的表包括但不限于：

| 表 | 旧字段 | 新字段 |
|----|--------|--------|
| `membership` | `puid`, `ouid` | `person_id`, `organization_id` |
| `resource` | `ouid`, `puid` | `organization_id`, `person_id` |
| `warehouse` | `ouid` | `organization_id` |
| `transaction` | `ouid` | `organization_id` |
| `party` | `puid`, `ouid` | `person_id`, `organization_id` |

---

## 4. 登录名规则

只支持 `.cn` 登录名：

```text
{person.puid}@{organization.ouid}.cn
```

示例：

```text
caocao@wei.cn
```

解析为：

```json
{
  "puid": "caocao",
  "ouid": "wei"
}
```

约束：

- `person.puid` 只允许英文、数字、下划线、短横线。
- `organization.ouid` 只允许英文、数字、下划线、短横线。
- 不支持 `.com`、`.org` 或中文登录名。

---

## 5. 用户注册

### API

```http
POST /auth/register
```

### Request

```json
{
  "login": "caocao@wei.cn",
  "password": "demo123",
  "name": "曹操",
  "role": "主公"
}
```

### 实现流程

1. 校验 `login` 格式。
2. 解析 `puid=caocao`、`ouid=wei`。
3. 查询 `organization.ouid = ouid`，不存在返回 404。
4. 查询 `person.puid = puid`。
5. 如果 person 不存在，创建：
   - `puid = puid`
   - `name = request.name`
6. 查询 `account.login = request.login`。
7. 如果 account 不存在，创建：
   - `person_id = person.id`
   - `login = request.login`
   - `password = hash(password)`
   - `salt` 按哈希方案处理
   - `status = active`
8. 如果 account 已存在：
   - 必须属于同一个 `person_id`
   - 密码必须校验通过，否则返回 409
9. 查询 `membership(person_id=person.id, organization_id=organization.id)`。
10. 如果 membership 不存在，创建 membership，role 默认 `member`。
11. 返回 person、organization、account、membership。

### Response

```json
{
  "person": {
    "id": 8,
    "puid": "caocao",
    "name": "曹操"
  },
  "organization": {
    "id": 2,
    "ouid": "wei",
    "name": "魏国",
    "type": "company"
  },
  "account": {
    "id": 1,
    "login": "caocao@wei.cn",
    "status": "active"
  },
  "membership": {
    "role": "主公"
  }
}
```

---

## 6. 用户登录

### API

```http
POST /auth/login
```

### Request

```json
{
  "login": "caocao@wei.cn",
  "password": "demo123"
}
```

### 实现流程

1. 校验 `login` 格式。
2. 解析 `puid` 和 `ouid`。
3. 查询 `account.login = request.login`，不存在返回 401。
4. 校验 `account.status = active`，否则返回 403。
5. 通过 `account.person_id` 查询 person。
6. 校验 `person.puid` 与登录名中的 `puid` 一致。
7. 查询 `organization.ouid = ouid`。
8. 查询 membership：

```sql
SELECT role
FROM membership
WHERE person_id = :person_id
  AND organization_id = :organization_id;
```

9. membership 不存在返回 401 或 403。
10. 校验 `account.password`。
11. 签发 JWT。
12. 返回 token 和登录上下文。

### JWT payload

JWT 只放业务字段，不夹杂数据库数字主键。

```json
{
  "puid": "caocao",
  "person_name": "曹操",
  "ouid": "wei",
  "organization_name": "魏国",
  "organization_type": "company",
  "role": "主公"
}
```

### Response

```json
{
  "access_token": "...",
  "token_type": "bearer",
  "person": {
    "id": 8,
    "puid": "caocao",
    "name": "曹操"
  },
  "organization": {
    "id": 2,
    "ouid": "wei",
    "name": "魏国",
    "type": "company"
  },
  "account": {
    "id": 1,
    "login": "caocao@wei.cn",
    "status": "active"
  },
  "membership": {
    "role": "主公"
  }
}
```

---

## 7. 代码修改点

### `src/db/database.py`

- schema 增加 `person.puid`
- schema 增加 `organization.ouid`
- schema 新增 `account`
- 增加按 `person.puid` 查询 person 的函数
- 增加按 `organization.ouid` 查询 organization 的函数
- 增加 account 查询和创建函数
- 增加 membership 校验函数
- 将除 `person` / `organization` 外所有表的 `puid` / `ouid` 数字外键重命名为 `person_id` / `organization_id`

### `src/auth/auth.py`

- 实现密码 hash
- 实现密码 verify
- 实现 JWT 创建
- 实现 JWT 解析
- 密码算法优先 Argon2；如果依赖接入成本高，允许先用 bcrypt。

### `src/app.py`

新增接口：

```http
POST /auth/register
POST /auth/login
```

### `scripts/init_db.py`

初始化样例数据：

```text
liubei@shu.cn / demo123
caocao@wei.cn / demo123
sunquan@wu.cn / demo123
zhugeliang@shu.cn / demo123
```

### `agents/tdd/test_auth_api.py`

新增黑盒测试：

- `test_register_success`
- `test_register_invalid_login_format`
- `test_register_unknown_org`
- `test_login_success`
- `test_login_wrong_password`
- `test_login_wrong_org_membership`
- `test_login_unknown_org`
- `test_login_inactive_account`

---

## 8. 禁止事项

- 禁止在 `person` 表保存密码。
- 禁止明文密码入库。
- 禁止绕过 `membership` 判断组织权限。
- 禁止用 `person.name` 或 `organization.name` 登录。
- 禁止支持 `.com`，当前只支持 `.cn`。

---

## 9. 验收标准

- `caocao@wei.cn / demo123` 登录成功，返回 `ouid=home`、`ouid=wei`。
- `caocao@shu.cn / demo123` 登录失败，因为 membership 不存在。
- `caocao@wei.cn / wrong` 登录失败，返回 401。
- `caocao@unknown.cn / demo123` 登录失败。
- `曹操@魏国.cn / demo123` 登录失败。
- `account.status != active` 登录失败，返回 403。
- 登录成功后，前端和 `/chat` 使用 token 或登录态中的 `ouid`。
