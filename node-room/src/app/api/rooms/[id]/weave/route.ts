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
