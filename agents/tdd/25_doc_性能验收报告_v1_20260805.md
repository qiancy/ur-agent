# PERF-01 性能验收报告

> 日期：2026-08-05
> 范围：数据库连接池、首屏聚合接口、前端首屏接线。
> 状态：功能验收已通过；远程 Demo 环境耗时数据待录屏前补测。

## 1. 本轮实现

- 后端数据库访问从 thread-local 连接复用升级为 `psycopg2.pool.ThreadedConnectionPool`。
- 配置新增 `database.pool_min/pool_max` 与环境变量 `DB_POOL_MIN/DB_POOL_MAX`。
- `_fetch/_execute` 统一从连接池取连接并归还；坏连接重试一次。
- 显式事务函数统一使用事务 helper，执行 `commit/rollback` 后归还连接。
- FastAPI startup 初始化连接池，shutdown 关闭连接池。
- pool 耗尽抛 `DatabasePoolExhaustedError`，API 层返回 503。
- 新增聚合接口：
  - `GET /seller/workbench`
  - `GET /spaces/current/dashboard`
- 前端首屏加载改造：
  - `WorkbenchView` 只调用 `sellerWorkbench()`。
  - `GenericSpaceView` 只调用 `getSpaceDashboard()`。

## 2. 已执行验证

```bash
python3 -m compileall src agents/tdd
python3 -m pytest agents/tdd/test_config.py agents/tdd/test_perf01_aggregate_and_pool.py -v
cd web && npm run test -- src/api/seller.test.ts src/api/spaces.test.ts src/views/WorkbenchView.test.ts src/views/GenericSpaceView.test.ts
cd web && npm run build
```

结果：

- `compileall`：通过。
- 后端配置 + PERF-01 契约：28 passed。
- 前端聚合相关：36 passed。
- 前端 build：通过。

## 3. 待录屏前补测

需要在真实 Demo 前后端都启动后补测：

| 场景 | 目标 | 结果 |
| :--- | ---: | :--- |
| `/seller/workbench` 首包 | < 1.5s | 待测 |
| `/spaces/current/dashboard` 首包 | < 2.0s | 待测 |
| Header 切 ecommerce 到库存可见 | < 1.5s | 待测 |
| Header 切 campaign 到时间线可见 | < 2.0s | 待测 |

连接数检查：

```sql
SELECT state, count(*)
FROM pg_stat_activity
WHERE datname = 'unires'
GROUP BY state
ORDER BY state;
```

要求：

- 多次刷新后连接数稳定，不随刷新次数线性增长。
- 服务停止后不残留应用连接。

## 4. 风险记录

- 当前聚合接口减少了前端 HTTP 往返，并通过后端线程池并行调用现有 helper；尚未合并复杂 SQL。
- 若真实远程环境中 `/spaces/current/dashboard` 仍超过 2s，应优先合并 `get_space_overview/get_space_resources` 内部 SQL，减少资源循环查询。
