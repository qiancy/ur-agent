#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T5 QA 截图脚本：用 playwright + 本地 Chrome 截取 CR-01 演示验收 5 张图。

前置：
  - 后端 :8000 与前端 :5174 均已启动；
  - 登录密码来自环境变量 DEMO_ZHANSAN_PASSWORD 或未提交的 .env（不得写入源码）。
输出：agents/tdd/screenshots/qa_*.png
"""
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "agents" / "tdd" / "screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)

from dotenv import load_dotenv

# 优先级：环境变量 > 未提交 .env；override=False 保证 shell 环境优先
load_dotenv(REPO_ROOT / ".env", override=False)

from playwright.sync_api import sync_playwright

FRONTEND = os.getenv("FE_URL", "http://localhost:5174")
LOGIN = os.getenv("DEMO_LOGIN", "zhansan")
PASSWORD = os.getenv("DEMO_ZHANSAN_PASSWORD", "").strip()
if not PASSWORD:
    raise RuntimeError("DEMO_ZHANSAN_PASSWORD is required for QA screenshots")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def shot(page, name, width, height=900):
    page.set_viewport_size({"width": width, "height": height})
    page.wait_for_timeout(800)
    path = OUT_DIR / f"qa_{name}_{width}px.png"
    page.screenshot(path=str(path), full_page=False)
    print(f"[ok] {path}")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME, headless=True)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()

        page.goto(FRONTEND, wait_until="networkidle")
        page.evaluate("localStorage.clear()")
        page.goto(FRONTEND, wait_until="networkidle")
        page.wait_for_selector('[data-test="login-form"]', timeout=30000)
        page.fill('[data-test="login"]', LOGIN)
        page.fill('[data-test="password"]', PASSWORD)
        page.click('button[type="submit"]')
        page.wait_for_selector('[data-test="app-header"]', timeout=20000)
        page.wait_for_timeout(1500)

        shot(page, "01_workbench", 1440)

        page.click('[data-test="space-menu-toggle"]')
        page.wait_for_timeout(500)
        shot(page, "02_space_menu", 1440)
        page.keyboard.press("Escape")
        page.click('[data-test="space-menu-toggle"]')

        # 切到非 ecommerce（家庭/舰队）通用观察面板
        page.select_option('[data-test="org-switch"]', "fire_xinye_shu")
        page.wait_for_selector('[data-test="generic-space"]', timeout=20000)
        page.wait_for_selector('[data-test="ov-name"]', timeout=20000)
        page.wait_for_timeout(1000)
        shot(page, "03_non_ecommerce", 1440)

        # 1280 无横向溢出
        shot(page, "04_1280", 1280)

        # 窄屏 header
        shot(page, "05_narrow", 480, 900)

        browser.close()


if __name__ == "__main__":
    raise SystemExit(main())
