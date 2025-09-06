import argparse
import asyncio
from pathlib import Path

from playwright.async_api import async_playwright


async def main(base_url: str, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        for name in ["index", "interactive"]:
            url = f"{base_url}/{name}.html"
            try:
                response = await page.goto(url)
                if not response or not response.ok:
                    raise RuntimeError(f"Failed to load {url}")
                await page.screenshot(path=output_dir / f"{name}_page.png")
            except Exception as e:
                print(f"Error verifying {url}: {e}")

        await browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify UI pages")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument(
        "--output-dir", default="jules-scratch/verification", type=Path
    )
    args = parser.parse_args()
    asyncio.run(main(args.base_url, args.output_dir))
