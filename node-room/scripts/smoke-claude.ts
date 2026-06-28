import { openingFrame, replyToMention, weave, harvestDraft } from "../src/lib/claude";
import type { Message, Room } from "../src/lib/rooms";

const room: Room = {
  id: "demo",
  nodeTitle: "What does trust actually require of us?",
  nodeDescription:
    "Several people said trust matters but meant different things by it.",
  facilitationPrompt: "Keep it grounded in concrete stories, not abstractions.",
  facilitatorToken: "x",
  listed: true,
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
