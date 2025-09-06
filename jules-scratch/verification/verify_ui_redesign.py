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
            for route, name in [
                ("index.html", "index_page.png"),
                ("interactive.html", "interactive_page.png"),
            ]:
                try:
                    response = await page.goto(
                        f"{BASE_URL}/{route}", timeout=10000
                    )
                except PlaywrightTimeoutError as exc:
                    raise RuntimeError(
                        f"Timeout navigating to {route}: {exc}"
                    ) from exc

                if not response or not response.ok:
                    status = response.status if response else "no response"
                    raise RuntimeError(
                        f"Failed to load {route}: status {status}"
                    )

                await page.screenshot(path=str(OUTPUT_DIR / name))
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
