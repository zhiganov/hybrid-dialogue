# Catalogue → node-room integration + lobby — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make each catalogue invitation lead into a shared node-room room, and turn node-room's home page into a live lobby of listed conversations.

**Architecture:** Two tracks in `zhiganov/hybrid-dialogue`. Track A changes the node-room Next.js app (a `listed` flag, a lobby home page, a facilitator unlist switch). Track B adds a Python generator step that provisions one room per invitation and bakes the links into the static catalogue. Track A ships first because Track B relies on the `listed` create param and links to the lobby.

**Tech Stack:** Next.js 15 (App Router, server components), React 19, TypeScript, `pg`, Vitest (node-room); Python 3 stdlib (generator). node-room deploys to Railway, auto-deploys on push to `main`. Catalogue deploys to Netlify.

**Design spec:** `docs/plans/2026-06-28-catalogue-noderoom-integration-design.md`

## Global Constraints

- node-room migrations are **manual**: `DATABASE_URL=<Postgres public URL> npm run migrate` from `node-room/`. Get the Postgres `DATABASE_PUBLIC_URL` from Railway at run time (Postgres service variables). **Never commit the connection string or any API key.**
- `ANTHROPIC_API_KEY` stays in Railway env only. `create_rooms.py` needs no key.
- Facilitator tokens are secret: they live only in `output/rooms-<date>.json` (gitignored). Only `room_url` (the `/room/<id>` form) is public.
- The generator adds **no new pip dependencies** (stdlib only).
- node-room verification gate for every Track A task: `npx tsc --noEmit` passes and `npm run build` succeeds, run from `node-room/`.
- Run all node-room commands from `node-room/`; all generator commands from `invitation-generator/`.

---

## Track A — node-room app

### Task A1: Add the `listed` column (migration)

**Files:**
- Create: `node-room/migrations/002_add_listed.sql`

**Interfaces:**
- Produces: a `rooms.listed BOOLEAN NOT NULL DEFAULT true` column that later tasks read/write.

- [ ] **Step 1: Write the migration**

```sql
-- node-room/migrations/002_add_listed.sql
ALTER TABLE rooms ADD COLUMN listed BOOLEAN NOT NULL DEFAULT true;
```

- [ ] **Step 2: Run it against production Postgres**

Fetch the Postgres `DATABASE_PUBLIC_URL` from Railway (Postgres service → variables), then from `node-room/`:

Run: `DATABASE_URL="<public url>" npm run migrate`
Expected: prints `skip 001_init.sql` then `applied 002_add_listed.sql`

- [ ] **Step 3: Commit**

```bash
git add node-room/migrations/002_add_listed.sql
git commit -m "feat(node-room): add listed column to rooms"
```

---

### Task A2: `rooms.ts` — listed support, `listRooms`, `setRoomListed`

**Files:**
- Modify: `node-room/src/lib/rooms.ts`
- Test: `node-room/src/lib/rooms.itest.ts`

**Interfaces:**
- Consumes: existing `query`, `Room`, `RoomRow`, `toRoom`, `createRoom`.
- Produces:
  - `Room.listed: boolean`
  - `createRoom(input: { nodeTitle; nodeDescription; facilitationPrompt; listed?: boolean }): Promise<Room>` (defaults `listed` to `true`)
  - `type LobbyRoom = { id; nodeTitle; nodeDescription; participantCount: number; messageCount: number; lastActivityAt: string | null; createdAt: string }`
  - `listRooms(): Promise<LobbyRoom[]>`
  - `setRoomListed(roomId: string, listed: boolean): Promise<void>`

- [ ] **Step 1: Add `listed` to the `Room` type and row mapping**

In `rooms.ts`, add `listed: boolean;` to the `Room` type and to `RoomRow`, and add `listed: r.listed,` to `toRoom`:

```ts
export type Room = {
  id: string;
  nodeTitle: string;
  nodeDescription: string;
  facilitationPrompt: string;
  facilitatorToken: string;
  listed: boolean;
  createdAt: string;
};
```
```ts
type RoomRow = {
  id: string;
  node_title: string;
  node_description: string;
  facilitation_prompt: string;
  facilitator_token: string;
  listed: boolean;
  created_at: string;
};
const toRoom = (r: RoomRow): Room => ({
  id: r.id,
  nodeTitle: r.node_title,
  nodeDescription: r.node_description,
  facilitationPrompt: r.facilitation_prompt,
  facilitatorToken: r.facilitator_token,
  listed: r.listed,
  createdAt: r.created_at,
});
```

- [ ] **Step 2: Accept `listed` in `createRoom`**

Replace the `createRoom` function body with:

```ts
export async function createRoom(input: {
  nodeTitle: string;
  nodeDescription: string;
  facilitationPrompt: string;
  listed?: boolean;
}): Promise<Room> {
  const id = generateToken();
  const facilitatorToken = generateToken();
  const rows = await query<RoomRow>(
    `INSERT INTO rooms (id, node_title, node_description, facilitation_prompt, facilitator_token, listed)
     VALUES ($1,$2,$3,$4,$5,$6) RETURNING *`,
    [id, input.nodeTitle, input.nodeDescription, input.facilitationPrompt, facilitatorToken, input.listed ?? true]
  );
  return toRoom(rows[0]);
}
```

- [ ] **Step 3: Add `listRooms` and `setRoomListed`**

Append to `rooms.ts`:

```ts
export type LobbyRoom = {
  id: string;
  nodeTitle: string;
  nodeDescription: string;
  participantCount: number;
  messageCount: number;
  lastActivityAt: string | null;
  createdAt: string;
};

export async function listRooms(): Promise<LobbyRoom[]> {
  const rows = await query<{
    id: string;
    node_title: string;
    node_description: string;
    created_at: string;
    participant_count: number;
    message_count: number;
    last_activity_at: string | null;
  }>(
    `SELECT r.id, r.node_title, r.node_description, r.created_at,
       COALESCE(p.cnt, 0)::int AS participant_count,
       COALESCE(m.cnt, 0)::int AS message_count,
       m.last_at AS last_activity_at
     FROM rooms r
     LEFT JOIN (SELECT room_id, count(*) AS cnt FROM participants GROUP BY room_id) p
       ON p.room_id = r.id
     LEFT JOIN (SELECT room_id, count(*) AS cnt, max(created_at) AS last_at FROM messages GROUP BY room_id) m
       ON m.room_id = r.id
     WHERE r.listed = true
     ORDER BY COALESCE(m.last_at, r.created_at) DESC`
  );
  return rows.map((r) => ({
    id: r.id,
    nodeTitle: r.node_title,
    nodeDescription: r.node_description,
    participantCount: r.participant_count,
    messageCount: r.message_count,
    lastActivityAt: r.last_activity_at,
    createdAt: r.created_at,
  }));
}

export async function setRoomListed(roomId: string, listed: boolean): Promise<void> {
  await query("UPDATE rooms SET listed = $2 WHERE id = $1", [roomId, listed]);
}
```

- [ ] **Step 4: Add an integration test**

Append to `rooms.itest.ts` (it runs only when `TEST_DATABASE_URL` is set, like the existing cases). Match the file's existing import/setup style:

```ts
test("listRooms returns only listed rooms, newest activity first; setRoomListed hides one", async () => {
  const shown = await rooms.createRoom({ nodeTitle: "Shown", nodeDescription: "d", facilitationPrompt: "" });
  const hidden = await rooms.createRoom({ nodeTitle: "Hidden", nodeDescription: "d", facilitationPrompt: "", listed: false });
  let lobby = await rooms.listRooms();
  const ids = lobby.map((r) => r.id);
  expect(ids).toContain(shown.id);
  expect(ids).not.toContain(hidden.id);
  await rooms.setRoomListed(shown.id, false);
  lobby = await rooms.listRooms();
  expect(lobby.map((r) => r.id)).not.toContain(shown.id);
});
```

- [ ] **Step 5: Run the integration test (needs a test DB)**

Run (from `node-room/`, with a scratch Postgres): `TEST_DATABASE_URL="<scratch db url>" npx vitest run src/lib/rooms.itest.ts`
Expected: PASS. If no scratch DB is available, skip and rely on the manual lobby check in Task A4.

- [ ] **Step 6: Typecheck, then commit**

Run: `npx tsc --noEmit`  Expected: exit 0
```bash
git add node-room/src/lib/rooms.ts node-room/src/lib/rooms.itest.ts
git commit -m "feat(node-room): listRooms, setRoomListed, listed on createRoom"
```

---

### Task A3: API — `listed` on create, `PATCH` to toggle

**Files:**
- Modify: `node-room/src/app/api/rooms/route.ts`
- Create: `node-room/src/app/api/rooms/[id]/route.ts`

**Interfaces:**
- Consumes: `createRoom` (with `listed`), `setRoomListed`, `requireFacilitator`.
- Produces: `PATCH /api/rooms/[id]` body `{ listed: boolean }`, facilitator-gated.

- [ ] **Step 1: Accept `listed` in POST /api/rooms**

In `api/rooms/route.ts`, change the destructure and the `createRoom` call:

```ts
  const { nodeTitle, nodeDescription, facilitationPrompt, listed } = body ?? {};
  if (!nodeTitle || !nodeDescription) {
    return Response.json({ error: "nodeTitle and nodeDescription are required" }, { status: 400 });
  }
  const room = await createRoom({
    nodeTitle,
    nodeDescription,
    facilitationPrompt: facilitationPrompt ?? "",
    listed: typeof listed === "boolean" ? listed : true,
  });
```

- [ ] **Step 2: Create the PATCH route**

```ts
// node-room/src/app/api/rooms/[id]/route.ts
import type { NextRequest } from "next/server";
import { requireFacilitator } from "@/lib/facilitator";
import { setRoomListed } from "@/lib/rooms";

export async function PATCH(req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const gate = await requireFacilitator(req, id);
  if ("error" in gate) return gate.error;
  const { listed } = (await req.json()) ?? {};
  if (typeof listed !== "boolean") {
    return Response.json({ error: "listed (boolean) is required" }, { status: 400 });
  }
  await setRoomListed(id, listed);
  return Response.json({ ok: true, listed });
}
```

- [ ] **Step 3: Typecheck + build, then commit**

Run: `npx tsc --noEmit && npm run build`  Expected: both succeed
```bash
git add node-room/src/app/api/rooms/route.ts "node-room/src/app/api/rooms/[id]/route.ts"
git commit -m "feat(node-room): listed on create + PATCH /api/rooms/[id]"
```

---

### Task A4: Lobby home page

**Files:**
- Modify: `node-room/src/app/page.tsx`

**Interfaces:**
- Consumes: `listRooms` from `@/lib/rooms`.

- [ ] **Step 1: Replace the home page with a lobby**

```tsx
// node-room/src/app/page.tsx
import Link from "next/link";
import { listRooms } from "@/lib/rooms";

export const dynamic = "force-dynamic";

function timeAgo(iso: string | null): string {
  if (!iso) return "no posts yet";
  const secs = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 1000));
  if (secs < 45) return "just now";
  const mins = Math.round(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.round(hrs / 24)}d ago`;
}

export default async function Home() {
  const rooms = await listRooms();
  return (
    <main className="page">
      <header className="page-head">
        <h1 className="title">Hybrid Dialogue</h1>
        <p className="lede">
          A small group and Claude think together in writing, over days. Enter a
          conversation below, or start one of your own.
        </p>
      </header>

      {rooms.length === 0 ? (
        <p className="empty">No conversations yet. You could open the first one.</p>
      ) : (
        <ol className="thread" aria-label="Open conversations">
          {rooms.map((r) => (
            <li className="entry" key={r.id}>
              <p className="entry-meta">
                <span>
                  {r.participantCount} {r.participantCount === 1 ? "person" : "people"}
                </span>
                <span className="entry-dot" aria-hidden="true">
                  &middot;
                </span>
                <span>{timeAgo(r.lastActivityAt)}</span>
              </p>
              <h2 className="section-title">
                <Link className="link" href={`/room/${r.id}`}>
                  {r.nodeTitle}
                </Link>
              </h2>
              <p className="entry-body">{r.nodeDescription}</p>
            </li>
          ))}
        </ol>
      )}

      <p>
        <Link className="link" href="/create">
          Start a conversation room
        </Link>
      </p>
    </main>
  );
}
```

- [ ] **Step 2: Build, then commit**

Run: `npm run build`  Expected: succeeds; `/` is now dynamic (ƒ) rather than static.
```bash
git add node-room/src/app/page.tsx
git commit -m "feat(node-room): home page lists listed rooms (lobby)"
```

- [ ] **Step 3: Manual check after deploy**

After the push auto-deploys: create two rooms via `/create` (leave one listed, one with the lobby box unchecked once Task A5 lands; until then both list). Confirm the listed room appears on `/` with participant count + time, and the room title links into it.

---

### Task A5: Facilitator "Show in lobby" toggle

**Files:**
- Modify: `node-room/src/app/room/[id]/manage/page.tsx`
- Modify: `node-room/src/app/room/[id]/manage/ManageClient.tsx`

**Interfaces:**
- Consumes: `PATCH /api/rooms/[id]`, `Room.listed`.

- [ ] **Step 1: Pass `listed` into the client**

In `manage/page.tsx`, change the render line:

```tsx
  return <ManageClient roomId={room.id} nodeTitle={room.nodeTitle} listed={room.listed} />;
```

- [ ] **Step 2: Add the toggle to `ManageClient`**

Add `listed: boolean` to the props type. Add state and a handler near the other handlers:

```tsx
  const [listed, setListed] = useState(props.listed);

  async function toggleListed() {
    setBusy("listed");
    setError(null);
    const next = !listed;
    try {
      const res = await fetch(`/api/rooms/${roomId}?key=${key}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ listed: next }),
      });
      if (!res.ok) {
        setError("Could not update lobby visibility. Please try again.");
        return;
      }
      setListed(next);
    } catch {
      setError("Could not update lobby visibility. Please try again.");
    } finally {
      setBusy(null);
    }
  }
```

Add a panel as the first `<section className="panel">` after the header block:

```tsx
      <section className="panel">
        <h2 className="section-title">Lobby</h2>
        <p className="field-hint">
          {listed
            ? "Listed on the home page so people can find and join this conversation."
            : "Hidden from the home page. Only people with the link can join."}
        </p>
        <div className="btn-row">
          <button className="btn btn--quiet" onClick={toggleListed} disabled={busy !== null}>
            {busy === "listed" ? "Updating" : listed ? "Hide from lobby" : "Show in lobby"}
          </button>
        </div>
      </section>
```

- [ ] **Step 3: Typecheck + build, then commit**

Run: `npx tsc --noEmit && npm run build`  Expected: both succeed
```bash
git add "node-room/src/app/room/[id]/manage/page.tsx" "node-room/src/app/room/[id]/manage/ManageClient.tsx"
git commit -m "feat(node-room): facilitator show/hide in lobby toggle"
```

- [ ] **Step 4: Manual check after deploy**

Open a room's `/manage?key=…`, click "Hide from lobby", confirm it disappears from `/`; click "Show in lobby", confirm it returns.

---

### Task A6: noindex node-room pages

**Files:**
- Modify: `node-room/src/app/layout.tsx`

- [ ] **Step 1: Add robots noindex to the metadata**

Read `layout.tsx` first. If it already exports `metadata`, merge in `robots`; otherwise add the export:

```ts
export const metadata = {
  title: "Hybrid Dialogue",
  robots: { index: false, follow: false },
};
```

- [ ] **Step 2: Build, then commit**

Run: `npm run build`  Expected: succeeds
```bash
git add node-room/src/app/layout.tsx
git commit -m "chore(node-room): noindex the inquiry pages"
```

---

## Track B — generator

### Task B1: `create_rooms.py` — provision rooms idempotently

**Files:**
- Create: `invitation-generator/create_rooms.py`
- Create: `invitation-generator/test_create_rooms.py`

**Interfaces:**
- Produces: `output/rooms-<date>.json` mapping `slug(title) → { title, room_id, facilitator_token, room_url, manage_url }`, and a `provision(invs, base, mapping, create_fn)` function used by the test.

- [ ] **Step 1: Write the script**

```python
#!/usr/bin/env python3
"""Provision one node-room room per invitation, idempotently.

Reads an invitations-*.json, creates a node-room room per invitation via
POST {base}/api/rooms, and writes a private mapping rooms-<date>.json keyed
by slug(title). Re-runs reuse existing rooms (no duplicates). The mapping
holds facilitator tokens and is gitignored; only room_url is public.

Usage:
  python create_rooms.py --input output/invitations-2026-06-27.json \
      --base https://node-room-web-production.up.railway.app
"""
import argparse
import glob
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).parent


def slug(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return s[:60] or "conversation"


def facilitation_brief(inv: dict) -> str:
    framing = inv.get("framing", "").strip()
    return (
        f"This is an asynchronous small-group conversation. {framing}\n\n"
        "Help the group surface questions, stories, challenges, and syntheses, "
        "and draw the threads toward a harvestable shared understanding. Stay "
        "quiet unless asked or unless a weave will genuinely help."
    )


def create_room(base: str, inv: dict) -> dict:
    payload = json.dumps(
        {
            "nodeTitle": inv.get("title", ""),
            "nodeDescription": inv.get("framing", ""),
            "facilitationPrompt": facilitation_brief(inv),
            "listed": True,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{base.rstrip('/')}/api/rooms",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def provision(invs, base, mapping, create_fn):
    base = base.rstrip("/")
    mapping["base_url"] = base
    mapping.setdefault("rooms", {})
    for inv in invs:
        title = inv.get("title", "")
        key = slug(title)
        if key in mapping["rooms"]:
            print(f"skip (exists): {title}")
            continue
        try:
            res = create_fn(base, inv)
        except Exception as ex:  # noqa: BLE001 - log and continue per design
            print(f"FAILED: {title} ({ex})", file=sys.stderr)
            continue
        rid, tok = res["id"], res["facilitatorToken"]
        mapping["rooms"][key] = {
            "title": title,
            "room_id": rid,
            "facilitator_token": tok,
            "room_url": f"{base}/room/{rid}",
            "manage_url": f"{base}/room/{rid}/manage?key={tok}",
        }
        print(f"created: {title} -> {base}/room/{rid}")
    return mapping


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", help="invitations-*.json (defaults to newest in ./output)")
    ap.add_argument("--base", default="https://node-room-web-production.up.railway.app")
    ap.add_argument("--out", default=str(HERE / "output"))
    args = ap.parse_args()

    inp = args.input
    if not inp:
        cands = sorted(glob.glob(str(HERE / "output" / "invitations-*.json")))
        if not cands:
            raise SystemExit("No invitations-*.json found; pass --input")
        inp = cands[-1]

    data = json.loads(pathlib.Path(inp).read_text(encoding="utf-8"))
    invs = data.get("invitations", [])
    m = re.search(r"(\d{4}-\d{2}-\d{2})", pathlib.Path(inp).name)
    date_str = m.group(1) if m else "rooms"

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    mapping_path = out / f"rooms-{date_str}.json"
    mapping = {"base_url": args.base, "rooms": {}}
    if mapping_path.exists():
        mapping = json.loads(mapping_path.read_text(encoding="utf-8"))

    provision(invs, args.base, mapping, create_room)
    mapping_path.write_text(json.dumps(mapping, indent=2), encoding="utf-8")
    print(f"Wrote {mapping_path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Write the idempotency test**

```python
# invitation-generator/test_create_rooms.py
import unittest
from create_rooms import provision, slug


class TestProvision(unittest.TestCase):
    def test_creates_then_reuses(self):
        invs = [{"title": "Trust, said plainly", "framing": "x"}, {"title": "The timezone problem", "framing": "y"}]
        calls = []

        def fake(base, inv):
            calls.append(inv["title"])
            return {"id": "id-" + slug(inv["title"]), "facilitatorToken": "tok"}

        mapping = provision(invs, "http://x", {"rooms": {}}, fake)
        self.assertEqual(calls, ["Trust, said plainly", "The timezone problem"])
        self.assertEqual(set(mapping["rooms"]), {slug(i["title"]) for i in invs})
        self.assertTrue(mapping["rooms"][slug("Trust, said plainly")]["room_url"].endswith("/room/id-trust-said-plainly"))

        calls.clear()
        again = provision(invs, "http://x", mapping, fake)
        self.assertEqual(calls, [])  # nothing recreated
        self.assertEqual(set(again["rooms"]), {slug(i["title"]) for i in invs})


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the test**

Run (from `invitation-generator/`): `python -m unittest test_create_rooms -v`
Expected: PASS (`test_creates_then_reuses`)

- [ ] **Step 4: Gitignore the rooms map, then commit**

Confirm `output/` is already gitignored at the repo root (it is). If a narrower ignore is needed, add `invitation-generator/output/rooms-*.json`. Then:
```bash
git add invitation-generator/create_rooms.py invitation-generator/test_create_rooms.py
git commit -m "feat(generator): create_rooms.py provisions node-room rooms idempotently"
```

- [ ] **Step 5: Provision the real rooms (manual, side-effecting)**

Run (from `invitation-generator/`): `python create_rooms.py --input output/invitations-2026-06-27.json`
Expected: `created: …` lines for each invitation, and `Wrote output/rooms-2026-06-27.json`. These are live rooms; verify a couple appear in the lobby at the node-room URL. Keep `rooms-2026-06-27.json` local (it holds facilitator tokens).

---

### Task B2: `render_html.py` — enter links, propose/lobby links, export URLs

**Files:**
- Modify: `invitation-generator/render_html.py`

**Interfaces:**
- Consumes: `output/rooms-<date>.json` (optional, via `--rooms`).

- [ ] **Step 1: Thread a room map + base through `build` and `render_entries`**

Change `render_entries(invs)` to `render_entries(invs, room_urls)` where `room_urls` is `{title: room_url}`. Inside the loop, after computing `meta`, add:

```python
        room_url = room_urls.get(inv.get("title", ""))
        enter = (
            f'<a class="enter" href="{e(room_url)}" target="_blank" rel="noopener">Enter the conversation &rarr;</a>'
            if room_url else ""
        )
        data_room = f' data-room="{e(room_url)}"' if room_url else ""
```

Change the article open tag to include `data_room`, and add the `enter` anchor into the `.gutter` after the join button:

```python
        out.append(f"""
      <article class="entry" data-type="{t}" id="c{i}" style="--k:{meta['color']}"{data_room}>
        <div class="gutter">
          <span class="acc">{i:02d}</span>
          <span class="tag"><span class="swatch"></span>{meta['label']}</span>
          <button class="join" aria-pressed="false"><span class="jl">Add to my list</span></button>
          {enter}
        </div>
```

- [ ] **Step 2: Add the CSS for `.enter`**

Append to the `CSS` string (near `.join`):

```css
.enter{font:inherit; font-size:.8rem; font-weight:700; text-decoration:none; color:var(--paper);
  background:var(--ink); border:1px solid var(--ink); border-radius:2px; padding:.4rem .6rem; text-align:center}
.enter:hover{opacity:.85}
```

- [ ] **Step 3: Add the global "propose" + "lobby" links**

In `build()`, accept `base` and add links in the masthead under the `lede`. Add the two anchors after the `<p class="lede">…</p>` line in the masthead block (only when `base` is set):

```python
    live_links = (
        f'<p class="livelinks">'
        f'<a class="link" href="{e(base)}/" target="_blank" rel="noopener">See all live conversations &rarr;</a>'
        f' &nbsp;&middot;&nbsp; '
        f'<a class="link" href="{e(base)}/create" target="_blank" rel="noopener">Propose another conversation &rarr;</a>'
        f'</p>'
    ) if base else ""
```

Insert `+ live_links +` into the returned HTML right after the `lede` paragraph, and add CSS:

```css
.livelinks{margin:.2rem 0 0; font-size:.92rem}
.link{color:var(--ink); font-weight:700}
```

- [ ] **Step 4: Update the export JS to carry room URLs**

In the `JS` string, change `picks()` and the formatters:

```js
  function picks(){
    return cards.filter(function(c){return c.dataset.chosen;}).map(function(c){
      return { title:c.querySelector('.title').textContent.trim(), type:c.dataset.type, room:c.dataset.room||'' };
    });
  }
  function asMarkdown(p){
    var s='# My conversations — Hybrid Dialogue\n\n';
    p.forEach(function(it){ s+='- **'+it.title+'**'+(it.room?'  '+it.room:'')+'\n'; });
    return s;
  }
  function asMessage(p){
    var s="I'd like to join "+p.length+" of the conversations:\n";
    p.forEach(function(it,i){ s+=(i+1)+'. '+it.title+(it.room?' — '+it.room:'')+'\n'; });
    return s.trim();
  }
```

- [ ] **Step 5: Wire `--rooms` in `main()` and pass `room_urls` + `base`**

In `main()`, add the arg and load the map:

```python
    ap.add_argument("--rooms", help="rooms-*.json from create_rooms.py (optional)")
```
```python
    room_urls, base = {}, ""
    if args.rooms:
        rm = json.loads(pathlib.Path(args.rooms).read_text(encoding="utf-8"))
        base = rm.get("base_url", "")
        room_urls = {v["title"]: v["room_url"] for v in rm.get("rooms", {}).values()}
```
Change the `build(...)` call to `build(data, args.model, date_str, room_urls, base)` and update `build`'s signature to `def build(data, model, date_str, room_urls=None, base=""):` with `room_urls = room_urls or {}` and pass `room_urls` into `render_entries(invs, room_urls)`.

- [ ] **Step 6: Render smoke (no rooms, then with rooms)**

Run (from `invitation-generator/`):
`python render_html.py --input output/invitations-2026-06-27.json`
Expected: still writes the HTML, no enter links (graceful fallback).

Then with the map:
`python render_html.py --input output/invitations-2026-06-27.json --rooms output/rooms-2026-06-27.json`
Verify the output contains the new markup:
`grep -c 'class="enter"' output/invitations-2026-06-27.html` (expect 6)
`grep -c 'See all live conversations' output/invitations-2026-06-27.html` (expect 1)
`grep -c 'data-room=' output/invitations-2026-06-27.html` (expect 6)

- [ ] **Step 7: Commit**

```bash
git add invitation-generator/render_html.py
git commit -m "feat(generator): enter links, lobby/propose links, room URLs in export"
```

- [ ] **Step 8: Deploy the catalogue**

Rebuild the deployable folder (the single `index.html`) and deploy to Netlify per `claude-config/docs/deployments.md` (site `d214e36e-…`, `--no-build`). Confirm clicking "Enter the conversation" lands in a live room and "See all live conversations" opens the lobby.

---

## Self-Review

**Spec coverage:**
- Shared room per invitation → B1 (create_rooms) + B2 (enter links). ✓
- Static catalogue, links baked in → B2. ✓
- Reusable, idempotent generator step → B1 (`provision` + mapping reuse) + test. ✓
- node-room home becomes a lobby → A4. ✓
- `listed` flag (migration, create param, list query, toggle) → A1, A2, A3, A5. ✓
- Lobby shows listed rooms incl. empty, ordered by activity → A2 (`listRooms` uses `COALESCE(last_at, created_at)`, no message-count filter). ✓
- PATCH kill switch, facilitator-gated → A3. ✓
- "Propose another conversation" + lobby link on catalogue → B2 step 3. ✓
- Private facilitator tokens, public room URLs only → B1 (mapping gitignored; render uses only `room_url`). ✓
- noindex → A6. ✓

**Placeholder scan:** No TBD/TODO; every code step shows real code; secrets are referenced as run-time fetches, never literals. ✓

**Type consistency:** `Room.listed`, `createRoom({…listed?})`, `LobbyRoom`, `listRooms()`, `setRoomListed()` are defined in A2 and consumed unchanged in A3/A4/A5; `provision`/`slug`/`create_room` names match between B1 script and B1 test; `room_urls` keyed by title matches B1's stored `title` field and B2's `inv.title` lookup. ✓
