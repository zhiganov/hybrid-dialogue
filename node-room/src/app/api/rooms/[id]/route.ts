import type { NextRequest } from "next/server";
import { requireDesigner } from "@/lib/designer";
import { setRoomListed, updateRoom } from "@/lib/rooms";
import { validateRoomEdits } from "@/lib/domain";

export async function PATCH(req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const gate = await requireDesigner(req, id);
  if ("error" in gate) return gate.error;

  const body = ((await req.json().catch(() => null)) ?? {}) as Record<string, unknown>;

  const hasListed = typeof body.listed === "boolean";
  const result = validateRoomEdits(body);
  if (!result.ok) {
    return Response.json({ error: result.message, message: result.message }, { status: 400 });
  }
  const hasContent = Object.keys(result.fields).length > 0;
  if (!hasListed && !hasContent) {
    return Response.json({ error: "Nothing to update.", message: "Nothing to update." }, { status: 400 });
  }

  if (hasListed) await setRoomListed(id, body.listed as boolean);

  let room = gate.room;
  if (hasContent) {
    room = await updateRoom(id, result.fields);
  } else if (hasListed) {
    room = { ...room, listed: body.listed as boolean };
  }

  return Response.json({ ok: true, room });
}
