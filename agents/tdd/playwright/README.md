# Playwright 录屏专项测试

本目录用于 2026-08-06 Demo 录屏前的 DEMO-DATA-02/双场景端到端冒烟测试。测试会打开真实浏览器，**只登录一次**，随后通过 Header 在个人空间、电商空间、战役空间之间切换，形成一条连续的多空间录屏主流程。

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
# 每个数据屏加载完成后停留毫秒数（默认 4000，录屏时可调大）
export E2E_HOLD_MS=4000
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

## 主流程与话术

单一用例 `test_recording_main_flow`，全程只登录一次：

| 步骤 | 覆盖场景 | 产品卖点话术 |
| :--- | :--- | :--- |
| 1 | 登录 `liuming`，默认进入个人空间 | “用一个账号登录，系统自动进入刘明自己的个人工作空间。” |
| 2 | Header 去 AI 化 + 空间展示 | “顶部只显示用户、个人空间、类型和角色，AI 入口收归在工作台内。” |
| 3 | Header 切到明灯文创小店 | “切空间必须经过后端校验并重签 JWT，前端不伪造。” |
| 4 | 库存/流水/摘要/Seller AI | “6 个商品、低库存标签、经营摘要和 Seller AI 一起恢复，AI 指出最低库存是草船借箭纪念徽章（3枚）。” |
| 5 | Header 切到新野火攻复盘空间 | “切到战役复盘后前端停止调用 Seller 接口，8 条时间线和信息流/物流/人流清晰可见。” |
| 6 | 回到电商空间 | “再次切回店铺仍无需重新登录，多空间数据互不串扰。” |

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

- `test_recording_main_flow` 用例 `PASSED`
- `videos/` 下有 WebM 文件
- 扫描不应命中测试代码中的旧数字身份字段

全部通过后输出：

```text
Playwright 录屏脚本就绪，等待手动录屏开拍。
```
