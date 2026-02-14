# UI Requirements: Bayan Tender — Slate-Indigo Enterprise Design System

This document defines the complete design system for the Bayan Tender Management System UI transformation. All agents MUST reference this document when making any styling decisions.

---

## 1. Color System

### 1.1 Primary Brand — Indigo

| Token | Value | Usage |
|-------|-------|-------|
| `--bayan-primary` | `#4F46E5` (Indigo-600) | Primary buttons, active states, brand elements |
| `--bayan-primary-hover` | `#4338CA` (Indigo-700) | Button hover |
| `--bayan-primary-active` | `#3730A3` (Indigo-800) | Button active/pressed |
| `--bayan-primary-foreground` | `#FFFFFF` | Text on primary backgrounds |
| `--bayan-primary-light` | `rgba(79, 70, 229, 0.08)` | Subtle primary backgrounds |
| `--bayan-primary-ring` | `rgba(79, 70, 229, 0.15)` | Focus ring shadow |

### 1.2 Neutral Palette — Slate (replacing Zinc)

| Token | Value | Usage |
|-------|-------|-------|
| `--bayan-slate-50` | `#F8FAFC` | Page backgrounds, hover states |
| `--bayan-slate-100` | `#F1F5F9` | Secondary backgrounds, table headers |
| `--bayan-slate-200` | `#E2E8F0` | Borders, dividers |
| `--bayan-slate-300` | `#CBD5E1` | Disabled states, placeholder borders |
| `--bayan-slate-400` | `#94A3B8` | Placeholder text, icons |
| `--bayan-slate-500` | `#64748B` | Secondary text, muted labels |
| `--bayan-slate-600` | `#475569` | Body text alternate |
| `--bayan-slate-700` | `#334155` | Strong labels, form labels |
| `--bayan-slate-800` | `#1E293B` | Headings, portal header |
| `--bayan-slate-900` | `#0F172A` | Sidebar background, darkest text |
| `--bayan-slate-950` | `#020617` | Near-black |

### 1.3 Semantic Colors

| Token | Light Value | Usage |
|-------|-------------|-------|
| `--bayan-background` | `#FFFFFF` | Main content background |
| `--bayan-foreground` | `#0F172A` (Slate-900) | Primary text |
| `--bayan-card` | `#FFFFFF` | Card backgrounds |
| `--bayan-card-foreground` | `#0F172A` | Card text |
| `--bayan-secondary` | `#F1F5F9` (Slate-100) | Secondary button bg, muted areas |
| `--bayan-secondary-foreground` | `#0F172A` | Text on secondary |
| `--bayan-muted` | `#F1F5F9` (Slate-100) | Muted backgrounds |
| `--bayan-muted-foreground` | `#64748B` (Slate-500) | Muted/secondary text |
| `--bayan-muted-text` | `#94A3B8` (Slate-400) | Placeholder text |
| `--bayan-accent` | `#F1F5F9` (Slate-100) | Hover/accent backgrounds |
| `--bayan-accent-foreground` | `#0F172A` | Text on accent |
| `--bayan-border` | `#E2E8F0` (Slate-200) | All borders |
| `--bayan-input` | `#E2E8F0` (Slate-200) | Input borders |
| `--bayan-ring` | `#4F46E5` (Indigo-600) | Focus rings |

### 1.4 Sidebar Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `--bayan-sidebar-bg` | `#0F172A` (Slate-900) | Sidebar background |
| `--bayan-sidebar-foreground` | `#F8FAFC` (Slate-50) | Sidebar text |
| `--bayan-sidebar-border` | `#1E293B` (Slate-800) | Sidebar borders |
| `--bayan-sidebar-accent` | `rgba(248, 250, 252, 0.08)` | Sidebar hover |
| `--bayan-sidebar-accent-foreground` | `#F8FAFC` | Sidebar hover text |
| `--bayan-sidebar-active` | `rgba(79, 70, 229, 0.15)` | Active menu item bg |
| `--bayan-sidebar-active-border` | `#4F46E5` | Active menu item left border |
| `--bayan-sidebar-muted` | `#94A3B8` (Slate-400) | Sidebar secondary text |

### 1.5 Status Colors

| Status | Color | Background | Usage |
|--------|-------|------------|-------|
| Success | `#16A34A` (Green-600) | `#F0FDF4` (Green-50) | Approved, completed, passed |
| Warning | `#D97706` (Amber-600) | `#FFFBEB` (Amber-50) | Pending, review needed |
| Danger | `#DC2626` (Red-600) | `#FEF2F2` (Red-50) | Rejected, errors, overdue |
| Info | `#2563EB` (Blue-600) | `#EFF6FF` (Blue-50) | Published, informational |

---

## 2. Typography

### 2.1 Font Family
```
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
```

### 2.2 Size Scale

| Name | Size | Line Height | Usage |
|------|------|-------------|-------|
| xs | 0.75rem (12px) | 1rem | Badges, captions, timestamps |
| sm | 0.875rem (14px) | 1.25rem | Body text, table cells, form inputs |
| base | 1rem (16px) | 1.5rem | Default body text |
| lg | 1.125rem (18px) | 1.75rem | Section titles, card headers |
| xl | 1.25rem (20px) | 1.75rem | Page sub-headings |
| 2xl | 1.5rem (24px) | 2rem | Page headings |
| 3xl | 1.875rem (30px) | 2.25rem | Dashboard metrics |
| 4xl | 2.25rem (36px) | 2.5rem | Hero text (auth pages) |

### 2.3 Weight Scale

| Name | Value | Usage |
|------|-------|-------|
| Normal | 400 | Body text, descriptions |
| Medium | 500 | Buttons, labels, nav items |
| Semibold | 600 | Headings, table headers, form labels |
| Bold | 700 | Page titles, KPI values, logo text |

---

## 3. Spacing

4px base unit scale:

| Token | Value |
|-------|-------|
| `--bayan-spacing-0.5` | 0.125rem (2px) |
| `--bayan-spacing-1` | 0.25rem (4px) |
| `--bayan-spacing-1.5` | 0.375rem (6px) |
| `--bayan-spacing-2` | 0.5rem (8px) |
| `--bayan-spacing-3` | 0.75rem (12px) |
| `--bayan-spacing-4` | 1rem (16px) |
| `--bayan-spacing-5` | 1.25rem (20px) |
| `--bayan-spacing-6` | 1.5rem (24px) |
| `--bayan-spacing-8` | 2rem (32px) |
| `--bayan-spacing-10` | 2.5rem (40px) |
| `--bayan-spacing-12` | 3rem (48px) |
| `--bayan-spacing-16` | 4rem (64px) |
| `--bayan-spacing-20` | 5rem (80px) |
| `--bayan-spacing-24` | 6rem (96px) |

---

## 4. Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `--bayan-radius-sm` | 0.375rem (6px) | Small inputs, badges, chips |
| `--bayan-radius` | 0.5rem (8px) | Default (buttons, cards) |
| `--bayan-radius-lg` | 0.75rem (12px) | Cards, dialogs |
| `--bayan-radius-xl` | 1rem (16px) | Large cards, modals |
| `--bayan-radius-2xl` | 1.5rem (24px) | Auth page cards |
| `--bayan-radius-full` | 9999px | Avatars, pill badges |

---

## 5. Shadows

| Token | Value | Usage |
|-------|-------|-------|
| `--bayan-shadow-xs` | `0 1px 2px 0 rgba(0, 0, 0, 0.05)` | Subtle lift (buttons) |
| `--bayan-shadow-sm` | `0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)` | Cards |
| `--bayan-shadow` | `0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)` | Elevated cards |
| `--bayan-shadow-lg` | `0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)` | Dropdowns, popovers |
| `--bayan-shadow-xl` | `0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)` | Dialogs |
| `--bayan-shadow-dialog` | `0 25px 50px -12px rgba(0, 0, 0, 0.25)` | Modal overlays |

---

## 6. Component Patterns

### 6.1 Card
```scss
.bayan-card {
  background: var(--bayan-card);
  border: 1px solid var(--bayan-border);
  border-radius: var(--bayan-radius-lg);
  box-shadow: var(--bayan-shadow-sm);
  overflow: hidden;
}
```

### 6.2 Page Header
```scss
.bayan-page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;

  h1, h2 {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--bayan-foreground);
    margin: 0;
  }
}
```

### 6.3 KPI Card
```scss
.bayan-kpi-card {
  background: var(--bayan-card);
  border: 1px solid var(--bayan-border);
  border-left: 4px solid var(--kpi-color, var(--bayan-primary));
  border-radius: var(--bayan-radius-lg);
  box-shadow: var(--bayan-shadow-sm);
  padding: 1.25rem 1.5rem;
}
```

### 6.4 Status Badge
```scss
.bayan-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.75rem;
  border-radius: var(--bayan-radius-full);
  font-size: 0.75rem;
  font-weight: 600;
  line-height: 1;
  white-space: nowrap;

  &.badge-success { background: var(--bayan-success-bg); color: var(--bayan-success); }
  &.badge-warning { background: var(--bayan-warning-bg); color: var(--bayan-warning); }
  &.badge-danger { background: var(--bayan-danger-bg); color: var(--bayan-danger); }
  &.badge-info { background: var(--bayan-info-bg); color: var(--bayan-info); }
  &.badge-neutral { background: var(--bayan-slate-100); color: var(--bayan-slate-600); }
}
```

### 6.5 Dialog Pattern
```scss
// Applied via PrimeNG overrides in styles.scss
.p-dialog {
  border-radius: var(--bayan-radius-xl);
  box-shadow: var(--bayan-shadow-dialog);
  overflow: hidden;

  .p-dialog-header {
    padding: 1.25rem 1.5rem;
    border-bottom: 1px solid var(--bayan-border);
    background: var(--bayan-card);

    .p-dialog-title {
      font-size: 1.125rem;
      font-weight: 600;
      color: var(--bayan-foreground);
    }
  }

  .p-dialog-content {
    padding: 1.5rem;
  }

  .p-dialog-footer {
    padding: 1rem 1.5rem;
    border-top: 1px solid var(--bayan-border);
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
  }
}
```

### 6.6 Form Field Pattern
```scss
.bayan-form-field {
  margin-bottom: 1.25rem;

  label {
    display: block;
    font-weight: 600;
    font-size: 0.875rem;
    color: var(--bayan-slate-700);
    margin-bottom: 0.5rem;
  }

  .field-required {
    color: #DC2626;
    margin-left: 0.125rem;
  }

  .field-hint {
    font-size: 0.8rem;
    color: var(--bayan-muted-foreground);
    margin-top: 0.25rem;
  }

  .field-error {
    font-size: 0.8rem;
    color: #DC2626;
    margin-top: 0.25rem;
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }
}
```

### 6.7 Table Header Pattern
```scss
.bayan-table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--bayan-border);
  background: var(--bayan-card);
  border-radius: var(--bayan-radius-lg) var(--bayan-radius-lg) 0 0;
}
```

### 6.8 Empty State
```scss
.bayan-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  color: var(--bayan-muted-foreground);

  i {
    font-size: 3rem;
    margin-bottom: 1rem;
    color: var(--bayan-slate-300);
  }

  h4 {
    font-size: 1rem;
    font-weight: 600;
    color: var(--bayan-slate-700);
    margin-bottom: 0.5rem;
  }

  p {
    margin: 0;
    font-size: 0.875rem;
    color: var(--bayan-slate-500);
  }
}
```

---

## 7. Layout Specifications

| Element | Expanded | Collapsed |
|---------|----------|-----------|
| Sidebar width | 280px | 64px |
| Header height | 64px | 64px |
| Content max-width | 1400px | — |
| Content padding | 1.5rem | 1.5rem |

### 7.1 Sidebar (Dark Theme)
```scss
.sidebar-container {
  background: var(--bayan-sidebar-bg);  // #0F172A
  color: var(--bayan-sidebar-foreground);  // #F8FAFC
  border-right: 1px solid var(--bayan-sidebar-border);  // #1E293B

  .menu-item {
    color: var(--bayan-sidebar-muted);  // #94A3B8
    &:hover {
      background: var(--bayan-sidebar-accent);  // rgba(248,250,252,0.08)
      color: var(--bayan-sidebar-foreground);  // #F8FAFC
    }
    &.active {
      background: var(--bayan-sidebar-active);  // rgba(79,70,229,0.15)
      color: #FFFFFF;
      border-left: 3px solid var(--bayan-sidebar-active-border);  // #4F46E5
    }
  }

  .menu-icon {
    color: var(--bayan-sidebar-muted);
    .active & { color: #A5B4FC; }  // Indigo-300 for active icons
  }
}
```

### 7.2 Header
```scss
.header-container {
  background: var(--bayan-card);  // #FFFFFF
  border-bottom: 1px solid var(--bayan-border);
  height: 64px;

  .logo-icon {
    color: var(--bayan-primary);  // #4F46E5
  }

  .logo-text {
    color: var(--bayan-foreground);
    font-weight: 700;
  }
}
```

---

## 8. PrimeNG Override Standards

All PrimeNG components used in the app must be overridden in `styles.scss` to match the design system.

### 8.1 Buttons (p-button)
- Default: `bg: var(--bayan-primary)`, `color: #FFF`, `border-radius: var(--bayan-radius)`
- Hover: `bg: var(--bayan-primary-hover)`
- Active: `bg: var(--bayan-primary-active)`
- Outlined: `border: 1px solid var(--bayan-border)`, `color: var(--bayan-foreground)`
- Text: transparent bg, `color: var(--bayan-foreground)`
- Severity: success=`#16A34A`, danger=`#DC2626`, warning=`#D97706`
- Disabled: `opacity: 0.5`

### 8.2 Cards (p-card)
- `border-radius: var(--bayan-radius-lg)`
- `border: 1px solid var(--bayan-border)`
- `box-shadow: var(--bayan-shadow-sm)` (upgraded from none)
- `background: var(--bayan-card)`

### 8.3 Data Table (p-datatable)
- Header: `bg: var(--bayan-slate-50)`, `color: var(--bayan-slate-600)`, uppercase, 0.75rem
- Body row: `padding: 0.75rem 1rem`, hover `bg: var(--bayan-slate-50)`
- Sort icon: indigo when active
- Selection: indigo checkbox
- Striped (optional): alternating `var(--bayan-slate-50)` / `white`

### 8.4 Dialog (p-dialog)
- `border-radius: var(--bayan-radius-xl)`
- `box-shadow: var(--bayan-shadow-dialog)`
- Header: bottom border, 600 weight title
- Content: `padding: 1.5rem`
- Footer: top border, flex-end gap-3
- Backdrop: `rgba(15, 23, 42, 0.5)` (dark slate overlay)

### 8.5 Form Inputs (p-inputtext, p-dropdown, p-multiselect, p-calendar, p-textarea)
- `border-radius: var(--bayan-radius-sm)`
- `border: 1px solid var(--bayan-input)`
- Focus: `box-shadow: 0 0 0 3px var(--bayan-primary-ring)`, `border-color: var(--bayan-primary)`
- Hover: `border-color: var(--bayan-slate-300)`

### 8.6 TabView (p-tablist, p-tab, p-tabpanels)
- Tab bar: `border-bottom: 1px solid var(--bayan-border)`
- Inactive tab: `color: var(--bayan-muted-foreground)`, no bottom border
- Hover: `color: var(--bayan-foreground)`, `border-bottom: 2px solid var(--bayan-slate-300)`
- Active: `color: var(--bayan-foreground)`, `border-bottom: 2px solid var(--bayan-primary)`, 600 weight

### 8.7 Steps (p-steps)
- Inactive: `border: var(--bayan-slate-300)`, `bg: white`, `color: var(--bayan-slate-400)`
- Active: `bg: var(--bayan-primary)`, `color: #FFF`, `border: var(--bayan-primary)`
- Completed: same as active or with checkmark icon
- Connector: `bg: var(--bayan-primary)` (completed), `var(--bayan-slate-200)` (upcoming)

### 8.8 Toast (p-toast)
- `border-radius: var(--bayan-radius)`
- `border: 1px solid var(--bayan-border)`
- `border-left: 4px solid {severity-color}`
- `box-shadow: var(--bayan-shadow-lg)`

### 8.9 Badge (p-badge)
- `border-radius: var(--bayan-radius-full)`
- `font-size: 0.75rem`
- `font-weight: 600`
- Colors: match severity

### 8.10 Paginator (p-paginator)
- Active page: `bg: var(--bayan-primary)`, `color: #FFF`, circular
- Inactive: `bg: transparent`, `color: var(--bayan-slate-600)`
- Hover: `bg: var(--bayan-slate-100)`

### 8.11 Dropdown Panel (p-dropdown-panel, p-multiselect-panel)
- `border-radius: var(--bayan-radius-lg)`
- `box-shadow: var(--bayan-shadow-lg)`
- `border: 1px solid var(--bayan-border)`
- Item hover: `bg: var(--bayan-slate-50)`
- Selected: `bg: var(--bayan-primary-light)`, `color: var(--bayan-primary)`

### 8.12 Checkbox (p-checkbox)
- Unchecked: `border: 1px solid var(--bayan-input)`, `border-radius: var(--bayan-radius-sm)`
- Checked: `bg: var(--bayan-primary)`, `border-color: var(--bayan-primary)`

### 8.13 Tooltip (p-tooltip)
- `bg: var(--bayan-slate-900)`, `color: #FFF`
- `border-radius: var(--bayan-radius-sm)`
- `font-size: 0.8rem`
- `padding: 0.5rem 0.75rem`

### 8.14 Menu / Popup Menu (p-menu)
- `border-radius: var(--bayan-radius-lg)`
- `box-shadow: var(--bayan-shadow-lg)`
- `border: 1px solid var(--bayan-border)`
- Item: `padding: 0.625rem 1rem`, hover `bg: var(--bayan-slate-50)`
- Separator: `border-color: var(--bayan-border)`

### 8.15 Panel Menu (p-panelmenu) — Sidebar specific
- Header: transparent bg, white text on dark sidebar
- Active: indigo left border, indigo-tinted background
- Submenu: indented, lighter text color
- Icons: slate-400 default, white or indigo-300 when active

### 8.16 Password (p-password)
- Input: inherits standard input styling
- Toggle icon: `color: var(--bayan-slate-400)`

### 8.17 Confirm Dialog (p-confirmdialog)
- Inherits dialog pattern
- Reject button: outlined
- Accept/Confirm button: severity-appropriate (danger for deletes, primary for confirms)

### 8.18 FileUpload (p-fileupload)
- Drop zone: dashed border `var(--bayan-slate-300)`, `border-radius: var(--bayan-radius-lg)`
- Hover/drag: `border-color: var(--bayan-primary)`, `bg: var(--bayan-primary-light)`
- Icon: large, `color: var(--bayan-slate-400)`

### 8.19 ProgressBar
- Track: `bg: var(--bayan-slate-200)`, `border-radius: var(--bayan-radius-full)`
- Fill: `bg: var(--bayan-primary)`, `border-radius: var(--bayan-radius-full)`

### 8.20 Avatar (p-avatar)
- Background: `var(--bayan-primary)` (for letter avatars)
- Color: `#FFFFFF`
- `border-radius: var(--bayan-radius-full)`

---

## 9. Dark Mode

Apply via `.dark-mode` class on body or root element.

### 9.1 Token Overrides

| Token | Dark Value |
|-------|-----------|
| `--bayan-background` | `#020617` (Slate-950) |
| `--bayan-foreground` | `#F8FAFC` (Slate-50) |
| `--bayan-card` | `#0F172A` (Slate-900) |
| `--bayan-card-foreground` | `#F8FAFC` |
| `--bayan-primary` | `#818CF8` (Indigo-400, lighter for dark bg) |
| `--bayan-primary-hover` | `#6366F1` (Indigo-500) |
| `--bayan-primary-foreground` | `#FFFFFF` |
| `--bayan-secondary` | `#1E293B` (Slate-800) |
| `--bayan-secondary-foreground` | `#F8FAFC` |
| `--bayan-muted` | `#1E293B` (Slate-800) |
| `--bayan-muted-foreground` | `#94A3B8` (Slate-400) |
| `--bayan-muted-text` | `#64748B` (Slate-500) |
| `--bayan-accent` | `#1E293B` (Slate-800) |
| `--bayan-accent-foreground` | `#F8FAFC` |
| `--bayan-border` | `#1E293B` (Slate-800) |
| `--bayan-input` | `#1E293B` (Slate-800) |
| `--bayan-ring` | `#818CF8` (Indigo-400) |
| `--bayan-sidebar-bg` | `#020617` (Slate-950) |
| `--bayan-sidebar-foreground` | `#F8FAFC` |
| `--bayan-sidebar-border` | `#0F172A` |
| `--bayan-sidebar-accent` | `rgba(248, 250, 252, 0.05)` |
| `--bayan-sidebar-accent-foreground` | `#F8FAFC` |

### 9.2 Dark Mode Component Specifics
- Table header: `bg: var(--bayan-muted)`, `color: var(--bayan-muted-foreground)`
- Table row hover: `bg: var(--bayan-slate-800)`
- Scrollbar track: `var(--bayan-slate-900)`
- Scrollbar thumb: `var(--bayan-slate-700)`
- Input focus: `box-shadow: 0 0 0 3px rgba(129, 140, 248, 0.2)` (using dark primary)
- Dialogs: same shadow, darker backdrop `rgba(2, 6, 23, 0.7)`

---

## 10. Prohibited Changes

This section mirrors the PRD constraints for redundancy. ALL agents must respect these rules:

### 10.1 Do NOT Modify
- **TypeScript logic**: No changes to methods, signals, computed properties, subscriptions, event handlers
- **Services**: No changes to any .service.ts file
- **Models**: No changes to any .model.ts file
- **Guards**: No changes to auth.guard.ts or any guard file
- **Routes**: No changes to any .routes.ts file
- **Backend**: No changes to any file outside frontend/src/

### 10.2 Allowed Modifications
- `template:` blocks — HTML structure, CSS classes, PrimeNG attributes
- `styles:` blocks — All CSS within component
- `imports:` arrays in @Component — Only for adding PrimeNG modules for template use
- `styles.scss` — Global tokens and overrides
- `index.html` — Only meta tags and loading styles

### 10.3 Verification Checklist
After every component modification:
- [ ] No method bodies were changed
- [ ] No signal/computed definitions were changed
- [ ] No service calls were added or removed
- [ ] No @Input/@Output decorators were changed
- [ ] Only template, styles, and imports were modified
- [ ] Design tokens from this document were used (not hardcoded colors)
