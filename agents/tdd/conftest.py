"""
TDD conftest — session 级安全网与共享 fixture。
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"


def _check_account(login: str) -> bool:
    """检查账号是否存在，兼容开发仓（src/）和目标仓（backend/src/）。"""
    cmd = [
        sys.executable, "-c",
        "import sys; sys.path.insert(0, r'" + str(BACKEND_DIR) + "'); "
        "from src.db.database import get_db_connection; "
        "c = get_db_connection(); "
        "cur = c.cursor(); "
        "cur.execute('SELECT 1 FROM account WHERE login = %s', ('" + login + "',)); "
        "print('EXISTS' if cur.fetchone() else 'MISSING'); "
        "cur.close(); c.close()"
    ]
    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    return result.stdout.strip() == "EXISTS"


def _seed_if_missing(login: str, script_name: str) -> None:
    """账号不存在且环境变量存在时自动补种。"""
    if not _check_account(login):
        password_var = "DEMO_ZHANSAN_PASSWORD" if login == "zhansan" else "DEMO_LIUMING_PASSWORD"
        if os.getenv(password_var):
            subprocess.run(
                [sys.executable, str(BACKEND_DIR / "scripts" / script_name)],
                capture_output=True,
            )


@pytest.fixture(scope="session", autouse=True)
def _ensure_demo_data_survives():
    """session 级安全网：全量跑完后确保 demo 种子数据存在。

    注意：yield 后代码只在正常 session 结束时执行。
    pytest 被中断（Ctrl-C / crash）时不会执行，需手动补种。
    """
    yield
    _seed_if_missing("zhansan", "seed_demo_data.py")
    _seed_if_missing("liuming", "seed_recording_data.py")
