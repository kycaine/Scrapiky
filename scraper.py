#!/usr/bin/env python3
"""
Google Maps Harvester
Stack: Python 3.10+ · Playwright · playwright-stealth
Output: CSV + JSON (+ optional Gemini WFC analysis)
"""

import argparse
import asyncio
import csv
import json
import logging
import os
import random
import re
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
    TimeoutError as PlaywrightTimeout,
)
from playwright_stealth import Stealth

load_dotenv()

# Logger setup using ANSI colors
ANSI = {
    "DEBUG":    "\033[36m",   # cyan
    "INFO":     "\033[32m",   # green
    "WARNING":  "\033[33m",   # yellow
    "ERROR":    "\033[31m",   # red
    "CRITICAL": "\033[1;31m", # bold red
    "RESET":    "\033[0m",
}

class _AnsiFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        color = ANSI.get(record.levelname, ANSI["RESET"])
        record.levelname = f"{color}[{record.levelname}]{ANSI['RESET']}"
        return super().format(record)

def _setup_logger(name: str = "gmaps") -> logging.Logger:
    handler = logging.StreamHandler()
    handler.setFormatter(_AnsiFormatter("%(levelname)s %(asctime)s  %(message)s", datefmt="%H:%M:%S"))
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger

log = _setup_logger()

@dataclass
class BusinessRecord:
    name: str = ""
    rating: Optional[float] = None
    review_count: Optional[int] = None
    category: str = ""
    address: str = ""
    website: str = ""
    phone: str = ""
    google_maps_url: str = ""
    wfc_analysis: str = ""

async def _human_delay(min_ms: int = 300, max_ms: int = 900) -> None:
    """Random sleep to emulate human behavior."""
    await asyncio.sleep(random.uniform(min_ms / 1000, max_ms / 1000))

async def _random_mouse_move(page: Page) -> None:
    """Move mouse to a random position."""
    vw = await page.evaluate("window.innerWidth")
    vh = await page.evaluate("window.innerHeight")
    x = random.randint(100, vw - 100)
    y = random.randint(100, vh - 100)
    await page.mouse.move(x, y, steps=random.randint(5, 15))

async def _launch_browser(playwright: Playwright, headless: bool) -> tuple[Browser, BrowserContext]:
    """Launch Chromium with stealth and realistic fingerprint."""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    ]

    browser = await playwright.chromium.launch(
        headless=headless,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
            "--lang=en-US,en;q=0.9",
        ],
    )

    context = await browser.new_context(
        user_agent=random.choice(user_agents),
        locale="en-US",
        timezone_id="UTC",
        viewport={"width": 1366, "height": 768},
        java_script_enabled=True,
        bypass_csp=True,
    )

    await context.set_extra_http_headers({
        "Accept-Language": "en-US,en;q=0.9",
        "Sec-Ch-Ua-Platform": '"Windows"',
    })

    return browser, context

async def _navigate_to_search(page: Page, keyword: str) -> None:
    """Navigate to Google Maps search results."""
    search_url = f"https://www.google.com/maps/search/{keyword.replace(' ', '+')}/"
    log.info(f"Navigating to: {search_url}")
    await page.goto(search_url, wait_until="domcontentloaded", timeout=60_000)

    try:
        consent_btn = page.locator('button[aria-label*="Accept"], form[action*="consent"] button')
        if await consent_btn.count() > 0:
            await consent_btn.first.click()
            log.debug("Dismissed consent dialog.")
            await _human_delay(500, 1000)
    except PlaywrightTimeout:
        pass

async def _scroll_results_panel(page: Page, max_results: int) -> list[str]:
    """Scroll and collect unique place URLs."""
    CARD_SELECTOR = 'a[class*="hfpxzc"]'
    urls: set[str] = set()

    log.info("Waiting for results panel...")
    try:
        await page.wait_for_selector(CARD_SELECTOR, timeout=30_000)
    except PlaywrightTimeout:
        log.error("No result cards appeared.")
        return []

    stale_scroll_count = 0
    prev_url_count = 0

    while len(urls) < max_results:
        current_cards = page.locator(CARD_SELECTOR)
        count = await current_cards.count()
        for i in range(count):
            href = await current_cards.nth(i).get_attribute("href")
            if href and "/place/" in href:
                urls.add(href)
        
        log.info(f"  Collected {len(urls)} URLs so far...")

        if len(urls) >= max_results:
            break

        end_marker = page.locator("text=You've reached the end of the list, text=Anda telah mencapai akhir daftar")
        if await end_marker.count() > 0:
            log.info("End of list reached.")
            break

        await page.evaluate("document.querySelector('[role=\"feed\"]')?.scrollBy(0, document.querySelector('[role=\"feed\"]').scrollHeight)")
        await _human_delay(1500, 2500)
        await _random_mouse_move(page)

        if len(urls) == prev_url_count:
            stale_scroll_count += 1
        else:
            stale_scroll_count = 0

        if stale_scroll_count >= 4:
            log.warning("Scrolling stalled. Assuming end of results.")
            break

        prev_url_count = len(urls)

    return list(urls)[:max_results]

async def _extract_detail(page: Page) -> dict:
    """Extract data from a place detail panel."""
    data: dict = {}

    try:
        await page.wait_for_selector("h1", timeout=10_000)
    except PlaywrightTimeout:
        pass

    # Name
    try:
        name_el = page.locator('h1').first
        raw = (await name_el.inner_text(timeout=5_000)).strip()
        data["name"] = raw if raw not in ("Results", "Hasil") else ""
    except Exception:
        data["name"] = ""

    # Rating
    try:
        rating_el = page.locator('[class*="F7nice"] span[aria-hidden="true"]')
        raw_rating = (await rating_el.first.inner_text(timeout=5_000)).strip()
        data["rating"] = float(raw_rating.replace(",", "."))
    except Exception:
        data["rating"] = None

    # Review count
    try:
        review_block = page.locator('[class*="F7nice"]')
        raw_text = (await review_block.first.inner_text(timeout=5_000)).strip()
        paren_match = re.search(r"\(([\d.,]+)\)", raw_text)
        if paren_match:
            raw_num = paren_match.group(1)
            data["review_count"] = int(raw_num.replace(".", "").replace(",", ""))
        else:
            data["review_count"] = None
    except Exception:
        data["review_count"] = None

    # Category
    try:
        cat_el = page.locator('button[jsaction*="category"]')
        data["category"] = (await cat_el.first.inner_text(timeout=5_000)).strip()
    except Exception:
        data["category"] = ""

    # Address
    try:
        addr_el = page.locator('[data-item-id="address"] [class*="Io6YTe"]')
        data["address"] = (await addr_el.first.inner_text(timeout=5_000)).strip()
    except Exception:
        data["address"] = ""

    # Website
    try:
        web_el = page.locator('[data-item-id="authority"] a')
        data["website"] = (await web_el.first.get_attribute("href", timeout=5_000)) or ""
    except Exception:
        data["website"] = ""

    # Phone
    try:
        phone_el = page.locator('[data-item-id*="phone:tel:"] [class*="Io6YTe"]')
        data["phone"] = (await phone_el.first.inner_text(timeout=5_000)).strip()
    except Exception:
        data["phone"] = ""

    data["google_maps_url"] = page.url
    return data

async def scrape(keyword: str, max_results: int, headless: bool) -> list[BusinessRecord]:
    """Orchestrates the scraping flow."""
    records: list[BusinessRecord] = []

    async with async_playwright() as pw:
        browser, context = await _launch_browser(pw, headless)
        page: Page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        try:
            await _navigate_to_search(page, keyword)
            await _human_delay(1500, 2500)

            place_urls = await _scroll_results_panel(page, max_results)
            log.info(f"Total unique URLs to process: {len(place_urls)}")

            for idx, url in enumerate(place_urls, start=1):
                try:
                    log.info(f"[{idx}/{len(place_urls)}] Visiting: {url}")
                    await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                    await _human_delay(1500, 3000)

                    detail = await _extract_detail(page)
                    record = BusinessRecord(
                        name=detail.get("name", ""),
                        rating=detail.get("rating"),
                        review_count=detail.get("review_count"),
                        category=detail.get("category", ""),
                        address=detail.get("address", ""),
                        website=detail.get("website", ""),
                        phone=detail.get("phone", ""),
                        google_maps_url=url,
                    )
                    
                    if not record.name:
                        title = await page.title()
                        record.name = title.split(" - ")[0].split(" – ")[0]

                    records.append(record)
                    log.info(f"  ✔ {record.name} | ⭐ {record.rating} ({record.review_count} reviews) | 📍 {record.address[:40] if record.address else '-'}")

                except PlaywrightTimeout as e:
                    log.warning(f"  Timeout on URL {idx}: {e}. Skipping.")
                except Exception as e:
                    log.error(f"  Unexpected error on URL {idx}: {e}")

        finally:
            await context.close()
            await browser.close()

    return records

def _analyze_wfc_with_gemini(records: list[BusinessRecord]) -> list[BusinessRecord]:
    """Analyze suitability for 'Work From Cafe' using Gemini AI."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or api_key == "your_gemini_api_key_here":
        log.error("GEMINI_API_KEY not set. Skipping analysis.")
        return records

    try:
        import google.generativeai as genai
    except ImportError:
        log.error("google-generativeai not installed.")
        return records

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    log.info("Running Gemini WFC analysis...")
    for record in records:
        if not record.name:
            continue
        prompt = (
            f"Determine if this place is suitable for remote work (Work From Cafe / WFC).\n\n"
            f"Place Info:\n"
            f"- Name: {record.name}\n"
            f"- Category: {record.category}\n"
            f"- Rating: {record.rating} ({record.review_count} reviews)\n"
            f"- Address: {record.address}\n\n"
            f"Provide a brief assessment (2-3 sentences) based on the data. "
            f"End with either: [SUITABLE FOR WFC] or [NOT SUITABLE FOR WFC]."
        )
        try:
            response = model.generate_content(prompt)
            record.wfc_analysis = response.text.strip()
            log.info(f"  Gemini ✔ {record.name}")
            time.sleep(0.5)
        except Exception as e:
            log.warning(f"  Gemini error for '{record.name}': {e}")
            record.wfc_analysis = "Analysis failed."

    return records

def _export(records: list[BusinessRecord], keyword: str, output_dir: Path) -> None:
    """Export results to CSV and JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_keyword = re.sub(r"[^\w\-]", "_", keyword)[:40]
    base_name = f"{safe_keyword}_{timestamp}"

    # CSV
    csv_path = output_dir / f"{base_name}.csv"
    fieldnames = list(BusinessRecord.__dataclass_fields__.keys())
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow(asdict(r))
    log.info(f"CSV  → {csv_path}")

    # JSON
    json_path = output_dir / f"{base_name}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in records], f, ensure_ascii=False, indent=2)
    log.info(f"JSON → {json_path}")

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Google Maps Scraper")
    parser.add_argument("--keyword", "-k", required=True, help="Search keyword")
    parser.add_argument("--max", "-m", type=int, default=20, dest="max_results", help="Max results")
    parser.add_argument("--headless", action="store_true", help="Run headless")
    parser.add_argument("--gemini", action="store_true", help="Enable Gemini analysis")
    parser.add_argument("--output", "-o", type=Path, default=Path("output"), help="Output directory")
    return parser.parse_args()

async def main() -> None:
    args = _parse_args()
    log.info("=" * 40)
    log.info(f"  Keyword: {args.keyword}")
    log.info(f"  Max: {args.max_results}")
    log.info(f"  Headless: {args.headless}")
    log.info(f"  Gemini: {args.gemini}")
    log.info("=" * 40)

    records = await scrape(keyword=args.keyword, max_results=args.max_results, headless=args.headless)
    log.info(f"Scraped {len(records)} records.")

    if not records:
        sys.exit(0)

    if args.gemini:
        records = _analyze_wfc_with_gemini(records)

    _export(records, args.keyword, args.output)
    log.info("Execution complete! ✅")

if __name__ == "__main__":
    asyncio.run(main())
