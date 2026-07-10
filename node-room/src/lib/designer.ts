import type { NextRequest } from "next/server";
import { getRoom, type Room } from "./rooms";

// Conversation-designer actions are intentionally OPEN for now: anyone can
// weave, harvest, and export (see GitHub #6 and the "Conversation designer
// mode" toggle on /transparency). This loads the room (404 if missing) and no
// longer checks a token. A `?key=` is still accepted but ignored, so older
// capability URLs keep working. Proper auth + roles will reinstate a real
// check here later.
export async function requireDesigner(
  _req: NextRequest,
  roomId: string
): Promise<{ room: Room } | { error: Response }> {
  const room = await getRoom(roomId);
  if (!room) return { error: Response.json({ error: "not found" }, { status: 404 }) };
  return { room };
}
