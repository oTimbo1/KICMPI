# KicMPi Website — Style & Branding Investigation

> **Purpose:** The KicMPi RAG concept web app should visually resemble https://www.kicmpi.com/ so the client relates to it immediately. This document records the site's design system (colors, typography, components, layout patterns) as measured from the live site on **2026-11-02**, plus the decisions for how we reproduce it in the concept app.
>
> **Method:** raw HTML + full theme CSS (`uh_theme`, a custom Drupal theme by Urban Heroes) parsed for design tokens, the logo SVG parsed for brand colors, and full-page screenshots captured as visual reference.
>
> **Reference screenshots:** [`kicmpi-home-top.jpg`](assets/kicmpi-home-top.jpg) (header + hero + news) · [`kicmpi-home-full.jpg`](assets/kicmpi-home-full.jpg) (entire homepage).
> **Logo asset:** already downloaded for the app → [`/frontend/public/kicmpi-logo.svg`](../../frontend/public/kicmpi-logo.svg)

---

## 1. Brand identity

- **Logo:** geometric sans-serif wordmark "**KiC|MPi**" (stylised `K i C | M P i`) in **brand blue `#0069B4`** with **magenta `#E6007E` dots** over the two `i`s. Below it, small blue tagline: "Kennis- en Innovatiecentrum Maintenance Procesindustrie". (See `kicmpi-logo.svg`.)
- **Overall feel:** clean, corporate, Dutch public-sector-modern. Lots of white space, full-bleed industrial photography, blue/magenta accents on a white base. Not playful, not dark — light and structured.
- **Language:** Dutch (UI, content, dates in `dd-mm-yyyy` format, e.g. `21-09-2026`).

## 2. Color system (measured from CSS)

| Token | Hex | Usage on kicmpi.com |
|---|---|---|
| **kicmpi-blue** (primary) | `#1668B1` | Buttons (bg), section titles, links, logo-adjacent UI |
| **kicmpi-blue-hover** | `#104D84` | Nav-link / button hover (darker blue) |
| **kicmpi-navy** | `#0B3356` | Primary button hover, dark overlays, dark text on light accents |
| **kicmpi-logo-blue** | `#0069B4` | Logo wordmark only |
| **kicmpi-magenta** (accent) | `#E5027E` | Active nav link + nav hover, news/event **dates**, breadcrumb, white-button text, mobile menu toggle, newsletter submit button, selected radio — the *attention* color |
| **kicmpi-logo-magenta** | `#E6007E` | Dots in the logo |
| text-primary | `#333333` / `#4A4A4A` | Headings/body on white |
| text-muted | `#666666`, `#999999` | Secondary text, footer text |
| border/hairline | `#CCCCCC`, `#E6E6E6` | Borders, dividers |
| bg-white | `#FFFFFF` | Default page background |
| bg-stripe-a / bg-stripe-b | `#FCFCFC` / `#EBEBEB` | The signature **diagonal-striped section** background (45° repeating gradient, 6–8 px stripes — a very subtle fabric texture) |
| footer-bg | ≈ `#222222` (near-black, from screenshot) | Footer band |
| pillar-card colors (approx., from screenshot) | blue ≈ `#1668B1`, black ≈ `#1A1A1A`, magenta ≈ `#E5027E`, green ≈ `#6C9A3F` | The 4 "Innovatiepijlers" cards (Digital & Robotics / Compliance / Corrosie / Circulair & Energie) — rendered as one image on the site |

**Rules observed:**
- Blue is the *action & heading* color. Magenta is the *highlight & state* color (active, date, CTA-on-white). They are never used together on the same element.
- Grays are very light and cool; no warm grays.
- No gradients on UI elements (the only "pattern" is the subtle diagonal stripe texture).

## 3. Typography (measured from CSS + Typekit kit)

- **Font:** **Prometo** (Adobe Typekit; weights 400, 500, 600, 700 + italics). A geometric-humanist sans-serif: friendly, rounded terminals, fairly wide.
- **Scale (measured):** base `16 px`; `h1` = 2 em (32 px); `h2`/`.h2` = `28 px`; large display up to 36–64 px on hero; small labels 14 px. Line height ≈ 1.5 for body.
- **Weights:** regular 400 for body, **600–700 for nav links, buttons, card titles** (the site leans on semibold a lot).
- Section titles: blue `#1668B1`, bold, left-aligned, generous margin below.

> **Decision for the concept app:** Prometo is a licensed Typekit font (kit is domain-locked to kicmpi.com) → we **cannot** load it from our app. We use a free, visually close geometric sans as stand-in: **Figtree** (Google Fonts, 400–700) as first choice, **Inter** as fallback alternative. Both ship with the app (no external network dependency at demo time). The swap is a one-line Tailwind config change if the client later provides a licensed copy of Prometo.

## 4. Buttons & interactive elements (measured from CSS)

| Variant | Style (final, cascade-resolved) |
|---|---|
| **Primary `.btn`** | `padding: 6px 24px` (up to `12px 24px`), **pill** `border-radius: 25px`, bg `#1668B1`, white text, `font-weight: 600`, no border; **hover → bg `#0B3356`** (navy) |
| **`.more-link`** (e.g. "Meer nieuws »") | Same pill style, right-aligned in its section, arrow `»` suffix |
| **`.btn--white`** (hero CTA on dark photo) | bg `#FFFFFF`, **text `#E5027E` (magenta)**, pill |
| **`.btn--border`** | transparent, `2px solid #1668B1`, text `#1668B1`, radius 5 px |
| **Inputs** (newsletter form) | borderless, **pill `border-radius: 25px`**, `padding: 12px 24px` |
| **Submit (newsletter)** | magenta `#E5027E` **circular** button with white arrow icon |
| **Mobile menu toggle** | pill with `3px solid #E5027E`, magenta text |
| Links | color inherit; nav links `font-weight: 600` with `0.5s` color transition; **active/hover → magenta `#E5027E`**; breadcrumbs magenta with blue links |

## 5. Layout patterns (from screenshots + HTML structure)

1. **Header:** white, sticky, full-width. Logo left (max-height 65 px), horizontal nav right (Home, Projecten, Innovaties, Kalender, Downloads, Nieuws, Leden, Contact, Transitiecoaching) + user icon far right. Active page = **magenta**. Thin shadow under header.
2. **Hero:** full-bleed industrial-plant photograph, **dark blue overlay**, a **dark semi-transparent content box** (right of center) with white bold title, white body text and stacked **white pill buttons**. Height ≈ 500 px–100 vh.
3. **Sections:** alternating **white** and **diagonal-striped light-gray** bands (`section--striped-grey`). Each section starts with a **blue bold title** (left-aligned).
4. **Cards:**
   - *News:* small image left, **magenta date**, bold title, intro text, "»" more-link.
   - *Kalender:* image with dark gradient, **date chip** (big day number + short month, white on dark) bottom-left, bold white title over image.
   - *Projecten:* 2-column grid, image with dark gradient bottom, white title over image, **magenta check badge** (bottom-right) for finished projects.
   - *USP row:* 3 columns, **circular outline icons** (radius 100 %) + label (Projecten / Leden / Kalender).
5. **Footer:** near-black band, 3 columns (Contact / address / social icons), **blue column headings**, muted gray text, centered copyright line at the very bottom ("Concept & realisatie: Urban Heroes").

## 6. Radii & spacing

- **Pill (25 px)** = buttons & inputs (the signature shape).
- **3–5 px** = small elements (base buttons, borders).
- **100 % / 50 %** = circular icons/badges.
- Cards are mostly **square-cornered** with image overlays (no big rounding) — keep the concept app's cards at ≤ 8 px radius.
- Vertical rhythm is generous: 24 px base margins, full-width bands with centered content column.

## 7. Do / Don't for the concept app

**Do:**
- White base + light gray striped bands; blue `#1668B1` for headings & primary actions; magenta `#E5027E` for active states, dates, highlights and the white-CTA text.
- Pill buttons (primary blue → navy hover; white variant with magenta text).
- Sticky white header with logo left / nav right; active tab in magenta.
- Blue bold section titles, left-aligned.
- Dutch UI language, `dd-mm-yyyy` dates, semibold (600) emphasis.
- Keep it light, airy, corporate — industrial-imagery hero optional (a navy/blue gradient hero is an acceptable stand-in without photos).

**Don't:**
- No dark-mode look, no heavy shadows, no glassmorphism, no gradients on buttons.
- Don't mix blue and magenta on one element.
- Don't use warm grays or saturated greens/oranges outside the 4 pillar colors.
- Don't over-round (no `rounded-2xl+` cards).

## 8. Tailwind design tokens (drop-in for the concept app)

```js
// tailwind theme extension (see PLAN_WEBAPP_V1.md)
colors: {
  kicmpi: {
    blue:      '#1668B1',  // primary action / headings / links
    blueDeep:  '#104D84',  // hover (links)
    navy:      '#0B3356',  // hover (buttons) / dark hero
    magenta:   '#E5027E',  // accent: active, dates, CTA-on-white, highlights
    ink:       '#333333',  // primary text
    slate:     '#4A4A4A',  // secondary text
    muted:     '#999999',  // tertiary text
    line:      '#E6E6E6',  // hairlines
    stripeA:   '#FCFCFC',  // striped-section base
    stripeB:   '#EBEBEB',  // striped-section stripe
    dark:      '#222222',  // footer
  },
  fontFamily: { sans: ['Figtree', 'Inter', 'system-ui', 'sans-serif'] },
}
```

Signature striped section (reproduces `section--striped-grey`):

```css
.bg-kicmpi-stripes {
  background: repeating-linear-gradient(
    45deg,
    #FCFCFC 0px, #FCFCFC 6px,
    #EBEBEB 6px, #EBEBEB 8px
  );
}
```
