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
