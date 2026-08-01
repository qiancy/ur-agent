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
8. [Seller 库存经营](#seller-库存经营)
9. [交易 Transaction](#交易-transaction)
10. [参与方 Party](#参与方-party)
11. [汇总 Summary](#汇总-summary)
12. [AI 对话 Chat](#ai-对话-chat)

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

## Seller 库存经营

Seller API 面向 ecommerce 店铺，全部使用 Bearer JWT 决定当前店铺上下文。请求体和查询参数不得提交 `puid`、`ouid` 或数据库内部主键字段；商品、仓库和流水只暴露业务字段。Seller 商品只统计 `resource.type = "physical"` 且 active 的资源，知识、财务、人力等非库存资源不进入 Seller 商品视图。

### `POST /seller/purchase-in`

买入入库。库存、交易记录和库存流水在同一个事务中提交或回滚。

**Headers**:
| 名称 | 必填 | 说明 |
|------|------|------|
| Authorization | 是 | `Bearer <access_token>` |

**Request Body**:
```json
{
  "product_uid": "phone_case_white",
  "warehouse_code": "main",
  "location_path": "A-01",
  "quantity": 10,
  "unit": "件",
  "total_amount": 80.00,
  "counterparty_name": "供应商A"
}
```

**Response**:
```json
{
  "status": "ok",
  "operation_type": "purchase_in",
  "product_uid": "phone_case_white",
  "warehouse_code": "main",
  "location_path": "A-01",
  "quantity_delta": 10.0,
  "new_quantity": 10.0,
  "unit": "件",
  "total_amount": 80.0,
  "counterparty_name": "供应商A",
  "movement_uid": "mv_xxxxxx"
}
```

### `POST /seller/sales-out`

卖出出库。库存不足返回 `409`，且不创建交易记录或库存流水。

**Request Body**:
```json
{
  "product_uid": "phone_case_white",
  "warehouse_code": "main",
  "location_path": "A-01",
  "quantity": 3,
  "unit": "件",
  "total_amount": 45.00,
  "counterparty_name": "淘宝买家"
}
```

**Response**:
```json
{
  "status": "ok",
  "operation_type": "sales_out",
  "product_uid": "phone_case_white",
  "warehouse_code": "main",
  "location_path": "A-01",
  "quantity_delta": -3.0,
  "new_quantity": 7.0,
  "unit": "件",
  "total_amount": 45.0,
  "counterparty_name": "淘宝买家",
  "movement_uid": "mv_xxxxxx"
}
```

### `GET /seller/stock`

查询当前店铺库存。

**Query Parameters**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| product_uid | string | 否 | 商品业务标识 |

**Response**:
```json
[
  {
    "product_uid": "phone_case_white",
    "warehouse_code": "main",
    "location_path": "A-01",
    "quantity": 7.0,
    "unit": "件"
  }
]
```

### `GET /seller/inventory-movements`

查询库存流水。默认响应保持数组，不包裹分页对象；未传 `limit` 时忽略 `offset`。

**Query Parameters**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| product_uid | string | 否 | 商品业务标识 |
| operation_type | string | 否 | `purchase_in` 或 `sales_out` |
| date_from | string | 否 | 开始日期，`YYYY-MM-DD` |
| date_to | string | 否 | 结束日期，`YYYY-MM-DD`，包含当天 |
| limit | int | 否 | 1..200 |
| offset | int | 否 | 大于等于 0 |

**Response**:
```json
[
  {
    "movement_uid": "mv_xxxxxx",
    "operation_type": "sales_out",
    "product_uid": "phone_case_white",
    "warehouse_code": "main",
    "location_path": "A-01",
    "quantity_delta": -3.0,
    "new_quantity": 7.0,
    "unit": "件",
    "total_amount": 45.0,
    "counterparty_name": "淘宝买家",
    "created_at": "2026-07-31T10:20:30"
  }
]
```

### `GET /seller/summary`

查询当前店铺经营摘要。金额类字段保留 2 位小数；库存数量、低库存列表和库存估值始终基于当前实时库存，日期范围只影响采购、销售、流水计数和热销商品统计。

**Query Parameters**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| date_from | string | 否 | 开始日期，`YYYY-MM-DD` |
| date_to | string | 否 | 结束日期，`YYYY-MM-DD`，包含当天 |
| low_stock_threshold | number | 否 | 低库存阈值，默认 5，必须大于等于 0 |
| top_n | int | 否 | 热销商品数量，默认 5，范围 1..20 |

**Response**:
```json
{
  "status": "ok",
  "date_from": "2026-07-01",
  "date_to": "2026-07-31",
  "sales_amount": 450.0,
  "purchase_amount": 300.0,
  "net_cash_flow": 150.0,
  "purchase_count": 3,
  "sales_count": 8,
  "movement_count": 11,
  "product_count": 4,
  "stock_location_count": 6,
  "current_stock_quantity": 32.0,
  "estimated_inventory_value": 256.0,
  "valuation_method": "weighted_average_purchase_cost",
  "low_stock_items": [
    {
      "product_uid": "phone_case_white",
      "quantity": 3.0,
      "unit": "件"
    }
  ],
  "top_products_by_sales": [
    {
      "product_uid": "phone_case_white",
      "sales_amount": 180.0,
      "sales_quantity": 12.0
    }
  ]
}
```

### `GET /seller/product-summary`

按商品查询采购、销售、当前库存和库存估值。不传 `product_uid` 时返回当前店铺所有 active physical 商品；不存在、非 active 或非 physical 商品返回空数组。

**Query Parameters**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| product_uid | string | 否 | 商品业务标识 |
| date_from | string | 否 | 统计开始日期 |
| date_to | string | 否 | 统计结束日期 |

**Response**:
```json
{
  "status": "ok",
  "items": [
    {
      "product_uid": "phone_case_white",
      "unit": "件",
      "current_quantity": 17.0,
      "purchase_quantity": 20.0,
      "sales_quantity": 3.0,
      "purchase_amount": 160.0,
      "sales_amount": 45.0,
      "movement_count": 2,
      "estimated_inventory_value": 136.0
    }
  ]
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
