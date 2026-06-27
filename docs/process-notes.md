# Process notes

## 2026-06-27 — Field catalogue of conversations
- **Done:** Built `invitation-generator` (generate.py → 6 conversation invitations + people recs + Kumu CSVs from the survey; render_html.py → navigable HTML). Created public repo `zhiganov/hybrid-dialogue`, deployed the page to Netlify. Wrote the Beat-3 node-room spec. Redesigned the HTML with impeccable (field-catalogue: warm OKLCH, Bitter + Atkinson Hyperlegible) after frontend-design read as AI-generated; then made it whole-group with per-reader opt-in and fixed a note-field-on-opt-in bug.
- **Decisions:** Beat 2 now, Beat 3 later (spec only); artifact is whole-group (opt-in), not convener-only; MIT/OSS; Netlify not Vercel; no participant PII in the public repo (`data/` + `output/` gitignored).
- **State:** Live at https://hybrid-dialogue-sqixgw.netlify.app (Netlify site `d214e36e-72c7-41b1-b86e-9b4ccc1c5451`). Repo clean + pushed. Generated output stays local.
- **Next:** Draft the message to Ben to share the link; optionally file a Beat-3 GitHub issue; optional impeccable polish pass.
