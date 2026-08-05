# data/campaigns — 示例空间包

本目录存放产品预置的示例空间包（campaign packs），通过 `POST /campaigns/import`
或 `scripts/seed_demo_spaces.py` 导入数据库。

## 文件清单

| 文件 | campaign_code | campaign_name | 组织 ouid | 组织 type | 说明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `fire_xinye.json` | `fire_xinye` | 火烧新野 | `fire_xinye_shu` / `fire_xinye_wei` | `military` | 火烧新野战役（回归/演示场景） |
| `family_learning.json` | `family_learning` | 家庭学习空间 | `zhangsan_family` | `family` | 张三家庭学习空间 |
| `deep_space_fleet.json` | `deep_space_fleet` | 深空远航舰队 | `deep_space_fleet` | `starship` | 原创深空远航舰队设定 |

## 顶层结构（schema）

每个空间包是单个 JSON 文件，顶层字段如下（对照 `src/routers/campaign.py` 的导入逻辑）：

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `campaign_code` | string | 空间包唯一业务代码（英文安全字符） |
| `campaign_name` | string | 空间包展示名称 |
| `organizations` | array | 组织：`ouid`/`name`/`type`/`description`/`funds`/`reputation` |
| `persons` | array | 人员：`puid`/`name`（可选 `birth_date`） |
| `memberships` | array | 成员关系：`puid`/`ouid`/`role` |
| `warehouses` | array | 仓库：`ouid`/`name`/`code`/`location`（physical 资源库位用） |
| `resources` | array | 资源：`ouid`/`name`/`type`/`unit`/`amount`/`content`/`currency`/`puid`/`warehouse_code` |
| `transactions` | array | 交易：`ouid`/`amount`/`category`/`description`/`parties` |
| `events` | array | 事件：`ouid`/`seq`/`title`/`description` + 维度标签（见下） |

## 事件维度标签

每个事件对象携带四个**顶层**字符串字段，`/campaigns/import` 会把整个事件配置原样写入
`campaign_event.payload`（JSONB），replay / `/spaces/current/timeline` 原样返回，
因此前端从 `event.payload.info_flow` 等位置读取。空串或缺失即表示该维度不适用：

| 字段 | 含义 |
| :--- | :--- |
| `info_flow` | 信息流：情报、通知、指令的传递 |
| `logistics_flow` | 物流：物资、辎重、物品的流转 |
| `people_flow` | 人流：参与该事件的人员 |
| `risk` | 风险：事件潜在的失败因素 |

## 资源类型

`resources[].type` 覆盖四类资源，前端观察面板按类型分组：

| type | 说明 | 典型字段 |
| :--- | :--- | :--- |
| `physical` | 实物资源 | `unit`/`amount`/`warehouse_code` |
| `knowledge` | 知识/资料 | `content` |
| `financial` | 资金/预算 | `amount`/`currency` |
| `human` | 人员职责/任务 | `puid`（关联人员） |

## 预置种子脚本

```bash
PYTHONPATH=. python scripts/seed_demo_spaces.py
```

- 幂等：按 `campaign_code` 查询已存在 active 导入则跳过。
- 演示用户 `zhansan`（puid=`zhansan`，name=张三）：建立 4 空间 membership
  （`fe06_spike_*` 既有淘宝卖家店铺、`fire_xinye_shu`、`zhangsan_family`、
  `deep_space_fleet`），并为其创建 `zhansan@{ouid}` 登录账号。
- 密码：从环境变量 `DEMO_ZHANSAN_PASSWORD` 或项目根未提交的 `.env` 读取；
  未配置则跳过账号创建并在 stdout 提示。密码绝不写入源码。
