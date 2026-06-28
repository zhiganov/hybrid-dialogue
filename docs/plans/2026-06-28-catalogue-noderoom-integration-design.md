# Field catalogue → node-room integration — design

**Date:** 2026-06-28
**Status:** approved design, ready for implementation plan
**Repo:** `zhiganov/hybrid-dialogue` (`invitation-generator/` + `node-room/`)

## Goal

Turn each conversation in the static field catalogue (Beat 2) into a doorway to a live, shared node-room conversation (Beat 3). Today the catalogue lets a reader "Add to my list" (localStorage) and copy that list — picks that lead nowhere. With node-room online, each invitation becomes one persistent shared room: everyone who picks a conversation meets in the same room, and "my list" becomes the set of rooms a reader has joined.

## Decisions (settled in brainstorming)

1. **Shared rooms, one per invitation.** Not ad-hoc per-person rooms. Everyone who enters conversation N lands in the same room N.
2. **Page stays static.** No live room state (no participant counts/activity). The page is regenerated with room links baked in; it never calls node-room at view time.
3. **Reusable generator step.** Room provisioning is a pipeline step driven by the invitations JSON, idempotent across re-runs, usable for any future inquiry, not a one-off for the current six.

## Architecture

One new step between `generate.py` and `render_html.py`:

```
survey CSV → generate.py → invitations-<date>.json
                              ↓
                      create_rooms.py        (NEW)  → node-room POST /api/rooms
                              ↓
                  rooms-<date>.json (private, gitignored)
                              ↓
            render_html.py (JSON + room map) → invitations-<date>.html (public room links)
                              ↓
                         Netlify deploy
```

### Component 1 — `invitation-generator/create_rooms.py` (new)

- **Input:** an `invitations-<date>.json`; the node-room base URL (CLI arg / env `NODE_ROOM_URL`, default `https://node-room-web-production.up.railway.app`).
- **Per invitation**, call `POST {base}/api/rooms` with:
  - `nodeTitle` = `title`
  - `nodeDescription` = `framing`
  - `facilitationPrompt` = a short, **general** facilitator brief built from the framing plus the contribution kinds to invite. It does **not** quote or name individual survey respondents (so Claude's opening frame stays general and does not name people who may not show up).
- **Output mapping** `rooms-<date>.json`:
  ```json
  {
    "base_url": "https://node-room-web-production.up.railway.app",
    "rooms": {
      "<title-slug>": {
        "title": "...",
        "room_id": "...",
        "facilitator_token": "...",
        "room_url": "{base}/room/{id}",
        "manage_url": "{base}/room/{id}/manage?key={token}"
      }
    }
  }
  ```
- **Idempotency:** key by `slug(title)`. On run, load an existing `rooms-<date>.json` if present; reuse any slug already mapped (no new room), create only missing ones, write the map back. Renaming a conversation yields a new slug, hence a new room (the old one is orphaned, harmless). There is no node-room "find room by title" API and IDs are random, so this local map is the source of truth for idempotency. (Chosen over adding a slug/create-or-get system to node-room, which would be scope creep.)
- **Error handling:** per-invitation try/except; on failure, log and continue, leaving that slug unmapped. A later re-run fills the gap. `render_html` degrades gracefully for any unmapped invitation.

### Component 2 — `invitation-generator/render_html.py` (changed)

- New optional input: `--rooms rooms-<date>.json`. Build a `slug → room_url` dict.
- In `render_entries`, when a room URL exists for the invitation:
  - add a prominent **"Enter the conversation →"** anchor (opens the room in a new tab),
  - add `data-room="<url>"` on the `.entry` article.
- Keep the existing "Add to my list" toggle. The "my list" filter and the sticky footer stay, but now mean "rooms I've bookmarked."
- If no room URL for an invitation: render exactly as today (save toggle only, no enter link).

### Component 3 — export JS (changed, inside `render_html.py`)

- `picks()` reads `data-room` per chosen card.
- `asMarkdown` / `asMessage` include the room URL per pick, e.g. `1. <title> — <room url>`, so the copied artifact is a list of live links, not bare titles.

## Data flow & boundaries

- **Public (page + git):** room URLs only (`/room/<id>`).
- **Private (convener only, gitignored):** `rooms-<date>.json` holds the facilitator tokens and `/manage?key=…` links that gate harvest + export. It lives in `output/` (already gitignored alongside PII-bearing artifacts). The convener (Ben/Artem) holds these to run each room's harvest.
- `ANTHROPIC_API_KEY` stays in Railway; the opening frame is generated server-side by node-room. `create_rooms.py` needs no key (POST `/api/rooms` is unauthenticated by design).
- Running `create_rooms.py` against the production base URL **provisions real live rooms**. That is the intended effect; it is the act of opening the conversations.

## Testing

- **Unit (idempotency):** given a pre-populated `rooms-<date>.json`, the create call is not made for mapped slugs; an unmapped slug triggers exactly one create. Mock the HTTP call.
- **Unit (render):** an invitation with a room URL renders the enter link + `data-room`; one without renders the current fallback.
- **Manual end-to-end:** run the full pipeline against live node-room, open the regenerated page, click a generated link, confirm it lands in the room and a name can be entered.

## Out of scope (YAGNI)

- Live room state on the page (counts, activity, "who's inside").
- Identity/name handoff from page to room — readers enter their name in node-room as today.
- Rebuilding the catalogue as a node-room-served dynamic "lobby" (a possible future direction; not built).
- A slug / create-or-get API in node-room (idempotency stays in the local map).

## Inherent trade-off

Rooms sit empty until people arrive, and the convener holds one facilitator/manage link per room (six for the current cohort). This is inherent to the shared-room model and accepted.
