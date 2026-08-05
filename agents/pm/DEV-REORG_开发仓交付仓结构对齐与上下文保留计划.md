# 开发仓交付仓结构对齐与上下文保留计划

> 角色：项目经理
> 日期：2026-08-05
> 状态：按开发组 review 修订，可下发执行
> 核心目标：先整理开发主仓 `/Volumes/data/research/amd.com/unires/unires-agent`，形成与交付仓一致的 `backend/`、`frontend/`、`docs/`、`tests/` 产品结构；再把 `/data/research/amd.com/ur-agent` 收敛为同一仓库的 release worktree，避免后续手工复制导致漂移。

## 1. PM 结论

采纳开发组 review 中的关键意见，并明确执行路线：

1. 当前最高优先级是**整理开发主仓结构**，不是继续在交付仓里手工修补。
2. `/data/research/amd.com/ur-agent` 当前已经是独立 Git 仓库，不能直接覆盖。PM 决策采用 **方案 B：先备份现有 `ur-agent`，再重建为 `release/github` worktree**。
3. GitHub 空仓库最终只接收 `release/github` 分支。是否删除 GitHub 仓库重建或 `push --force`，必须在 release worktree 全部验收通过后由 PM 二次确认。
4. `agents/`、`AGENTS.md`、PM/TDD/SA 中间文档保留在开发主仓，不进入公开交付仓。
5. 目录移动、路径修复、测试迁移必须有可复现命令，不能只写原则。

不采纳长期保留两个独立仓库手工同步。短期看脚本同步成本低，但后续会持续出现“开发仓能跑、交付仓不一致”的问题，不适合比赛前最后收口。

## 2. 当前事实基线

开发主仓当前仍是旧结构：

```text
src/        # 后端代码，尚未移动
web/        # Vue 前端，尚未移动
scripts/    # 后端脚本，尚未移动
data/       # 后端 seed 数据，尚未移动
agents/     # 开发上下文，必须保留
docs/       # 产品文档，保留
backend/    # 不存在
frontend/   # 不存在
tests/      # 不存在
```

已知工作区状态：

- 当前分支：`protect/pre-ur-agent-copy-20260805`
- 已有未提交路径相关改动：`README.md`、`docs/ARCHITECTURE.md`、`scripts/unires_agent.sh`
- 另有无关改动：`AGENTS.md`、SA 模板 docx 文件名变化
- 计划文件：`agents/pm/DEV-REORG_开发仓交付仓结构对齐与上下文保留计划.md`

交付目录当前是独立仓库：

```text
/data/research/amd.com/ur-agent
branch: main
remotes:
  lab2   ssh://git@1.117.223.223:3322/unires/ur-agent.git
  origin git@github.com:qiancy/ur-agent.git
```

该目录已有提交和未提交文档改动，必须先备份，不能直接 `rm -rf` 或覆盖。

## 3. 目标目录

开发主仓目标结构：

```text
unires-agent/
├── backend/
│   ├── src/
│   ├── scripts/
│   ├── data/
│   ├── requirements.txt
│   ├── profile.yaml
│   ├── .env.example
│   └── Dockerfile
├── frontend/
├── docs/
├── tests/
│   ├── backend/
│   └── playwright/
├── README.md
├── docker-compose.yml
├── pytest.ini
├── LICENSE
├── AGENTS.md       # 仅开发主仓保留
└── agents/         # 仅开发主仓保留
```

交付 worktree 目标结构：

```text
ur-agent/
├── backend/
├── frontend/
├── docs/
├── tests/
├── README.md
├── docker-compose.yml
├── pytest.ini
└── LICENSE
```

差异规则：

- 开发主仓保留 `agents/`、`AGENTS.md`、内部过程文档。
- 交付 worktree 禁止出现 `agents/`、`AGENTS.md`、`.env`、缓存、截图、视频、过程报告、个人工具配置。
- 后端 Python 包名仍为 `src`，不改成 `backend.src`。后端命令统一在 `backend/` 目录内执行：`PYTHONPATH=. python3 -m uvicorn src.app:app ...`。

## 4. `ur-agent` 处理方案

### 4.1 采用方案 B：备份后转 worktree

执行前必须先完成备份记录：

```bash
git -C /data/research/amd.com/ur-agent status --short --branch
git -C /data/research/amd.com/ur-agent remote -v
git -C /data/research/amd.com/ur-agent log --oneline -10
```

备份建议：

```bash
mv /data/research/amd.com/ur-agent /data/research/amd.com/ur-agent.backup-20260805
```

或使用带时间戳的目录名：

```bash
mv /data/research/amd.com/ur-agent /data/research/amd.com/ur-agent.backup-20260805-HHMMSS
```

备份验收：

- 备份目录存在。
- 备份目录中 `.git/` 存在。
- `git -C <backup-dir> status --short --branch` 可正常执行。
- `lab2` 与 `origin` remote 已记录。

只有备份验收通过，才能在原路径创建 worktree：

```bash
git worktree add /data/research/amd.com/ur-agent release/github
```

如果 `release/github` 分支不存在，先从开发主线创建：

```bash
git switch dev
git switch -c release/github
git switch dev
git worktree add /data/research/amd.com/ur-agent release/github
```

> 注意：实际分支名以当前项目主线为准。如果当前仍使用保护分支推进，则先在保护分支完成重构并验收，再合并到 `dev`，最后从 `dev` 创建 `release/github`。

### 4.2 GitHub 清理策略

GitHub 端有两种可选方式：

- 推荐：保留远程仓库，等 `release/github` 全绿后执行一次 `push --force-with-lease`，把历史收敛为干净交付分支。
- 备选：删除并重建 GitHub 仓库，然后首次推送 `release/github`。

两种方式都属于发布动作，开发组不得自行执行。必须由 PM 明确批准后进行。

## 5. 开发主仓重构执行步骤

### 5.1 阶段一：保护与盘点

先确认分支和工作区：

```bash
git branch --show-current
git status --short
git diff -- README.md docs/ARCHITECTURE.md docker-compose.yml scripts/unires_agent.sh
git diff -- AGENTS.md
```

处理原则：

- `DEV-REORG` 计划文档可单独提交。
- 不要把 SA 模板 docx 文件名变化混入目录重构提交。
- 当前 SA 模板文件名修正（`.docx.docx` -> `.docx`）由 SA 负责人单独提交；如开发组代为提交，也必须使用独立提交，不得与 DEV-REORG 混在一起。
- 不要单独提交“指向 `backend/` 但目录还不存在”的 README/脚本改动；这些路径修复应与目录移动进入同一个可运行提交。
- `.env` 只保留本地，不移动、不提交。后续后端运行需要 `backend/.env` 时，由开发者本地复制，不能进入 Git。

关闭可能占用路径和端口的进程：

```bash
pkill -f uvicorn || true
pkill -f "npm run dev" || true
pkill -f vite || true
```

### 5.2 阶段二：目录移动

用 `git mv` 保留历史：

```bash
mkdir -p backend tests/backend tests/playwright

git mv src backend/src
git mv scripts backend/scripts
git mv data backend/data
git mv web frontend

git mv requirements.txt backend/requirements.txt
git mv profile.yaml backend/profile.yaml
git mv .env.example backend/.env.example
git mv Dockerfile backend/Dockerfile
```

保持根目录文件：

- `README.md`
- `docker-compose.yml`
- `pytest.ini`
- `LICENSE`
- `.gitignore`
- `docs/`
- `agents/`
- `AGENTS.md`

不得移动真实 `.env`。如果本地开发需要，可以在重构后手工执行：

```bash
cp .env backend/.env
```

该命令只允许本地执行，`backend/.env` 必须被 `.gitignore` 忽略。

### 5.3 阶段三：测试迁移

将可执行测试从 `agents/tdd/` 收敛到 `tests/`，但保留历史计划、报告、截图在 `agents/tdd/`。

迁移规则：

- `agents/tdd/conftest.py` -> `tests/backend/conftest.py`
- `agents/tdd/[0-9]*.py` -> `tests/backend/`
- `agents/tdd/playwright/conftest.py` -> `tests/playwright/conftest.py`
- `agents/tdd/playwright/test_*.py` -> `tests/playwright/`
- `agents/tdd/playwright/requirements.txt` -> `tests/playwright/requirements.txt`
- `agents/tdd/playwright/run_recording.sh` -> `tests/playwright/run_recording.sh`
- `agents/tdd/playwright/install_browsers.sh` -> `tests/playwright/install_browsers.sh`
- `agents/tdd/playwright/README.md` -> `tests/playwright/README.md`

不迁移：

- `agents/tdd/*_doc_*.md`
- `agents/tdd/README.md`
- `agents/tdd/screenshots/`
- `agents/tdd/playwright/videos/`
- `agents/tdd/__pycache__/`

说明：

- 当前可执行后端测试文件均为数字前缀命名，例如 `10_test_seller_inventory_api_v1_20260731.py`。
- 不使用 `test_*.py` 作为迁移 glob，因为现有文件名并非以 `test_` 开头。
- `16_setup_fire_newye_campaign_v1_20260721.py` 是可执行辅助脚本，也进入 `tests/backend/`，但不应被 pytest 默认收集。

建议命令：

```bash
git mv agents/tdd/conftest.py tests/backend/conftest.py
for f in agents/tdd/[0-9]*.py; do git mv "$f" "tests/backend/$(basename "$f")"; done
git mv agents/tdd/playwright/conftest.py tests/playwright/conftest.py
git mv agents/tdd/playwright/test_*.py tests/playwright/
git mv agents/tdd/playwright/requirements.txt tests/playwright/requirements.txt
git mv agents/tdd/playwright/run_recording.sh tests/playwright/run_recording.sh
git mv agents/tdd/playwright/install_browsers.sh tests/playwright/install_browsers.sh
git mv agents/tdd/playwright/README.md tests/playwright/README.md
```

迁移后必须修正测试中的路径假设：

- 后端根目录：`REPO_ROOT / "backend"`
- 后端脚本：`backend/scripts/*.py`
- 后端数据：`backend/data/*`
- 前端目录：`frontend/`
- Playwright 视频目录：`tests/playwright/videos/`

### 5.4 阶段四：路径修复

必须统一以下入口：

```bash
cd backend && PYTHONPATH=. python3 -m uvicorn src.app:app --host 127.0.0.1 --port 8000
cd backend && PYTHONPATH=. python3 scripts/init_db.py
cd backend && PYTHONPATH=. python3 scripts/seed_recording_data.py
cd frontend && npm run dev -- --host 127.0.0.1 --port 5173
```

重点检查：

```bash
rg -n "agents/tdd|web/|cd web|src/app.py|scripts/init_db.py|data/campaigns|profile.yaml|\\.env.example" README.md docs docker-compose.yml backend frontend tests
rg -n "Path\\(__file__\\).*parents|REPO_ROOT|load_dotenv|profile.yaml|data/campaigns" backend/src backend/scripts tests
rg -n "agents/tdd/screenshots|agents/tdd/videos|playwright/videos" backend/scripts tests
```

修复要求：

- `backend/src/config.py` 的 `REPO_ROOT` 应指向 `backend/`，继续读取 `backend/profile.yaml` 和 `backend/.env`。
- `backend/src/auth/auth.py`、`backend/scripts/*.py` 的 `.env` 路径应指向 `backend/.env`。
- `backend/src/routers/campaign.py` 的 campaign data 路径应指向 `backend/data/campaigns`。
- `backend/scripts/capture_qa_screenshots.py` 如果保留在开发主仓，只能作为开发 QA 辅助工具；其截图输出目录必须显式指向开发仓 `agents/tdd/screenshots/`，不得作为 release worktree 录屏入口。
- Python import 仍使用 `from src...`，不做包名重命名。
- 前端 API base URL 逻辑不因目录名变化而改变。

### 5.5 阶段五：根目录清理

可直接物理清理的忽略产物：

```bash
rm -rf __pycache__ .pytest_cache output pytestdebug.log
find . -name "__pycache__" -type d -prune -exec rm -rf {} +
find . -name ".DS_Store" -type f -delete
```

需先归档或 PM 确认后处理的文件：

- `test_chat.py`
- `test_chat_diagnosis.py`
- `CHAT_INTERFACE_FIX.md`
- `evidence-01.md`
- `analysis_sequence_diagram_manage_assets.md`

建议策略：

- 如仍有排障价值，移动到 `agents/archive/`。
- 如确认无价值，再删除。
- 不允许把这些文件带入交付 worktree。

`opencode.json`、`.opencode/`、`.claude/`、`.codegraph/` 属个人/工具上下文，开发仓可保留本地忽略，交付仓必须排除。

## 6. 提交策略

建议拆成 4 个提交，避免一包混杂：

1. `docs(pm): approve DEV-REORG execution plan`
   - 只提交本计划文档。
2. `chore(repo): restructure source tree into backend frontend tests`
   - `src -> backend/src`
   - `web -> frontend`
   - `scripts -> backend/scripts`
   - `data -> backend/data`
   - 后端根配置文件移动
   - README、架构、启动脚本、Docker、pytest 路径修复
3. `test(repo): move executable tests out of agents context`
   - `agents/tdd/*.py -> tests/backend/`
   - `agents/tdd/playwright/* -> tests/playwright/`
   - 测试路径修复
4. `chore(release): create github release worktree`
   - 创建 `release/github`
   - `/data/research/amd.com/ur-agent` 备份后转 worktree
   - 清理 release 分支内部上下文

明确禁止：

- 把 SA 模板 docx 重命名和目录重构混到同一提交。
- 把 `.env`、截图、视频、缓存提交。
- 在 `release/github` worktree 直接修业务逻辑。
- 没有备份就删除 `/data/research/amd.com/ur-agent`。

## 7. 验收命令

### 7.1 结构验收

```bash
test -d backend/src
test -d backend/scripts
test -d backend/data
test -d frontend/src
test -d tests/backend
test -d tests/playwright
test ! -d src
test ! -d web
test -d agents
```

### 7.2 后端验收

```bash
cd backend
PYTHONPATH=. python3 -m compileall src scripts ../tests
PYTHONPATH=. python3 -m pytest -c ../pytest.ini ../tests/backend/24_test_config_v1_20260802.py ../tests/backend/26_test_perf01_aggregate_and_pool_v1_20260805.py -v
PYTHONPATH=. python3 -m pytest -c ../pytest.ini ../tests/backend/19_test_auth_api_v1_20260722.py ../tests/backend/21_test_demo_smoke_v1_20260804.py ../tests/backend/23_test_recording_smoke_v1_20260804.py -v
```

### 7.3 前端验收

```bash
cd frontend
npm run test
npm run build
```

如果刚执行完后端验收并仍停留在 `backend/` 目录，应使用：

```bash
cd ../frontend
npm run test
npm run build
```

### 7.4 Playwright 录屏验收

```bash
bash tests/playwright/install_browsers.sh
bash tests/playwright/run_recording.sh
```

### 7.5 安全与路径扫描

```bash
rg -n "sk-|AKIA|BEGIN RSA|PRIVATE KEY|DB_PASSWORD=.*[^<]" backend frontend docs tests README.md docker-compose.yml
rg -n '"pid"|"oid"|\bpid\b|\boid\b' backend/src frontend/src tests
rg -n "person_id|organization_id|account_id|membership_id|resource_id|warehouse_id|transaction_id" frontend/src backend/src/routers tests
rg -n "agents/tdd|web/|cd web|^src/|scripts/init_db.py" README.md docs docker-compose.yml backend frontend tests
```

扫描解释：

- 安全扫描命中文档中的“禁止字段集合”可以接受，但业务 DTO、前端展示、API 响应路径不得命中 DB 数字 ID。
- `backend/src/db/` 内部 SQL 使用 `person_id`、`organization_id` 是允许的。
- `agents/` 内历史文档可保留旧路径，但交付分支不得包含 `agents/`。

## 8. Release Worktree 验收

创建 worktree 后，在 `/data/research/amd.com/ur-agent` 内验证：

```bash
git status --short --branch
test -d backend/src
test -d frontend/src
test -d docs
test -d tests
test ! -d agents
test ! -f AGENTS.md
test ! -f .env
find . -name "__pycache__" -o -name ".DS_Store" -o -path "*/node_modules/*" -o -path "*/dist/*"
```

运行最小交付验收：

```bash
cd /data/research/amd.com/ur-agent/backend
PYTHONPATH=. python3 -m compileall src scripts ../tests

cd /data/research/amd.com/ur-agent/frontend
npm run build
```

GitHub 推送前必须确认：

- `git worktree list` 能看到 `/data/research/amd.com/ur-agent` 绑定到 `release/github`。
- `release/github` 分支只含产品文件。
- 远程 `origin` 指向目标 GitHub 仓库。
- PM 明确批准 `push --force-with-lease` 或重建仓库。

## 9. 风险与边界

- 当前 README 和架构文档已部分指向 `backend/` / `frontend/`，在目录移动完成前会短暂不一致。该不一致不能进入最终提交。
- `scripts/setup_env.sh` 仍可能写旧目录，应一并修复或标记废弃。
- `scripts/capture_qa_screenshots.py` 是开发仓 QA 截图工具，不是交付仓运行入口；release worktree 中应优先使用 `tests/playwright/`，不要从该脚本生成截图。
- 测试迁移后，`agents/tdd/` 的历史文档不要批量改路径；只更新新执行入口和交付文档。
- 如果 `ur-agent.backup-*` 中有需要保留的中文 pod 文档，应评估后合并到开发主仓 `docs/`，不要直接把整个备份仓混入。
- 若重构后测试因远端 DB 波动失败，必须单独重跑确认；结构性失败不得忽略。

## 10. 下发给开发组的执行口径

开发组按以下顺序推进：

1. 提交本计划文档，作为 PM 批准记录。
2. 排除无关 docx/个人工具文件，确认工作区只剩 DEV-REORG 相关改动。
3. 执行开发主仓目录重构，修复路径并跑后端/前端最小验收。
4. 迁移可执行测试到 `tests/`，保留 `agents/` 作为内部上下文。
5. 清理根目录缓存、日志、临时脚本；过程文档归档到 `agents/archive/` 或等 PM 删除确认。
6. 备份现有 `/data/research/amd.com/ur-agent`，验证备份可读。
7. 创建 `release/github` worktree 到 `/data/research/amd.com/ur-agent`。
8. 在 worktree 内做交付验收和安全扫描。
9. PM 确认后再处理 GitHub 远程：优先 `push --force-with-lease`，必要时删除并重建空仓。

完成标准：开发仓和交付仓产品结构一致，开发上下文完整保留，公开仓干净可运行。
