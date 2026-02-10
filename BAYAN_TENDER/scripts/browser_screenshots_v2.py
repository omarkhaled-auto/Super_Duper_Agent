"""
Browser automation script v2 - improved login handling and comprehensive screenshots.
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

async def login(context, email, password="Bayan@2024"):
    """Login with a fresh page to avoid stale state."""
    page = await context.new_page()
    page.set_default_timeout(15000)

    await page.goto(f"{UI_BASE}/login")
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(1)

    # Check if we're on login page
    current_url = page.url
    if "/login" not in current_url:
        # Might be redirected to dashboard - clear storage and retry
        await context.clear_cookies()
        await page.goto(f"{UI_BASE}/login")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(1)

    # Fill login form
    await page.fill('input[placeholder="Enter your email"]', email)
    await page.fill('input[placeholder="Enter your password"]', password)

    # Click Sign In
    await page.click('button:has-text("Sign In")')
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(2)

    print(f"  [OK] Logged in as {email}")
    return page

async def navigate_to_tender(page, tender_ref):
    """Navigate to a tender by reference."""
    await page.goto(f"{UI_BASE}/tenders")
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(2)

    # Click on the tender row
    row = page.locator(f'tr:has-text("{tender_ref}")').first
    await row.click(timeout=10000)
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(2)
    print(f"  [OK] Navigated to {tender_ref}")

async def click_tab(page, tab_name):
    """Click a tab by name - PrimeNG tabs use button[role=tab]."""
    tab = page.locator(f'button[role="tab"]:has-text("{tab_name}")').first
    await tab.click()
    await asyncio.sleep(2)

async def main():
    print("=" * 70)
    print("BAYAN TENDER - Comprehensive Browser Verification v2")
    print("=" * 70)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="en-US"
        )

        # ========================================================
        # GAP A: Excel Bid Import Wizard
        # ========================================================
        print("\n=== GAP A: Excel Bid Import Wizard ===")
        page = await login(context, "tendermgr@bayan.ae")

        await navigate_to_tender(page, "TNR-2026-0003")

        # Click Bids tab
        await click_tab(page, "Bids")
        await asyncio.sleep(2)
        await screenshot(page, "gapA-bids-tab.png")

        # Look for bid row with action buttons
        # Get the first bid row's view/details button
        try:
            # Try the eye icon button
            view_btns = page.locator('button.p-button-text:has(i.pi-eye), button[ptooltip="View Details"]')
            count = await view_btns.count()
            print(f"  Found {count} view buttons")
            if count > 0:
                await view_btns.first.click()
                await asyncio.sleep(2)
                await screenshot(page, "gapA-bid-details-dialog.png")

                # Find the Import BOQ / Import Wizard button
                import_btns = page.locator('button:has-text("Import"), button:has(i.pi-file-import)')
                import_count = await import_btns.count()
                print(f"  Found {import_count} import buttons in dialog")

                if import_count > 0:
                    await import_btns.first.click()
                    await asyncio.sleep(2)
                    await screenshot(page, "gapA-step01-upload.png", full_page=True)
                    print("  [OK] Import wizard opened!")

                    # Try clicking Parse File button
                    try:
                        parse_btn = page.locator('button:has-text("Parse File"), button:has-text("Parse")')
                        if await parse_btn.count() > 0:
                            await parse_btn.first.click()
                            await asyncio.sleep(5)
                            await screenshot(page, "gapA-step01-parsed.png", full_page=True)
                    except:
                        pass

                    # Look for Next/Auto-Map button to proceed
                    try:
                        auto_map_btn = page.locator('button:has-text("Auto-Map"), button:has-text("Next")')
                        if await auto_map_btn.count() > 0:
                            await auto_map_btn.first.click()
                            await asyncio.sleep(3)
                            await screenshot(page, "gapA-step02-columns.png", full_page=True)
                    except:
                        pass

                    # Try more steps
                    for step, names in [
                        ("step03-matching", ["Match", "Next"]),
                        ("step04-normalize", ["Normalize", "Next"]),
                        ("step05-validate", ["Validate", "Import", "Execute", "Next"]),
                    ]:
                        try:
                            for name in names:
                                btn = page.locator(f'button:has-text("{name}")')
                                if await btn.count() > 0:
                                    await btn.first.click()
                                    await asyncio.sleep(3)
                                    break
                            await screenshot(page, f"gapA-{step}.png", full_page=True)
                        except:
                            pass
                else:
                    print("  [WARN] No import buttons found in bid details dialog")
                    # Take screenshot of what's visible
                    await screenshot(page, "gapA-bid-details-no-import.png", full_page=True)
            else:
                # Try clicking the row directly
                bid_rows = page.locator('tbody tr')
                if await bid_rows.count() > 0:
                    await bid_rows.first.click()
                    await asyncio.sleep(2)
                    await screenshot(page, "gapA-bid-row-click.png")
        except Exception as e:
            print(f"  [WARN] Gap A wizard: {str(e)[:100]}")
            await screenshot(page, "gapA-error.png")

        await page.close()

        # ========================================================
        # GAP C: Documents Tab
        # ========================================================
        print("\n=== GAP C: Documents Tab ===")
        page = await login(context, "tendermgr@bayan.ae")

        await navigate_to_tender(page, "TNR-2026-0003")
        await click_tab(page, "Documents")
        await asyncio.sleep(2)
        await screenshot(page, "gapC-documents-tab-empty.png")

        # Upload dialog
        upload_btn = page.locator('button:has-text("Upload Document")').first
        await upload_btn.click()
        await asyncio.sleep(1)
        await screenshot(page, "gapC-upload-dialog.png")

        # Cancel
        await page.locator('button:has-text("Cancel")').first.click()
        await asyncio.sleep(1)

        await page.close()

        # ========================================================
        # GAP B: Approval Workflow
        # ========================================================
        print("\n=== GAP B: Approval Workflow ===")
        page = await login(context, "tendermgr@bayan.ae")

        await navigate_to_tender(page, "TNR-2026-0003")
        await click_tab(page, "Approval")
        await asyncio.sleep(2)
        await screenshot(page, "gapB-approval-tab-tm-view.png")
        await screenshot(page, "gapB-approval-history.png", full_page=True)

        await page.close()

        # Approver view
        page = await login(context, "approver@bayan.ae")

        # Dashboard view
        await screenshot(page, "gapB-approver-dashboard.png")

        # Navigate to tender
        try:
            await navigate_to_tender(page, "TNR-2026-0003")
            await click_tab(page, "Approval")
            await asyncio.sleep(2)
            await screenshot(page, "gapB-approver-view.png")
        except Exception as e:
            print(f"  [WARN] Approver tender nav: {str(e)[:100]}")

        await page.close()

        # ========================================================
        # BONUS: Evaluation Tab (Comparable Sheet + Sensitivity)
        # ========================================================
        print("\n=== BONUS: Evaluation ===")
        page = await login(context, "tendermgr@bayan.ae")

        await navigate_to_tender(page, "TNR-2026-0003")
        await click_tab(page, "Evaluation")
        await asyncio.sleep(2)
        await screenshot(page, "bonus-evaluation-tab.png")

        # Look for evaluation sub-navigation
        try:
            # Check for Comparable button/link
            comp_btn = page.locator('button:has-text("Comparable"), a:has-text("Comparable"), [class*="sub-tab"]:has-text("Comparable")')
            if await comp_btn.count() > 0:
                await comp_btn.first.click()
                await asyncio.sleep(2)
                await screenshot(page, "bonus-comparable-with-bid-prices.png", full_page=True)
            else:
                # Try looking for sub-nav buttons
                sub_btns = page.locator('.evaluation-sub-nav button, .sub-tabs button')
                count = await sub_btns.count()
                print(f"  Found {count} evaluation sub-buttons")
                await screenshot(page, "bonus-evaluation-subnav.png", full_page=True)
        except Exception as e:
            print(f"  [WARN] Comparable: {str(e)[:100]}")

        # Sensitivity Analysis
        try:
            sens_btn = page.locator('button:has-text("Sensitivity"), button:has-text("Analysis")')
            if await sens_btn.count() > 0:
                await sens_btn.first.click()
                await asyncio.sleep(3)
                await screenshot(page, "bonus-sensitivity-scenarios.png", full_page=True)
            else:
                print("  [INFO] No sensitivity button found on current view")
        except Exception as e:
            print(f"  [WARN] Sensitivity: {str(e)[:100]}")

        await page.close()

        # ========================================================
        # REGRESSION: All Tenders Accessible
        # ========================================================
        print("\n=== REGRESSION CHECK ===")
        page = await login(context, "tendermgr@bayan.ae")

        # Tenders list
        await page.goto(f"{UI_BASE}/tenders")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)
        await screenshot(page, "regression-tenders-list.png")

        # TNR-2026-0001
        try:
            await navigate_to_tender(page, "TNR-2026-0001")
            await screenshot(page, "regression-tnr-0001.png")
        except:
            print("  [WARN] TNR-2026-0001 navigation failed")

        # TNR-2026-0002
        try:
            await navigate_to_tender(page, "TNR-2026-0002")
            await screenshot(page, "regression-tnr-0002.png")
        except:
            print("  [WARN] TNR-2026-0002 navigation failed")

        # TNR-2026-0003
        try:
            await navigate_to_tender(page, "TNR-2026-0003")
            await screenshot(page, "regression-tnr-0003.png")

            # Bids tab
            await click_tab(page, "Bids")
            await asyncio.sleep(2)
            await screenshot(page, "regression-tnr-0003-bids.png")

            # Approval tab
            await click_tab(page, "Approval")
            await asyncio.sleep(2)
            await screenshot(page, "regression-tnr-0003-approval.png")

            # BOQ tab
            await click_tab(page, "BOQ")
            await asyncio.sleep(2)
            await screenshot(page, "regression-tnr-0003-boq.png")

        except Exception as e:
            print(f"  [WARN] TNR-0003 regression: {str(e)[:100]}")

        # Console errors check
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        await page.goto(f"{UI_BASE}/tenders")
        await asyncio.sleep(3)
        print(f"  Console errors: {len(console_errors)}")

        await page.close()
        await browser.close()

    # Summary
    print(f"\n{'=' * 70}")
    print(f"Screenshots saved to: {SCREENSHOT_DIR}")
    screenshots = sorted(os.listdir(SCREENSHOT_DIR))
    print(f"Total screenshots: {len(screenshots)}")
    for s in screenshots:
        size = os.path.getsize(os.path.join(SCREENSHOT_DIR, s))
        print(f"  {s} ({size:,} bytes)")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
