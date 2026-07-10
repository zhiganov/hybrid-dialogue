import type { NextRequest } from "next/server";
import { addMessage, getMessages } from "@/lib/rooms";
import { requireDesigner } from "@/lib/designer";
import { rateLimit } from "@/lib/ratelimit";
import { weave } from "@/lib/claude";

export async function POST(req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const gate = await requireDesigner(req, id);
  if ("error" in gate) return gate.error;
  if (!rateLimit(`weave:${id}`, 8, 60 * 60 * 1000)) {
    return Response.json(
      { error: "rate_limited", message: "This conversation has been woven several times in the last hour. Please wait a little before weaving again." },
      { status: 429 }
    );
  }
  const recent = (await getMessages(id, 0)).slice(-12);
  const body = await weave(gate.room, recent);
  const message = await addMessage({ roomId: id, authorType: "claude", participantId: null, body, contributionTag: null });
  return Response.json({ message });
}
