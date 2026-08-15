"""Capture the README screenshots from a running stack.

These are real captures, not mockups. Bring the stack up and seed it first:

    docker compose -f docker-compose.yml up -d --build
    python scripts/init_data_via_api.py
    curl -X POST http://localhost:8000/train

Then run this script. Grafana's request-rate and latency panels only show a
curve if the platform has served traffic, so drive some predictions before
capturing if you want populated graphs.

Requires: pip install playwright && playwright install chromium
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

DOCS = Path(__file__).resolve().parent.parent / "docs"
GRAFANA_DASHBOARD = "/d/api-perf-dashboard/ai-performance-platform-e28094-metrics"


def _grafana_login(page: Page, base: str, user: str, password: str) -> None:
    page.goto(f"{base}/login", wait_until="networkidle")
    page.wait_for_timeout(2000)
    page.fill('input[name="user"]', user)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_timeout(4000)
    # Grafana interposes a "change password" step on first login.
    for label in ("Skip", "Skip now"):
        try:
            page.get_by_role("button", name=label).click(timeout=2500)
            page.wait_for_timeout(1500)
            return
        except Exception:
            continue


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grafana", default="http://localhost:3000")
    parser.add_argument("--prometheus", default="http://localhost:9090")
    parser.add_argument("--dashboard", default="http://localhost:8501")
    parser.add_argument("--grafana-user", default="admin")
    parser.add_argument("--grafana-password", default="admin")
    args = parser.parse_args()

    DOCS.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()

        # --- Prometheus targets -------------------------------------------
        page = browser.new_context(viewport={"width": 1440, "height": 900}).new_page()
        page.goto(f"{args.prometheus}/targets", wait_until="networkidle")
        page.wait_for_timeout(3000)
        page.screenshot(path=str(DOCS / "prometheus-screenshot.png"))
        print("wrote docs/prometheus-screenshot.png")

        # --- Grafana dashboard --------------------------------------------
        page = browser.new_context(viewport={"width": 1600, "height": 1250}).new_page()
        _grafana_login(page, args.grafana, args.grafana_user, args.grafana_password)
        page.goto(
            f"{args.grafana}{GRAFANA_DASHBOARD}?orgId=1&from=now-30m&to=now&kiosk",
            wait_until="networkidle",
        )
        page.wait_for_timeout(12000)  # panels query Prometheus before painting
        page.screenshot(path=str(DOCS / "grafana-screenshot.png"), full_page=True)
        print("wrote docs/grafana-screenshot.png")

        # --- Streamlit dashboard ------------------------------------------
        page = browser.new_context(viewport={"width": 1440, "height": 1000}).new_page()
        page.goto(args.dashboard, wait_until="networkidle")
        page.wait_for_timeout(15000)  # Streamlit renders progressively
        page.screenshot(path=str(DOCS / "dashboard-screenshot.png"), full_page=True)
        print("wrote docs/dashboard-screenshot.png")

        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
