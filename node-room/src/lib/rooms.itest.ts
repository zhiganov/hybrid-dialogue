import { afterAll, beforeAll, describe, expect, test } from "vitest";

const url = process.env.TEST_DATABASE_URL;
const d = url ? describe : describe.skip;

d("rooms data access (integration)", () => {
  beforeAll(() => {
    process.env.DATABASE_URL = url;
  });
  afterAll(async () => {
    const { query } = await import("./db");
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
      participantId: ana.id,
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
