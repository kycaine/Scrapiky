"""Browser launch and anti-detection helpers."""

import asyncio
import random

from playwright.async_api import Browser, BrowserContext, Page, Playwright


async def human_delay(min_ms: int = 300, max_ms: int = 900) -> None:
    """Random sleep to emulate human behavior."""
    await asyncio.sleep(random.uniform(min_ms / 1000, max_ms / 1000))

async def random_mouse_move(page: Page) -> None:
    """Move mouse to a random position."""
    vw = await page.evaluate("window.innerWidth")
    vh = await page.evaluate("window.innerHeight")
    x = random.randint(100, vw - 100)
    y = random.randint(100, vh - 100)
    await page.mouse.move(x, y, steps=random.randint(5, 15))

async def launch_browser(playwright: Playwright, headless: bool) -> tuple[Browser, BrowserContext]:
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
