# Design

Visual system for the node room. Warm paper and ink, light, one clay accent. Calm, legibility-first, product register. Derived from the confirmed shape brief (`docs/plans/2026-06-27-node-room-design.md` is the product spec; this file is the visual system).

## Theme

Light. Scene: a facilitator on her phone in the evening, tea gone cold, catching up on what three people wrote to a slow conversation since yesterday, deciding whether to add her own thought before bed. Warm, unhurried, reading-first. Depth comes from a second warm-neutral surface and hairlines, not shadows.

## Color (OKLCH, Restrained)

Tinted neutrals, hued warm (~hue 60-85) toward the clay accent. One accent. Never `#000`/`#fff`.

```
--paper:        oklch(0.975 0.012 83);   /* page background */
--paper-raised: oklch(0.955 0.015 80);   /* composer, panels, fields, code blocks */
--ink:          oklch(0.28 0.013 60);    /* body text (AA+ on paper) */
--ink-soft:     oklch(0.44 0.014 58);    /* meta, secondary (AA on paper) */
--hairline:     oklch(0.88 0.012 80);    /* dividers, borders */

--clay:         oklch(0.56 0.12 46);     /* accent fill: primary button, active tag, focus ring */
--clay-ink:     oklch(0.47 0.12 44);     /* accent as text: links, Claude label (AA on paper) */
--clay-tint:    oklch(0.965 0.022 60);   /* soft wash behind Claude's weave */
--paper-on-clay:oklch(0.985 0.008 83);   /* text on a clay fill */
```

Tag pigments (low chroma, distinct but calm; the tag WORD carries the meaning, color only reinforces, so no info is color-only):

```
--tag-question:  oklch(0.48 0.06 240);  bg oklch(0.96 0.02 240)   /* slate-blue */
--tag-story:     oklch(0.46 0.06 150);  bg oklch(0.96 0.02 150)   /* sage */
--tag-challenge: oklch(0.50 0.10 35);   bg oklch(0.96 0.03 40)    /* clay-red */
--tag-synthesis: oklch(0.48 0.07 305);  bg oklch(0.96 0.02 305)   /* plum */
```

Accent discipline (60-30-10 by visual weight): paper + reading type ~60-30; clay only on the one primary action per view, the active tag, Claude's voice, focus rings, and inline text links in prose (not lists of headings, e.g. lobby room titles are ink with a hover underline). Never decorative.

## Typography

One family: **Atkinson Hyperlegible** (designed for low-vision and dyslexia; loaded via `next/font/google`, weights 400 + 700 + italic, `display: swap`). Single hyperlegible family is the legibility-first, anti-slop choice; hierarchy comes from size + weight + space, not a second face. Family resemblance to the invitation page (which paired Atkinson with Bitter) without cloning it.

Fixed rem scale (product), ratio ~1.25:

```
--text-xs:   0.8125rem;  /* 13px  meta, tag chip */
--text-sm:   0.9375rem;  /* 15px  secondary, labels */
--text-base: 1.0625rem;  /* 17px  body (>=16px) */
--text-lg:   1.375rem;   /* 22px  section headings */
--text-xl:   1.875rem;   /* 30px  node title */
```

- Body line-height 1.6; headings 1.2. Measure 62ch for reading and message bodies.
- `text-wrap: pretty` on bodies, `balance` on headings. `font-kerning: normal`.
- All-caps tag labels are NOT used; tag words are sentence-case for legibility.

## Spacing & shape

4pt base scale, semantic tokens: `--space-1:4px --space-2:8px --space-3:12px --space-4:16px --space-6:24px --space-8:32px --space-12:48px --space-16:64px`. Use `gap`, not margins, for sibling spacing. Radii: `--radius-sm:6px` (chips, fields, buttons), `--radius-md:10px` (panels). No heavy shadows; elevation via `--paper-raised` + hairline.

## Layout

- **Site header**: a slim, quiet bar on every page (paper, hairline bottom border, inner content aligned to the reading column). The `Hybrid Dialogue` wordmark links home; quiet `About` and `Under the hood` links; one clay `Start a conversation` action. Global navigation that recedes, not a toolbar, no sidebar.
- One centered reading column, `max-width: 64ch`, generous page padding, mobile-first (the column is already the mobile layout; padding tightens at narrow widths). No sidebars, no cards-per-message, no metric tiles.
- **Thread**: a list of typographic entries. Each entry: a quiet meta line (author, middot, relative time, tag chip) then the body in reading type. Entries separated by `--space-8` and a hairline; not boxes.
- **Claude weave entry**: full-column soft `--clay-tint` band with a small clay diamond mark and a clay-ink "weave" label. Distinct and present, never louder than people.
- **Composer**: a `--paper-raised` panel in normal flow at the foot of the column (not a floating chat bar). Textarea, an inline quiet tag selector, one clay primary action.
- **Join / welcome**: centered, node title (xl), description, one name field, one primary action.
- **Manage**: same column; labeled sections (Weave, Harvest, Export), one primary action each, the harvest editor as a paper-raised writing area.
- **Create**: same column; labeled fields; on success the participant link and the private facilitator link in distinct copy-friendly blocks.

## Components & states

Every interactive element ships default / hover / focus-visible / active / disabled, and busy/loading where it triggers async work. 44px minimum tap targets.

- **Button** `.btn`: `.btn--primary` (clay fill, `--paper-on-clay` text), `.btn--quiet` (paper-raised, ink, hairline border). Hover darkens ~4% L; focus-visible clay ring (2px, offset); disabled drops to ink-soft on paper-raised with no clay.
- **Tag chip** `.tag` + `.tag--{kind}`: tinted bg, hued text, the word.
- **Field** `.field` (label above, input/textarea on paper-raised, hairline, clay focus ring).
- **Link** `.link`: clay-ink, underline on hover/focus. **Room link** `.room-link`: ink lobby title, hover underline in clay (titles are not clay). **Inline code** `.code`: model identifiers.
- **Header nav** `.site-header`: quiet global bar. `.site-name` (ink wordmark, links home), `.nav-link` (ink-soft quiet links), `.nav-cta` (small clay-fill "Start a conversation").
- **States covered**: pre-join, empty thread (opening frame + gentle first-contribution prompt), default, posting (button busy, disabled), post error (quiet inline message, draft preserved), polled arrival (gentle), harvest none/generating/draft/finalized, export gated until a harvest exists with a plain reason, form submitting/success.

## Motion

150-250ms, ease-out, state-only. New messages fade in with a 4px rise. Button background transitions on hover. No layout-property animation, no choreography. `@media (prefers-reduced-motion: reduce)` removes transitions and transforms.

## Accessibility

WCAG AA+ on all text (ink and ink-soft on paper, clay-ink links, paper-on-clay on clay all verified to pass). Visible non-color-only focus (clay ring). Full keyboard operability; `<label>` associated with every control; the thread is an `aria-live="polite"` region so polled arrivals are announced. No information by color alone (tag words, status text). `prefers-reduced-motion` honored.
