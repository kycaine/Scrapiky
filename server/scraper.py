#!/usr/bin/env python3
"""
Google Maps Harvester
Stack: Python 3.10+ · Playwright · playwright-stealth
Output: CSV + JSON (+ optional Gemini WFC analysis)
"""

import argparse
import asyncio
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from playwright.async_api import (
    Page,
    async_playwright,
    TimeoutError as PlaywrightTimeout,
)
from playwright_stealth import Stealth

from logger import log
from browser import human_delay, random_mouse_move, launch_browser
from extractor import extract_detail
from exporter import make_output_paths, init_csv, append_record

load_dotenv()

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
            await human_delay(500, 1000)
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
        await human_delay(1500, 2500)
        await random_mouse_move(page)

        if len(urls) == prev_url_count:
            stale_scroll_count += 1
        else:
            stale_scroll_count = 0

        if stale_scroll_count >= 4:
            log.warning("Scrolling stalled. Assuming end of results.")
            break

        prev_url_count = len(urls)

    return list(urls)[:max_results]

async def scrape(keyword: str, max_results: int, headless: bool, output_dir: Path = Path("output"), filters: dict = None) -> tuple[list[BusinessRecord], Path | None, Path | None]:
    """Orchestrates the scraping flow with incremental saving."""
    records: list[BusinessRecord] = []
    csv_path = None
    json_path = None

    if filters is None:
        filters = {}

    filter_no_phone = filters.get("FILTER_NO_PHONE", os.getenv("FILTER_NO_PHONE", "false").lower() == "true")
    filter_has_website = filters.get("FILTER_HAS_WEBSITE", os.getenv("FILTER_HAS_WEBSITE", "false").lower() == "true")
    filter_no_review = filters.get("FILTER_NO_REVIEW", os.getenv("FILTER_NO_REVIEW", "false").lower() == "true")
    filter_low_rating = filters.get("FILTER_LOW_RATING", False)

    async with async_playwright() as pw:
        browser, context = await launch_browser(pw, headless)
        page: Page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        try:
            await _navigate_to_search(page, keyword)
            await human_delay(1500, 2500)

            place_urls = await _scroll_results_panel(page, max_results)
            log.info(f"Total unique URLs to process: {len(place_urls)}")

            # Create output files immediately after finding URLs
            if place_urls:
                csv_path, json_path = make_output_paths(keyword, output_dir)
                fieldnames = list(BusinessRecord.__dataclass_fields__.keys())
                init_csv(csv_path, fieldnames)

            for idx, url in enumerate(place_urls, start=1):
                try:
                    log.info(f"[{idx}/{len(place_urls)}] Visiting: {url}")
                    await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                    await human_delay(1500, 3000)

                    detail = await extract_detail(page)
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

                    # Apply filters
                    if filter_no_phone and not record.phone:
                        log.info(f"  [SKIPPED] {record.name} - No phone")
                        continue
                    if filter_has_website and record.website:
                        log.info(f"  [SKIPPED] {record.name} - Has website")
                        continue
                    if filter_no_review and (record.review_count is None or record.review_count == 0):
                        log.info(f"  [SKIPPED] {record.name} - No reviews")
                        continue
                    if filter_low_rating:
                        try:
                            # Safely check if rating exists and is a number less than 3
                            if record.rating is None or float(str(record.rating).replace(',', '.')) < 3.0:
                                log.info(f"  [SKIPPED] {record.name} - Rating < 3.0 ({record.rating})")
                                continue
                        except Exception:
                            # If parsing fails or rating is weird, skip to be safe if filter is on
                            log.info(f"  [SKIPPED] {record.name} - Invalid Rating ({record.rating})")
                            continue

                    records.append(record)
                    log.info(f"  ✔ {record.name} | ⭐ {record.rating} ({record.review_count} reviews) | 📍 {record.address[:40] if record.address else '-'}")

                    # Save immediately
                    if csv_path and json_path:
                        append_record(record, csv_path, json_path, records)

                except PlaywrightTimeout as e:
                    log.warning(f"  Timeout on URL {idx}: {e}. Skipping.")
                except Exception as e:
                    log.error(f"  Unexpected error on URL {idx}: {e}")

        finally:
            await context.close()
            await browser.close()

    return records, csv_path, json_path

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Google Maps Scraper")
    parser.add_argument("--keyword", "-k", required=True, help="Search keyword")
    parser.add_argument("--max", "-m", type=int, default=20, dest="max_results", help="Max results")
    parser.add_argument("--headless", action="store_true", help="Run headless")
    parser.add_argument("--output", "-o", type=Path, default=Path("output"), help="Output directory")
    return parser.parse_args()

async def main() -> None:
    args = _parse_args()
    log.info("=" * 40)
    log.info(f"  Keyword: {args.keyword}")
    log.info(f"  Max: {args.max_results}")
    log.info(f"  Headless: {args.headless}")
    log.info("=" * 40)

    records, csv_path, json_path = await scrape(keyword=args.keyword, max_results=args.max_results, headless=args.headless, output_dir=args.output)
    log.info(f"Scraped {len(records)} records.")

    if not records:
        sys.exit(0)

    log.info("Execution complete! ✅")

if __name__ == "__main__":
    asyncio.run(main())
