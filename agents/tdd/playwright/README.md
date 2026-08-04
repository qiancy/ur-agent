# Playwright 录屏专项测试

本目录用于 2026-08-06 Demo 录屏前的 FE-08/双场景端到端冒烟测试。测试会打开真实浏览器，覆盖登录、Header、组织切换、非电商隔离、Seller AI 和库存页面。

## 安装

```bash
bash agents/tdd/playwright/install_browsers.sh
```

## 前置服务

录屏测试不负责启动服务。运行前请确保：

- 后端：`http://localhost:8000`
- 前端：`http://localhost:5173`
- Demo 数据已通过 `scripts/seed_demo_data.py` 写入测试库
- `zhansan` 演示密码可用

可选环境变量：

```bash
export E2E_BASE_URL=http://localhost:5173
export E2E_API_BASE=http://localhost:8000
export DEMO_ZHANSAN_PASSWORD=demo123
```

如果只想录制前端交互、暂时绕过真实 LLM，可临时开启：

```bash
export E2E_FAKE_SELLER_CHAT=1
```

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
| `test_01_login_and_context_storage` | 登录与本地上下文 | “看，我们用单一账号登录，系统自动识别了该用户的业务空间，并且前端上下文里只有 `puid/ouid` 这样的业务身份。” |
| `test_02_header_no_ai_input_and_org_display` | Header 去 AI 化 | “顶部只显示用户、空间、类型和角色，AI 入口统一收归在工作台内，界面干净不干扰。” |
| `test_03_switch_organization_jwt_refresh` | 组织切换和 JWT 刷新 | “切换空间必须经过后端校验并重新签发 JWT，前端不会伪造当前组织。” |
| `test_04_non_ecommerce_api_isolation` | 非电商空间 API 隔离 | “切到战役空间后，前端完全停止调用 Seller 库存、摘要和 AI 接口，数据不会串空间。” |
| `test_05_ecommerce_workbench_and_seller_ai` | 电商库存 + Seller AI | “切回淘宝卖家空间后，库存和 Seller AI 恢复工作，AI 能基于真实库存指出最低库存商品。” |

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

