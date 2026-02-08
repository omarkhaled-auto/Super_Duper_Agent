"""
Browser automation script to take screenshots for all milestone verifications.
Uses Playwright to navigate the Bayan Tender Management System UI.
"""
import asyncio
import os
import time
from playwright.async_api import async_playwright

UI_BASE = "http://localhost:4201"
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "..", "final-100-screenshots")

# Ensure screenshot directory exists
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

async def screenshot(page, name, full_page=False):
    """Take a screenshot and save it."""
    path = os.path.join(SCREENSHOT_DIR, name)
    await page.screenshot(path=path, full_page=full_page)
    print(f"  [SCREENSHOT] {name}")
    return path

async def login(page, email, password="Bayan@2024"):
    """Login to the application."""
    await page.goto(f"{UI_BASE}/login")
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(1)

    # Fill login form
    email_input = page.locator('input[type="email"], input[formControlName="email"], input[placeholder*="email" i]').first
    pwd_input = page.locator('input[type="password"]').first

    await email_input.fill(email)
    await pwd_input.fill(password)

    # Click login button
    login_btn = page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign In")').first
    await login_btn.click()

    # Wait for navigation
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(2)
    print(f"  [OK] Logged in as {email}")

async def navigate_to_tender(page, tender_ref):
    """Navigate to a specific tender's details page."""
    # Go to tenders list
    await page.goto(f"{UI_BASE}/tenders")
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(2)

    # Click on the tender
    tender_link = page.locator(f'text="{tender_ref}"').first
    try:
        await tender_link.click(timeout=5000)
    except:
        # Try clicking on any row containing the reference
        row = page.locator(f'tr:has-text("{tender_ref}")').first
        await row.click(timeout=5000)

    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(2)
    print(f"  [OK] Navigated to {tender_ref}")

async def click_tab(page, tab_name):
    """Click a tab in the tender details page."""
    tab = page.locator(f'li:has-text("{tab_name}"), [role="tab"]:has-text("{tab_name}"), .p-tabview-nav li:has-text("{tab_name}")').first
    await tab.click()
    await asyncio.sleep(2)

async def gap_a_screenshots(page):
    """Gap A: Excel Bid Import Wizard screenshots."""
    print("\n=== GAP A: Excel Bid Import Wizard ===")

    await login(page, "tendermgr@bayan.ae")
    await navigate_to_tender(page, "TNR-2026-0003")

    # Click Bids tab
    await click_tab(page, "Bids")
    await asyncio.sleep(2)
    await screenshot(page, "gapA-bids-tab.png")

    # Click on a bid to open details
    bid_row = page.locator('tr:has-text("Gulf MEP"), tr:has-text("bidder")').first
    try:
        # Try clicking the view/details button
        view_btn = page.locator('button[ptooltip="View Details"], button:has(i.pi-eye), button:has(i.pi-search)').first
        await view_btn.click(timeout=5000)
    except:
        try:
            await bid_row.click(timeout=5000)
        except:
            print("  [WARN] Could not click bid row, trying action buttons...")
            action_btns = page.locator('.action-buttons button, td button').all()
            for btn in await action_btns:
                await btn.click()
                break

    await asyncio.sleep(2)
    await screenshot(page, "gapA-bid-details-dialog.png")

    # Find and click Import BOQ button
    try:
        import_btn = page.locator('button:has-text("Import BOQ"), button:has-text("Import Wizard"), button:has(i.pi-file-import)').first
        await import_btn.click(timeout=5000)
        await asyncio.sleep(2)
        await screenshot(page, "gapA-step01-upload.png", full_page=True)
        print("  [OK] Wizard opened - Step 1 screenshot taken")

        # The wizard is now open - try to interact with it
        # Check if there's a Parse button
        parse_btn = page.locator('button:has-text("Parse"), button:has-text("Upload"), button:has-text("Start")').first
        try:
            await parse_btn.click(timeout=5000)
            await asyncio.sleep(3)
            await screenshot(page, "gapA-step01-parsed.png", full_page=True)
            print("  [OK] Parse completed screenshot")
        except:
            print("  [WARN] Could not click Parse button")

        # Try to proceed through wizard steps
        next_btn = page.locator('button:has-text("Next"), button:has-text("Auto-Map"), button:has-text("Map Columns")').first
        try:
            await next_btn.click(timeout=5000)
            await asyncio.sleep(2)
            await screenshot(page, "gapA-step02-columns.png", full_page=True)
            print("  [OK] Step 2 - Column mapping screenshot")
        except:
            print("  [WARN] Could not proceed to step 2")

        # Continue through steps
        for step_num, step_name in [(3, "matching"), (4, "normalize"), (5, "validate")]:
            try:
                next_btn = page.locator('button:has-text("Next"), button:has-text("Match"), button:has-text("Normalize"), button:has-text("Validate"), button:has-text("Import")').first
                await next_btn.click(timeout=5000)
                await asyncio.sleep(3)
                await screenshot(page, f"gapA-step0{step_num}-{step_name}.png", full_page=True)
                print(f"  [OK] Step {step_num} - {step_name} screenshot")
            except:
                print(f"  [WARN] Could not proceed to step {step_num}")

    except Exception as e:
        print(f"  [WARN] Could not open wizard: {str(e)[:100]}")
        await screenshot(page, "gapA-wizard-attempt.png", full_page=True)

async def gap_b_screenshots(page):
    """Gap B: Approval workflow screenshots (uses TNR-2026-0003 which is already awarded)."""
    print("\n=== GAP B: Approval Workflow ===")

    await login(page, "tendermgr@bayan.ae")
    await navigate_to_tender(page, "TNR-2026-0003")

    # Click Approval tab
    await click_tab(page, "Approval")
    await asyncio.sleep(2)
    await screenshot(page, "gapB-approval-tab-tm-view.png")
    print("  [OK] Approval tab screenshot")

    # Check if there's approval history
    await screenshot(page, "gapB-approval-history.png", full_page=True)

    # Check approval status
    try:
        status_element = page.locator('.approval-status, .workflow-status, [data-testid="approval-status"]').first
        await screenshot(page, "gapB-approval-status.png")
        print("  [OK] Approval status screenshot")
    except:
        pass

    # Login as approver to see approver view
    await login(page, "approver@bayan.ae")
    await asyncio.sleep(2)

    # Check for pending approvals on dashboard
    await screenshot(page, "gapB-approver-dashboard.png")

    # Navigate to TNR-2026-0003
    try:
        await navigate_to_tender(page, "TNR-2026-0003")
        await click_tab(page, "Approval")
        await asyncio.sleep(2)
        await screenshot(page, "gapB-approver-view.png")
        print("  [OK] Approver view screenshot")
    except Exception as e:
        print(f"  [WARN] Could not navigate to tender as approver: {str(e)[:100]}")

async def gap_c_screenshots(page):
    """Gap C: Documents Tab screenshots."""
    print("\n=== GAP C: Documents Tab ===")

    await login(page, "tendermgr@bayan.ae")
    await navigate_to_tender(page, "TNR-2026-0003")

    # Click Documents tab
    await click_tab(page, "Documents")
    await asyncio.sleep(2)
    await screenshot(page, "gapC-documents-tab-empty.png")
    print("  [OK] Documents tab empty state screenshot")

    # Try to click Upload button
    try:
        upload_btn = page.locator('button:has-text("Upload"), button[data-testid="upload-document-btn"]').first
        await upload_btn.click(timeout=5000)
        await asyncio.sleep(1)
        await screenshot(page, "gapC-upload-dialog.png")
        print("  [OK] Upload dialog screenshot")

        # Close the dialog
        cancel_btn = page.locator('button:has-text("Cancel")').first
        await cancel_btn.click(timeout=3000)
        await asyncio.sleep(1)
    except Exception as e:
        print(f"  [WARN] Upload dialog: {str(e)[:100]}")

async def bonus_sensitivity_screenshots(page):
    """Bonus: Sensitivity Analysis screenshots."""
    print("\n=== BONUS: Sensitivity Analysis ===")

    await login(page, "tendermgr@bayan.ae")
    await navigate_to_tender(page, "TNR-2026-0003")

    # Click Evaluation tab
    await click_tab(page, "Evaluation")
    await asyncio.sleep(2)
    await screenshot(page, "bonus-evaluation-tab.png")

    # Try to find sensitivity analysis button or comparable sheet
    try:
        # Look for Comparable sub-tab
        comparable_btn = page.locator('button:has-text("Comparable"), a:has-text("Comparable"), [data-testid*="comparable"]').first
        await comparable_btn.click(timeout=5000)
        await asyncio.sleep(2)
        await screenshot(page, "bonus-comparable-with-bid-prices.png", full_page=True)
        print("  [OK] Comparable sheet screenshot")
    except:
        print("  [WARN] Could not find comparable sheet button")

    # Look for sensitivity analysis
    try:
        sensitivity_btn = page.locator('button:has-text("Sensitivity"), button:has-text("Analysis"), [data-testid*="sensitivity"]').first
        await sensitivity_btn.click(timeout=5000)
        await asyncio.sleep(3)
        await screenshot(page, "bonus-sensitivity-scenarios.png", full_page=True)
        print("  [OK] Sensitivity analysis screenshot")
    except:
        print("  [WARN] Could not find sensitivity analysis button")

async def regression_screenshots(page):
    """Regression check screenshots."""
    print("\n=== REGRESSION CHECK ===")

    await login(page, "tendermgr@bayan.ae")

    # Check TNR-2026-0001
    try:
        await navigate_to_tender(page, "TNR-2026-0001")
        await screenshot(page, "regression-tnr-0001.png")
        print("  [OK] TNR-2026-0001 loads correctly")
    except:
        print("  [WARN] Could not load TNR-2026-0001")

    # Check TNR-2026-0002
    try:
        await navigate_to_tender(page, "TNR-2026-0002")
        await screenshot(page, "regression-tnr-0002.png")
        print("  [OK] TNR-2026-0002 loads correctly")
    except:
        print("  [WARN] Could not load TNR-2026-0002")

    # Check TNR-2026-0003
    try:
        await navigate_to_tender(page, "TNR-2026-0003")
        await screenshot(page, "regression-tnr-0003.png")
        print("  [OK] TNR-2026-0003 loads correctly")

        # Check bids tab still accessible
        await click_tab(page, "Bids")
        await asyncio.sleep(2)
        await screenshot(page, "regression-tnr-0003-bids.png")
        print("  [OK] Bids tab accessible")

        # Check approval tab
        await click_tab(page, "Approval")
        await asyncio.sleep(2)
        await screenshot(page, "regression-tnr-0003-approval.png")
        print("  [OK] Approval tab accessible")

    except Exception as e:
        print(f"  [WARN] TNR-2026-0003 regression: {str(e)[:100]}")

    # Check console errors
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
    await page.goto(f"{UI_BASE}/tenders")
    await asyncio.sleep(3)
    if console_errors:
        print(f"  [WARN] Console errors: {len(console_errors)}")
        for err in console_errors[:5]:
            print(f"    - {err[:100]}")
    else:
        print("  [OK] No console errors detected")

async def main():
    print("=" * 70)
    print("BAYAN TENDER - Browser Verification & Screenshots")
    print("=" * 70)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="en-US"
        )
        page = await context.new_page()

        # Set a reasonable timeout
        page.set_default_timeout(10000)

        try:
            # Test basic connectivity
            print("\n[CHECK] Testing UI connectivity...")
            response = await page.goto(f"{UI_BASE}")
            print(f"  Status: {response.status}")
            await asyncio.sleep(2)
            await screenshot(page, "00-landing-page.png")

            # Gap C first (simplest to verify)
            await gap_c_screenshots(page)

            # Gap A: Bid Import Wizard
            await gap_a_screenshots(page)

            # Gap B: Approval Workflow
            await gap_b_screenshots(page)

            # Bonus: Sensitivity Analysis
            await bonus_sensitivity_screenshots(page)

            # Regression Check
            await regression_screenshots(page)

        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            await screenshot(page, "error-state.png")
            raise
        finally:
            await browser.close()

    print(f"\n{'=' * 70}")
    print(f"Screenshots saved to: {SCREENSHOT_DIR}")
    screenshots = os.listdir(SCREENSHOT_DIR)
    print(f"Total screenshots: {len(screenshots)}")
    for s in sorted(screenshots):
        size = os.path.getsize(os.path.join(SCREENSHOT_DIR, s))
        print(f"  {s} ({size:,} bytes)")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
