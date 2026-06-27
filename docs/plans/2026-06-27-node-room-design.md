# Node Room — Design Spec

- **Date:** 2026-06-27
- **Author:** Artem (with Claude)
- **Status:** Approved for implementation
- **Supersedes:** the pre-brainstorm draft, kept at `2026-06-27-node-room-design-v1-draft.md`

## Context

Ben Roberts is running a July 2026 design inquiry into better tools for asynchronous and hybrid conversation ("Hybrid Conversation Toolkit"). His design describes a four-beat arc — **EXPRESS → MAP → DROP INTO → HARVEST**. Beats 1, 2, and 4 already run as Forms → Sheets → Claude → Kumu (and this repo's `invitation-generator/` covers MAP). Beat 3, "DROP INTO" — the actual small-group conversation — is currently just a bare Google Doc.

This spec covers **Beat 3 only**: replacing that bare Doc with a real shared room where a small group plus Claude (as a quiet facilitator) converse, producing a harvest that feeds back to Ben's Kumu map.

Source docs:
- Invitation: https://docs.google.com/document/d/1yGdE0unAFX8oLi8PBCBWubcYtzKMnA5U-zeZ41P9SEw/edit
- Design rationale: https://docs.google.com/document/d/1KJZHTj3_Xka6M56e55GpXvR9D-4m7O_KOcXS2flo-2U/edit

## Goal

An **async**, link-shared, web-based conversation room — seeded by an engagement node — where a handful of invited participants and Claude converse over hours or days. The conversation accretes like a forum thread; everything is visible to all; Claude bridges people who never overlap; the facilitator harvests it into a Kumu-ready output.

## Key decisions (resolved in brainstorming, 2026-06-27)

1. **Async-first, not live.** People drop in over hours/days; messages accrete; no presence, no realtime channels. This is truest to the inquiry's thesis (most async tools wrongly treat conversation as synchronous-stretched-over-time) and far leaner to build. New messages arrive by light client polling.
2. **Next.js + Postgres on Railway.** One platform hosts the app and the database. Vercel is reserved for Harmonica in this workspace; Railway matches the "stateful service" convention and keeps app + DB in one project.
3. **Quiet facilitator that auto-weaves across visits.** Claude opens the frame, stays silent during human exchange, answers when @-mentioned, and after a few new contributions posts one weave (a connection between people / synthesis / opening question). The async superpower is Claude connecting people who were never in the room at the same time.
4. **v1 includes a lean harvest + Kumu export.** Without it the room is a chat with no carry-forward output; the harvest loop is what connects Beat 3 back to Ben's map.

## Non-goals (v1)

- The MAP layer (Beats 1–2) — stays Forms → Sheets → Claude → Kumu / `invitation-generator/`.
- Live / synchronous mode, "who's here" presence, typing indicators.
- Live Kumu sync — manual CSV export only.
- The mycelium spatial visualization — that is Kumu's job.
- Scheduling, mobile app, roles beyond facilitator/participant, threading UI, accounts/passwords.

## Users

- **Facilitator** (Ben or a convener) — creates a room from a node, monitors it, triggers harvest, exports to Kumu. Holds a private manage link.
- **Participant** — invited via the room link, joins with a display name, converses.

## Experience (happy path)

1. Facilitator opens the manage link, creates a room from an engagement node: node title + description + Claude facilitation instructions. Gets a shareable participant link.
2. Participant opens the link → enters a display name once (stored in a cookie token) → enters the room.
3. Claude posts the opening frame derived from the node.
4. Participants converse asynchronously. Each message can carry an optional contribution tag: **question / story / challenge / synthesis**.
5. Claude facilitates — silent by default. It (a) replies when **@claude** mentioned, and (b) after ~4 new human contributions auto-posts one weave: a synthesis, a connection surfaced *between people*, or an opening question.
6. Facilitator clicks **Harvest** → Claude distills the thread into a draft → facilitator edits inline → finalizes.
7. Facilitator clicks **Export for Kumu** → downloads CSV rows matching Ben's schema.

## Architecture

- **Frontend + server:** Next.js (App Router) + TypeScript. Routes:
  - `/room/[id]` — participant view (read accreting thread, post with optional tag, @claude).
  - `/room/[id]/manage?key=<facilitator_token>` — facilitator view (create room, Weave now, Harvest, Export for Kumu).
- **Data:** Postgres on Railway, accessed via plain `pg` and a thin typed data module (`lib/db.ts`). No heavy ORM. Schema managed by SQL files in `migrations/`, applied via a small `npm run migrate` script.
- **Claude:** Anthropic SDK (`@anthropic-ai/sdk`) called only from Next.js server routes; API key stays server-side (Railway env var `ANTHROPIC_API_KEY`).
- **Updates:** client polls a fetch-since endpoint (~5s while the tab is visible). No realtime.
- **Host:** Railway — one service for the Next.js app, one Postgres database, same project.

### Data model (Postgres)

- `rooms`: id, node_title, node_description, facilitation_prompt, facilitator_token, created_at
- `participants`: id, room_id, display_name, token (cookie-stored, identifies a returning visitor within a room), joined_at
- `messages`: id, room_id, author_type (`human` | `claude` | `system`), participant_id (nullable), body, contribution_tag (nullable enum: `question` | `story` | `challenge` | `synthesis`), created_at
- `harvests`: id, room_id, body (Claude draft, human-edited), finalized_at (nullable)

### API routes

- `POST /api/rooms` — create room (returns id + facilitator_token + participant link). Manage-gated.
- `POST /api/rooms/[id]/join` — register a display name, set participant cookie token.
- `POST /api/rooms/[id]/messages` — post a human message (body + optional tag). Triggers @claude reply or weave check.
- `GET  /api/rooms/[id]/messages?since=<id|ts>` — poll for new messages.
- `POST /api/rooms/[id]/weave` — facilitator-triggered weave. Manage-gated.
- `POST /api/rooms/[id]/harvest` — generate harvest draft. Manage-gated.
- `PUT  /api/rooms/[id]/harvest` — save edited / finalize harvest. Manage-gated.
- `GET  /api/rooms/[id]/export.csv` — Kumu CSV. Manage-gated.

### Claude integration (server-side)

- **Opening frame** — on room creation, a `system`/`claude` message derived from node title + description + facilitation prompt.
- **@claude mention** → assemble context (node frame + facilitation prompt + recent messages) → reply once. Model: `claude-sonnet-4-6` (snappy), streamed.
- **Auto-weave** → after ~4 new human messages since Claude's last post (debounced; threshold tunable), one weave. Model: `claude-opus-4-8` with adaptive thinking (`thinking: { type: "adaptive" }`).
- **Harvest** → facilitator-triggered; distills the full transcript into an editable draft. Model: `claude-opus-4-8`, adaptive thinking.
- **System prompt** encodes the "amplifier, not replacement" stance: encourage human-to-human exchange, synthesize rather than opine, surface connections *between people*, stay quiet unless it adds value.
- **Abuse guard:** a per-room cooldown on Claude-triggering actions so `@claude` cannot be spammed into runaway cost.

Cost note: small-group async volume keeps spend trivial. `claude-opus-4-8` is $5/$25 per MTok; `claude-sonnet-4-6` is $3/$15.

### Identity & access

- Open by link: anyone with the room link can read and post. A display name is entered once; a per-room cookie token means a returning visitor posts as themselves. No passwords, no required email.
- The facilitator holds a separate `?key=<facilitator_token>` manage link — the only privileged surface. All manage-gated routes verify the token.

### Kumu export (manual)

A server route emits CSV matching Ben's two-sheet schema:
- **Elements:** a row `Label=<harvest short title>`, `Type=Harvest`.
- **Connections:** `Person → Harvest` (Type `Harvested`) for each participant, and `Harvest → Engagement Node`.

Facilitator downloads and pastes into the Elements / Connections Google Sheets. No live sync.

## UI

The room and manage surfaces are built through the **impeccable** skill in the **product** register (app UI that serves the conversation, not a marketing page). The repo currently has `PRODUCT.md`/`DESIGN.md` shaped for the invitation artifact (a brand-register page); the node-room is a different surface, so impeccable's `teach`/`shape` gates run for it at build time rather than reusing the invitation page's visual system wholesale.

## Ops

- Anthropic tokens are the only meaningful running cost; quiet-by-default facilitation plus small groups keep it low.
- Railway hosts the Next.js service and Postgres in one project. Secrets (`ANTHROPIC_API_KEY`, DB URL) are Railway env vars; the key is never exposed client-side.
- Deploy follows the workspace Railway conventions (see `claude-config/docs/deployments.md`).

## Defaults (tunable during build)

- Poll interval: 5s while tab visible.
- Auto-weave threshold: 4 new human messages since Claude's last post.
- Data layer: plain `pg` + SQL migrations, no ORM.

## Build order (high level — detailed plan to follow)

1. Scaffold Next.js + TypeScript in `node-room/`; Railway project + Postgres; migrations + `lib/db.ts`.
2. Room create + join + post + poll (no Claude yet) — the bare async thread.
3. Claude: opening frame, @claude reply, auto-weave, abuse guard.
4. Harvest draft → edit → finalize.
5. Kumu CSV export.
6. impeccable pass on room + manage UI.
7. Deploy to Railway; smoke-test the full DROP INTO → HARVEST loop with a real node.

## Open questions (carry into the plan)

- Repo org stays personal `zhiganov/hybrid-dialogue` (the node-room as a subfolder). A shared/CIBC org or Ben's org could be revisited if other builder-respondents join.
- Weave cadence (count vs. count-plus-timer) — tune during build.
