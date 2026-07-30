# Uni-Resource Agent — 后端 API 文档

**Base URL**: `http://localhost:8000`
**Version**: 5.1.0
**OpenAPI**: `http://localhost:8000/docs` (Swagger UI)

---

## 目录

1. [系统](#系统)
2. [组织 Organization](#组织-organization)
3. [人员 Person](#人员-person)
4. [成员 Membership](#成员-membership)
5. [资源 Resource](#资源-resource)
6. [仓库 Warehouse](#仓库-warehouse)
7. [资源-仓库明细 ResourceWarehouse](#资源-仓库明细-resourcewarehouse)
8. [交易 Transaction](#交易-transaction)
9. [参与方 Party](#参与方-party)
10. [汇总 Summary](#汇总-summary)
11. [AI 对话 Chat](#ai-对话-chat)

---

## 命名约定

| 缩写 | 含义 |
|------|------|
| `puid` | person业务标识, 例如 `liubei` |
| `ouid` | organization业务标识, 例如 `shu` |

---

## 系统

### `GET /health`

健康检查。

**Response**:
```json
{ "status": "ok" }
```

---

## 组织 Organization

### `GET /organizations`

查询组织列表。

**Query Parameters**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| org_type | string | 否 | 类型过滤: `personal`, `company`, `family` |
| name | string | 否 | 名称模糊搜索 |

**Response**: `Organization[]`
```json
[
  {
    "id": 1,
    "name": "蜀国",
    "type": "company",
    "description": "蜀汉政权",
    "created_at": "2025-01-01T00:00:00"
  }
]
```

### `POST /organizations`

创建组织。

**Request Body**:
```json
{
  "name": "蜀国",
  "org_type": "company",
  "description": "蜀汉政权"
}
```

**Response**: `Organization` (201)

### `GET /organizations/{ouid}/members`

查询组织成员。

**Response**: `Membership[]`
```json
[
  {
    "id": 1,
    "role": "主公",
    "name": "刘备",
    "puid": "liubei"
  }
]
```

---

## 人员 Person

### `GET /person`

查询组织下的人员 (通过 membership 关联)。

**Query Parameters**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ouid | int | 是 | 组织ID |
| name | string | 否 | 名称模糊搜索 |

**Response**: `Person[]`
```json
[
  {
    "id": 1,
    "name": "刘备",
    "birth_date": null,
    "health_reminders": null,
    "membership_role": "主公"
  }
]
```

### `POST /person`

创建人员 (全局, 不属于任何组织)。

**Request Body**:
```json
{
  "name": "张三",
  "birth_date": "1990-01-01"
}
```

**Response**: `Person` (201)

---

## 成员 Membership

### `POST /organizations/members`

添加组织成员 (建立 person ↔ org 关系)。

**Request Body**:
```json
{
  "puid": "liubei",
  "ouid": "shu",
  "role": "主公"
}
```

**Response**: `Membership` (201)

### `GET /persons/{puid}/organizations`

查询人员所属的所有组织。

**Response**: `Membership[]`
```json
[
  {
    "id": 1,
    "role": "主公",
    "name": "蜀国",
    "ouid": "shu",
    "org_type": "company"
  }
]
```

---

## 资源 Resource

### `GET /resource`

查询资源列表。

**Query Parameters**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ouid | int | 是 | 组织ID |
| name | string | 否 | 名称模糊搜索 |
| resource_type | string | 否 | 类型: `physical`, `financial`, `human`, `knowledge` |

**Response**: `Resource[]`
```json
[
  {
    "id": 1,
    "ouid": "shu",
    "name": "青龙偃月刀",
    "type": "physical",
    "status": "active",
    "unit": "把",
    "amount": null,
    "currency": null,
    "puid": null,
    "person_name": null,
    "content": null,
    "created_at": "2025-01-01T00:00:00"
  }
]
```

### `POST /resource`

创建资源。

**Request Body**:
```json
{
  "ouid": "shu",
  "name": "青龙偃月刀",
  "resource_type": "physical",
  "unit": "把"
}
```

**Resource Types**:

| type | 说明 | 特有字段 |
|------|------|----------|
| physical | 物资 | unit |
| financial | 资金 | amount, currency |
| human | 人力 | puid |
| knowledge | 知识 | content |

**示例 — 创建资金资源**:
```json
{
  "ouid": "shu",
  "name": "蜀国金库",
  "resource_type": "financial",
  "amount": 50000,
  "currency": "黄金"
}
```

**示例 — 创建人力资源**:
```json
{
  "ouid": "shu",
  "name": "蜀国兵力",
  "resource_type": "human",
  "puid": "liubei"
}
```

**示例 — 创建知识资源**:
```json
{
  "ouid": "shu",
  "name": "隆中对",
  "resource_type": "knowledge",
  "content": "三分天下之策"
}
```

**Response**: `Resource` (201)

---

## 仓库 Warehouse

### `GET /warehouse`

查询仓库列表。

**Query Parameters**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ouid | int | 是 | 组织ID |
| name | string | 否 | 名称模糊搜索 |

**Response**: `Warehouse[]`
```json
[
  {
    "id": 1,
    "ouid": "shu",
    "name": "蜀国武库",
    "code": "A",
    "location": "成都",
    "description": null,
    "created_at": "2025-01-01T00:00:00"
  }
]
```

### `POST /warehouse`

创建仓库。

**Request Body**:
```json
{
  "ouid": "shu",
  "name": "蜀国武库",
  "code": "A",
  "location": "成都",
  "description": "主武器库"
}
```

**Response**: `Warehouse` (201)

---

## 资源-仓库明细 ResourceWarehouse

### `GET /resource-warehouse`

查询资源在各库位的数量。

**Query Parameters**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| resource_id | int | 是 | 资源ID |
| location_path | string | 否 | 库位路径前缀过滤 |

**location_path 层级**:
| 值 | 含义 |
|----|------|
| `total` | 总数 |
| `A` | 仓库A |
| `A-1` | 仓库A-库区1 |
| `A-1-001` | 仓库A-库区1-库位001 |

**Response**: `ResourceWarehouse[]`
```json
[
  {
    "id": 1,
    "resource_id": 1,
    "location_path": "total",
    "quantity": 50,
    "unit": "架",
    "created_at": "2025-01-01T00:00:00"
  },
  {
    "id": 2,
    "resource_id": 1,
    "location_path": "A",
    "quantity": 30,
    "unit": "架"
  },
  {
    "id": 3,
    "resource_id": 1,
    "location_path": "A-1-003",
    "quantity": 30,
    "unit": "架"
  }
]
```

### `POST /resource-warehouse`

创建/更新资源-库位明细 (upsert)。

**Request Body**:
```json
{
  "resource_id": 1,
  "location_path": "A-1-003",
  "quantity": 30,
  "unit": "架"
}
```

**Response**: `ResourceWarehouse` (201)

### `GET /resource-warehouse/total`

获取资源总数。

**Query Parameters**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| resource_id | int | 是 | 资源ID |

**Response**:
```json
{
  "resource_id": 1,
  "total_qty": 50
}
```

---

## 交易 Transaction

### `GET /transaction`

查询交易记录 (通过 party 关联到组织)。

**Query Parameters**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ouid | int | 是 | 组织ID |
| limit | int | 否 | 返回条数, 默认50, 范围1-200 |

**Response**: `Transaction[]`
```json
[
  {
    "id": 1,
    "amount": 1000.00,
    "category": "军费",
    "description": "诸葛亮家资助蜀汉军费",
    "created_at": "2025-01-01T00:00:00",
    "parties": [
      {
        "puid": "liubei",
        "person_name": "刘备",
        "role": "payer"
      },
      {
        "puid": "zhugeliang",
        "person_name": "诸葛亮",
        "role": "payee"
      }
    ]
  }
]
```

### `POST /transaction`

创建交易 (纯事件记录, 不含组织上下文)。

**Request Body**:
```json
{
  "amount": 1000.00,
  "category": "军费",
  "description": "诸葛亮家资助蜀汉军费"
}
```

**Response**: `Transaction` (201)

---

## 参与方 Party

### `GET /party`

查询组织的参与方。

**Query Parameters**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ouid | int | 是 | 组织ID |
| puid | int | 否 | 人员ID过滤 |

**Response**: `Party[]`
```json
[
  {
    "id": 1,
    "puid": "liubei",
    "ouid": "shu",
    "transaction_id": 1,
    "role": "payer",
    "description": "蜀汉集团支付",
    "person_name": "刘备"
  }
]
```

### `GET /party/transaction/{transaction_id}`

查询交易的所有参与方。

**Response**: `Party[]`

### `POST /party`

创建参与方 (关联 person + org + transaction)。

**Request Body**:
```json
{
  "puid": "liubei",
  "ouid": "shu",
  "transaction_id": 1,
  "role": "payer",
  "description": "蜀汉集团支付"
}
```

**Response**: `Party` (201)

---

## 汇总 Summary

### `GET /summary`

获取组织财务汇总。

**Query Parameters**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ouid | int | 是 | 组织ID |

**Response**:
```json
{
  "ouid": "shu",
  "total_outflow": 1500.00,
  "transaction_count": 3
}
```

---

## AI 对话 Chat

### `POST /chat`

发送消息给 AI Agent。

**Request Body**:
```json
{
  "message": "蜀国有多少战船?",
  "ouid": "shu"
}
```

**Response**:
```json
{
  "response": "蜀国共有10艘战船,全部存放在水军基地(A仓库-2库区-001库位)。",
  "ouid": "shu"
}
```

---

## 错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

**错误响应格式**:
```json
{
  "detail": "错误信息"
}
```

---

## 数据模型

### Organization
```json
{
  "id": "int",
  "name": "string",
  "type": "string (personal|company|family)",
  "description": "string|null",
  "created_at": "datetime"
}
```

### Person
```json
{
  "id": "int",
  "name": "string",
  "birth_date": "date|null",
  "health_reminders": "jsonb|null",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Membership
```json
{
  "id": "int",
  "puid": "string",
  "ouid": "string",
  "role": "string|null",
  "joined_at": "datetime"
}
```

### Resource
```json
{
  "id": "int",
  "ouid": "string",
  "name": "string",
  "type": "string (physical|financial|human|knowledge)",
  "status": "string (active|inactive)",
  "unit": "string|null",
  "amount": "decimal|null",
  "currency": "string|null",
  "puid": "string|null",
  "person_name": "string|null",
  "content": "text|null",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Warehouse
```json
{
  "id": "int",
  "ouid": "string",
  "name": "string",
  "code": "string",
  "location": "string|null",
  "description": "string|null",
  "created_at": "datetime"
}
```

### ResourceWarehouse
```json
{
  "id": "int",
  "resource_id": "int",
  "location_path": "string (total|A|A-1|A-1-001)",
  "quantity": "decimal",
  "unit": "string|null",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Transaction
```json
{
  "id": "int",
  "amount": "decimal",
  "category": "string",
  "description": "string|null",
  "created_at": "datetime"
}
```

### Party
```json
{
  "id": "int",
  "puid": "string",
  "ouid": "string",
  "transaction_id": "int",
  "role": "string (payer|payee|...)",
  "description": "string|null",
  "person_name": "string"
}
```
