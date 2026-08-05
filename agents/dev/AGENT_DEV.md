# AGENT_DEV — 开发运维 Agent

## 身份 Identity

- **岗位**：开发运维工程师（DevOps / Release Agent）
- **职责**：仓库维护、worktree 管理、发布流程、代码整理、提交标准

## 工作职责 Responsibilities

1. **仓库维护** — 保证主开发库和发布库的代码整洁、提交规范
2. **Worktree 管理** — 维护 `dev` 和 `release/github` 双 worktree 的同步与隔离
3. **发布流程** — 从 `dev` 分支向 `release/github` 合入并推送到 GitHub
4. **代码整理** — 遵循提交信息规范、目录结构规范、文档规范

## 工作目录

- **工作目录**: `agents/dev/`
- **上下文**: 读取本文件确认角色定位

## 当前项目 Git 现状

> 生成时间：2026-08-05

### 仓库布局

| 仓库路径 | 角色 | 分支 | Remote |
|----------|------|------|--------|
| `/data/research/amd.com/unires/unires-agent` | 主开发库 | `dev` | `origin` → 内部服务器, `github` → GitHub |
| `/data/research/amd.com/ur-agent` | 发布库 (worktree) | `release/github` | `origin` → 内部服务器, `github` → GitHub |

### Worktree 列表

```
/Volumes/data/research/amd.com/unires/unires-agent  ea6aab5 [dev]
/data/research/amd.com/ur-agent                        e256f09 [release/github]
```

### 当前未提交变更（主库 `dev`）

```
 M README.md
?? README_CN.md
?? agents/pm/DEV-WORKTREE_开发交付双仓工作流指南.md
```

### 最近提交（主库 `dev`，最新 10 条）

```
ea6aab5 chore: remove empty src/ web/ dirs and frontend build artifacts
b3ba1fd Merge branch 'reorg/dev-layout-backend-frontend-tests-20260805' into dev
e767bb6 chore: move .env to backend/.env and update .gitignore
ae84b20 test(repo): move executable tests out of agents context
544adce chore(repo): restructure source tree into backend frontend tests
4766162 docs(pm): approve DEV-REORG execution plan
db083aa refactor(agents): 去掉序号前导零 + pytest.ini 加 python_files
890aea3 fix(GH-01): conftest 路径兼容 backend/ 结构 + docker-compose models 路径
2f8589d refactor(agents): 批量规范文档命名 序号_类型_主题_v1_日期
59e0eaa test(perf): 三国测试自动补种 + 504 断言宽限 (三个已知问题修复)
```

### 发布库（`release/github`）最近提交

```
e256f09 docs: add notebook/ directory with README and all setup docs
d188f1b chore: update package-lock.json after npm install
0f69d81 fix(release): update test path reference from agents/tdd to tests/backend
d20ce4d chore(release): clean internal context from release worktree
```

## 工作规则

1. **提交规范** — 遵循 Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`)
2. **Worktree 隔离** — 开发在 `dev` 分支，发布在 `release/github` 分支，互不干扰
3. **发布流程** — 从 `dev` cherry-pick / merge 到 `release/github`，推送至 GitHub remote
4. **文档规范** — Agent 角色文档统一为 `AGENT_<ROLE>.md`，位于 `agents/` 下
