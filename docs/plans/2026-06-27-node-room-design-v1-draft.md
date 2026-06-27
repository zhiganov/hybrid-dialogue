# Node Room — Design Spec

- **Date:** 2026-06-27
- **Author:** Artem (with Claude)
- **Status:** Draft for review

## Context

Ben Roberts is running a July 2026 design inquiry into better tools for asynchronous/hybrid conversation ("Chat Tool"). His full design describes a four-beat arc — **EXPRESS → MAP → DROP INTO → HARVEST** — where the novel surface is a *map* of conversations happening elsewhere, not a chat venue. Beats 1, 2, and 4 run today on Google Forms → Sheets → Claude → Kumu. Beat 3 ("DROP INTO" — the actual small-group conversation) is currently just a bare Google Doc.

This spec covers **Beat 3 only**: replacing that bare Doc with a real shared room where a small group plus Claude (as facilitator) converse, producing a harvest that feeds back to the Kumu map.

Source docs:
- Invitation: https://docs.google.com/document/d/1yGdE0unAFX8oLi8PBCBWubcYtzKMnA5U-zeZ41P9SEw/edit
- Design rationale: https://docs.google.com/document/d/1KJZHTj3_Xka6M56e55GpXvR9D-4m7O_KOcXS2flo-2U/edit

## Goal

A small-group, **live**, web-based conversation room — seeded by an engagement node — where a handful of invited participants and Claude converse together, everything visible to all, producing a human-edited harvest exportable to Ben's Kumu map.

## Non-goals (v1)

- The MAP layer (Beats 1–2) — stays Forms → Sheets → Claude → Kumu.
- The mycelium spatial visualization — that is Kumu's job.
- Live Kumu sync — manual CSV export only.
- Live-call scheduling, mobile app, roles beyond facilitator/participant, threading UI.

## Users

- **Facilitator** (Ben or a convener) — creates a room from a node, triggers the harvest, exports to Kumu.
- **Participant** — invited via link, joins with a display name, converses.

## Experience (happy path)

1. Facilitator creates a room from an engagement node: node title + description + Claude facilitation instructions. Gets a share link.
2. Participant opens the link → enters a display name (email optional, prefilled if known) → enters the live room.
3. Claude posts the opening frame derived from the node.
4. Participants converse in real time. Each message can carry an optional contribution tag: **question / story / challenge / synthesis**.
5. Claude facilitates — silent by default. It (a) replies when @-mentioned (streamed token-by-token), and (b) posts a periodic "weave": a synthesis, a surfaced connection between people, or an opening question, when enough new material has accrued.
6. Facilitator clicks **Harvest** → Claude distills the conversation into a draft → facilitator edits it → finalizes. (AI assists; the human decides what matters.)
7. Facilitator clicks **Export for Kumu** → downloads CSV rows matching Ben's schema.

## Architecture

- **Frontend:** Next.js (App Router) + React. Primary route `/room/[id]`; a lightweight `/room/[id]/manage` for the facilitator (create, harvest, export).
- **Realtime + data + auth:** Supabase — Postgres for storage, Realtime channels for the live shared stream and presence, anonymous/lightweight auth for join-by-link.
- **Claude:** Anthropic API (`@anthropic-ai/sdk`) called only from Next.js server routes (API key stays server-side). Streaming via `messages.stream()` for live replies.
- **Host:** Netlify or Railway (Vercel is reserved for Harmonica in this workspace).

### Data model (Postgres / Supabase)

- `rooms`: id, node_title, node_description, facilitation_prompt, created_by, created_at
- `participants`: id, room_id, display_name, email (nullable), joined_at
- `messages`: id, room_id, author_type (`human` | `claude` | `system`), participant_id (nullable), body, contribution_tag (nullable enum), created_at
- `harvests`: id, room_id, body (Claude draft, human-edited), finalized_at (nullable)

### Realtime

Clients subscribe to `messages` inserts scoped to their `room_id` → instant shared stream for everyone. A presence channel powers an optional "who's here" indicator.

### Claude integration (server-side)

Two trigger paths, both via a server route that calls Anthropic:

1. **@claude mention** → assemble context (node frame + facilitation prompt + recent messages) → `messages.stream()` → insert a `claude` message, streaming tokens to clients. Model: `claude-sonnet-4-6` for snappy latency.
2. **Periodic weave** → debounced trigger after N new human messages (and/or a timer) → synthesis call → insert a `claude` message. Model: `claude-opus-4-8` with adaptive thinking (`thinking: {type: "adaptive"}`).

**Harvest:** facilitator-triggered route → Claude distills the full transcript → returns an editable draft stored in `harvests`. Model: `claude-opus-4-8`, adaptive thinking.

**System prompt** encodes the "amplifier, not replacement" stance: encourage human-to-human exchange, synthesize rather than opine, surface connections *between people*, stay quiet unless it adds value.

Cost note: small-group volume keeps spend trivial. Opus 4.8 is $5/$25 per MTok; Sonnet 4.6 is $3/$15.

### Kumu export (manual)

A server route emits CSV matching Ben's two-sheet schema:
- **Elements:** a row `Label=<harvest short title>`, `Type=Harvest`.
- **Connections:** `Person → Harvest` (Type `Harvested`) and `Harvest → Engagement Node`.

Facilitator downloads and pastes into the Elements / Connections Google Sheets. No live sync.

## Ops

- Anthropic tokens are the only meaningful running cost; the quiet-by-default facilitator plus small groups keep it low.
- Supabase free tier is sufficient for a July prototype.

## Open questions (to confirm before build)

- **Repo + license:** recommend a **public OSS repo** — it honors the inquiry's stated AI ethic (community-owned, data-sovereign) and lets other builder-respondents (Ana/Social Roots, Rijon, Eugene, Graham Lawes) collaborate. Org: personal `zhiganov` vs a shared/CIBC org vs Ben's — TBD.
- **Weave cadence:** every N messages vs timer — tune during build.
- **Presence ("who's here"):** include in v1 or cut.
