# Design

A naturalist's field catalogue, not a dashboard. The page reads like a printed field notebook: warm paper, sepia ink, specimen entries with classification tags and margin annotations. Voice over chrome.

## Theme

Light and warm. Scene: a facilitator at a sunlit kitchen table on a weekend morning, leafing through a field notebook, deciding which of six gatherings to host. Paper-and-ink, hand-kept, calm. Never dark, never neon.

## Color

OKLCH throughout. Tinted neutrals (warm ochre hue), never `#000`/`#fff`. Strategy: **committed / full-palette** — the four conversation kinds are real roles carried as muted herbarium pigments, not decoration.

- `--paper`: `oklch(0.925 0.018 80)` — warm manila (page). Deliberately not cream (#F4F1EA).
- `--sheet`: `oklch(0.955 0.013 85)` — lighter specimen sheet, for inset notes.
- `--ink`: `oklch(0.27 0.018 60)` — warm sepia-black (text).
- `--ink-soft`: `oklch(0.44 0.02 62)` — secondary text.
- `--faint`: `oklch(0.58 0.016 68)` — captions, metadata.
- `--rule`: `oklch(0.82 0.02 75)` — warm hairline dividers.
- Kind pigments (roles): content `oklch(0.5 0.08 150)` leaf-green · tension `oklch(0.52 0.13 38)` iron-gall rust · process `oklch(0.46 0.08 256)` indigo · relational `oklch(0.6 0.1 75)` ochre.
- Kind is **never** signalled by color alone — always paired with its text label. Pigment appears as a small swatch beside ink text (keeps text at AA on paper).

## Typography

Off the reflex-reject list. Two families, both deliberate.

- **Bitter** (sturdy slab serif): site title, conversation titles, participant voices (italic). The printed-field-guide voice.
- **Atkinson Hyperlegible** (body, labels, controls): chosen because legibility-is-respect is a product principle — it's engineered for low-vision and dyslexic readers.
- Fluid `clamp()` headings, ≥1.25 step ratio. Labels: Atkinson, small, letter-spaced.

## Layout

Single-column **specimen catalogue**, left-aligned, asymmetric. No cards, no card grid, no side-stripe borders.

- Each conversation is an **entry** in a two-part grid: a narrow left **label gutter** (accession number + kind tag + disposition control) and a main body (title, description, sub-sections).
- Entries are separated by full-width warm rules and generous space — a running notebook, not boxed cards.
- Sub-sections per entry: **Collected from** (the voices, as hanging-indent margin annotations), **Who might fit** (read-only suggestions), **Not yet in the collection** (archetypes, set apart).
- Mobile: the gutter stacks above the body.

## Components

- **Kind tag** — pigment swatch + small-caps label.
- **Opt-in control** — one "add to my list" toggle per entry; chosen entries get a soft highlight (never dim the rest). The note field appears only once an entry is chosen.
- **Who might fit** — read-only list of suggested people (name + why). Not assignable; people self-select.
- **Field-log footer** — sticky paper strip: running tally of your picks + export ("copy my list" / "as message"). No glassmorphism; solid paper + top rule.
- **Browse by kind** — filter tags in the masthead, plus a "My list" filter.

## Motion

Minimal. Ease-out only, no bounce, never animate layout properties. No entrance choreography — the voice is calm. Respect `prefers-reduced-motion` (disable transitions). State changes (cut/dim) transition gently.

## Accessibility

WCAG AA. Atkinson Hyperlegible body; no infinite-scroll feel; strong sectioning; kind never color-only; visible keyboard focus; full responsive to phone.
