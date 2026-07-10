# node-room transcript enrichment — design spec

**Status:** design approved (brainstorm 2026-06-29), pending implementation plan.
**Tracks:** [hybrid-dialogue#20](https://github.com/zhiganov/hybrid-dialogue/issues/20).
**Goal:** enrich or pre-populate a node-room conversation from the transcript of a Zoom call, so a group's live discussion can carry into the async room, done honestly: transcript-derived material reads as clearly AI-processed and distinct from a participant's own words, is anonymized, and is trivially mutable and excludable from the harvest.

## Locked decisions (from the brainstorm)

1. **Scope:** full pipeline: manual upload + Fireflies, both pre-populate and enrich, full controls.
2. **Consent:** the conversation designer attests consent at import; items are anonymized (no speaker names).
3. **Placement:** interleaved in the thread chronologically, each item visually distinct with a provenance label.
4. **Fireflies:** in-app pull by transcript ID/URL using the host's Fireflies key (reaches the host's own calls). Manual upload is the universal path for everyone else.
5. **Curation:** the designer reviews / edits / drops extracted items in a preview before anything posts.
6. **Harvest:** transcript items are excluded from the harvest and the Kumu export by default; the designer opts specific items in.

## Principle

This feature only earns its place if it never lets AI-extracted call material masquerade as a human contribution (the same honesty concern as [#14](https://github.com/zhiganov/hybrid-dialogue/issues/14)) and never leaks speaker identities (the anonymization ethic of [#2](https://github.com/zhiganov/hybrid-dialogue/issues/2) / Megan's Community Legibility Spec). Provenance and anonymization are enforced structurally in the data model, not just in copy.

## End-to-end flow

On the manage page, the conversation designer opens an **Import from a call** panel:

1. Pick a source: drop a VTT / plain-text file, or paste a Fireflies transcript URL/ID.
2. Tick **"I have consent to import this call"** (required; recorded on the import).
3. Server parses the transcript and AI-extracts anonymized statements.
4. Server returns a **preview** (nothing persisted yet).
5. Designer selects / edits / drops items.
6. **Commit** → the `imports` row is written and the selected items become messages in the room.

"Pre-populate" and "enrich" are the same mechanism: pre-populate imports into an empty room; enrich imports into an active one. No separate code path.

## Data model

New table **`imports`** (one row per imported call; also the consent record):

```
imports(
  id           uuid primary key,
  room_id      uuid not null references rooms(id),
  source_kind  text not null,          -- 'upload' | 'fireflies'
  source_label text not null,          -- e.g. "call on 27 June 2026"
  source_ref   text,                   -- filename or Fireflies transcript id
  consent_attested boolean not null,   -- always true at commit
  created_at   timestamptz not null default now()
)
```

**`messages`** gains three columns and one `author_type` value:

```
alter table messages
  add column import_id  uuid references imports(id),
  add column muted      boolean not null default false,
  add column in_harvest boolean not null default false;
-- author_type gains 'transcript' (verify/relax any CHECK constraint on author_type)
```

A transcript item = `author_type='transcript'`, `participant_id=null`, `import_id` set, `body` = the anonymized statement, `contribution_tag` = the AI-assigned kind. `muted` hides it from the thread; `in_harvest` opts it into the harvest/export.

**Migration is manual** in node-room (no auto-migrate). Ship as a SQL migration; confirm whether `author_type` has a CHECK/enum constraint that must be widened.

## Extraction + parsing (server-side, host key)

- `parseTranscript(raw, format)` → normalize VTT / plain text / Fireflies JSON to plain text.
- `extractContributions(text, room)` → one Sonnet call with a JSON-schema tool. Prompt: pull the important statements / ideas / questions / tensions as **standalone, anonymized** (no names) self-contained contributions; assign a contribution kind; dedup; cap volume (~12-15 items). If the transcript exceeds the input budget, cap length and flag truncation. Runs on the host key like weave/harvest (models live in `src/lib/claude.ts` `MODELS`).
- `fetchFirefliesTranscript(id)` → Fireflies GraphQL API via a new `FIREFLIES_API_KEY` Railway env var (host key). See `claude-config/memory/reference_fireflies_api.md` for the GraphQL shape.

## Provenance, rendering, controls

- Transcript entries render distinct from human contributions and from Claude's weave: their own `.entry--transcript` treatment plus a provenance label "from the call on {date} · AI-extracted". Never a human name, never `author_type='human'`.
- **Designer-only controls** (shown in designer mode): per-item **mute** (hides from the thread) and per-item **include-in-harvest**; bulk include/exclude and hide-all at the import level.

## Harvest / export / weave

- The harvest (`getAllMessages` path) and the Kumu export (`buildKumuCsv`, and the export route's tag counting) **exclude** `author_type='transcript'` unless `in_harvest=true`, and always skip `muted`. The harvest stays a distillation of what the humans said unless the designer opts items in.
- Claude's **weave/reply** context *includes* non-muted transcript items (they are live material in the room); they simply do not drive the harvest by default.

## API surface (all designer-gated via `requireDesigner`)

- `POST /api/rooms/[id]/import` → parse + extract, return an ephemeral preview (no persistence).
- `POST /api/rooms/[id]/import/commit` → create the `imports` row + insert the selected transcript messages.
- `PATCH /api/rooms/[id]/messages/[messageId]` → `{ muted?, in_harvest? }` (designer-gated; also the natural home for [#18](https://github.com/zhiganov/hybrid-dialogue/issues/18) later).

## Error handling + limits

Bad/unparseable file → 400. Fireflies fetch failure → clear error. Empty or failed extraction → a message, nothing posted. Oversized transcript → cap length and tell the designer it was truncated.

## Testing

- Pure units: `parseTranscript` (VTT + plain text), extraction JSON validation, the harvest/export transcript filter.
- Integration (`rooms.itest.ts` pattern): import → commit → confirm items are excluded from the harvest until opted in.
- **Real-LLM smoke** on the extraction prompt (repo rule for LLM-gated changes): a real transcript in, verify anonymized, kind-tagged, deduped, capped items out.

## Build decomposition (for the implementation plan)

1. Schema + manual migration (`imports` table, `messages` columns, `author_type` value).
2. Data layer: `createImport`, `addTranscriptMessages`, mute/in_harvest updates; harvest + export filters.
3. Parsing + extraction + Fireflies fetch libs.
4. API routes: `/import` (preview), `/import/commit`, message `PATCH`.
5. Manage UI: the Import panel (source → consent → preview/curate → commit).
6. RoomClient: transcript entry rendering + designer mute/harvest controls.
7. Tests + real-LLM smoke.

## Known limitation (shared with #18)

The thread's incremental `since`-poll does not propagate a *post-commit* mute to other clients until a full reload; committed items themselves propagate fine (they are new rows). Most exclusion happens in the pre-commit preview, so this is minor for v1; a full reconciliation is #18's concern.

## Relates to

- [#2](https://github.com/zhiganov/hybrid-dialogue/issues/2) harvest→Kumu consent/anonymization boundary.
- [#14](https://github.com/zhiganov/hybrid-dialogue/issues/14) honesty about what is AI vs human.
- [#17](https://github.com/zhiganov/hybrid-dialogue/issues/17) auto-detect kind (extraction assigns kinds; shared classification).
- [#18](https://github.com/zhiganov/hybrid-dialogue/issues/18) edit/delete + the poll-propagation limitation.
