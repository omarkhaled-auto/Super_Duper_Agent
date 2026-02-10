"""
Focused script to capture the bid import wizard screenshots.
"""
import asyncio
import os
from playwright.async_api import async_playwright

UI_BASE = "http://localhost:4201"
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "..", "final-100-screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

async def screenshot(page, name, full_page=False):
    path = os.path.join(SCREENSHOT_DIR, name)
    await page.screenshot(path=path, full_page=full_page)
    print(f"  [SCREENSHOT] {name}")

async def main():
    print("=== Wizard Screenshot Capture ===\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="en-US"
        )
        page = await context.new_page()
        page.set_default_timeout(20000)

        # Login
        await page.goto(f"{UI_BASE}/login")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(1)
        await page.fill('input[placeholder="Enter your email"]', "tendermgr@bayan.ae")
        await page.fill('input[placeholder="Enter your password"]', "Bayan@2024")
        await page.click('button:has-text("Sign In")')
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)
        print("[OK] Logged in")

        # Navigate to TNR-2026-0003
        await page.goto(f"{UI_BASE}/tenders")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)
        await page.locator('tr:has-text("TNR-2026-0003")').first.click()
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        # Click Bids tab
        await page.locator('button[role="tab"]:has-text("Bids")').first.click()
        await asyncio.sleep(2)

        # Click View Details button - use pTooltip attribute
        view_btn = page.locator('button[ptooltip="View Details"]').first
        await view_btn.click()
        await asyncio.sleep(2)
        print("[OK] Bid details dialog opened")

        # Click "Import BOQ Wizard" button
        wizard_btn = page.locator('button:has-text("Import BOQ Wizard")')
        count = await wizard_btn.count()
        print(f"  Found {count} 'Import BOQ Wizard' buttons")

        if count > 0:
            await wizard_btn.first.click()
            await asyncio.sleep(3)
            await screenshot(page, "gapA-step01-upload.png", full_page=True)
            print("[OK] Step 1: Wizard opened")

            # Inspect wizard content
            # List all visible buttons
            all_btns = page.locator('button:visible')
            btn_count = await all_btns.count()
            print(f"\n  Visible buttons: {btn_count}")
            for i in range(btn_count):
                text = await all_btns.nth(i).text_content()
                text = text.strip()
                if text and len(text) < 50:
                    print(f"    [{i}] '{text}'")

            # Try to find Parse File button
            parse_btn = page.locator('button:has-text("Parse File"), button:has-text("Parse")')
            parse_count = await parse_btn.count()
            print(f"\n  Parse buttons: {parse_count}")

            if parse_count > 0:
                await parse_btn.first.click()
                print("  [CLICK] Parse File")
                await asyncio.sleep(8)  # Give it time to parse
                await screenshot(page, "gapA-step01-parsed.png", full_page=True)
                print("[OK] Parsed!")

                # List buttons again after parse
                all_btns2 = page.locator('button:visible')
                btn_count2 = await all_btns2.count()
                print(f"\n  Buttons after parse: {btn_count2}")
                for i in range(btn_count2):
                    text = await all_btns2.nth(i).text_content()
                    text = text.strip()
                    if text and len(text) < 50:
                        print(f"    [{i}] '{text}'")

            # Try step navigation
            # The wizard uses a stepper - look for Next or step-specific buttons
            for step_num in range(2, 6):
                try:
                    next_btn = page.locator(f'button:has-text("Next"), button:has-text("Step {step_num}")')
                    if await next_btn.count() > 0:
                        await next_btn.first.click()
                        await asyncio.sleep(3)
                        step_names = {2: "columns", 3: "matching", 4: "normalize", 5: "validate"}
                        name = step_names.get(step_num, f"step{step_num}")
                        await screenshot(page, f"gapA-step0{step_num}-{name}.png", full_page=True)
                        print(f"[OK] Step {step_num}: {name}")
                    else:
                        print(f"  No Next/Step {step_num} button found")
                        break
                except Exception as e:
                    print(f"  Step {step_num} error: {str(e)[:60]}")
                    break

        else:
            print("[WARN] No Import BOQ Wizard button - listing all buttons in dialog")
            dialog_btns = page.locator('.p-dialog-content button:visible, .p-dialog-footer button:visible')
            dc = await dialog_btns.count()
            for i in range(dc):
                text = await dialog_btns.nth(i).text_content()
                print(f"  [{i}] '{text.strip()[:60]}'")

        # ========== Evaluation Sub-tabs ==========
        print("\n=== Evaluation Sub-tabs ===")
        await page.goto(f"{UI_BASE}/tenders")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)
        await page.locator('tr:has-text("TNR-2026-0003")').first.click()
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        # Evaluation tab
        await page.locator('button[role="tab"]:has-text("Evaluation")').first.click()
        await asyncio.sleep(2)

        # Look for sub-navigation buttons
        eval_btns = page.locator('button:visible')
        btn_count = await eval_btns.count()
        print(f"Visible buttons: {btn_count}")
        eval_btn_texts = []
        for i in range(btn_count):
            text = await eval_btns.nth(i).text_content()
            text = text.strip()
            if text and len(text) < 50:
                eval_btn_texts.append((i, text))
                print(f"  [{i}] '{text}'")

        # Try to click "Evaluation Setup" or "Technical Scoring" or "Combined Scorecard"
        for btn_text in ["Combined Scorecard", "Scorecard", "Technical Scoring"]:
            btn = page.locator(f'button:has-text("{btn_text}")')
            if await btn.count() > 0:
                await btn.first.click()
                await asyncio.sleep(2)
                await screenshot(page, f"bonus-{btn_text.lower().replace(' ', '-')}.png", full_page=True)
                print(f"[OK] {btn_text} screenshot")
                break

        # Try to find and click sensitivity analysis
        sens_btn = page.locator('button:has-text("Sensitivity")')
        if await sens_btn.count() > 0:
            await sens_btn.first.click()
            await asyncio.sleep(3)
            await screenshot(page, "bonus-sensitivity-scenarios.png", full_page=True)
            print("[OK] Sensitivity Analysis screenshot")
        else:
            # The sensitivity analysis might be a dialog triggered from scorecard
            # Look for "Run Analysis" or analysis buttons
            analysis_btn = page.locator('button:has-text("Run Analysis"), button:has-text("Analysis")')
            if await analysis_btn.count() > 0:
                await analysis_btn.first.click()
                await asyncio.sleep(3)
                await screenshot(page, "bonus-sensitivity-scenarios.png", full_page=True)
                print("[OK] Analysis screenshot")

        await page.close()
        await browser.close()

    print("\n=== Done ===")
    screenshots = sorted(os.listdir(SCREENSHOT_DIR))
    print(f"Total screenshots: {len(screenshots)}")
    for s in screenshots:
        size = os.path.getsize(os.path.join(SCREENSHOT_DIR, s))
        print(f"  {s} ({size:,} bytes)")

asyncio.run(main())
