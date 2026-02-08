"""Quick inspect of bid tab action buttons."""
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        page.set_default_timeout(15000)

        await page.goto("http://localhost:4201/login")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(1)
        await page.fill('input[placeholder="Enter your email"]', "tendermgr@bayan.ae")
        await page.fill('input[placeholder="Enter your password"]', "Bayan@2024")
        await page.click('button:has-text("Sign In")')
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        await page.goto("http://localhost:4201/tenders")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)
        await page.locator('tr:has-text("TNR-2026-0003")').first.click()
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        # Click Bids tab
        await page.locator('button[role="tab"]:has-text("Bids")').first.click()
        await asyncio.sleep(2)

        # Inspect action buttons in the bids table
        # From the screenshot, there are eye, download, and import icons per row
        action_btns = page.locator('td button, .action-buttons button, button:has(i.pi)')
        count = await action_btns.count()
        print(f"Action buttons found: {count}")
        for i in range(min(count, 20)):
            btn = action_btns.nth(i)
            visible = await btn.is_visible()
            if visible:
                html = await btn.inner_html()
                tooltip = await btn.get_attribute("ptooltip") or ""
                text = await btn.text_content()
                classes = await btn.get_attribute("class") or ""
                print(f"  [{i}] tooltip='{tooltip}' text='{text.strip()[:30]}' html='{html[:100]}' class='{classes[:60]}'")

        # Also check the first row specifically
        first_row = page.locator('tbody tr').first
        row_btns = first_row.locator('button')
        row_btn_count = await row_btns.count()
        print(f"\nFirst row buttons: {row_btn_count}")
        for i in range(row_btn_count):
            btn = row_btns.nth(i)
            html = await btn.inner_html()
            tooltip = await btn.get_attribute("ptooltip") or ""
            print(f"  [{i}] tooltip='{tooltip}' html='{html[:120]}'")

        await browser.close()

asyncio.run(main())
