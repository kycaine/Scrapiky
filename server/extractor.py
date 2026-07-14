"""Detail page data extraction from Google Maps place panels."""

import re

from playwright.async_api import Page, TimeoutError as PlaywrightTimeout


async def extract_detail(page: Page) -> dict:
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
        phone = (await phone_el.first.inner_text(timeout=5_000)).strip()
        phone = phone.replace("-", "").replace(" ", "").replace("+", "")
        if phone.startswith("0"):
            phone = "62" + phone[1:]
        data["phone"] = phone
    except Exception:
        data["phone"] = ""

    data["google_maps_url"] = page.url
    return data
