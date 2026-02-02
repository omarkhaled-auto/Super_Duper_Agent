"""Built-in UI Design Standards for Agent Team.

Provides baseline UI quality constraints that are injected into every
orchestrator prompt.  When no custom standards file is configured the
built-in ``UI_DESIGN_STANDARDS`` constant is used.  A custom file path
can override it via ``config.design_reference.standards_file``.
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Built-in standards constant
# ---------------------------------------------------------------------------

UI_DESIGN_STANDARDS = r"""
============================================================
UI DESIGN STANDARDS (ALWAYS APPLIED — BASELINE QUALITY)
============================================================

These standards are MANDATORY for every agent producing UI code.
They exist because LLMs reproduce the statistical median of their
training data — a phenomenon called "distributional convergence."
Without explicit constraints, every generated UI converges toward
the same purple-gradient, Inter-font, three-card-grid template.

------------------------------------------------------------
LAYER 1: DESIGN DIRECTION & ANTI-SLOP
------------------------------------------------------------

### 1. DISTRIBUTIONAL CONVERGENCE WARNING

LLMs default to the training-data average:
- Purple/indigo as primary color (from Tailwind UI demos)
- Inter, Roboto, or Arial as the only fonts
- Three identical icon-title-description cards for features
- Centered everything, oversized heroes, shadow overload
- Generic marketing copy: "unleash the power of..."

You MUST actively resist these defaults. Every choice should be
INTENTIONAL, not statistical.

### 2. DESIGN DIRECTION REQUIREMENT

BEFORE writing any UI code, choose a bold aesthetic direction for
the project. The direction must match the project's PURPOSE:

| Direction        | When to Use                              | Key Traits                                    |
|------------------|------------------------------------------|-----------------------------------------------|
| Brutalist        | Developer tools, technical products      | Raw, monospace, sharp edges, high contrast     |
| Luxury           | Premium services, fintech, fashion       | Serif headings, generous whitespace, muted     |
| Editorial        | Content platforms, news, publishing      | Strong type hierarchy, columns, pull quotes    |
| Retro-futuristic | Creative tools, gaming, experimental     | Neon accents, dark backgrounds, bold geometry  |
| Organic          | Health, wellness, sustainability         | Rounded shapes, earthy tones, natural textures |
| Playful          | Children, casual apps, entertainment     | Bright colors, rounded fonts, illustrations    |
| Industrial       | Manufacturing, logistics, enterprise     | Mono fonts, data-dense, muted palette          |
| Minimal Modern   | SaaS dashboards, productivity tools      | Clean lines, subtle color, functional layout   |

Commit to ONE direction. A fintech dashboard is NOT a children's
game is NOT a news site. If the user hasn't specified a direction,
infer one from the project's domain. NEVER default to "generic
modern SaaS."

### 3. TYPOGRAPHY: DISTINCTIVE CHOICES

NEVER use Inter, Roboto, or Arial as the primary font. These are
the training-data default. Choose from distinctive alternatives:

| Category     | Font Options                                        |
|--------------|-----------------------------------------------------|
| Editorial    | Playfair Display, Fraunces, Newsreader, Lora        |
| Startup      | Clash Display, Satoshi, Cabinet Grotesk, General Sans|
| Technical    | IBM Plex Mono, JetBrains Mono, Space Grotesk        |
| Distinctive  | Bricolage Grotesque, Syne, Outfit, Plus Jakarta Sans |
| Luxury       | Cormorant Garamond, Libre Baskerville, DM Serif     |

Font pairing rules:
- One display/heading font + one body font
- Heading and body fonts MUST have visible contrast
- Use weight EXTREMES: 100-200 for light, 800-900 for bold
  (NOT timid 400 vs 600)
- Size jumps of 3x+ between heading and body, not 1.5x

### 4. ANTI-PATTERNS: SLOP-001 through SLOP-015

| Code     | Name                    | What AI Does                                 | Fix                                                      |
|----------|-------------------------|----------------------------------------------|----------------------------------------------------------|
| SLOP-001 | Purple/Indigo Default   | bg-indigo-500 on everything                  | Choose colors from project context intentionally          |
| SLOP-002 | Generic Font Trio       | Inter, Roboto, or Arial everywhere           | Pick from distinctive font categories (Section 3)        |
| SLOP-003 | Three-Box Cliche        | Features = 3 identical cards                 | Vary: lists, asymmetric grids, bento, comparison tables   |
| SLOP-004 | Center-Everything       | All text centered                            | Left-align body. Center only hero headings/taglines       |
| SLOP-005 | Oversized Hero          | 100vh hero with massive text + CTA           | Hero 50-70vh max. Get to content fast                    |
| SLOP-006 | Shadow/Glow Overload    | Drop shadows on cards, buttons, inputs, text | Max 2-3 shadow levels. Meaningful elevation only          |
| SLOP-007 | Generic Copy            | "Unleash the power" / "Transform workflow"   | Write specific copy describing what the product does      |
| SLOP-008 | Decoration Overload     | Floating orbs, mesh gradients, noise filler  | Clean backgrounds. Decoration only for brand identity     |
| SLOP-009 | Off-Grid Spacing        | 13px here, 37px there, no rhythm             | EVERY spacing value on the 4/8px grid                    |
| SLOP-010 | Font Weight Timidity    | 400 vs 600 only                              | Use EXTREMES: 100/200 for light, 800/900 for bold        |
| SLOP-011 | Missing States          | No error, loading, empty, disabled states    | EVERY interactive component needs all 7 states            |
| SLOP-012 | Rounded-Everything      | Same border-radius on all elements           | Define radius system: sm/md/lg/full per component type    |
| SLOP-013 | No Visual Hierarchy     | Only font-size distinguishes elements        | Use size + weight + color + spacing. One dominant per section |
| SLOP-014 | Gradient Abuse          | Multi-color gradients on buttons+cards+bg    | Gradients only for hero/emphasis. Max 2 colors, subtle    |
| SLOP-015 | No Brand Differentiation| Every site looks identical regardless of purpose | Pick a design direction (Section 2). Match to domain     |

------------------------------------------------------------
LAYER 2: QUALITY FRAMEWORK
------------------------------------------------------------

### 5. SPACING SYSTEM

Base unit: 8px. All spacing values MUST be multiples of 4px or 8px.

| Token | Value | Usage                          |
|-------|-------|--------------------------------|
| xs    | 4px   | Inline element gaps            |
| sm    | 8px   | Tight internal padding         |
| md    | 16px  | Standard padding, card gaps    |
| lg    | 24px  | Section internal padding       |
| xl    | 32px  | Section gaps                   |
| 2xl   | 48px  | Major section separators       |
| 3xl   | 64px  | Page-level vertical spacing    |

Rules:
- Never use arbitrary pixel values (13px, 37px, 22px)
- Consistent rhythm across all files and components
- Use the same token names project-wide

### 6. COLOR SYSTEM ARCHITECTURE

Structure colors by semantic role, not by visual appearance:

| Role      | Purpose                          | Usage Cap    |
|-----------|----------------------------------|--------------|
| Primary   | Brand identity, CTAs, key links  | 10-15% max   |
| Secondary | Supporting actions, accents      | 5-10%        |
| Neutral   | Backgrounds, text, borders       | 70-80%       |
| Success   | Confirmations, positive states   | On-demand    |
| Warning   | Caution, approaching limits      | On-demand    |
| Error     | Failures, destructive actions    | On-demand    |
| Info      | Informational, help states       | On-demand    |

Rules:
- 80% neutral principle: most of the screen is neutral tones
- Primary color on max 10-15% of the visible area
- Every color must have a named token (not raw hex in code)
- Ensure 4.5:1 contrast ratio for body text (WCAG AA)
- Ensure 3:1 contrast ratio for large text and UI elements

### 7. COMPONENT PATTERNS

Standard component categories and their requirements:

**Buttons**: Primary, secondary, ghost, destructive variants.
  All variants need: default, hover, focus, active, disabled, loading states.

**Cards**: Container with consistent padding, radius, and optional elevation.
  Variants: default, interactive (hover lift), selected, disabled.

**Forms**: Labels always visible. Error messages inline below field.
  Required field indicators. Validation on blur and submit.

**Navigation**: Clear active state. Mobile responsive (hamburger or bottom nav).
  Keyboard accessible. Current page indicator.

**Modals/Dialogs**: Focus trap. Escape to close. Overlay backdrop.
  Accessible title. Close button. Prevent body scroll.

**Tables**: Sticky headers. Row hover. Sortable columns.
  Responsive: horizontal scroll or card layout on mobile.

### 8. COMPONENT STATE COMPLETENESS

ALL interactive components MUST have these states implemented:

| State    | Description                            | Visual Indicator         |
|----------|----------------------------------------|--------------------------|
| Default  | Resting state                          | Base styles              |
| Hover    | Mouse over (desktop)                   | Subtle background/color  |
| Focus    | Keyboard focus                         | Visible focus ring       |
| Active   | Being clicked/pressed                  | Pressed/depressed visual |
| Disabled | Cannot interact                        | Reduced opacity, cursor  |
| Loading  | Async operation in progress            | Spinner/skeleton         |
| Error    | Invalid state or failed operation      | Red border, error text   |
| Empty    | No data to display                     | Friendly empty message   |

AI-generated code typically produces ONLY the default state.
This is the single biggest quality gap between AI and professional UI.

### 9. LAYOUT PATTERNS

Responsive breakpoints:
- sm: 640px — mobile landscape
- md: 768px — tablet
- lg: 1024px — desktop
- xl: 1280px — wide desktop

Rules:
- Mobile-first: base styles target mobile, then add complexity
- Max content width: 1280px (or 1440px for dashboards)
- Container padding: 16px on mobile, 24-32px on desktop
- Grid: 12-column on desktop, stack on mobile
- No horizontal scroll on any breakpoint

### 10. MOTION & ANIMATION

- Duration: 150-300ms for micro-interactions, 300-500ms for page transitions
- Easing: ease-out for enters, ease-in for exits, ease-in-out for state changes
- Purpose: Animation must serve function (feedback, orientation, hierarchy)
- NEVER add animation purely for decoration
- ALWAYS respect `prefers-reduced-motion: reduce`

### 11. ACCESSIBILITY MINIMUMS (WCAG AA)

Non-negotiable requirements:
- Color contrast: 4.5:1 for body text, 3:1 for large text (18px+)
- Focus indicators: visible on ALL interactive elements (2px+ outline)
- Semantic HTML: use correct elements (button not div, nav not div)
- Keyboard navigation: all interactive elements reachable via Tab
- Form labels: every input has a visible associated label
- Alt text: every meaningful image has descriptive alt text
- Touch targets: minimum 44x44px on mobile
- Language: html lang attribute set
- Heading hierarchy: h1 → h2 → h3, no skipped levels
- ARIA: use only when native HTML semantics are insufficient

### 12. FRAMEWORK-ADAPTIVE NOTES

**React + Tailwind / shadcn/ui**:
- Define design tokens in tailwind.config (extend theme)
- Use CSS custom properties for dynamic values
- shadcn/ui components as base — customize, don't use defaults as-is
- Use className merging (cn utility) for variant overrides
- Responsive with Tailwind breakpoint prefixes (sm:, md:, lg:)

**Next.js**:
- Use CSS Modules or Tailwind. Avoid global CSS beyond reset.
- Server Components for static UI, Client Components for interactive
- next/font for optimized font loading (not CDN links)

**Vue**:
- Scoped styles in SFC. CSS custom properties for theming.
- Utility-first CSS or component-scoped Tailwind

**Vanilla HTML/CSS/JS**:
- CSS custom properties for all design tokens
- BEM or utility-first naming convention
- Responsive via media queries, mobile-first

**Svelte**:
- Component-scoped styles. CSS custom properties for theming.
- Transitions with built-in transition directives

------------------------------------------------------------
COPY & TEXT QUALITY
------------------------------------------------------------

- Write specific, concrete descriptions — not marketing platitudes
- Error messages should be helpful and human: "That email doesn't
  look right" not "Error: Invalid input detected"
- Button text is action-oriented: "Save Changes", "Create Project",
  "Sign In" — never just "Submit" or "Click Here"
- Headings describe content, not hype: "Pricing" not "Unlock Your
  Potential"
- Empty states have personality: "No projects yet — create your
  first one!" not blank space or "No data"
- Loading states are informative: "Loading your dashboard..." not
  just a spinner
""".strip()


def load_ui_standards(standards_file: str = "") -> str:
    """Load UI standards from a custom file or fall back to built-in.

    Args:
        standards_file: Path to a custom standards file.  Empty string
            or a path that cannot be read falls back to built-in.

    Returns:
        The standards text (stripped of leading/trailing whitespace).
    """
    if standards_file:
        path = Path(standards_file)
        try:
            return path.read_text(encoding="utf-8").strip()
        except (OSError, UnicodeDecodeError):
            pass  # callers warn separately
    return UI_DESIGN_STANDARDS
