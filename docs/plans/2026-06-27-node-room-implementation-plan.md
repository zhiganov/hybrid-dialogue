# Node Room Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the async, link-shared Beat 3 "node room" — a small group plus Claude (quiet facilitator) converse over hours/days, producing a Kumu-ready harvest.

**Architecture:** Next.js (App Router, TypeScript) on Railway with a Railway Postgres database. Participant view at `/room/[id]`, facilitator view at `/room/[id]/manage`. The browser polls a fetch-since endpoint (~5s) for new messages; there is no realtime. The Anthropic SDK is called only from server route handlers, so the API key stays server-side.

**Tech Stack:** Next.js 15 (App Router) · React 19 · TypeScript · `pg` (node-postgres) · `@anthropic-ai/sdk` · `nanoid` · Tailwind CSS · Vitest. Deployed on Railway (web service + Postgres in one project).

## Global Constraints

These apply to every task. Exact values are copied from the spec (`docs/plans/2026-06-27-node-room-design.md`).

- **Async only.** No realtime channels, no presence/"who's here", no typing indicators. New messages arrive by client polling (default 5s while the tab is visible).
- **Anthropic key is server-side only.** Read `process.env.ANTHROPIC_API_KEY` exclusively inside route handlers / `lib/` modules that run on the server. Never expose it to client components.
- **Models:** `@claude` mention reply → `claude-sonnet-4-6` (snappy). Auto-weave and harvest → `claude-opus-4-8` with `thinking: { type: "adaptive" }`. Do NOT pass `budget_tokens`, `temperature`, `top_p`, or `top_k` to Opus 4.8 (all return 400). Use the exact model ID strings; do not append date suffixes.
- **Streaming for long calls.** Weave and harvest use `client.messages.stream(...)` + `await stream.finalMessage()` to avoid HTTP timeouts. The mention reply may use non-streaming `client.messages.create(...)` with `max_tokens: 1024`.
- **Contribution tags enum:** exactly `question | story | challenge | synthesis` (nullable on a message).
- **Auto-weave threshold:** 4 new human messages since Claude's last post (tunable constant). **Poll interval:** 5s (tunable constant).
- **Per-room Claude cooldown:** reject a Claude-triggering action if the room produced a Claude message within the last 20 seconds (guards `@claude` spam).
- **Facilitator gating:** every manage-only route verifies a `facilitator_token` (passed as `?key=` or an `x-facilitator-token` header) against the room row before acting.
- **Copy rule:** no em dashes in any user-facing string (use commas, colons, periods, or parentheses). Also not `--`.
- **"Amplifier, not replacement" stance** is encoded in the Claude system prompts: encourage human-to-human exchange, synthesize rather than opine, surface connections between people, stay quiet unless it adds value.
- **Repo:** code lives in the `node-room/` subfolder of the public `zhiganov/hybrid-dialogue` repo. Real participant data and generated output stay gitignored.
- **UI visual design comes from the impeccable skill (Task 8), not hand-rolled.** UI tasks (6, 7) build behavior + structure; defer palette/type/spacing to Task 8.

---

## File Structure

```
node-room/
  package.json
  tsconfig.json
  next.config.ts
  vitest.config.ts
  postcss.config.mjs
  tailwind.config.ts
  .env.example
  .gitignore
  README.md
  migrations/
    001_init.sql
  scripts/
    migrate.ts                 # applies migrations/*.sql, tracks in _migrations
    smoke-claude.ts            # real-LLM smoke for lib/claude.ts
  src/
    lib/
      domain.ts                # pure logic (tokens, mention, tags, weave, kumu csv)
      domain.test.ts
      db.ts                    # pg Pool singleton + query helper
      rooms.ts                 # data-access functions
      rooms.itest.ts           # integration test (gated on TEST_DATABASE_URL)
      claude.ts                # Anthropic calls + system prompts
    app/
      room/[id]/page.tsx       # participant view (server component shell)
      room/[id]/RoomClient.tsx # participant client component (thread + composer + poll)
      room/[id]/manage/page.tsx        # facilitator view shell
      room/[id]/manage/ManageClient.tsx
      api/rooms/route.ts                       # POST create
      api/rooms/[id]/join/route.ts             # POST join
      api/rooms/[id]/messages/route.ts         # GET poll, POST message
      api/rooms/[id]/weave/route.ts            # POST weave (manage)
      api/rooms/[id]/harvest/route.ts          # POST draft, PUT save (manage)
      api/rooms/[id]/export/route.ts           # GET csv (manage)
```

Each `lib/` file has one responsibility: `domain.ts` is pure (no IO, fully unit-tested), `db.ts` owns the pool, `rooms.ts` owns SQL, `claude.ts` owns Anthropic. Route handlers are thin: parse → call `lib` → respond.

---

### Task 1: Scaffold the Next.js app

**Files:**
- Create: `node-room/package.json`, `node-room/tsconfig.json`, `node-room/next.config.ts`, `node-room/vitest.config.ts`, `node-room/postcss.config.mjs`, `node-room/tailwind.config.ts`, `node-room/.gitignore`, `node-room/.env.example`, `node-room/src/app/layout.tsx`, `node-room/src/app/globals.css`, `node-room/src/app/page.tsx`
- Test: `node-room/src/lib/smoke.test.ts`

**Interfaces:**
- Produces: a runnable Next.js app (`npm run dev`), a passing `npm test` (Vitest), and `npm run migrate` / `npm run smoke:claude` script entries (scripts authored in later tasks).

- [ ] **Step 1: Create `package.json`**

```json
{
  "name": "node-room",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "test": "vitest run",
    "migrate": "tsx scripts/migrate.ts",
    "smoke:claude": "tsx scripts/smoke-claude.ts"
  },
  "dependencies": {
    "@anthropic-ai/sdk": "^0.69.0",
    "nanoid": "^5.0.0",
    "next": "^15.1.0",
    "pg": "^8.13.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "devDependencies": {
    "@types/node": "^22.0.0",
    "@types/pg": "^8.11.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.4.0",
    "tsx": "^4.19.0",
    "typescript": "^5.7.0",
    "vitest": "^2.1.0"
  }
}
```

- [ ] **Step 2: Create config files**

`tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "ES2022"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./src/*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

`next.config.ts`:
```typescript
import type { NextConfig } from "next";
const nextConfig: NextConfig = {};
export default nextConfig;
```

`vitest.config.ts`:
```typescript
import { defineConfig } from "vitest/config";
export default defineConfig({
  test: { environment: "node", include: ["src/**/*.test.ts"] },
});
```

`postcss.config.mjs`:
```javascript
export default { plugins: { tailwindcss: {}, autoprefixer: {} } };
```

`tailwind.config.ts`:
```typescript
import type { Config } from "tailwindcss";
export default {
  content: ["./src/**/*.{ts,tsx}"],
  theme: { extend: {} },
  plugins: [],
} satisfies Config;
```

- [ ] **Step 3: Create `.gitignore` and `.env.example`**

`.gitignore`:
```
node_modules/
.next/
.env
.env.local
*.tsbuildinfo
next-env.d.ts
```

`.env.example`:
```
DATABASE_URL=postgres://user:pass@host:5432/dbname
ANTHROPIC_API_KEY=sk-ant-...
# Optional, only for the gated integration test:
TEST_DATABASE_URL=postgres://user:pass@host:5432/test_dbname
```

- [ ] **Step 4: Create the app shell**

`src/app/globals.css`:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

`src/app/layout.tsx`:
```tsx
import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Hybrid Dialogue",
  description: "A shared conversation room with Claude as a quiet facilitator.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
```

`src/app/page.tsx`:
```tsx
export default function Home() {
  return (
    <main style={{ padding: 24 }}>
      <h1>Hybrid Dialogue node room</h1>
      <p>Open a room link to join a conversation.</p>
    </main>
  );
}
```

- [ ] **Step 5: Write a smoke test to prove Vitest runs**

`src/lib/smoke.test.ts`:
```typescript
import { expect, test } from "vitest";

test("vitest runs", () => {
  expect(1 + 1).toBe(2);
});
```

- [ ] **Step 6: Install and verify**

Run: `cd node-room && npm install && npm test`
Expected: Vitest reports `1 passed`.

Run: `npm run build`
Expected: Next build completes with no type errors (an empty app builds clean).

- [ ] **Step 7: Commit**

```bash
git -C node-room add -A
git -C ../.. add node-room
git commit -m "feat(node-room): scaffold Next.js + TS + Tailwind + Vitest"
```

---

### Task 2: Pure domain logic

**Files:**
- Create: `node-room/src/lib/domain.ts`
- Test: `node-room/src/lib/domain.test.ts`

**Interfaces:**
- Produces:
  - `CONTRIBUTION_TAGS: readonly ["question","story","challenge","synthesis"]`
  - `type ContributionTag = (typeof CONTRIBUTION_TAGS)[number]`
  - `isValidTag(value: unknown): value is ContributionTag`
  - `generateToken(): string` — 21-char url-safe id
  - `mentionsClaude(body: string): boolean` — true if the message contains `@claude` (case-insensitive, word-boundary)
  - `WEAVE_THRESHOLD = 4`, `POLL_INTERVAL_MS = 5000`, `CLAUDE_COOLDOWN_MS = 20000`
  - `shouldWeave(humanMessagesSinceLastClaude: number): boolean`
  - `type KumuRow = Record<string, string>`
  - `buildKumuCsv(input: KumuExportInput): { elements: string; connections: string }`
  - `type KumuExportInput = { harvestTitle: string; nodeTitle: string; participants: string[] }`

- [ ] **Step 1: Write the failing test**

`src/lib/domain.test.ts`:
```typescript
import { describe, expect, test } from "vitest";
import {
  CONTRIBUTION_TAGS,
  isValidTag,
  generateToken,
  mentionsClaude,
  shouldWeave,
  WEAVE_THRESHOLD,
  buildKumuCsv,
} from "./domain";

describe("tags", () => {
  test("valid tags pass", () => {
    for (const t of CONTRIBUTION_TAGS) expect(isValidTag(t)).toBe(true);
  });
  test("invalid tags fail", () => {
    expect(isValidTag("idea")).toBe(false);
    expect(isValidTag(null)).toBe(false);
    expect(isValidTag(undefined)).toBe(false);
  });
});

describe("generateToken", () => {
  test("is 21 url-safe chars and unique", () => {
    const a = generateToken();
    const b = generateToken();
    expect(a).toMatch(/^[A-Za-z0-9_-]{21}$/);
    expect(a).not.toBe(b);
  });
});

describe("mentionsClaude", () => {
  test("detects @claude case-insensitively", () => {
    expect(mentionsClaude("hey @claude what do you think?")).toBe(true);
    expect(mentionsClaude("@Claude")).toBe(true);
    expect(mentionsClaude("ask @CLAUDE here")).toBe(true);
  });
  test("ignores when absent or embedded", () => {
    expect(mentionsClaude("no mention here")).toBe(false);
    expect(mentionsClaude("email claude@example.com")).toBe(false);
  });
});

describe("shouldWeave", () => {
  test("weaves at threshold, not before", () => {
    expect(shouldWeave(WEAVE_THRESHOLD - 1)).toBe(false);
    expect(shouldWeave(WEAVE_THRESHOLD)).toBe(true);
    expect(shouldWeave(WEAVE_THRESHOLD + 1)).toBe(true);
  });
});

describe("buildKumuCsv", () => {
  const out = buildKumuCsv({
    harvestTitle: "Trust, said plainly",
    nodeTitle: "What does trust require?",
    participants: ["Ana", "Rijon"],
  });
  test("elements has the harvest row typed Harvest", () => {
    expect(out.elements).toContain("Label,Type");
    expect(out.elements).toContain('"Trust, said plainly",Harvest');
  });
  test("connections links each person to the harvest and the harvest to the node", () => {
    expect(out.connections).toContain("From,To,Type");
    expect(out.connections).toContain('Ana,"Trust, said plainly",Harvested');
    expect(out.connections).toContain('Rijon,"Trust, said plainly",Harvested');
    expect(out.connections).toContain(
      '"Trust, said plainly","What does trust require?",Harvested'
    );
  });
});
```

- [ ] **Step 2: Run the test to confirm it fails**

Run: `cd node-room && npx vitest run src/lib/domain.test.ts`
Expected: FAIL with "Cannot find module './domain'".

- [ ] **Step 3: Implement `domain.ts`**

```typescript
import { nanoid } from "nanoid";

export const CONTRIBUTION_TAGS = [
  "question",
  "story",
  "challenge",
  "synthesis",
] as const;
export type ContributionTag = (typeof CONTRIBUTION_TAGS)[number];

export function isValidTag(value: unknown): value is ContributionTag {
  return (
    typeof value === "string" &&
    (CONTRIBUTION_TAGS as readonly string[]).includes(value)
  );
}

export function generateToken(): string {
  return nanoid(); // 21 url-safe chars by default
}

const MENTION_RE = /(^|[^A-Za-z0-9_@])@claude\b/i;
export function mentionsClaude(body: string): boolean {
  return MENTION_RE.test(body);
}

export const WEAVE_THRESHOLD = 4;
export const POLL_INTERVAL_MS = 5000;
export const CLAUDE_COOLDOWN_MS = 20000;

export function shouldWeave(humanMessagesSinceLastClaude: number): boolean {
  return humanMessagesSinceLastClaude >= WEAVE_THRESHOLD;
}

export type KumuExportInput = {
  harvestTitle: string;
  nodeTitle: string;
  participants: string[];
};

function csvCell(value: string): string {
  // Quote when the cell contains a comma, quote, or newline; double inner quotes.
  if (/[",\n]/.test(value)) return `"${value.replace(/"/g, '""')}"`;
  return value;
}

function csvRow(cells: string[]): string {
  return cells.map(csvCell).join(",");
}

export function buildKumuCsv(input: KumuExportInput): {
  elements: string;
  connections: string;
} {
  const elements = [
    csvRow(["Label", "Type"]),
    csvRow([input.harvestTitle, "Harvest"]),
  ].join("\n");

  const connectionRows = [csvRow(["From", "To", "Type"])];
  for (const person of input.participants) {
    connectionRows.push(csvRow([person, input.harvestTitle, "Harvested"]));
  }
  connectionRows.push(
    csvRow([input.harvestTitle, input.nodeTitle, "Harvested"])
  );
  const connections = connectionRows.join("\n");

  return { elements, connections };
}
```

- [ ] **Step 4: Run the test to confirm it passes**

Run: `cd node-room && npx vitest run src/lib/domain.test.ts`
Expected: PASS (all assertions green).

- [ ] **Step 5: Commit**

```bash
git -C ../.. add node-room/src/lib/domain.ts node-room/src/lib/domain.test.ts
git commit -m "feat(node-room): pure domain logic (tags, mention, weave, kumu csv)"
```

---

### Task 3: Database layer (schema, pool, data access)

**Files:**
- Create: `node-room/migrations/001_init.sql`, `node-room/scripts/migrate.ts`, `node-room/src/lib/db.ts`, `node-room/src/lib/rooms.ts`
- Test: `node-room/src/lib/rooms.itest.ts` (named `.itest.ts` so the default `*.test.ts` Vitest glob skips it; run explicitly when `TEST_DATABASE_URL` is set)

**Interfaces:**
- Consumes: `generateToken`, `ContributionTag` from `domain.ts`.
- Produces (all in `rooms.ts`):
  - `type AuthorType = "human" | "claude" | "system"`
  - `type Room = { id: string; nodeTitle: string; nodeDescription: string; facilitationPrompt: string; facilitatorToken: string; createdAt: string }`
  - `type Participant = { id: string; roomId: string; displayName: string; token: string; joinedAt: string }`
  - `type Message = { id: number; roomId: string; authorType: AuthorType; participantId: string | null; authorName: string | null; body: string; contributionTag: ContributionTag | null; createdAt: string }`
  - `type Harvest = { id: number; roomId: string; body: string; finalizedAt: string | null }`
  - `createRoom(input: { nodeTitle: string; nodeDescription: string; facilitationPrompt: string }): Promise<Room>`
  - `getRoom(id: string): Promise<Room | null>`
  - `addParticipant(roomId: string, displayName: string): Promise<Participant>`
  - `getParticipantByToken(roomId: string, token: string): Promise<Participant | null>`
  - `addMessage(input: { roomId: string; authorType: AuthorType; participantId: string | null; body: string; contributionTag: ContributionTag | null }): Promise<Message>`
  - `getMessages(roomId: string, sinceId: number): Promise<Message[]>` — ordered by `id` ascending, `id > sinceId`
  - `getAllMessages(roomId: string): Promise<Message[]>`
  - `humanMessagesSinceLastClaude(roomId: string): Promise<number>`
  - `lastClaudeMessageAt(roomId: string): Promise<string | null>`
  - `saveHarvestDraft(roomId: string, body: string): Promise<Harvest>` (upsert)
  - `finalizeHarvest(roomId: string, body: string): Promise<Harvest>`
  - `getHarvest(roomId: string): Promise<Harvest | null>`

- [ ] **Step 1: Write the schema**

`migrations/001_init.sql`:
```sql
CREATE TABLE IF NOT EXISTS rooms (
  id                  TEXT PRIMARY KEY,
  node_title          TEXT NOT NULL,
  node_description    TEXT NOT NULL,
  facilitation_prompt TEXT NOT NULL,
  facilitator_token   TEXT NOT NULL,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS participants (
  id           TEXT PRIMARY KEY,
  room_id      TEXT NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
  display_name TEXT NOT NULL,
  token        TEXT NOT NULL,
  joined_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS participants_room_idx ON participants(room_id);

CREATE TABLE IF NOT EXISTS messages (
  id              BIGSERIAL PRIMARY KEY,
  room_id         TEXT NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
  author_type     TEXT NOT NULL CHECK (author_type IN ('human','claude','system')),
  participant_id  TEXT REFERENCES participants(id) ON DELETE SET NULL,
  body            TEXT NOT NULL,
  contribution_tag TEXT CHECK (contribution_tag IN ('question','story','challenge','synthesis')),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS messages_room_id_idx ON messages(room_id, id);

CREATE TABLE IF NOT EXISTS harvests (
  id           BIGSERIAL PRIMARY KEY,
  room_id      TEXT NOT NULL UNIQUE REFERENCES rooms(id) ON DELETE CASCADE,
  body         TEXT NOT NULL,
  finalized_at TIMESTAMPTZ
);
```

- [ ] **Step 2: Write the migrate runner**

`scripts/migrate.ts`:
```typescript
import { readFileSync, readdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { Pool } from "pg";

const here = dirname(fileURLToPath(import.meta.url));
const migrationsDir = join(here, "..", "migrations");

async function main() {
  const url = process.env.DATABASE_URL;
  if (!url) throw new Error("DATABASE_URL is not set");
  const pool = new Pool({ connectionString: url });
  await pool.query(
    `CREATE TABLE IF NOT EXISTS _migrations (name TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())`
  );
  const files = readdirSync(migrationsDir).filter((f) => f.endsWith(".sql")).sort();
  for (const file of files) {
    const done = await pool.query("SELECT 1 FROM _migrations WHERE name = $1", [file]);
    if (done.rowCount) {
      console.log(`skip ${file}`);
      continue;
    }
    const sql = readFileSync(join(migrationsDir, file), "utf8");
    await pool.query("BEGIN");
    try {
      await pool.query(sql);
      await pool.query("INSERT INTO _migrations(name) VALUES ($1)", [file]);
      await pool.query("COMMIT");
      console.log(`applied ${file}`);
    } catch (e) {
      await pool.query("ROLLBACK");
      throw e;
    }
  }
  await pool.end();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
```

- [ ] **Step 3: Write the pool helper**

`src/lib/db.ts`:
```typescript
import { Pool, type QueryResultRow } from "pg";

let pool: Pool | null = null;

function getPool(): Pool {
  if (!pool) {
    const connectionString = process.env.DATABASE_URL;
    if (!connectionString) throw new Error("DATABASE_URL is not set");
    pool = new Pool({ connectionString });
  }
  return pool;
}

export async function query<T extends QueryResultRow>(
  text: string,
  params: unknown[] = []
): Promise<T[]> {
  const result = await getPool().query<T>(text, params);
  return result.rows;
}
```

- [ ] **Step 4: Write the data-access functions**

`src/lib/rooms.ts`:
```typescript
import { query } from "./db";
import { generateToken, type ContributionTag } from "./domain";

export type AuthorType = "human" | "claude" | "system";

export type Room = {
  id: string;
  nodeTitle: string;
  nodeDescription: string;
  facilitationPrompt: string;
  facilitatorToken: string;
  createdAt: string;
};
export type Participant = {
  id: string;
  roomId: string;
  displayName: string;
  token: string;
  joinedAt: string;
};
export type Message = {
  id: number;
  roomId: string;
  authorType: AuthorType;
  participantId: string | null;
  authorName: string | null;
  body: string;
  contributionTag: ContributionTag | null;
  createdAt: string;
};
export type Harvest = {
  id: number;
  roomId: string;
  body: string;
  finalizedAt: string | null;
};

type RoomRow = {
  id: string;
  node_title: string;
  node_description: string;
  facilitation_prompt: string;
  facilitator_token: string;
  created_at: string;
};
const toRoom = (r: RoomRow): Room => ({
  id: r.id,
  nodeTitle: r.node_title,
  nodeDescription: r.node_description,
  facilitationPrompt: r.facilitation_prompt,
  facilitatorToken: r.facilitator_token,
  createdAt: r.created_at,
});

export async function createRoom(input: {
  nodeTitle: string;
  nodeDescription: string;
  facilitationPrompt: string;
}): Promise<Room> {
  const id = generateToken();
  const facilitatorToken = generateToken();
  const rows = await query<RoomRow>(
    `INSERT INTO rooms (id, node_title, node_description, facilitation_prompt, facilitator_token)
     VALUES ($1,$2,$3,$4,$5) RETURNING *`,
    [id, input.nodeTitle, input.nodeDescription, input.facilitationPrompt, facilitatorToken]
  );
  return toRoom(rows[0]);
}

export async function getRoom(id: string): Promise<Room | null> {
  const rows = await query<RoomRow>("SELECT * FROM rooms WHERE id = $1", [id]);
  return rows[0] ? toRoom(rows[0]) : null;
}

type ParticipantRow = {
  id: string;
  room_id: string;
  display_name: string;
  token: string;
  joined_at: string;
};
const toParticipant = (r: ParticipantRow): Participant => ({
  id: r.id,
  roomId: r.room_id,
  displayName: r.display_name,
  token: r.token,
  joinedAt: r.joined_at,
});

export async function addParticipant(
  roomId: string,
  displayName: string
): Promise<Participant> {
  const id = generateToken();
  const token = generateToken();
  const rows = await query<ParticipantRow>(
    `INSERT INTO participants (id, room_id, display_name, token)
     VALUES ($1,$2,$3,$4) RETURNING *`,
    [id, roomId, displayName, token]
  );
  return toParticipant(rows[0]);
}

export async function getParticipantByToken(
  roomId: string,
  token: string
): Promise<Participant | null> {
  const rows = await query<ParticipantRow>(
    "SELECT * FROM participants WHERE room_id = $1 AND token = $2",
    [roomId, token]
  );
  return rows[0] ? toParticipant(rows[0]) : null;
}

type MessageRow = {
  id: string;
  room_id: string;
  author_type: AuthorType;
  participant_id: string | null;
  author_name: string | null;
  body: string;
  contribution_tag: ContributionTag | null;
  created_at: string;
};
const toMessage = (r: MessageRow): Message => ({
  id: Number(r.id),
  roomId: r.room_id,
  authorType: r.author_type,
  participantId: r.participant_id,
  authorName: r.author_name,
  body: r.body,
  contributionTag: r.contribution_tag,
  createdAt: r.created_at,
});

const MESSAGE_SELECT = `
  SELECT m.id, m.room_id, m.author_type, m.participant_id,
         p.display_name AS author_name, m.body, m.contribution_tag, m.created_at
  FROM messages m
  LEFT JOIN participants p ON p.id = m.participant_id
`;

export async function addMessage(input: {
  roomId: string;
  authorType: AuthorType;
  participantId: string | null;
  body: string;
  contributionTag: ContributionTag | null;
}): Promise<Message> {
  const inserted = await query<{ id: string }>(
    `INSERT INTO messages (room_id, author_type, participant_id, body, contribution_tag)
     VALUES ($1,$2,$3,$4,$5) RETURNING id`,
    [input.roomId, input.authorType, input.participantId, input.body, input.contributionTag]
  );
  const rows = await query<MessageRow>(`${MESSAGE_SELECT} WHERE m.id = $1`, [inserted[0].id]);
  return toMessage(rows[0]);
}

export async function getMessages(roomId: string, sinceId: number): Promise<Message[]> {
  const rows = await query<MessageRow>(
    `${MESSAGE_SELECT} WHERE m.room_id = $1 AND m.id > $2 ORDER BY m.id ASC`,
    [roomId, sinceId]
  );
  return rows.map(toMessage);
}

export async function getAllMessages(roomId: string): Promise<Message[]> {
  return getMessages(roomId, 0);
}

export async function humanMessagesSinceLastClaude(roomId: string): Promise<number> {
  const rows = await query<{ count: string }>(
    `SELECT count(*)::text AS count FROM messages
     WHERE room_id = $1 AND author_type = 'human'
       AND id > COALESCE(
         (SELECT max(id) FROM messages WHERE room_id = $1 AND author_type = 'claude'), 0)`,
    [roomId]
  );
  return Number(rows[0].count);
}

export async function lastClaudeMessageAt(roomId: string): Promise<string | null> {
  const rows = await query<{ created_at: string }>(
    `SELECT created_at FROM messages
     WHERE room_id = $1 AND author_type = 'claude'
     ORDER BY id DESC LIMIT 1`,
    [roomId]
  );
  return rows[0]?.created_at ?? null;
}

type HarvestRow = { id: string; room_id: string; body: string; finalized_at: string | null };
const toHarvest = (r: HarvestRow): Harvest => ({
  id: Number(r.id),
  roomId: r.room_id,
  body: r.body,
  finalizedAt: r.finalized_at,
});

export async function saveHarvestDraft(roomId: string, body: string): Promise<Harvest> {
  const rows = await query<HarvestRow>(
    `INSERT INTO harvests (room_id, body) VALUES ($1,$2)
     ON CONFLICT (room_id) DO UPDATE SET body = EXCLUDED.body
     RETURNING *`,
    [roomId, body]
  );
  return toHarvest(rows[0]);
}

export async function finalizeHarvest(roomId: string, body: string): Promise<Harvest> {
  const rows = await query<HarvestRow>(
    `INSERT INTO harvests (room_id, body, finalized_at) VALUES ($1,$2, now())
     ON CONFLICT (room_id) DO UPDATE SET body = EXCLUDED.body, finalized_at = now()
     RETURNING *`,
    [roomId, body]
  );
  return toHarvest(rows[0]);
}

export async function getHarvest(roomId: string): Promise<Harvest | null> {
  const rows = await query<HarvestRow>("SELECT * FROM harvests WHERE room_id = $1", [roomId]);
  return rows[0] ? toHarvest(rows[0]) : null;
}
```

- [ ] **Step 5: Write the gated integration test**

`src/lib/rooms.itest.ts` (run manually; skips itself if `TEST_DATABASE_URL` is unset):
```typescript
import { afterAll, beforeAll, describe, expect, test } from "vitest";

const url = process.env.TEST_DATABASE_URL;
const d = url ? describe : describe.skip;

d("rooms data access (integration)", () => {
  beforeAll(() => {
    process.env.DATABASE_URL = url;
  });
  afterAll(async () => {
    const { query } = await import("./db");
    // Clean only rows created by this run is overkill for a scratch DB; truncate.
    await query("TRUNCATE rooms, participants, messages, harvests RESTART IDENTITY CASCADE");
  });

  test("create room, join, post, poll, weave-count, harvest", async () => {
    const rooms = await import("./rooms");
    const room = await rooms.createRoom({
      nodeTitle: "What does trust require?",
      nodeDescription: "A conversation about trust.",
      facilitationPrompt: "Keep it grounded in stories.",
    });
    expect(room.facilitatorToken).toMatch(/^[A-Za-z0-9_-]{21}$/);

    const ana = await rooms.addParticipant(room.id, "Ana");
    const found = await rooms.getParticipantByToken(room.id, ana.token);
    expect(found?.displayName).toBe("Ana");

    const m1 = await rooms.addMessage({
      roomId: room.id,
      authorType: "human",
      participantId: ana.token ? ana.id : null,
      body: "What strikes me is how rare it is.",
      contributionTag: "story",
    });
    expect(m1.authorName).toBe("Ana");
    expect(m1.contributionTag).toBe("story");

    const since = await rooms.getMessages(room.id, 0);
    expect(since.length).toBe(1);
    const after = await rooms.getMessages(room.id, m1.id);
    expect(after.length).toBe(0);

    expect(await rooms.humanMessagesSinceLastClaude(room.id)).toBe(1);
    await rooms.addMessage({
      roomId: room.id,
      authorType: "claude",
      participantId: null,
      body: "A weave.",
      contributionTag: null,
    });
    expect(await rooms.humanMessagesSinceLastClaude(room.id)).toBe(0);

    const draft = await rooms.saveHarvestDraft(room.id, "Draft harvest.");
    expect(draft.finalizedAt).toBeNull();
    const fin = await rooms.finalizeHarvest(room.id, "Final harvest.");
    expect(fin.finalizedAt).not.toBeNull();
    expect((await rooms.getHarvest(room.id))?.body).toBe("Final harvest.");
  });
});
```

- [ ] **Step 6: Verify**

If you have a Postgres available, run:
```bash
cd node-room
DATABASE_URL=$TEST_DATABASE_URL npm run migrate
npx vitest run src/lib/rooms.itest.ts
```
Expected: `migrate` prints `applied 001_init.sql`; the integration test passes.

If no Postgres is available locally, run `npx vitest run` (the `.itest.ts` is outside the default glob and the unit suite stays green); the integration test is exercised against Railway Postgres in Task 9.

- [ ] **Step 7: Commit**

```bash
git -C ../.. add node-room/migrations node-room/scripts/migrate.ts node-room/src/lib/db.ts node-room/src/lib/rooms.ts node-room/src/lib/rooms.itest.ts
git commit -m "feat(node-room): postgres schema, pool, data access + migrate runner"
```

---

### Task 4: Claude integration

**Files:**
- Create: `node-room/src/lib/claude.ts`, `node-room/scripts/smoke-claude.ts`

**Interfaces:**
- Consumes: `Message`, `Room` from `rooms.ts`.
- Produces (in `claude.ts`):
  - `openingFrame(room: Room): Promise<string>`
  - `replyToMention(room: Room, recent: Message[]): Promise<string>`
  - `weave(room: Room, recent: Message[]): Promise<string>`
  - `harvestDraft(room: Room, all: Message[]): Promise<string>`

- [ ] **Step 1: Implement `claude.ts`**

```typescript
import Anthropic from "@anthropic-ai/sdk";
import type { Message, Room } from "./rooms";

const STANCE = `You are a quiet facilitator in a small, asynchronous group conversation.
People drop in over hours or days, so they often will not be present at the same time.
Your role is to amplify human-to-human dialogue, not to replace it:
- Encourage people to respond to each other, not to you.
- Synthesize and connect rather than opine or lecture.
- Surface connections between what different people have said, especially across visits.
- Stay brief. Speak only when it adds something a participant could not easily add themselves.
- Never use em dashes. Use commas, colons, periods, or parentheses instead.`;

function client(): Anthropic {
  if (!process.env.ANTHROPIC_API_KEY) throw new Error("ANTHROPIC_API_KEY is not set");
  return new Anthropic();
}

function frame(room: Room): string {
  return `The conversation node is titled: "${room.nodeTitle}".
Description: ${room.nodeDescription}
Facilitation guidance for you: ${room.facilitationPrompt}`;
}

function transcript(messages: Message[]): string {
  return messages
    .map((m) => {
      const who = m.authorType === "claude" ? "Facilitator" : m.authorName ?? "Someone";
      const tag = m.contributionTag ? ` [${m.contributionTag}]` : "";
      return `${who}${tag}: ${m.body}`;
    })
    .join("\n");
}

// Short, snappy reply when a participant writes @claude.
export async function replyToMention(room: Room, recent: Message[]): Promise<string> {
  const res = await client().messages.create({
    model: "claude-sonnet-4-6",
    max_tokens: 1024,
    system: STANCE,
    messages: [
      {
        role: "user",
        content: `${frame(room)}

Recent messages:
${transcript(recent)}

A participant addressed you with @claude. Respond briefly and helpfully, then hand the thread back to the group. Do not summarize the whole conversation; answer what was asked.`,
      },
    ],
  });
  return textOf(res);
}

// Periodic weave: one synthesis / connection / opening question.
export async function weave(room: Room, recent: Message[]): Promise<string> {
  const stream = client().messages.stream({
    model: "claude-opus-4-8",
    max_tokens: 1024,
    thinking: { type: "adaptive" },
    system: STANCE,
    messages: [
      {
        role: "user",
        content: `${frame(room)}

Recent contributions:
${transcript(recent)}

Post ONE short weave. Pick the single most useful move right now: name a connection between two people's contributions, offer a brief synthesis of an emerging thread, or ask one opening question. Two or three sentences. Address the group, not any one person, and invite them to keep talking to each other.`,
      },
    ],
  });
  return textOf(await stream.finalMessage());
}

// Opening frame posted when the room is created.
export async function openingFrame(room: Room): Promise<string> {
  const stream = client().messages.stream({
    model: "claude-opus-4-8",
    max_tokens: 1024,
    thinking: { type: "adaptive" },
    system: STANCE,
    messages: [
      {
        role: "user",
        content: `${frame(room)}

Write a short opening frame (three or four sentences) that welcomes people into this conversation and invites a first contribution. Warm, plain, and specific to the node. Do not list rules.`,
      },
    ],
  });
  return textOf(await stream.finalMessage());
}

// Harvest: distill the whole conversation into an editable draft.
export async function harvestDraft(room: Room, all: Message[]): Promise<string> {
  const stream = client().messages.stream({
    model: "claude-opus-4-8",
    max_tokens: 4096,
    thinking: { type: "adaptive" },
    system: STANCE,
    messages: [
      {
        role: "user",
        content: `${frame(room)}

Full conversation:
${transcript(all)}

Distill this into a harvest a human will edit and carry forward. Include:
1. A short title (one line).
2. The two or three threads that mattered most, each in a sentence or two, grounded in what people actually said.
3. Any open question worth carrying into the next conversation.
Keep it tight and faithful. This is a draft for a human to refine, not a transcript.`,
      },
    ],
  });
  return textOf(await stream.finalMessage());
}

function textOf(message: Anthropic.Message): string {
  return message.content
    .filter((b): b is Anthropic.TextBlock => b.type === "text")
    .map((b) => b.text)
    .join("")
    .trim();
}
```

- [ ] **Step 2: Write the real-LLM smoke script**

Per the workspace rule "real-LLM smoke for prompt edits," this proves the prompts elicit the intended shape from the actual model.

`scripts/smoke-claude.ts`:
```typescript
import { openingFrame, replyToMention, weave, harvestDraft } from "../src/lib/claude";
import type { Message, Room } from "../src/lib/rooms";

const room: Room = {
  id: "demo",
  nodeTitle: "What does trust actually require of us?",
  nodeDescription:
    "Several people said trust matters but meant different things by it.",
  facilitationPrompt: "Keep it grounded in concrete stories, not abstractions.",
  facilitatorToken: "x",
  createdAt: new Date().toISOString(),
};

const msg = (
  authorName: string | null,
  authorType: Message["authorType"],
  body: string,
  contributionTag: Message["contributionTag"] = null
): Message => ({
  id: 0,
  roomId: "demo",
  authorType,
  participantId: null,
  authorName,
  body,
  contributionTag,
  createdAt: new Date().toISOString(),
});

async function main() {
  const recent: Message[] = [
    msg("Ana", "human", "For me trust is letting someone see a draft before it is good.", "story"),
    msg("Rijon", "human", "Does that still hold when the stakes are high, not just a draft?", "question"),
    msg("Lee", "human", "I distrust people who never show me anything unfinished.", "challenge"),
    msg("Ana", "human", "So maybe trust is built by exchanging unfinished things?", "synthesis"),
  ];

  console.log("\n=== OPENING FRAME ===\n", await openingFrame(room));
  console.log("\n=== WEAVE ===\n", await weave(room, recent));
  console.log(
    "\n=== MENTION REPLY ===\n",
    await replyToMention(room, [...recent, msg("Lee", "human", "@claude what connects these?")])
  );
  console.log("\n=== HARVEST DRAFT ===\n", await harvestDraft(room, recent));
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
```

- [ ] **Step 3: Run the smoke and read the output**

Run:
```bash
cd node-room
set -a; source ~/claude-project/.env.anthropic; set +a
npm run smoke:claude
```
Expected: four sections print. Verify by eye: the weave is two to three sentences and connects people (not a lecture), the mention reply is brief and answers the question, the harvest has a title plus a few grounded threads, and no output contains an em dash. If a section is off-shape, tune the prompt in `claude.ts` and re-run (do not move on until the real model follows the rules).

- [ ] **Step 4: Commit**

```bash
git -C ../.. add node-room/src/lib/claude.ts node-room/scripts/smoke-claude.ts
git commit -m "feat(node-room): Claude facilitation (opening, mention reply, weave, harvest) + real-LLM smoke"
```

---

### Task 5: API routes

**Files:**
- Create: `node-room/src/app/api/rooms/route.ts`, `node-room/src/app/api/rooms/[id]/join/route.ts`, `node-room/src/app/api/rooms/[id]/messages/route.ts`, `node-room/src/app/api/rooms/[id]/weave/route.ts`, `node-room/src/app/api/rooms/[id]/harvest/route.ts`, `node-room/src/app/api/rooms/[id]/export/route.ts`
- Create (shared helper): `node-room/src/lib/facilitator.ts`

**Interfaces:**
- Consumes: everything from `rooms.ts`, `claude.ts`, and `domain.ts`.
- Produces (HTTP contract):
  - `POST /api/rooms` body `{ nodeTitle, nodeDescription, facilitationPrompt }` → `{ id, facilitatorToken }`. Side effect: posts the opening frame as a `claude` message.
  - `POST /api/rooms/[id]/join` body `{ displayName }` → `{ participantToken, displayName }`.
  - `GET /api/rooms/[id]/messages?since=<id>` → `{ messages: Message[] }`.
  - `POST /api/rooms/[id]/messages` body `{ participantToken, body, tag? }` → `{ message }`. Side effect: if cooldown clear, fires a mention reply (when `@claude`) or an auto-weave (when `shouldWeave`).
  - `POST /api/rooms/[id]/weave?key=<facilitatorToken>` → `{ message }` (manage-gated; bypasses the message-count threshold but still respects cooldown).
  - `POST /api/rooms/[id]/harvest?key=<facilitatorToken>` → `{ harvest }` (generates a draft).
  - `PUT /api/rooms/[id]/harvest?key=<facilitatorToken>` body `{ body, finalize? }` → `{ harvest }`.
  - `GET /api/rooms/[id]/export?key=<facilitatorToken>` → `text/csv` attachment (elements + connections concatenated with a header separator).

- [ ] **Step 1: Write the facilitator-gate helper**

`src/lib/facilitator.ts`:
```typescript
import type { NextRequest } from "next/server";
import { getRoom, type Room } from "./rooms";

export async function requireFacilitator(
  req: NextRequest,
  roomId: string
): Promise<{ room: Room } | { error: Response }> {
  const key =
    req.nextUrl.searchParams.get("key") ?? req.headers.get("x-facilitator-token") ?? "";
  const room = await getRoom(roomId);
  if (!room) return { error: Response.json({ error: "not found" }, { status: 404 }) };
  if (!key || key !== room.facilitatorToken) {
    return { error: Response.json({ error: "forbidden" }, { status: 403 }) };
  }
  return { room };
}
```

- [ ] **Step 2: Create-room route (with opening frame)**

`src/app/api/rooms/route.ts`:
```typescript
import type { NextRequest } from "next/server";
import { addMessage, createRoom } from "@/lib/rooms";
import { openingFrame } from "@/lib/claude";

export async function POST(req: NextRequest) {
  const body = await req.json();
  const { nodeTitle, nodeDescription, facilitationPrompt } = body ?? {};
  if (!nodeTitle || !nodeDescription) {
    return Response.json({ error: "nodeTitle and nodeDescription are required" }, { status: 400 });
  }
  const room = await createRoom({
    nodeTitle,
    nodeDescription,
    facilitationPrompt: facilitationPrompt ?? "",
  });
  try {
    const frame = await openingFrame(room);
    await addMessage({
      roomId: room.id,
      authorType: "claude",
      participantId: null,
      body: frame,
      contributionTag: null,
    });
  } catch (e) {
    // The room is usable even if the opening frame fails; log and continue.
    console.error("opening frame failed", e);
  }
  return Response.json({ id: room.id, facilitatorToken: room.facilitatorToken });
}
```

- [ ] **Step 3: Join route**

`src/app/api/rooms/[id]/join/route.ts`:
```typescript
import type { NextRequest } from "next/server";
import { addParticipant, getRoom } from "@/lib/rooms";

export async function POST(req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const { displayName } = (await req.json()) ?? {};
  if (!displayName || typeof displayName !== "string" || !displayName.trim()) {
    return Response.json({ error: "displayName is required" }, { status: 400 });
  }
  const room = await getRoom(id);
  if (!room) return Response.json({ error: "not found" }, { status: 404 });
  const participant = await addParticipant(id, displayName.trim().slice(0, 80));
  return Response.json({ participantToken: participant.token, displayName: participant.displayName });
}
```

- [ ] **Step 4: Messages route (poll + post + Claude triggers)**

`src/app/api/rooms/[id]/messages/route.ts`:
```typescript
import type { NextRequest } from "next/server";
import {
  addMessage,
  getMessages,
  getParticipantByToken,
  getRoom,
  humanMessagesSinceLastClaude,
  lastClaudeMessageAt,
} from "@/lib/rooms";
import { replyToMention, weave } from "@/lib/claude";
import { CLAUDE_COOLDOWN_MS, isValidTag, mentionsClaude, shouldWeave } from "@/lib/domain";

export async function GET(req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const since = Number(req.nextUrl.searchParams.get("since") ?? "0") || 0;
  const messages = await getMessages(id, since);
  return Response.json({ messages });
}

async function claudeCooldownClear(roomId: string): Promise<boolean> {
  const last = await lastClaudeMessageAt(roomId);
  if (!last) return true;
  return Date.now() - new Date(last).getTime() > CLAUDE_COOLDOWN_MS;
}

export async function POST(req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const { participantToken, body, tag } = (await req.json()) ?? {};
  if (!body || typeof body !== "string" || !body.trim()) {
    return Response.json({ error: "body is required" }, { status: 400 });
  }
  const room = await getRoom(id);
  if (!room) return Response.json({ error: "not found" }, { status: 404 });
  const participant = await getParticipantByToken(id, participantToken ?? "");
  if (!participant) return Response.json({ error: "join first" }, { status: 403 });

  const contributionTag = isValidTag(tag) ? tag : null;
  const message = await addMessage({
    roomId: id,
    authorType: "human",
    participantId: participant.id,
    body: body.trim(),
    contributionTag,
  });

  // Fire-and-forget Claude reaction so the POST returns immediately;
  // the new claude message appears on the next poll.
  void (async () => {
    try {
      if (!(await claudeCooldownClear(id))) return;
      const recent = (await getMessages(id, 0)).slice(-12);
      if (mentionsClaude(message.body)) {
        const reply = await replyToMention(room, recent);
        await addMessage({ roomId: id, authorType: "claude", participantId: null, body: reply, contributionTag: null });
        return;
      }
      const sinceClaude = await humanMessagesSinceLastClaude(id);
      if (shouldWeave(sinceClaude)) {
        const w = await weave(room, recent);
        await addMessage({ roomId: id, authorType: "claude", participantId: null, body: w, contributionTag: null });
      }
    } catch (e) {
      console.error("claude reaction failed", e);
    }
  })();

  return Response.json({ message });
}
```

- [ ] **Step 5: Weave route (manage)**

`src/app/api/rooms/[id]/weave/route.ts`:
```typescript
import type { NextRequest } from "next/server";
import { addMessage, getMessages } from "@/lib/rooms";
import { requireFacilitator } from "@/lib/facilitator";
import { weave } from "@/lib/claude";

export async function POST(req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const gate = await requireFacilitator(req, id);
  if ("error" in gate) return gate.error;
  const recent = (await getMessages(id, 0)).slice(-12);
  const body = await weave(gate.room, recent);
  const message = await addMessage({ roomId: id, authorType: "claude", participantId: null, body, contributionTag: null });
  return Response.json({ message });
}
```

- [ ] **Step 6: Harvest route (manage)**

`src/app/api/rooms/[id]/harvest/route.ts`:
```typescript
import type { NextRequest } from "next/server";
import { finalizeHarvest, getAllMessages, getHarvest, saveHarvestDraft } from "@/lib/rooms";
import { requireFacilitator } from "@/lib/facilitator";
import { harvestDraft } from "@/lib/claude";

export async function POST(req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const gate = await requireFacilitator(req, id);
  if ("error" in gate) return gate.error;
  const all = await getAllMessages(id);
  const draft = await harvestDraft(gate.room, all);
  const harvest = await saveHarvestDraft(id, draft);
  return Response.json({ harvest });
}

export async function PUT(req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const gate = await requireFacilitator(req, id);
  if ("error" in gate) return gate.error;
  const { body, finalize } = (await req.json()) ?? {};
  if (typeof body !== "string") return Response.json({ error: "body is required" }, { status: 400 });
  const harvest = finalize ? await finalizeHarvest(id, body) : await saveHarvestDraft(id, body);
  return Response.json({ harvest });
}

export async function GET(req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const gate = await requireFacilitator(req, id);
  if ("error" in gate) return gate.error;
  const harvest = await getHarvest(id);
  return Response.json({ harvest });
}
```

- [ ] **Step 7: Export route (manage)**

`src/app/api/rooms/[id]/export/route.ts`:
```typescript
import type { NextRequest } from "next/server";
import { getAllMessages, getHarvest } from "@/lib/rooms";
import { requireFacilitator } from "@/lib/facilitator";
import { buildKumuCsv } from "@/lib/domain";

export async function GET(req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const gate = await requireFacilitator(req, id);
  if ("error" in gate) return gate.error;

  const harvest = await getHarvest(id);
  if (!harvest) return Response.json({ error: "no harvest yet" }, { status: 400 });

  const title = harvest.body.split("\n")[0].replace(/^#+\s*/, "").slice(0, 120) || "Harvest";
  const participants = Array.from(
    new Set(
      (await getAllMessages(id))
        .filter((m) => m.authorType === "human" && m.authorName)
        .map((m) => m.authorName as string)
    )
  );

  const { elements, connections } = buildKumuCsv({
    harvestTitle: title,
    nodeTitle: gate.room.nodeTitle,
    participants,
  });

  const csv = `# Elements\n${elements}\n\n# Connections\n${connections}\n`;
  return new Response(csv, {
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": `attachment; filename="kumu-${id}.csv"`,
    },
  });
}
```

- [ ] **Step 8: Verify the build typechecks**

Run: `cd node-room && npm run build`
Expected: build succeeds (all routes typecheck). Functional verification of the routes happens end-to-end in Task 9 against Railway Postgres.

- [ ] **Step 9: Commit**

```bash
git -C ../.. add node-room/src/app/api node-room/src/lib/facilitator.ts
git commit -m "feat(node-room): API routes (rooms, join, messages, weave, harvest, export)"
```

---

### Task 6: Participant UI

**Files:**
- Create: `node-room/src/app/room/[id]/page.tsx`, `node-room/src/app/room/[id]/RoomClient.tsx`

**Interfaces:**
- Consumes: the `GET/POST /api/rooms/[id]/messages` and `POST /api/rooms/[id]/join` contracts; `getRoom` from `rooms.ts`; `CONTRIBUTION_TAGS`, `POLL_INTERVAL_MS` from `domain.ts`.
- Produces: a working participant page (join by name, read the accreting thread, post with an optional tag, `@claude`, poll for new messages). Visual styling is intentionally minimal here; Task 8 applies the impeccable design.

- [ ] **Step 1: Server component shell (loads room, 404s if missing)**

`src/app/room/[id]/page.tsx`:
```tsx
import { notFound } from "next/navigation";
import { getRoom } from "@/lib/rooms";
import { RoomClient } from "./RoomClient";

export default async function RoomPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const room = await getRoom(id);
  if (!room) notFound();
  return (
    <RoomClient
      roomId={room.id}
      nodeTitle={room.nodeTitle}
      nodeDescription={room.nodeDescription}
    />
  );
}
```

- [ ] **Step 2: Client component (join gate, thread, composer, polling)**

`src/app/room/[id]/RoomClient.tsx`:
```tsx
"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { CONTRIBUTION_TAGS, POLL_INTERVAL_MS, type ContributionTag } from "@/lib/domain";

type UiMessage = {
  id: number;
  authorType: "human" | "claude" | "system";
  authorName: string | null;
  body: string;
  contributionTag: ContributionTag | null;
  createdAt: string;
};

function tokenKey(roomId: string) {
  return `node-room-token-${roomId}`;
}

export function RoomClient(props: {
  roomId: string;
  nodeTitle: string;
  nodeDescription: string;
}) {
  const { roomId } = props;
  const [token, setToken] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [messages, setMessages] = useState<UiMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [tag, setTag] = useState<ContributionTag | "">("");
  const [sending, setSending] = useState(false);
  const sinceRef = useRef(0);

  useEffect(() => {
    setToken(localStorage.getItem(tokenKey(roomId)));
  }, [roomId]);

  const poll = useCallback(async () => {
    const res = await fetch(`/api/rooms/${roomId}/messages?since=${sinceRef.current}`);
    if (!res.ok) return;
    const data = (await res.json()) as { messages: UiMessage[] };
    if (data.messages.length) {
      sinceRef.current = data.messages[data.messages.length - 1].id;
      setMessages((prev) => [...prev, ...data.messages]);
    }
  }, [roomId]);

  useEffect(() => {
    void poll();
    const interval = setInterval(() => {
      if (document.visibilityState === "visible") void poll();
    }, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [poll]);

  async function join(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    const res = await fetch(`/api/rooms/${roomId}/join`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ displayName: name.trim() }),
    });
    if (!res.ok) return;
    const data = (await res.json()) as { participantToken: string };
    localStorage.setItem(tokenKey(roomId), data.participantToken);
    setToken(data.participantToken);
  }

  async function send(e: React.FormEvent) {
    e.preventDefault();
    if (!draft.trim() || !token) return;
    setSending(true);
    try {
      const res = await fetch(`/api/rooms/${roomId}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ participantToken: token, body: draft.trim(), tag: tag || undefined }),
      });
      if (res.ok) {
        setDraft("");
        setTag("");
        await poll();
      }
    } finally {
      setSending(false);
    }
  }

  if (!token) {
    return (
      <main style={{ maxWidth: 640, margin: "0 auto", padding: 24 }}>
        <h1>{props.nodeTitle}</h1>
        <p>{props.nodeDescription}</p>
        <form onSubmit={join}>
          <label>
            Your name
            <input value={name} onChange={(e) => setName(e.target.value)} required />
          </label>
          <button type="submit">Enter the conversation</button>
        </form>
      </main>
    );
  }

  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: 24 }}>
      <h1>{props.nodeTitle}</h1>
      <p>{props.nodeDescription}</p>

      <ol style={{ listStyle: "none", padding: 0 }}>
        {messages.map((m) => (
          <li key={m.id} style={{ margin: "16px 0" }}>
            <strong>{m.authorType === "claude" ? "Facilitator" : m.authorName}</strong>
            {m.contributionTag ? <em> ({m.contributionTag})</em> : null}
            <div style={{ whiteSpace: "pre-wrap" }}>{m.body}</div>
          </li>
        ))}
      </ol>

      <form onSubmit={send}>
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Add to the conversation (use @claude to ask the facilitator)"
          rows={3}
          required
        />
        <div>
          <select value={tag} onChange={(e) => setTag(e.target.value as ContributionTag | "")}>
            <option value="">No tag</option>
            {CONTRIBUTION_TAGS.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
          <button type="submit" disabled={sending}>
            {sending ? "Posting" : "Post"}
          </button>
        </div>
      </form>
    </main>
  );
}
```

- [ ] **Step 3: Verify it builds**

Run: `cd node-room && npm run build`
Expected: build succeeds. Full click-through happens in Task 9.

- [ ] **Step 4: Commit**

```bash
git -C ../.. add node-room/src/app/room/[id]/page.tsx node-room/src/app/room/[id]/RoomClient.tsx
git commit -m "feat(node-room): participant UI (join, thread, composer, polling)"
```

---

### Task 7: Facilitator UI

**Files:**
- Create: `node-room/src/app/room/[id]/manage/page.tsx`, `node-room/src/app/room/[id]/manage/ManageClient.tsx`
- Create: `node-room/src/app/create/page.tsx` (a minimal create form so a facilitator can make a room without curl)

**Interfaces:**
- Consumes: `POST /api/rooms`, the weave/harvest/export contracts, and `getRoom` for the manage shell. The manage page reads `?key=` from the URL and passes it on every privileged call.
- Produces: a create page (returns the participant link + the manage link), and a manage page (Weave now, Harvest draft, edit + finalize, Export for Kumu).

- [ ] **Step 1: Create-room form**

`src/app/create/page.tsx`:
```tsx
"use client";

import { useState } from "react";

export default function CreatePage() {
  const [nodeTitle, setNodeTitle] = useState("");
  const [nodeDescription, setNodeDescription] = useState("");
  const [facilitationPrompt, setFacilitationPrompt] = useState("");
  const [result, setResult] = useState<{ id: string; facilitatorToken: string } | null>(null);

  async function create(e: React.FormEvent) {
    e.preventDefault();
    const res = await fetch(`/api/rooms`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nodeTitle, nodeDescription, facilitationPrompt }),
    });
    if (res.ok) setResult(await res.json());
  }

  if (result) {
    const origin = typeof window !== "undefined" ? window.location.origin : "";
    return (
      <main style={{ maxWidth: 640, margin: "0 auto", padding: 24 }}>
        <h1>Room created</h1>
        <p>Share this link with participants:</p>
        <code>{`${origin}/room/${result.id}`}</code>
        <p>Your private facilitator link (keep it to yourself):</p>
        <code>{`${origin}/room/${result.id}/manage?key=${result.facilitatorToken}`}</code>
      </main>
    );
  }

  return (
    <main style={{ maxWidth: 640, margin: "0 auto", padding: 24 }}>
      <h1>Create a conversation room</h1>
      <form onSubmit={create}>
        <label>
          Node title
          <input value={nodeTitle} onChange={(e) => setNodeTitle(e.target.value)} required />
        </label>
        <label>
          Description
          <textarea value={nodeDescription} onChange={(e) => setNodeDescription(e.target.value)} required />
        </label>
        <label>
          Facilitation guidance for Claude
          <textarea value={facilitationPrompt} onChange={(e) => setFacilitationPrompt(e.target.value)} />
        </label>
        <button type="submit">Create room</button>
      </form>
    </main>
  );
}
```

- [ ] **Step 2: Manage shell**

`src/app/room/[id]/manage/page.tsx`:
```tsx
import { notFound } from "next/navigation";
import { getRoom } from "@/lib/rooms";
import { ManageClient } from "./ManageClient";

export default async function ManagePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const room = await getRoom(id);
  if (!room) notFound();
  return <ManageClient roomId={room.id} nodeTitle={room.nodeTitle} />;
}
```

- [ ] **Step 3: Manage client (weave, harvest, export)**

`src/app/room/[id]/manage/ManageClient.tsx`:
```tsx
"use client";

import { useEffect, useState } from "react";

export function ManageClient(props: { roomId: string; nodeTitle: string }) {
  const { roomId } = props;
  const [key, setKey] = useState("");
  const [harvest, setHarvest] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [finalized, setFinalized] = useState(false);

  useEffect(() => {
    const k = new URLSearchParams(window.location.search).get("key") ?? "";
    setKey(k);
    void fetch(`/api/rooms/${roomId}/harvest?key=${k}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (d?.harvest) {
          setHarvest(d.harvest.body);
          setFinalized(Boolean(d.harvest.finalizedAt));
        }
      });
  }, [roomId]);

  async function weaveNow() {
    setBusy("weave");
    try {
      await fetch(`/api/rooms/${roomId}/weave?key=${key}`, { method: "POST" });
    } finally {
      setBusy(null);
    }
  }

  async function generateHarvest() {
    setBusy("harvest");
    try {
      const res = await fetch(`/api/rooms/${roomId}/harvest?key=${key}`, { method: "POST" });
      if (res.ok) {
        const d = await res.json();
        setHarvest(d.harvest.body);
        setFinalized(false);
      }
    } finally {
      setBusy(null);
    }
  }

  async function saveHarvest(finalize: boolean) {
    setBusy("save");
    try {
      const res = await fetch(`/api/rooms/${roomId}/harvest?key=${key}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ body: harvest, finalize }),
      });
      if (res.ok) setFinalized(finalize);
    } finally {
      setBusy(null);
    }
  }

  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: 24 }}>
      <h1>Manage: {props.nodeTitle}</h1>

      <section>
        <button onClick={weaveNow} disabled={busy !== null}>
          {busy === "weave" ? "Weaving" : "Weave now"}
        </button>
      </section>

      <section>
        <h2>Harvest</h2>
        <button onClick={generateHarvest} disabled={busy !== null}>
          {busy === "harvest" ? "Generating" : "Generate draft"}
        </button>
        <textarea
          value={harvest}
          onChange={(e) => setHarvest(e.target.value)}
          rows={12}
          style={{ width: "100%" }}
        />
        <div>
          <button onClick={() => saveHarvest(false)} disabled={busy !== null || !harvest}>
            Save draft
          </button>
          <button onClick={() => saveHarvest(true)} disabled={busy !== null || !harvest}>
            Finalize
          </button>
          {finalized ? <span> (finalized)</span> : null}
        </div>
      </section>

      <section>
        <h2>Export</h2>
        <a href={`/api/rooms/${roomId}/export?key=${key}`}>Download Kumu CSV</a>
      </section>
    </main>
  );
}
```

- [ ] **Step 4: Verify it builds**

Run: `cd node-room && npm run build`
Expected: build succeeds.

- [ ] **Step 5: Commit**

```bash
git -C ../.. add node-room/src/app/create node-room/src/app/room/[id]/manage
git commit -m "feat(node-room): facilitator UI (create, weave now, harvest editor, export)"
```

---

### Task 8: Impeccable design pass

**Files:**
- Create: `node-room/PRODUCT.md`, `node-room/DESIGN.md`
- Modify: `node-room/src/app/globals.css`, `node-room/tailwind.config.ts`, `node-room/src/app/room/[id]/RoomClient.tsx`, `node-room/src/app/room/[id]/manage/ManageClient.tsx`, `node-room/src/app/create/page.tsx`, `node-room/src/app/room/[id]/page.tsx` (and the manage/create shells as needed for layout)

**Interfaces:**
- Consumes: the working, behavior-complete UI from Tasks 6 and 7. This task changes only presentation, not the fetch/poll/state logic or the HTTP contract.
- Produces: an impeccable-compliant product-register UI for the room and manage surfaces.

This task is design work, so it runs through the **impeccable** skill rather than TDD. Do not hand-roll the visuals.

- [ ] **Step 1: Run the impeccable setup gate**

Invoke `/impeccable teach` for `node-room/` to author `PRODUCT.md` and `DESIGN.md`. Register is **product** (app UI that serves the conversation, not a marketing page). Users: Ben Roberts plus ~16 facilitators, one dyslexic, all allergic to AI-generated slop. Purpose: a calm, legible, asynchronous reading-and-writing surface. Anti-references: generic chat-app UI, SaaS dashboard, hero-metric template. This is a different surface from the invitation artifact, so do not reuse that page's brand-register visual system wholesale.

- [ ] **Step 2: Shape, then craft**

Run `/impeccable shape` for the room thread + composer and the manage surface; get the shape brief confirmed. Then `/impeccable craft` to implement the design against the behavior already in place. Keep all `fetch`, polling, `localStorage`, and state code intact; restyle structure and tokens only.

- [ ] **Step 3: Honor the absolute bans and copy rule**

No colored `border-left` stripes, no gradient text, no glassmorphism, no hero-metric template, no identical-card grids, no reflex fonts. No em dashes in any visible copy. Tag chips (`question/story/challenge/synthesis`) get distinct, legible treatment that is not a side-stripe.

- [ ] **Step 4: Polish**

Run `/impeccable polish` over both surfaces before shipping. Then `cd node-room && npm run build` to confirm the styled app still builds.

- [ ] **Step 5: Commit**

```bash
git -C ../.. add node-room/PRODUCT.md node-room/DESIGN.md node-room/src
git commit -m "feat(node-room): impeccable design pass (product register)"
```

---

### Task 9: Deploy to Railway and smoke-test the full loop

**Files:**
- Create: `node-room/README.md` (run + deploy notes)
- Modify: `claude-config/docs/deployments.md` (add the node-room Railway row) — this is in the separate claude-config repo, committed directly to its `main`/`master`.

**Interfaces:**
- Consumes: the full app from Tasks 1 to 8.
- Produces: a live Railway deployment with Postgres, migrations applied, and a verified DROP INTO to HARVEST loop.

This task uses the **use-railway** skill for the infrastructure steps.

- [ ] **Step 1: Provision Railway (project + Postgres + web service)**

Use the `use-railway` skill to: create (or select) a Railway project for `hybrid-dialogue`, add a Postgres database, and create a web service from the `node-room/` subdirectory (set the service root/working directory to `node-room` so Nixpacks builds the Next.js app there). Set env vars on the web service: `DATABASE_URL` (reference the Postgres service's connection variable) and `ANTHROPIC_API_KEY` (an ingest-scoped key is not applicable here; use a standard key, kept only in Railway env, never in the repo).

- [ ] **Step 2: Apply migrations against Railway Postgres**

With the Railway `DATABASE_URL` available locally (via `railway run` or by exporting the public connection string):
```bash
cd node-room
railway run npm run migrate
```
Expected: `applied 001_init.sql`.

- [ ] **Step 3: Run the gated integration test against Railway Postgres**

```bash
cd node-room
TEST_DATABASE_URL="<railway postgres url>" npx vitest run src/lib/rooms.itest.ts
```
Expected: PASS. (Uses a scratch/clean database, since it truncates on teardown. If pointing at the live DB, skip this step and rely on the manual loop below.)

- [ ] **Step 4: Smoke-test the full loop in production**

On the deployed URL:
1. Visit `/create`, make a room with a real node title + description + facilitation prompt. Confirm you get a participant link and a manage link, and that the opening frame appears as a Facilitator message in the room.
2. Open the participant link in two browser profiles, join as two different names, and post a few tagged messages from each (including one `@claude ...`). Confirm the `@claude` reply appears within a few seconds (after a poll), and that after 4 human messages a weave appears.
3. In the manage view, click **Weave now** and confirm a weave posts. Click **Generate draft**, edit the harvest, **Finalize**.
4. Click **Download Kumu CSV** and confirm it contains an Elements row typed `Harvest` and Connections rows linking each participant to the harvest and the harvest to the node.

- [ ] **Step 5: Confirm no real participant data is committed**

Verify `node-room/.gitignore` covers `.env`, and that no room data, transcripts, or generated CSV are tracked. `git -C ../.. status` should be clean of any data files.

- [ ] **Step 6: Write the README and the deployments row**

`node-room/README.md`: what it is, local run (`npm install`, set `DATABASE_URL` + `ANTHROPIC_API_KEY`, `npm run migrate`, `npm run dev`), and the Railway deploy shape. Then add a `hybrid-dialogue (node-room)` row to `claude-config/docs/deployments.md` with the Railway project/service and the "service root = node-room, set DATABASE_URL + ANTHROPIC_API_KEY, migrations are manual via npm run migrate" notes.

- [ ] **Step 7: Commit**

```bash
git -C ../.. add node-room/README.md
git commit -m "docs(node-room): run + deploy notes"
# In the claude-config repo (docs-only → direct to main/master):
git -C ../claude-config add docs/deployments.md
git -C ../claude-config commit -m "docs: add hybrid-dialogue node-room Railway deploy row"
git -C ../claude-config push
```

---

## Self-Review

**1. Spec coverage** (checked against `2026-06-27-node-room-design.md`):
- Async-first, polling, no realtime/presence → Tasks 5, 6 (poll endpoint + client interval); no realtime code anywhere. ✓
- Next.js + Postgres on Railway → Tasks 1, 3, 9. ✓
- Data model (rooms, participants, messages, harvests) → Task 3 schema matches the spec fields. ✓
- API routes (create, join, post, poll, weave, harvest draft/save, export) → Task 5 covers all eight. ✓
- Claude: opening frame, @mention (sonnet), auto-weave (opus adaptive), harvest (opus adaptive), amplifier stance, cooldown → Tasks 4, 5. ✓
- Contribution tags enum → Tasks 2, 3, 5, 6. ✓
- Identity (name + cookie/localStorage token), facilitator `?key=` gate → Tasks 5, 6, 7. ✓
- Kumu export (Elements Harvest row; Person→Harvest Harvested; Harvest→Node) → Tasks 2, 5. ✓
- UI via impeccable, product register → Task 8. ✓
- Real-LLM smoke for prompts → Task 4 Step 3. ✓
- Deploy + prod verification (DoD item 6) → Task 9. ✓
- Defaults (poll 5s, weave 4, no ORM) → Task 2 constants, Task 3 plain pg. ✓

**2. Placeholder scan:** no "TBD"/"TODO"/"implement later"; every code step shows complete code. ✓

**3. Type consistency:** `Message`/`Room`/`Harvest`/`Participant` and `ContributionTag` are defined once (Tasks 2, 3) and consumed unchanged in Tasks 4 to 7. `getMessages(roomId, sinceId)` is the single read function (poll passes `since`, callers needing all pass `0` via `getAllMessages`). `requireFacilitator` returns `{ room } | { error }` and every manage route narrows with `"error" in gate`. Model IDs and `thinking: { type: "adaptive" }` match the Global Constraints and the claude-api reference. ✓

No gaps found.
