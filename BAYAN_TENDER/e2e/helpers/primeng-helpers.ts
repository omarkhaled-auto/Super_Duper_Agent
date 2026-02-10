import { Page } from '@playwright/test';

// ---------------------------------------------------------------------------
// Dropdown (p-dropdown)
// ---------------------------------------------------------------------------

/**
 * Select an option from a PrimeNG dropdown by visible text.
 *
 * @param page      Playwright Page
 * @param selector  CSS selector targeting the `<p-dropdown>` element
 * @param optionText  Visible label of the option to select
 */
export async function selectDropdown(
  page: Page,
  selector: string,
  optionText: string,
): Promise<void> {
  const dropdown = page.locator(selector);
  // Click the dropdown trigger to open the overlay panel
  await dropdown.locator('.p-dropdown-trigger, .p-dropdown-label').click();
  // Wait for the overlay panel to appear
  const panel = page.locator('.p-dropdown-panel');
  await panel.waitFor({ state: 'visible' });
  // Click the matching option
  await panel.locator('.p-dropdown-item').filter({ hasText: optionText }).click();
  // Wait for the panel to close
  await panel.waitFor({ state: 'hidden' });
}

// ---------------------------------------------------------------------------
// AutoComplete (p-autoComplete)
// ---------------------------------------------------------------------------

/**
 * Type into a PrimeNG autocomplete and select the first matching suggestion.
 */
export async function selectAutoComplete(
  page: Page,
  selector: string,
  searchText: string,
): Promise<void> {
  const autoComplete = page.locator(selector);
  const input = autoComplete.locator('input');
  await input.fill(searchText);
  // Wait for the suggestions panel
  const panel = page.locator('.p-autocomplete-panel');
  await panel.waitFor({ state: 'visible' });
  // Click the first matching item
  await panel.locator('.p-autocomplete-item').first().click();
  await panel.waitFor({ state: 'hidden' });
}

// ---------------------------------------------------------------------------
// Calendar (p-calendar)
// ---------------------------------------------------------------------------

/**
 * Select a date from a PrimeNG calendar.
 *
 * Opens the calendar popup, navigates forward/backward through months if the
 * target month differs from the currently displayed one, then clicks the day.
 */
export async function selectCalendarDate(
  page: Page,
  selector: string,
  date: Date,
): Promise<void> {
  const calendar = page.locator(selector);
  // Open the calendar overlay by clicking the input or trigger button
  await calendar.locator('input, .p-datepicker-trigger').first().click();

  const panel = page.locator('.p-datepicker');
  await panel.waitFor({ state: 'visible' });

  const targetYear = date.getFullYear();
  const targetMonth = date.getMonth(); // 0-indexed
  const targetDay = date.getDate();

  // Navigate to the correct month/year
  const maxNavigationAttempts = 24;
  for (let i = 0; i < maxNavigationAttempts; i++) {
    const monthYearText = await panel
      .locator('.p-datepicker-title')
      .textContent();

    if (!monthYearText) break;

    // Parse displayed month/year (e.g. "January 2026")
    const parts = monthYearText.trim().split(/\s+/);
    const displayedMonthStr = parts[0];
    const displayedYear = parseInt(parts[parts.length - 1], 10);
    const displayedMonth = monthNameToIndex(displayedMonthStr);

    const displayedTotal = displayedYear * 12 + displayedMonth;
    const targetTotal = targetYear * 12 + targetMonth;

    if (displayedTotal === targetTotal) break;

    if (displayedTotal < targetTotal) {
      await panel.locator('.p-datepicker-next').click();
    } else {
      await panel.locator('.p-datepicker-prev').click();
    }

    // Brief pause for the calendar to re-render
    await page.waitForTimeout(150);
  }

  // Click the target day — select only enabled day cells
  await panel
    .locator('td:not(.p-datepicker-other-month) > span:not(.p-disabled)')
    .filter({ hasText: new RegExp(`^${targetDay}$`) })
    .click();
}

/**
 * Convert an English month name to a 0-indexed month number.
 */
function monthNameToIndex(name: string): number {
  const months = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
  ];
  const idx = months.findIndex(
    (m) => m.toLowerCase() === name.toLowerCase(),
  );
  return idx === -1 ? 0 : idx;
}

// ---------------------------------------------------------------------------
// Checkbox (p-checkbox)
// ---------------------------------------------------------------------------

/**
 * Ensure a PrimeNG checkbox is checked.
 */
export async function checkCheckbox(
  page: Page,
  selector: string,
): Promise<void> {
  const checkbox = page.locator(selector);
  const box = checkbox.locator('.p-checkbox-box');
  const isChecked = await box.evaluate(
    (el) => el.classList.contains('p-highlight'),
  );
  if (!isChecked) {
    await box.click();
  }
}

/**
 * Ensure a PrimeNG checkbox is unchecked.
 */
export async function uncheckCheckbox(
  page: Page,
  selector: string,
): Promise<void> {
  const checkbox = page.locator(selector);
  const box = checkbox.locator('.p-checkbox-box');
  const isChecked = await box.evaluate(
    (el) => el.classList.contains('p-highlight'),
  );
  if (isChecked) {
    await box.click();
  }
}

// ---------------------------------------------------------------------------
// MultiSelect (p-multiSelect)
// ---------------------------------------------------------------------------

/**
 * Select one or more options in a PrimeNG multiSelect.
 */
export async function selectMultiSelect(
  page: Page,
  selector: string,
  options: string[],
): Promise<void> {
  const multiSelect = page.locator(selector);
  // Open the overlay
  await multiSelect.locator('.p-multiselect-trigger, .p-multiselect-label').click();

  const panel = page.locator('.p-multiselect-panel');
  await panel.waitFor({ state: 'visible' });

  for (const optionText of options) {
    await panel
      .locator('.p-multiselect-item')
      .filter({ hasText: optionText })
      .click();
  }

  // Close the panel by clicking the multiselect header close button or pressing Escape
  await page.keyboard.press('Escape');
  await panel.waitFor({ state: 'hidden' });
}

// ---------------------------------------------------------------------------
// FileUpload (p-fileUpload)
// ---------------------------------------------------------------------------

/**
 * Upload a file via a PrimeNG file upload component.
 * Targets the hidden `<input type="file">` under the component.
 */
export async function uploadFile(
  page: Page,
  selector: string,
  filePath: string,
): Promise<void> {
  const fileInput = page.locator(`${selector} input[type="file"]`);
  await fileInput.setInputFiles(filePath);
}

// ---------------------------------------------------------------------------
// Toast (p-toast)
// ---------------------------------------------------------------------------

/**
 * Wait for a PrimeNG toast to appear and return its text content.
 */
export async function getToastMessage(page: Page): Promise<string> {
  const toast = page.locator('.p-toast-message-text');
  await toast.first().waitFor({ state: 'visible', timeout: 10_000 });
  return (await toast.first().textContent()) ?? '';
}

/**
 * Wait for the PrimeNG toast message to auto-dismiss (disappear from DOM).
 */
export async function waitForToastToDisappear(page: Page): Promise<void> {
  await page
    .locator('.p-toast-message')
    .first()
    .waitFor({ state: 'hidden', timeout: 15_000 });
}

// ---------------------------------------------------------------------------
// ConfirmDialog (p-confirmDialog)
// ---------------------------------------------------------------------------

/**
 * Click Accept or Reject on a PrimeNG confirm dialog.
 */
export async function confirmDialog(
  page: Page,
  action: 'accept' | 'reject',
): Promise<void> {
  const dialog = page.locator('.p-confirm-dialog, p-confirmdialog .p-dialog');
  await dialog.waitFor({ state: 'visible' });

  if (action === 'accept') {
    await dialog.locator('.p-confirm-dialog-accept').click();
  } else {
    await dialog.locator('.p-confirm-dialog-reject').click();
  }

  await dialog.waitFor({ state: 'hidden' });
}

// ---------------------------------------------------------------------------
// DataTable (p-table)
// ---------------------------------------------------------------------------

const DEFAULT_TABLE = 'p-table';

/**
 * Return the number of visible data rows in a PrimeNG table.
 */
export async function getTableRowCount(
  page: Page,
  tableSelector: string = DEFAULT_TABLE,
): Promise<number> {
  return page.locator(`${tableSelector} .p-datatable-tbody > tr`).count();
}

/**
 * Get the text content of a specific table cell.
 * Both `rowIndex` and `colIndex` are 0-based.
 */
export async function getTableCellText(
  page: Page,
  rowIndex: number,
  colIndex: number,
  tableSelector: string = DEFAULT_TABLE,
): Promise<string> {
  const cell = page
    .locator(`${tableSelector} .p-datatable-tbody > tr`)
    .nth(rowIndex)
    .locator('td')
    .nth(colIndex);
  return (await cell.textContent())?.trim() ?? '';
}

/**
 * Click a specific row in a PrimeNG table (0-based index).
 */
export async function clickTableRow(
  page: Page,
  rowIndex: number,
  tableSelector: string = DEFAULT_TABLE,
): Promise<void> {
  await page
    .locator(`${tableSelector} .p-datatable-tbody > tr`)
    .nth(rowIndex)
    .click();
}

/**
 * Wait for the PrimeNG table loading overlay to disappear.
 */
export async function waitForTableLoad(
  page: Page,
  tableSelector: string = DEFAULT_TABLE,
): Promise<void> {
  const overlay = page.locator(
    `${tableSelector} .p-datatable-loading-overlay`,
  );
  // Only wait if the overlay is currently visible
  if (await overlay.isVisible()) {
    await overlay.waitFor({ state: 'hidden', timeout: 30_000 });
  }
}

// ---------------------------------------------------------------------------
// Steps / Stepper (p-steps)
// ---------------------------------------------------------------------------

/**
 * Return the 0-based index of the currently active step.
 */
export async function getStepperActiveIndex(page: Page): Promise<number> {
  const steps = page.locator('.p-steps-item');
  const count = await steps.count();

  for (let i = 0; i < count; i++) {
    const cls = await steps.nth(i).getAttribute('class');
    if (cls?.includes('p-highlight')) {
      return i;
    }
  }

  return -1;
}

/**
 * Click a specific step by its 0-based index.
 */
export async function clickStepperStep(
  page: Page,
  index: number,
): Promise<void> {
  await page.locator('.p-steps-item').nth(index).locator('a, .p-menuitem-link').click();
}

// ---------------------------------------------------------------------------
// Tag (p-tag)
// ---------------------------------------------------------------------------

/**
 * Read the visible text from a PrimeNG tag element.
 */
export async function getTagText(
  page: Page,
  selector: string,
): Promise<string> {
  const tag = page.locator(selector);
  return (await tag.locator('.p-tag-value, .p-tag').first().textContent())?.trim() ?? '';
}

// ---------------------------------------------------------------------------
// TreeTable (p-treeTable)
// ---------------------------------------------------------------------------

/**
 * Expand a row in a PrimeNG TreeTable by clicking its row toggler.
 * `rowIndex` is 0-based.
 */
export async function expandTreeTableRow(
  page: Page,
  rowIndex: number,
): Promise<void> {
  await page
    .locator('.p-treetable-tbody > tr')
    .nth(rowIndex)
    .locator('.p-treetable-toggler')
    .click();
}
