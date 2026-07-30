# 淘宝卖家 MVP 开发实施计划（严格 puid/ouid 版）

## 1. PM 决策

本计划以 `puid` / `ouid` 为唯一业务身份命名：

| 概念 | 字段 | 说明 |
|------|------|------|
| 人员业务标识 | `puid` | `person.puid`，字符串，唯一 |
| 组织业务标识 | `ouid` | `organization.ouid`，字符串，唯一 |
| 内部数据库主键 | `person_id` / `organization_id` | 只在服务端和数据库内部使用 |

红线：

1. 不再接受、返回、生成旧身份键。
2. 不做字段迁移，不写改列名 SQL。
3. 不做 token 适配，不写 token 键归一化层。
4. 不返回双键，不保留旧字段别名。
5. 旧表必须通过 `scripts/init_db.py` 或 `init_database(drop_all=True)` 重建。

## 2. 数据库方案

数据库只创建新结构：

```sql
CREATE TABLE organization (
  id SERIAL PRIMARY KEY,
  ouid VARCHAR(100) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  type VARCHAR(100) NOT NULL
);

CREATE TABLE person (
  id SERIAL PRIMARY KEY,
  puid VARCHAR(100) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL
);
```

所有业务表之间的关联统一使用数字外键：

| 表 | 关联字段 |
|----|----------|
| `membership` | `person_id`, `organization_id` |
| `resource` | `organization_id`, `person_id` |
| `warehouse` | `organization_id` |
| `transaction` | `organization_id` |
| `party` | `person_id`, `organization_id` |

`init_database(drop_all=False)` 只确保新 schema 存在，不修旧表。需要应用字段变更时，开发团队必须重新初始化数据库。

## 3. BE-01 范围

BE-01 只做权限隔离和严格命名收口：

| 文件 | 要求 |
|------|------|
| `src/db/database.py` | `organization.ouid`、`person.puid` 直接建表；删除字段迁移函数；删除数字 `ouid` 查询路径 |
| `src/auth/auth.py` | JWT 只包含 `puid`、`ouid`、角色字段；不解析旧键 |
| `src/routers/deps.py` | `require_org_context` 只返回 `puid/ouid/person_id/organization_id`；不返回旧别名 |
| `src/routers/resource.py` | `/resource-warehouse` GET/POST/total 必须鉴权或有明确 `ouid` 上下文，并校验资源归属 |
| `agents/tdd/test_seller_inventory_api.py` | 覆盖匿名读取、跨店铺读取/写入、非 ecommerce 回归 |

## 4. Seller API 约束

Seller API 不接收数据库主键作为业务输入：

| 场景 | 接受 | 拒绝 |
|------|------|------|
| 商品 | `product_uid` | `resource_id` 作为业务输入 |
| 仓库 | `warehouse_code` / `location_path` | `warehouse_id` 作为业务输入 |
| 组织 | JWT 中的 `ouid` | 前端传 `organization_id` |
| 人员 | JWT 中的 `puid` | 前端传 `person_id` |

后端内部可以用 `resolve_product_uid()` 和 `query_organization_by_ouid()` 将业务 UID 转换为数据库主键，但转换结果不得返回给业务端。

## 5. 验收标准

1. `src/` 中不存在旧业务身份键字段、参数、JWT 键或 SQL 列名。
2. 数据库建表 SQL 只包含 `person.puid` 和 `organization.ouid`。
3. 不存在身份字段迁移 helper、改列名 helper、token 键归一化层。
4. 不存在改列名 SQL 身份字段迁移方案。
5. `compileall` 通过。
6. `agents/tdd/test_seller_inventory_api.py` 全部通过。
7. 火烧新野 HTTP 回归不因 BE-01 变更产生新增失败。

## 6. 提交要求

开发提交前必须附扫描证据：

```bash
rg -n -P "(^|[^a-z0-9])[p]id([^a-z0-9]|$)|(^|[^a-z0-9])[o]id([^a-z0-9]|$)|[A-Za-z0-9]_([p]id|[o]id)\\b" src agents docs README.md AGENTS.md
rg -n "改列名 S[Q]L|token 键归一化[层]|_migrate[_]identity|_rename[_]column" src agents docs README.md
```

不得在 Python 业务代码、建表 SQL 或产品文档中保留旧身份字段。
