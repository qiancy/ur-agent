# GH-01 复制代码到 GitHub 空仓库计划

> 角色：项目经理
> 日期：2026-08-05
> 目标：将当前 Uni-Resource Agent 项目整理后复制到目标 GitHub 工作区 `/data/research/amd.com/ur-agent`，形成清爽、可运行、可评审的参赛提交代码。
> 前置状态：FE-11 已删除 Gradio 旧前端，产品唯一前端入口为 `web/` Vue + Vite。

## 1. PM Review 结论

FE-11 代码改造可以通过。

已确认：

- `src/frontend.py` 已删除。
- `agents/tdd/test_frontend_render.py` 已删除。
- `requirements.txt` 已移除 `gradio`。
- `scripts/unires_agent.sh` 不再启动旧前端，只提示 Vue 前端启动方式。
- `scripts/monitor.sh` 前端端口已改为 `5173`。
- `README.md` 和 `docs/ARCHITECTURE.md` 已更新为 Vue + Vite 前端。
- 后端编译、前端测试、前端构建均通过。

复制前必须处理：

- `agents/tdd/测试移交文档.md` 当前仍描述 FE-11 前的旧状态，例如 `src/frontend.py` 未提交、`test_frontend_render.py` 存在。该文档不能按现状复制到 GitHub。
- PM 结论：该文档属于开发移交过程文档，**不复制到干净仓库**。

## 2. 目标仓库形态

目标 GitHub 工作区已由用户确认：

```text
/data/research/amd.com/ur-agent
```

建议第一版 GitHub 仓库先保持当前可运行结构，不在复制时强行移动后端路径：

```text
ur-agent/
├── src/                    # FastAPI backend source
├── web/                    # Vue + Vite frontend
├── scripts/                # DB init, seed, service helpers
├── agents/tdd/             # 可复现 API/E2E 测试，剔除过程文档
├── docs/                   # 面向评委/用户的 API、架构、Demo 文档
├── data/                   # seed/init data, no secrets
├── README.md
├── requirements.txt
├── profile.yaml            # non-secret config only
├── .env.example            # placeholders only
├── pytest.ini
└── LICENSE
```

说明：

- `web/ -> frontend/`、`src/ -> backend/src/` 可以作为赛后 `GH-02` 工程整理任务。
- 比赛前不建议在复制时做目录大迁移，避免临近提交引入路径错误。
- README 中可以明确 `src/ = backend`、`web/ = frontend`，满足评审理解。
- `agents/pm/`、`agents/sa/` 中的大量开发计划/评审/中间建模文档默认不复制，只在本地工作仓库保留。
- `data/init_data/` 仅含 README.md，rsync 时一并复制，无害。

## 3. 复制策略：白名单优先

PM 决策：采用 **白名单复制**，不是整仓排除式复制。

原因：

- 干净 GitHub 仓库应呈现产品代码，而不是开发过程档案。
- 白名单能避免 `.env`、过程文档、临时输出、历史报告误入仓库。
- 评委只需要看到可运行代码、必要文档、可复现测试。

### 3.1 必须复制

```text
README.md
LICENSE
.gitignore
.env.example
profile.yaml
pytest.ini
requirements.txt
Dockerfile
docker-compose.yml
src/
web/
scripts/
data/
docs/API.md
docs/ARCHITECTURE.md
agents/tdd/*.py
agents/tdd/playwright/
agents/tdd/README.md
agents/tdd/TDD.md
agents/tdd/DEMO_双场景回归测试计划.md
agents/tdd/playwright/requirements.txt
agents/tdd/playwright/install_browsers.sh
```

### 3.2 可选复制

```text
AGENTS.md
agents/DBA_AGENT.md
agents/TDD_AGENT.md
docs/superpowers/specs/2026-08-01-profile-config-design.md
```

说明：

- `AGENTS.md` 对评委不是必要文件；如果担心暴露内部 agent 约束，可不复制。
- `docs/superpowers/` 仅在需要解释配置设计时复制，否则不进入参赛仓库。

### 3.3 不复制

```text
agents/pm/
agents/sa/
agents/tdd/*实现计划.md
agents/tdd/*报告.md
agents/tdd/*移交文档.md
agents/tdd/BE-*.md
agents/tdd/FE-*.md
agents/tdd/screenshots/
agents/tdd/playwright/videos/
agents/tdd/playwright/screenshots/
docs/frontend-demos/
output/
evidence-01.md
.summary.md
CHAT_INTERFACE_FIX.md
analysis_sequence_diagram_manage_assets.md
test_chat.py
test_chat_diagnosis.py
opencode.json
.opencode/
.codegraph/
```

历史过程文档在本地开发仓库保留即可，不进入 GitHub 交付仓库。

## 4. 禁止复制内容

以下文件/目录不得进入 GitHub：

```text
.env
.DS_Store
__pycache__/
.pytest_cache/
web/node_modules/
web/dist/
web/tsconfig.tsbuildinfo
output/
*.log
*.process_id
```

如目标仓库需要保留前端构建产物，必须由 PM 单独批准；默认不提交 `web/dist`。

## 5. 复制前收口清单

### 5.1 Git 状态

要求：

```bash
git status --short
```

只允许出现明确要提交/复制的文档；不允许出现：

- `.env`
- `node_modules`
- `dist`
- 临时日志
- 旧 Gradio 文件
- 状态过期的移交文档

当前待处理：

```text
agents/pm/FE-11_删除Gradio旧前端开发规格.md
agents/pm/PERF-01_数据库连接池与首屏聚合加载开发规格书.md
agents/pm/GH-01_复制代码到GitHub空仓库计划.md
agents/tdd/plan_01_三个已知问题修复_20260805.md
agents/tdd/测试移交文档.md
```

建议：

- `agents/pm/FE-11_删除Gradio旧前端开发规格.md`：本地保留，不复制到 GitHub。
- `agents/pm/PERF-01_数据库连接池与首屏聚合加载开发规格书.md`：本地保留，不复制到 GitHub。
- `agents/pm/GH-01_复制代码到GitHub空仓库计划.md`：本地执行计划，不复制到 GitHub。
- `agents/tdd/plan_01_三个已知问题修复_20260805.md`：过程修复计划，不复制到 GitHub。
- `agents/tdd/测试移交文档.md`：本地保留或删除，不复制到 GitHub。

### 5.2 安全扫描

```bash
rg -n "sk-|AKIA|api[_-]?key|secret|password|token" web/src src scripts agents docs README.md --type py --type ts --type md
rg -n '"pid"|"oid"|\bpid\b|\boid\b' src web/src agents/tdd/playwright
rg -n 'person_id|organization_id|membership_id|account_id|resource_id|warehouse_id|transaction_id' web/src
rg -n "gradio|src/frontend.py|python src/frontend.py|7860" README.md docs/ARCHITECTURE.md scripts requirements.txt
rg --files -g '*.process_id' .
```

验收口径：

- 无真实密钥。
- `web/src` 不出现 DB 数字 ID 对外字段。
- `src` / `web/src` 不恢复旧短别名。
- `gradio` 不在依赖和运行入口中出现。
- `7860` 只允许作为迁移说明出现，不允许作为启动端口。
- 无 `*.process_id` 文件进入仓库。

### 5.3 构建与测试

```bash
python3 -m compileall src agents/tdd
python3 -m pytest agents/tdd/test_config.py agents/tdd/test_perf01_aggregate_and_pool.py -v
cd web && npm run test
cd web && npm run build
git diff --check
```

如远程测试库可用，再补：

```bash
python3 -m pytest agents/tdd/test_demo_smoke.py agents/tdd/test_recording_smoke.py -v
```

## 6. 复制执行步骤

执行顺序：

1. 在当前工作区完成前置收口。
2. 确认目标目录 `/data/research/amd.com/ur-agent` 是空仓库或只含 `.git/`。
3. 白名单创建目录：

```bash
mkdir -p /data/research/amd.com/ur-agent
mkdir -p /data/research/amd.com/ur-agent/docs
mkdir -p /data/research/amd.com/ur-agent/agents/tdd
mkdir -p /data/research/amd.com/ur-agent/agents/tdd/playwright
```

4. 复制根文件：

```bash
cp README.md LICENSE .gitignore .env.example profile.yaml pytest.ini requirements.txt Dockerfile docker-compose.yml \
  /data/research/amd.com/ur-agent/
```

5. 复制代码与运行资源：

```bash
rsync -av \
  --exclude '__pycache__/' \
  --exclude '.DS_Store' \
  --exclude '*.pyc' \
  src/ /data/research/amd.com/ur-agent/src/

rsync -av \
  --exclude 'node_modules/' \
  --exclude 'dist/' \
  --exclude 'tsconfig.tsbuildinfo' \
  --exclude '.DS_Store' \
  web/ /data/research/amd.com/ur-agent/web/

rsync -av --exclude '__pycache__/' --exclude '.DS_Store' --exclude '*.pyc' \
  scripts/ /data/research/amd.com/ur-agent/scripts/

rsync -av --exclude '.DS_Store' \
  data/ /data/research/amd.com/ur-agent/data/
```

6. 复制面向评委/用户的文档：

```bash
cp docs/API.md docs/ARCHITECTURE.md /data/research/amd.com/ur-agent/docs/
```

7. 复制可复现测试：

```bash
cp agents/tdd/*.py /data/research/amd.com/ur-agent/agents/tdd/
cp agents/tdd/README.md agents/tdd/TDD.md agents/tdd/DEMO_双场景回归测试计划.md \
  /data/research/amd.com/ur-agent/agents/tdd/
cp agents/tdd/playwright/requirements.txt agents/tdd/playwright/install_browsers.sh \
  /data/research/amd.com/ur-agent/agents/tdd/playwright/
rsync -av \
  --exclude 'videos/' \
  --exclude 'screenshots/' \
  --exclude '__pycache__/' \
  --exclude '.DS_Store' \
  --exclude '*.pyc' \
  agents/tdd/playwright/ /data/research/amd.com/ur-agent/agents/tdd/playwright/
```

8. 进入目标仓库：

```bash
cd /data/research/amd.com/ur-agent
git status --short
```

9. 目标仓库复制结果反查：

```bash
find . -name '.env' -o -name '.DS_Store' -o -name '__pycache__' -o -name 'node_modules' -o -name 'dist' -o -path '*/playwright/videos' -o -path '*/playwright/screenshots'
find agents -path 'agents/pm' -o -path 'agents/sa' -o -name '*移交文档.md' -o -name '*实现报告.md' -o -name '*开发计划.md'
rg -n "gradio|src/frontend.py|python src/frontend.py|7860" README.md docs/ARCHITECTURE.md scripts requirements.txt
```

验收口径：

- 第一条命令在安装和构建前必须无输出。
- 第二条命令无输出。
- 第三条命令不得出现旧前端启动路径、依赖或端口；历史迁移说明如需保留，必须不影响启动指引。

10. 在目标仓库内重新跑验证：

```bash
python3 -m compileall src agents/tdd
python3 -m pytest agents/tdd/test_config.py agents/tdd/test_perf01_aggregate_and_pool.py -v
cd web && npm install
npm run test
npm run build
```

11. 构建后提交前检查：

```bash
git status --short
git status --short --ignored
```

验收口径：

- `git status --short` 只能出现白名单复制文件，不得出现 `.env`、`.DS_Store`、过程文档。
- `web/node_modules/`、`web/dist/` 如出现，必须只出现在 ignored 列表中，不能进入待提交列表。

12. 首次提交：

```bash
git add README.md LICENSE .gitignore .env.example profile.yaml pytest.ini requirements.txt Dockerfile docker-compose.yml
git add src/ web/ scripts/ data/
git add docs/API.md docs/ARCHITECTURE.md
git add agents/tdd/*.py agents/tdd/README.md agents/tdd/TDD.md agents/tdd/DEMO_双场景回归测试计划.md
git add agents/tdd/playwright/
git commit -m "feat: initial Uni-Resource Agent competition submission"
git push origin main
```

## 7. README 首屏要求

GitHub 首页 README 必须让评委 3 分钟内看懂：

1. 产品一句话：One AI. All Your Worlds.
2. 核心亮点：多空间上下文、资源统一建模、本地/私有 AI、卖家经营闭环、战役/家庭/舰队演示空间。
3. 快速启动：
   - 后端 8000
   - 前端 5173
4. Demo 账号说明：
   - 账号名可以写。
   - 密码不写真实值，只说明从 `.env` 配置或由演示环境提供。
5. 安全说明：
   - 不提交 `.env`
   - `profile.yaml` 无机密
   - API 不暴露 DB 数字 ID

## 8. PM 验收标准

复制到 GitHub 后，PM 按以下标准放行：

- GitHub 仓库可 clone 后按 README 启动。
- `requirements.txt` 无 `gradio`。
- `src/frontend.py` 不存在。
- Vue 前端测试和构建通过。
- 后端基础测试通过。
- `.env` 未提交。
- 无真实 API key / DB 密码 / JWT secret。
- README 不再指导启动旧前端。
- Playwright 录屏入口仍是 `localhost:5173`。
- `agents/pm/`、`agents/sa/`、中间开发计划、移交文档不进入 GitHub 交付仓库。

## 9. 后续任务

复制完成后再安排：

- `GH-02`：目录重命名评估与实施，考虑 `web/ -> frontend/`、`src/ -> backend/src/`。
- `OPS-01`：生产部署脚本，考虑 FastAPI + Vue dist/Nginx。
- `QA-01`：GitHub 仓库 clone 后的一键验收脚本。
