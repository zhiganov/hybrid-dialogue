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
