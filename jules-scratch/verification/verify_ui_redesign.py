import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Verify index page
        await page.goto('http://localhost:8000/index.html')
        await page.screenshot(path='jules-scratch/verification/index_page.png')

        # Verify interactive page
        await page.goto('http://localhost:8000/interactive.html')
        await page.screenshot(path='jules-scratch/verification/interactive_page.png')

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
