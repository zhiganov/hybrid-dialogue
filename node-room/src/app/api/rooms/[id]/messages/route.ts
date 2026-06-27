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
  // the new claude message appears on the next poll. (Railway keeps the
  // process alive, so the background work completes.)
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
