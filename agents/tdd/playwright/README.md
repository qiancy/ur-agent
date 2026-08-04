# Playwright 录屏专项测试

本目录用于 2026-08-06 Demo 录屏前的 DEMO-DATA-02/双场景端到端冒烟测试。测试会打开真实浏览器，覆盖登录默认个人空间、Header、组织切换、非电商隔离、Seller AI 和库存页面。

## 安装

```bash
bash agents/tdd/playwright/install_browsers.sh
```

## 前置服务

录屏测试不负责启动服务。运行前请确保：

- 后端：`http://localhost:8000`
- 前端：`http://localhost:5173`
- 新录屏数据已通过 `scripts/seed_recording_data.py` 写入测试库
- `liuming` 演示密码可用（`DEMO_LIUMING_PASSWORD`）

可选环境变量：

```bash
export E2E_BASE_URL=http://localhost:5173
export E2E_API_BASE=http://localhost:8000
export DEMO_RECORDING_LOGIN=liuming
export DEMO_LIUMING_PASSWORD='<未提交 .env 中配置>'
export DEMO_RECORDING_PERSONAL_OUID=liuming_personal
export DEMO_RECORDING_SHOP_OUID=liuming_mingdeng_shop
export DEMO_RECORDING_CAMPAIGN_OUID=liuming_xinye_review
```

`DEMO_LIUMING_PASSWORD` 只从仓库 `.env`（已被 gitignore）或环境变量读取，测试模块顶部会 `load_dotenv`；未设置时测试会直接退出并提示，绝不写死默认密码。

如果只想录制前端交互、暂时绕过真实 LLM，可临时开启：

```bash
export E2E_FAKE_SELLER_CHAT=1
```

该模式拦截 `/seller/chat`，返回固定答案：`库存最低的商品是草船借箭纪念徽章，当前库存 3枚。`
正式验收建议关闭该变量，让 `/seller/chat` 走真实后端链路。

## 录屏运行

```bash
bash agents/tdd/playwright/run_recording.sh
```

等价命令：

```bash
python3 -m pytest agents/tdd/playwright/test_demo_recording.py -m recording -v --headed --slowmo=500 --reruns 1
```

视频保底产物会写入：

```text
agents/tdd/playwright/videos/
```

## 用例与话术

| 用例 | 覆盖场景 | 产品卖点话术 |
| :--- | :--- | :--- |
| `test_01_login_and_context_storage` | 登录与本地上下文 | “看，我们用单一账号登录，系统识别出刘明的个人工作空间，前端上下文里只有 `puid/ouid` 这样的业务身份。” |
| `test_02_header_no_ai_input_and_org_display` | Header 去 AI 化 | “顶部只显示用户、个人空间、类型和角色，AI 入口统一收归在工作台内，界面干净不干扰。” |
| `test_03_switch_organization_jwt_refresh` | 组织切换和 JWT 刷新 | “从个人空间切到店铺必须经过后端校验并重新签发 JWT，前端不会伪造当前组织。” |
| `test_04_non_ecommerce_api_isolation` | 非电商空间 API 隔离 + 战役观察页 | “切到战役复盘空间后，前端完全停止调用 Seller 接口，数据不会串空间；同时能看到 8 条时间线和信息流/物流/人流的内容。” |
| `test_05_ecommerce_workbench_and_seller_ai` | 电商库存 + Seller AI | “切回明灯文创小店后，6 个商品、低库存标签和 Seller AI 一起恢复，AI 能基于真实库存指出最低库存商品是草船借箭纪念徽章（3枚）。” |

> Demo 数据口径见 `agents/pm/DEMO-DATA-02_全新录屏账号与数据开发测试安排.md`：
> 电商 6 商品/12 流水/低库存 2 项；最低库存锚点为 `草船借箭纪念徽章（3枚）`；
> 战役复盘 7 人员/7 资源/8 条时间线事件；liuming 登录默认进个人空间。

## 防录屏翻车检查

```bash
python3 -m pytest agents/tdd/playwright/test_demo_recording.py -m recording -v --headed --slowmo=500 --reruns 1
grep -r 'person''_id\|organization''_id' agents/tdd/playwright/ || true
ls -lh agents/tdd/playwright/videos/
```

验收口径：

- 5 个 `recording` 用例全部 `PASSED`
- `videos/` 下有 WebM 文件
- 扫描不应命中测试代码中的旧数字身份字段

全部通过后输出：

```text
Playwright 录屏脚本就绪，等待手动录屏开拍。
```
