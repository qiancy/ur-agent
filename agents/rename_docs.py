#!/usr/bin/env python3
"""
批量重命名 agents/ 下所有文档，遵循命名规则：
  序号_类型_主题_修订版本号(reversion)_日期.后缀

按文件创建时间排序（相同时间按文件名字母序），每个子目录内独立编号。
日期来源优先级：文件名内嵌日期 > git log --follow 最后提交日期 > 文件创建时间。
排除：rename_docs.py、README.md、playwright/、__pycache__/。
"""
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime

AGENTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "agents")
VERSION = "v1"
DATE_FMT = "%Y%m%d"

EXT_TYPE = {".md": "doc", ".py": "test", ".txt": "txt"}

KNOWN_PREFIXES = [
    r"BE[-_]?\d+", r"FE[-_]?\d+", r"AUTH[-_]?\d+", r"CR[-_]?\d+",
    r"PERF[-_]?\d+", r"GH[-_]?\d+", r"ORG[-_]?\d+",
    r"DEMO[-_]?DATA[-_]?\d*", r"DEMO[-_]?", r"uc\d+", r"u\d+",
    r"README", r"ASSISTANT_AGENT", r"DBA_AGENT", r"PM_AGENT",
    r"SA_AGENT", r"TDD_AGENT", r"conftest",
    # setup_fire_newye_campaign 不在此列，由下方手动剥离 setup_ 处理
    r"test_", r"plan_\d+", r"plan_",
    r"初始化API实现建议", r"测试报告", r"回归测试计划",
    r"测试执行指南", r"测试移交文档", r"火烧新野战役故事文档",
    r"场景优先级评估",
    r"\d+[-_]",
    r"requirements",
]
# 长前缀在前，短前缀在后，确保优先匹配更长的前缀
PREFIX_RE = re.compile(r"^(" + "|".join(KNOWN_PREFIXES) + r")", re.IGNORECASE)

# 从文件名中提取日期（如 plan_01_三个已知问题修复_20260805.md）
FILENAME_DATE_RE = re.compile(r"_(\d{8})(\.\w+)?$")
SKIP_FILES = {"README.md", "rename_docs.py", "conftest.py", "requirements.txt"}


def get_ftype(filepath: str) -> str:
    base = os.path.basename(filepath)
    if base == "conftest.py":
        return "fixture"
    if base == "requirements.txt":
        return "dep"
    _, ext = os.path.splitext(filepath)
    if base.startswith("test_"):
        return "test"
    if base.startswith("setup_"):
        return "setup"
    return EXT_TYPE.get(ext, "doc")


def get_topic(filepath: str) -> str:
    name = os.path.splitext(os.path.basename(filepath))[0]
    for cn, num in {"一": "1", "二": "2", "三": "3", "四": "4", "五": "5"}.items():
        name = name.replace(cn, num)
    # 去掉文件名中已有的日期后缀（如 _20260805）
    name = FILENAME_DATE_RE.sub("", name)
    name = PREFIX_RE.sub("", name)
    # 剥离 setup_ 前缀（如 setup_fire_newye_campaign → fire_newye_campaign）
    if name.startswith("setup_"):
        name = name[len("setup_"):]
    name = re.sub(r"[-_]+", "_", name).strip("_")
    name = name.replace(" ", "_")
    if not name:
        name = re.sub(r"[-_]+", "_", os.path.splitext(os.path.basename(filepath))[0]).strip("_")
    return name


def _git_date(filepath: str) -> str | None:
    """尝试用 git log --follow 获取文件首次提交日期。"""
    try:
        result = subprocess.run(
            ["git", "log", "--follow", "--format=%ci", "--diff-filter=A", "-1", "--", filepath],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            # %ci = committer date, ISO format: 2026-08-05 03:35:00 +0800
            date_str = result.stdout.strip().split()[0]
            return date_str.replace("-", "")
    except Exception:
        pass
    return None


def _filename_date(filepath: str) -> str | None:
    """从文件名中提取日期。"""
    m = FILENAME_DATE_RE.search(os.path.basename(filepath))
    if m:
        return m.group(1)
    return None


def get_date(filepath: str) -> str:
    """日期来源：文件名内嵌日期 > git 首次提交日期 > 文件创建时间。"""
    # 优先：文件名中的日期
    fd = _filename_date(filepath)
    if fd:
        return fd
    # 其次：git 首次提交日期
    gd = _git_date(filepath)
    if gd:
        return gd
    # 兜底：文件创建时间
    return datetime.fromtimestamp(os.path.getctime(filepath)).strftime(DATE_FMT)


def collect_groups() -> dict:
    groups = defaultdict(list)
    for root, dirs, files in os.walk(AGENTS_DIR):
        dirs[:] = [d for d in dirs if d not in ("playwright", "__pycache__")]
        for f in files:
            _, ext = os.path.splitext(f)
            if ext not in EXT_TYPE:
                continue
            if f in SKIP_FILES:
                continue
            if re.match(r"^\d{3}_", f):
                continue
            groups[root].append(os.path.join(root, f))
    for g in groups:
        groups[g].sort(key=lambda fp: (os.path.getctime(fp), os.path.basename(fp).lower()))
    return groups


def main(dry_run=True):
    groups = collect_groups()
    grand_total = 0
    all_moves = []

    for subdir in sorted(groups):
        files = groups[subdir]
        label = os.path.relpath(subdir, AGENTS_DIR)
        print(f"\n=== {label}/ ({len(files)} files) ===")

        for seq, fp in enumerate(files, 1):
            ftype = get_ftype(fp)
            topic = get_topic(fp)
            date = get_date(fp)
            ext = os.path.splitext(fp)[1]
            new_name = f"{seq:d}_{ftype}_{topic}_{VERSION}_{date}{ext}"
            new_path = os.path.join(subdir, new_name)
            old_name = os.path.basename(fp)

            if old_name == new_name:
                print(f"  = {old_name}")
                continue

            print(f"  {old_name}")
            print(f"    -> {new_name}")
            all_moves.append((fp, new_path))
            grand_total += 1

    print(f"\n{'='*60}")
    print(f"总计: {grand_total} 个文件需要重命名")

    if dry_run:
        print("\n[DRY RUN] 未执行实际操作。加 --execute 参数执行。")
        return

    for old_path, new_path in all_moves:
        os.rename(old_path, new_path)
        print(f"mv {old_path} -> {new_path}")

    print(f"\n完成: {grand_total} 个文件已重命名")


if __name__ == "__main__":
    main(dry_run="--execute" not in sys.argv)
