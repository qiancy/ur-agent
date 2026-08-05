# Git Worktree 开发交付双仓工作流指南

> 日期：2026-08-05
> 适用范围：Uni-Resource Agent 开发主仓（unires-agent）与交付仓（ur-agent）

---

## 1. 什么是 git worktree

Git worktree 允许你同时检出同一个仓库的**多个分支**到**不同的目录**中，每个目录都是一个独立的 working tree，可以分别编辑、提交、切换分支，互不干扰。

```
/Volumes/data/research/amd.com/unires/unires-agent/   ← dev 分支（开发主仓）
/data/research/amd.com/ur-agent/                       ← release/github 分支（交付仓）
```

两个目录共享同一个 `.git/objects` 和 `.git/refs`，只是工作文件和 HEAD 不同。

---

## 2. 当前项目的 worktree 配置

### 2.1 两个 worktree 的职责

| Worktree | 路径 | 分支 | 职责 | 能否修改业务代码 |
|----------|------|------|------|-----------------|
| 开发主仓 | `/Volumes/data/research/amd.com/unires/unires-agent` | `dev` | 日常开发、测试、调试 | ✅ 可以 |
| 交付仓 | `/data/research/amd.com/ur-agent` | `release/github` | 只读检查、安全扫描、发布 | ❌ 不可以 |

### 2.2 当前 worktree 注册信息

执行 `git worktree list --porcelain` 可以看到：

```
worktree /Volumes/data/research/amd.com/unires/unires-agent
HEAD 59e0eaa...
branch refs/heads/dev

worktree /data/research/amd.com/ur-agent
HEAD ae84b20...
branch refs/heads/release/github
```

**注意**：`HEAD` 指向每个 worktree 当前所在的 commit，切换分支时会自动更新。

---

## 3. 日常开发流程

### 3.1 在开发主仓（unires-agent）工作

```bash
cd /Volumes/data/research/amd.com/unires/unires-agent

# 确认在 dev 分支
git branch --show-current
# 输出：dev

# 正常开发：修改代码、运行测试
PYTHONPATH=. python -m uvicorn src.app:app --host 127.0.0.1 --port 8000

# 提交
git add .
git commit -m "feat: something"

# 推送
git push origin dev
```

### 3.2 同步到交付仓

开发完成后，将 `dev` 分支合并到 `release/github`，然后推送到 GitHub：

```bash
# 方式一：在开发主仓合并，再推送到 worktree
cd /Volumes/data/research/amd.com/unires/unires-agent

# 确保 dev 分支是最新的
git checkout dev
git pull origin dev

# 合并到 release/github
git switch release/github
git merge dev --no-edit

# 推送到 worktree（自动同步到 /data/research/amd.com/ur-agent）
git push origin release/github

# 推送到 GitHub
git push github release/github:main
```

```bash
# 方式二：直接在交付 worktree 中合并
cd /data/research/amd.com/ur-agent

# 从开发主仓拉取最新 dev
git fetch origin dev:dev

# 合并到当前分支（release/github）
git merge dev --no-edit

# 推送到 GitHub
git push github HEAD:main
```

### 3.3 在交付仓做检查（只读）

```bash
cd /data/research/amd.com/ur-agent

# 确认在 release/github 分支
git branch --show-current
# 输出：release/github

# 运行验收测试
PYTHONPATH=. python3 -m compileall src scripts ../tests
PYTHONPATH=. python3 -m pytest -c ../pytest.ini ../tests/backend/test_config.py -v

cd frontend
npm run test
npm run build
```

**注意**：交付仓的修改会同时出现在 release/github 分支上。如果需要在交付仓做临时修复，修改后需要提交并推送。

---

## 4. 常用 worktree 命令

### 4.1 查看当前 worktree 列表

```bash
git worktree list --porcelain
```

输出示例：
```
worktree /Volumes/data/research/amd.com/unires/unires-agent
HEAD 59e0eaa...
branch refs/heads/dev

worktree /data/research/amd.com/ur-agent
HEAD ae84b20...
branch refs/heads/release/github
```

### 4.2 添加新的 worktree

```bash
# 从 dev 分支创建一个新的 worktree
git worktree add /path/to/new-worktree dev
```

### 4.3 移除 worktree

```bash
# 先切换到其他分支
git switch dev

# 移除 worktree
git worktree remove /data/research/amd.com/ur-agent
```

### 4.4 清理 worktree 注册

如果 worktree 目录被手动删除，Git 的注册信息会残留。清理方法：

```bash
# 查看 worktree 列表，确认哪些已失效
git worktree list

# 清理失效的注册（不会删除实际文件）
git worktree prune
```

---

## 5. 分支流转图

```
开发主仓 (dev)
    │
    │ 日常开发、测试
    │ git add . && git commit && git push origin dev
    │
    ├──────────────────────────────────────┐
    │                                      │
    ▼                                      ▼
release/github ──► GitHub main (ur-agent)
    │                 比赛/公开交付
    │ git push github HEAD:main
    │
    ▼
/data/research/amd.com/ur-agent (worktree)
    交付仓，只读检查、安全扫描、验证
```

---

## 6. 注意事项

### 6.1 不要在交付仓修改业务代码

`release/github` 分支的设计目的是作为**交付快照**，不是第二开发分支。如果需要修复 bug：
1. 在开发主仓（`dev`）修复
2. 提交并推送到 `dev`
3. 合并到 `release/github`
4. 推送到 GitHub

### 6.2 worktree 共享 .git 目录

所有 worktree 共享同一个 `.git/objects` 和 `.git/refs`，这意味着：
- 在一个 worktree 中提交，其他 worktree 也能看到这些提交
- 但 `HEAD`（当前分支）是每个 worktree 独立的
- 如果在一个 worktree 中删除了分支，其他 worktree 也会受影响

### 6.3 不能在同一目录打开同一分支两次

```bash
# 错误：不能在同一个目录再 add 一个 worktree
git worktree add /Volumes/.../unires-agent dev
# 报错：'.../unires-agent' is already checked out at '.../unires-agent'
```

### 6.4 如果 ur-agent 目录被占用

如果 `/data/research/amd.com/ur-agent` 目录被其他进程占用（如打开在 VS Code 中），`git worktree add` 会失败。需要先关闭占用进程。

### 6.5 推送命令速查

| 操作 | 命令 |
|------|------|
| 推送 dev 到 origin | `git push origin dev` |
| 推送 release/github 到 lab2 | `git push origin release/github` |
| 推送 release/github 到 GitHub | `git push github release/github:main` |
| 强制推送（仅需 PM 批准后） | `git push github release/github:main --force-with-lease` |

---

## 7. 故障排查

### 7.1 worktree 注册失效

如果 worktree 目录被删除，但 Git 仍认为它存在：

```bash
git worktree list
# 可能会看到失效的 worktree

# 清理失效注册
git worktree prune
```

### 7.2 分支被占用无法切换

如果切换分支时报错"branch is currently checked out at..."：

```bash
# 查看哪个 worktree 正在使用该分支
git worktree list --porcelain | grep -A2 "branch refs/heads/your-branch"

# 切换到该 worktree 后切换其他分支，或关闭占用进程
```

### 7.3 恢复备份的 ur-agent

如果 worktree 出现问题，可以回退到备份：

```bash
# 移除当前 worktree
git worktree remove /data/research/amd.com/ur-agent

# 从备份恢复
mv /data/research/amd.com/ur-agent.backup-20260805 /data/research/amd.com/ur-agent

# 重新添加 worktree（如需要）
git worktree add /data/research/amd.com/ur-agent release/github
```

---

## 8. 相关文档

- [DEV-REORG_开发仓交付仓结构对齐与上下文保留计划.md](../pm/DEV-REORG_开发仓交付仓结构对齐与上下文保留计划.md)
- [GH-01_复制代码到GitHub空仓库计划.md](../pm/035_doc_复制代码到GitHub空仓库计划_v1_20260805.md)
