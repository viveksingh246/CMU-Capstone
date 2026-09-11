#!/usr/bin/env python3
"""Capture UI screenshots and chart assets for the capstone presentation."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS = PROJECT_ROOT / "docs" / "presentation_assets"
GALLERY = PROJECT_ROOT / "scripts" / "screenshot_gallery.py"
PORT = 8765
BASE = f"http://localhost:{PORT}"

VIEWS = [
    ("01_workspace", "workspace"),
    ("02_pipeline", "pipeline"),
    ("03_results", "results"),
    ("04_human_review", "human_review"),
    ("05_metrics", "metrics"),
]


def export_charts() -> None:
    sys.path.insert(0, str(PROJECT_ROOT))
    from scripts.demo_result import demo_scorecard
    from visualizations.charts import create_radar_chart, create_score_bar_chart

    ASSETS.mkdir(parents=True, exist_ok=True)
    scorecard = demo_scorecard()

    bar = create_score_bar_chart(scorecard)
    if bar is not None:
        bar.write_image(str(ASSETS / "06_scorecard_chart.png"), width=900, height=400, scale=2)

    radar = create_radar_chart(scorecard)
    if radar is not None:
        radar.write_image(str(ASSETS / "07_radar_chart.png"), width=900, height=420, scale=2)


def capture_streamlit_screenshots() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(GALLERY),
            "--server.headless",
            "true",
            "--server.port",
            str(PORT),
            "--browser.gatherUsageStats",
            "false",
        ],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        time.sleep(6)
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            for filename, view in VIEWS:
                url = f"{BASE}/?view={view}"
                page.goto(url, wait_until="networkidle", timeout=60000)
                time.sleep(2.5)
                out = ASSETS / f"{filename}.png"
                page.screenshot(path=str(out), full_page=True)
                print(f"Captured: {out}")
            browser.close()
    finally:
        proc.terminate()
        proc.wait(timeout=10)


def main() -> None:
    print("Exporting Plotly charts...")
    export_charts()
    print("Capturing Streamlit screenshots...")
    try:
        capture_streamlit_screenshots()
    except Exception as exc:
        print(f"Streamlit capture failed ({exc}); generating fallback architecture diagram only.")
    print(f"Assets directory: {ASSETS}")


if __name__ == "__main__":
    main()
