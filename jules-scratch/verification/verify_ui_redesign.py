import asyncio
import os
from pathlib import Path

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
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
            for page_name, shot_name in [
                ("index.html", "index_page.png"),
                ("interactive.html", "interactive_page.png"),
            ]:
                try:
                    response = await page.goto(
                        f"{BASE_URL}/{page_name}", timeout=5000
                    )
                    if not response or not response.ok:
                        raise RuntimeError(
                            f"Navigation to {page_name} failed: "
                            f"{response.status if response else 'no response'}"
                        )
                    await page.screenshot(path=str(OUTPUT_DIR / shot_name))
                except PlaywrightTimeoutError:
                    print(f"Timeout navigating to {page_name}")
                except Exception as exc:
                    print(f"Error navigating to {page_name}: {exc}")
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
