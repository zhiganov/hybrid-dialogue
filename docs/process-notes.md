# Process notes

## 2026-06-27 — Field catalogue of conversations
- **Done:** Built `invitation-generator` (generate.py → 6 conversation invitations + people recs + Kumu CSVs from the survey; render_html.py → navigable HTML). Created public repo `zhiganov/hybrid-dialogue`, deployed the page to Netlify. Wrote the Beat-3 node-room spec. Redesigned the HTML with impeccable (field-catalogue: warm OKLCH, Bitter + Atkinson Hyperlegible) after frontend-design read as AI-generated; then made it whole-group with per-reader opt-in and fixed a note-field-on-opt-in bug.
- **Decisions:** Beat 2 now, Beat 3 later (spec only); artifact is whole-group (opt-in), not convener-only; MIT/OSS; Netlify not Vercel; no participant PII in the public repo (`data/` + `output/` gitignored).
- **State:** Live at https://hybrid-dialogue-sqixgw.netlify.app (Netlify site `d214e36e-72c7-41b1-b86e-9b4ccc1c5451`). Repo clean + pushed. Generated output stays local.
- **Next:** Draft the message to Ben to share the link; optionally file a Beat-3 GitHub issue; optional impeccable polish pass.

## 2026-06-28 — Built Beat 3 node-room (async)
- **Done:** Brainstormed + speced Beat 3 (async-first), wrote the implementation plan, built the app via subagent-driven development (8 tasks: Next.js + Postgres on Railway, domain logic, data layer, Claude facilitation with real-LLM smoke, API routes, participant + facilitator UIs, impeccable warm-paper design pass). Opus whole-branch review fixed a poll dedup race + harvest finalized-reset + opus token headroom. Pushed branch `node-room`. Also audited a week of GitHub issues, fixed broken links/titles, saved the lessons.
- **Decisions:** async-first (no realtime); Next.js + Postgres on Railway (not Supabase); quiet auto-weave facilitator; v1 includes harvest + Kumu export; warm-paper / Atkinson product-register design.
- **State:** `node-room` code-complete (Tasks 1-8) + reviewed + pushed, NOT deployed. Issue #1 refreshed; Walt's community-legibility boundary comment answered.
- **Next:** Task 9 (Railway deploy + finish branch, Closes #1); then the boundary follow-up (tasks: read Megan's Community Legibility Spec → design issue → consent + anonymized export).

## 2026-06-28 — node-room live, catalogue lobby, cost + transparency
- **Done:** Megan-boundary follow-up (read both Community Legibility specs; opened design issue #2; anonymized the Kumu export to tags-as-themes + consent line at join). Deployed node-room to Railway (project `node-room`, web + Postgres, root `node-room/`) and merged node-room→main (Closes #1). Built the catalogue↔node-room integration via SDD: `create_rooms.py` provisions one room per invitation; `render_html` adds Enter/lobby/propose links; the node-room home is now a live lobby of `listed` rooms with a facilitator hide/show toggle. Provisioned the 6 real rooms + redeployed the catalogue (live for Ben's group). Dropped Opus (opening frame→Haiku, weave/harvest/reply→Sonnet, ~5x cheaper) + a code-level em-dash strip. Added a `/transparency` page (models + system prompts, GitHub-linked). Filed issues #3 (model switching), #4 (BYOK), #5 (prompt surface), #6 (auth), #7 (markdown renderer).
- **Decisions:** shared rooms (one per invitation); static catalogue + dynamic lobby coexist; listed-flag listing model; facilitator capability-URL is interim (#6); enforce hard output rules (no em dashes) in code, not just the prompt; manual migrations.
- **State:** Live. Catalogue https://hybrid-dialogue-sqixgw.netlify.app; lobby https://node-room-web-production.up.railway.app (6 rooms). `main` pushed; one uncommitted `.gitignore` line (`__pycache__/`).
- **Next:** node-room backlog #3/#4/#6/#7; set an Anthropic spend cap (rooms run on the host key).
