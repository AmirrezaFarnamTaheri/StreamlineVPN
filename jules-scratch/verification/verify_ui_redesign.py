import asyncio
import os
from pathlib import Path

from playwright.async_api import async_playwright

BASE_URL = os.environ.get("STREAMLINEVPN_BASE_URL", "http://localhost:8000")
OUTPUT_DIR = Path(
    os.environ.get("SCREENSHOT_DIR", "jules-scratch/verification")
)


async def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        try:
            await page.goto(f"{BASE_URL}/index.html")
            await page.screenshot(path=str(OUTPUT_DIR / "index_page.png"))

            await page.goto(f"{BASE_URL}/interactive.html")
            await page.screenshot(
                path=str(OUTPUT_DIR / "interactive_page.png")
            )
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
