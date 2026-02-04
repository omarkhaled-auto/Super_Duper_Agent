# LinkVault Dashboard Design Reference
## Based on Firecrawl.dev Aesthetic Analysis

**Analysis Date:** February 2, 2026
**Source:** https://firecrawl.dev
**Purpose:** Design system reference for LinkVault dashboard styling

---

## 1. Color System

### Primary Brand Color (Heat/Orange Accent)
The signature Firecrawl color - use this for primary CTAs and accent elements.

| Token | Hex Value | Usage |
|-------|-----------|-------|
| `heat-100` | `#fa5d19` | Primary buttons, active states, links |
| `heat-8` | `#fa5d190d` | Badge backgrounds, subtle highlights |
| `heat-4` | `#fa5d190a` | Very faint backgrounds, hover states |

### Neutral Colors - Light Theme

| Token | Hex Value | Usage |
|-------|-----------|-------|
| `surface` | `#ffffff` | Card backgrounds, main content area |
| `background-base` | `#f9f9f9` | Page background |
| `background-lighter` | `#fbfbfb` | Elevated surfaces |
| `accent-black` | `#262626` | Primary text |
| `border-faint` | `#ededed` | Subtle borders, dividers |
| `border-muted` | `#e8e8e8` | Secondary borders |
| `border-loud` | `#e6e6e6` | Prominent borders |

### Neutral Colors - Dark Theme

| Token | Hex Value | Usage |
|-------|-----------|-------|
| `surface` | `#171717` | Card backgrounds |
| `background-base` | `#0a0a0a` | Page background |
| `background-lighter` | `#141414` | Elevated surfaces |
| `accent-black` (inverted) | `#f5f5f5` | Primary text |
| `border-faint` | `#2a2a2a` | Subtle borders |
| `border-muted` | `#333333` | Secondary borders |

### Semantic Accent Colors

| Name | Light Mode | Dark Mode | Usage |
|------|------------|-----------|-------|
| Amethyst | `#9061ff` | `#a07aff` | Info states, secondary actions |
| Bluetron | `#2a6dfb` | `#5a8ffc` | Links, informational |
| Crimson | `#eb3424` | `#f05545` | Error states, destructive actions |
| Forest | `#42c366` | `#5cd47f` | Success states, positive indicators |
| Honey | `#ecb730` | `#f0c550` | Warning states, caution |

### Alpha Overlays (Black with opacity)
Used for hover states, overlays, and layering effects:
- `black-alpha-2` - Subtle hover background
- `black-alpha-4` through `black-alpha-88` - Progressive layering

---

## 2. Typography

### Font Families

```css
/* Primary font stack */
font-family: "Geist", "Geist Variable", system-ui, sans-serif;

/* Monospace (code, technical content) */
font-family: "GeistMono Variable", "Roboto Mono", monospace;

/* Alternative/Fallback */
font-family: "Suisse", "Roboto Sans", system-ui, sans-serif;
```

### Font Weights

| Weight | Value | Usage |
|--------|-------|-------|
| Regular | 400 | Body text |
| Book | 450 | Slightly emphasized body |
| Medium | 500 | Subheadings, labels |
| Semibold | 600 | Headings, important text |
| Bold | 700 | Primary headings, CTAs |

### Text Styles (Semantic)

| Style | Usage |
|-------|-------|
| `text-label-medium` | Form labels, small captions |
| `text-body-medium` | Main content text |
| `text-heading-*` | Page and section headings |

### Badge Typography
```css
.badge {
  font-size: 12px;
  line-height: 16px;
  font-weight: 450;
}
```

---

## 3. Spacing System

### Container Gutters
- Mobile: `24px` horizontal padding
- Desktop: `44px` horizontal padding

### Component Spacing
| Size | Pixels | Usage |
|------|--------|-------|
| xs | 4px | Badge padding-y, tight spacing |
| sm | 8px | Badge padding-x, icon gaps |
| md | 16px | Button padding-y, card padding |
| lg | 24px | Button padding-x, section gaps |
| xl | 32px | Large section gaps |
| 2xl | 44px | Container gutters (desktop) |

### Gap Pattern
- Standard component gap: `gap-24` (24px)
- Card grid gaps: 16-24px

---

## 4. Border System

### Border Radius
| Token | Value | Usage |
|-------|-------|-------|
| `rounded-6` | 6px | Buttons, badges, inputs |
| `rounded-8` | 8px | Cards, panels |
| `rounded-12` | 12px | Large cards, modals |

### Border Weights
- Default: 1px solid
- Use `border-faint` for subtle separation
- Use `border-muted` for secondary emphasis
- Use `border-loud` for prominent separation

---

## 5. Component Patterns

### Buttons

**Primary Button (CTA)**
```css
.btn-primary {
  background-color: #fa5d19;
  color: #ffffff;
  padding: 16px 24px;
  border-radius: 6px;
  font-weight: 500;
  transition: all 150ms ease;
}

.btn-primary:hover {
  background-color: #e5520f; /* Slightly darker */
}
```

**Secondary/Ghost Button**
```css
.btn-secondary {
  background-color: transparent;
  color: #262626;
  padding: 16px 24px;
  border-radius: 6px;
  border: 1px solid #e8e8e8;
  transition: all 150ms ease;
}

.btn-secondary:hover {
  background-color: rgba(0, 0, 0, 0.02); /* black-alpha-2 */
}
```

### Cards

```css
.card {
  background-color: #ffffff;
  border: 1px solid #ededed;
  border-radius: 8px;
  padding: 24px;
}

/* Dark mode */
.dark .card {
  background-color: #171717;
  border-color: #2a2a2a;
}
```

### Badges/Tags

```css
.badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  font-size: 12px;
  line-height: 16px;
  font-weight: 450;
  border-radius: 6px;
}

.badge-primary {
  background-color: #fa5d190a; /* heat-4 */
  color: #fa5d19;
}

.badge-success {
  background-color: rgba(66, 195, 102, 0.1);
  color: #42c366;
}

.badge-error {
  background-color: rgba(235, 52, 36, 0.1);
  color: #eb3424;
}
```

### Form Inputs

```css
.input {
  width: 100%;
  padding: 12px 16px;
  font-size: 14px;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  background-color: #ffffff;
  transition: border-color 150ms ease;
}

.input:focus {
  outline: none;
  border-color: #fa5d19;
  box-shadow: 0 0 0 3px #fa5d190a;
}

/* Dark mode */
.dark .input {
  background-color: #171717;
  border-color: #333333;
  color: #f5f5f5;
}
```

### Navigation Header

```css
.header {
  position: sticky;
  top: 0;
  left: 0;
  z-index: 101;
  background-color: #ffffff;
  border-bottom: 1px solid #ededed;
}

.dark .header {
  background-color: #0a0a0a;
  border-bottom-color: #2a2a2a;
}
```

### Tabs

```css
.tabs {
  display: flex;
  gap: 4px;
  border-bottom: 1px solid #ededed;
}

.tab {
  padding: 12px 16px;
  font-weight: 450;
  color: #666666;
  border-bottom: 2px solid transparent;
  transition: all 150ms ease;
}

.tab:hover {
  color: #262626;
  background-color: rgba(0, 0, 0, 0.02);
}

.tab.active {
  color: #fa5d19;
  border-bottom-color: #fa5d19;
}
```

---

## 6. Layout Patterns

### Container
```css
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}

@media (min-width: 1024px) {
  .container {
    padding: 0 44px;
  }
}
```

### Page Layout with Sidebar
```css
.layout {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 260px;
  flex-shrink: 0;
  border-right: 1px solid #ededed;
  background-color: #f9f9f9;
}

.main-content {
  flex: 1;
  overflow-x: clip;
}
```

### Card Grid
```css
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
}
```

---

## 7. Dark Theme Implementation

### Approach
Firecrawl uses CSS custom properties with a `.dark` class selector on the root element.

```css
:root {
  --color-surface: #ffffff;
  --color-background-base: #f9f9f9;
  --color-text-primary: #262626;
  --color-border-faint: #ededed;
  --color-border-muted: #e8e8e8;
}

.dark {
  --color-surface: #171717;
  --color-background-base: #0a0a0a;
  --color-text-primary: #f5f5f5;
  --color-border-faint: #2a2a2a;
  --color-border-muted: #333333;
}
```

### Key Principles
1. Background colors get darker (not simply inverted)
2. Text becomes light gray (`#f5f5f5`), not pure white
3. Borders become slightly lighter than backgrounds
4. Accent colors (like heat orange) remain consistent
5. Semantic colors (success, error) get slightly lighter for better contrast

---

## 8. Special Effects & Animations

### Transitions
```css
/* Standard transition for all interactive elements */
transition: all 150ms ease;
```

### Hover Effects
```css
/* Subtle background change on hover */
:hover {
  background-color: rgba(0, 0, 0, 0.02);
}

/* Color intensity change */
:hover {
  color: #fa5d19; /* heat-100 for maximum intensity */
}
```

### Focus States
```css
:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(250, 93, 25, 0.04);
}
```

### Loading States
- Use text indicators: "Loading status..."
- Implement skeleton loaders with `background-color: #f0f0f0` animating

---

## 9. Iconography

### Icon System
Firecrawl uses a semantic icon naming system:
- `key` - Authentication, API keys
- `play` - Playground, actions
- `file-lines` - Documents, content
- `magnifying-glass` - Search
- `robot` - AI/Agent features
- `code` - Technical, code-related
- `boxes-stacked` - Collections, SDKs
- `github` - GitHub integration
- `puzzle-piece` - Integrations

### Recommended Icon Library
Consider using:
- Lucide Icons (modern, consistent)
- Heroicons (Tailwind ecosystem)
- Phosphor Icons (flexible weights)

---

## 10. Implementation Notes for LinkVault

### CSS Variables Setup (Tailwind config or CSS)

```css
:root {
  /* Brand */
  --lv-primary: #fa5d19;
  --lv-primary-light: rgba(250, 93, 25, 0.04);

  /* Backgrounds */
  --lv-bg-base: #f9f9f9;
  --lv-bg-surface: #ffffff;
  --lv-bg-elevated: #fbfbfb;

  /* Text */
  --lv-text-primary: #262626;
  --lv-text-secondary: #666666;
  --lv-text-muted: #999999;

  /* Borders */
  --lv-border-faint: #ededed;
  --lv-border-muted: #e8e8e8;

  /* Semantic */
  --lv-success: #42c366;
  --lv-warning: #ecb730;
  --lv-error: #eb3424;
  --lv-info: #2a6dfb;
}

.dark {
  --lv-bg-base: #0a0a0a;
  --lv-bg-surface: #171717;
  --lv-bg-elevated: #141414;
  --lv-text-primary: #f5f5f5;
  --lv-text-secondary: #a0a0a0;
  --lv-text-muted: #666666;
  --lv-border-faint: #2a2a2a;
  --lv-border-muted: #333333;
  --lv-success: #5cd47f;
  --lv-warning: #f0c550;
  --lv-error: #f05545;
  --lv-info: #5a8ffc;
}
```

### Key Design Principles from Firecrawl

1. **Minimal Visual Noise** - Clean interfaces with purposeful elements
2. **High Contrast** - Ensure accessibility in both light/dark modes
3. **Consistent Spacing** - Use the 4px base unit (4, 8, 12, 16, 24, 32, 44)
4. **Orange as Accent** - Use sparingly for important actions/states
5. **Border-Based Hierarchy** - Use borders instead of shadows for depth
6. **Technical Aesthetic** - Monospace fonts for data/code elements

---

## Summary

The Firecrawl design system is characterized by:
- **Clean, minimal aesthetic** with purposeful color usage
- **Vibrant orange (#fa5d19)** as the primary accent color
- **Geist font family** for a modern, technical feel
- **Border-based visual hierarchy** over shadows
- **Comprehensive dark mode** with proper color mapping
- **Consistent 4px-based spacing** system
- **6px border radius** as the standard for interactive elements

This design reference should serve as the foundation for styling the LinkVault dashboard to achieve a professional, modern aesthetic similar to Firecrawl.
