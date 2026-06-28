# Field catalogue → node-room integration + live lobby — design

**Date:** 2026-06-28
**Status:** approved design (revised with lobby), ready for implementation plan
**Repo:** `zhiganov/hybrid-dialogue` (`invitation-generator/` + `node-room/`)

## Goal

Make the conversations in the field catalogue (Beat 2) lead into live, shared node-room rooms (Beat 3), and make all the actual conversations discoverable. Today the catalogue lets a reader "Add to my list" (localStorage) and copy that list, picks that lead nowhere. After this work:

1. Each catalogue invitation links into one persistent shared room.
2. node-room's home page becomes a **live lobby** that lists the conversations, so the six we proposed are not the only ones, members can open their own and everyone can find them.

The six generated invitations are explicitly a *starting set* (our analysis of the survey). Group members will have other conversations in mind; the design must let them add their own and have them appear.

## Decisions (settled in brainstorming)

1. **Shared rooms, one per invitation.** Everyone who enters conversation N lands in the same room N.
2. **The catalogue stays static.** The Netlify page is regenerated with room links baked in; it never calls node-room at view time. (This is about the catalogue surface only.)
3. **Reusable generator step.** Room provisioning is a pipeline step driven by the invitations JSON, idempotent across re-runs.
4. **node-room home page becomes a live lobby.** This is a *different* surface from the static catalogue: node-room is already a dynamic, DB-backed app, so a lobby there is natural and does not conflict with decision 2.
5. **Listing model = a `listed` flag.** Rooms carry a `listed` boolean. The lobby shows listed rooms; the convener can unlist junk. This is the control point because `/create` is open to anyone.
6. **Members propose conversations via `/create`** (already built and unauthenticated). The catalogue gets a "Propose another conversation" link to it.

## Architecture — two tracks, one feature

### Track A — node-room (the app): lobby + `listed` flag

- **Migration `002_add_listed.sql`:** `ALTER TABLE rooms ADD COLUMN listed BOOLEAN NOT NULL DEFAULT true;` Additive; existing rooms become listed. Run manually against the Postgres public URL (node-room convention; see deployments.md).
- **`rooms.ts`:**
  - `createRoom` accepts `listed` (default `true`).
  - `listRooms()` returns rooms `WHERE listed = true`, each with title, description, participant count, message count, and last-activity timestamp, ordered by last activity (then `created_at`) descending. Empty listed rooms still appear (a freshly opened conversation is a valid invitation; we do not gate the lobby on message count, to avoid a chicken-and-egg where the curated rooms never show because no one has posted yet).
  - `setRoomListed(roomId, listed)` updates the flag.
- **`POST /api/rooms`** accepts an optional `listed` in the body (default `true`).
- **`PATCH /api/rooms/[id]`** (new, facilitator-gated via `requireFacilitator`): body `{ listed: boolean }` → `setRoomListed`. The convener's kill switch.
- **Home page `/` (`app/page.tsx`)** becomes an async server component: query `listRooms()`, render the list (title, one-line description, participant count, last-activity "x ago", link to the room), keep the "Create a conversation room" link, and show a calm empty state when there are none.
- **Manage page (`ManageClient` + the new PATCH route):** add a "Show in lobby" toggle so the facilitator can list/unlist their room.
- **Privacy note:** the lobby makes `/` a public index of listed conversations. Add `noindex` to node-room pages so the inquiry is not search-indexed (the catalogue already sets `noindex`).

### Track B — generator (catalogue): provisioning + links

- **`invitation-generator/create_rooms.py` (new).** Reads an `invitations-<date>.json`; node-room base URL from `--base` / env `NODE_ROOM_URL` (default the Railway URL). For each invitation, `POST {base}/api/rooms` with `nodeTitle` = title, `nodeDescription` = framing, `facilitationPrompt` = a short general brief (framing + contribution kinds, no named survey quotes), `listed: true`. Writes a mapping `rooms-<date>.json` (keyed by `slug(title)`) holding `room_id`, `facilitator_token`, `room_url`, `manage_url`.
  - **Idempotency:** reuse any slug already in the mapping; create only missing ones; write back. Renaming a conversation yields a new room (old one orphaned, harmless). The local map is the source of truth (node-room has no find-by-title; IDs are random).
  - **Error handling:** per-invitation try/except; failures leave the slug unmapped; a later re-run fills the gap; `render_html` degrades gracefully.
- **`render_html.py` (changed):**
  - New optional `--rooms rooms-<date>.json`; build `slug → room_url`.
  - Per card with a room: a prominent **"Enter the conversation →"** anchor (new tab) plus `data-room="<url>"`. Without a room: render as today (save toggle only).
  - Keep the "Add to my list" toggle; "my list" now means bookmarked rooms. Export (`asMarkdown` / `asMessage`) includes each pick's room URL.
  - Add two global links in the masthead/footer: **"Propose another conversation →"** to `{base}/create`, and **"See all live conversations →"** to `{base}/` (the lobby).

## Data flow & boundaries

```
survey CSV → generate.py → invitations-<date>.json
                              ↓
                      create_rooms.py → node-room POST /api/rooms (listed:true)
                              ↓
                  rooms-<date>.json (private, gitignored)
                              ↓
            render_html.py (JSON + room map) → catalogue HTML (public room links + lobby link)
                              ↓                                    ↑
                         Netlify deploy            node-room lobby (/) lists listed rooms
```

- **Public:** catalogue room URLs (`/room/<id>`); the lobby at `/` listing listed rooms.
- **Private (convener only, gitignored `output/rooms-<date>.json`):** facilitator tokens and `/manage?key=…` links that gate weave/harvest/export/unlist.
- `ANTHROPIC_API_KEY` stays in Railway; opening frames are generated server-side. `create_rooms.py` needs no key.
- Running `create_rooms.py` against production provisions real live rooms; that is the intended act of opening the conversations.

## Testing

- **node-room unit:** `listRooms()` returns only `listed` rooms with correct counts/order; `setRoomListed` flips the flag; `PATCH` is facilitator-gated (rejects without the key). Add to the existing `src/lib` tests where they are CI-gated.
- **node-room manual:** run migration 002 on the public URL; create two rooms (one listed, one not); confirm only the listed one shows on `/`; toggle via the manage page and confirm it appears/disappears.
- **generator unit:** idempotency (existing map → no recreate; new slug → one create, mocked HTTP); render (room present → enter link + `data-room`; absent → fallback; Propose/lobby links always present).
- **end-to-end:** run the full pipeline against live node-room, open the regenerated catalogue, click "Enter", land in the room; open `/` and see it listed; open `/create`, make a room, see it appear in the lobby.

## Out of scope (YAGNI)

- Identity/name handoff from catalogue to room (readers enter their name in node-room as today).
- Rich lobby features: search, filters, categories, per-room activity sparklines. The v1 lobby is a single ordered list.
- Member-room curation workflow beyond the convener's list/unlist toggle (no approval queue).
- Replacing the static catalogue with a node-room-served editorial page; the two surfaces coexist (catalogue = editorial front door, lobby = live index).

## Trade-offs

- Rooms can sit empty until people arrive, and the convener holds one facilitator/manage link per curated room. Inherent to the shared-room model.
- The lobby makes listed conversations publicly visible at the Railway URL (mitigated by `noindex` and the `listed` flag default the convener controls). For a small, privately-shared inquiry this is acceptable.
