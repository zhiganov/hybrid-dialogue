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
