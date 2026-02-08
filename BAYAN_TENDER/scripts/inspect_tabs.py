"""Quick script to inspect tab structure on the tender details page."""
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        page.set_default_timeout(15000)

        # Login
        await page.goto("http://localhost:4201/login")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(1)
        await page.fill('input[placeholder="Enter your email"]', "tendermgr@bayan.ae")
        await page.fill('input[placeholder="Enter your password"]', "Bayan@2024")
        await page.click('button:has-text("Sign In")')
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        # Navigate to TNR-2026-0003
        await page.goto("http://localhost:4201/tenders")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)
        await page.locator('tr:has-text("TNR-2026-0003")').first.click()
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        # Inspect tab structure
        html = await page.inner_html('body')

        # Find all tab-related elements
        tab_elements = await page.locator('[role="tablist"] *, [class*="tab"], p-tabPanel, .p-tabview-panel').all()
        print(f"Tab elements found: {len(tab_elements)}")

        # Get the tab headers specifically
        tab_headers = await page.locator('[role="tab"]').all()
        print(f"\nRole=tab elements: {len(tab_headers)}")
        for i, el in enumerate(tab_headers):
            text = await el.text_content()
            tag = await el.evaluate("e => e.tagName")
            classes = await el.get_attribute("class") or ""
            visible = await el.is_visible()
            print(f"  [{i}] <{tag}> text='{text.strip()[:30]}' class='{classes[:50]}' visible={visible}")

        # Also look for p-tabview nav
        nav_links = await page.locator('.p-tabview-nav a, .p-tabview-nav span, ul[role="tablist"] li').all()
        print(f"\nTabview nav items: {len(nav_links)}")
        for i, el in enumerate(nav_links):
            text = await el.text_content()
            tag = await el.evaluate("e => e.tagName")
            visible = await el.is_visible()
            print(f"  [{i}] <{tag}> text='{text.strip()[:30]}' visible={visible}")

        # Print the HTML of the tab area
        try:
            tabview_html = await page.locator('[role="tablist"]').first.inner_html()
            print(f"\nTablist HTML (first 2000 chars):\n{tabview_html[:2000]}")
        except:
            print("\nNo [role='tablist'] found")

        # Try to get current URL and page title
        print(f"\nURL: {page.url}")
        title = await page.title()
        print(f"Title: {title}")

        await browser.close()

asyncio.run(main())
