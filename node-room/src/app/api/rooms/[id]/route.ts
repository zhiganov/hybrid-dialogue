import type { NextRequest } from "next/server";
import { requireFacilitator } from "@/lib/facilitator";
import { setRoomListed } from "@/lib/rooms";

export async function PATCH(req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const gate = await requireFacilitator(req, id);
  if ("error" in gate) return gate.error;
  const { listed } = (await req.json()) ?? {};
  if (typeof listed !== "boolean") {
    return Response.json({ error: "listed (boolean) is required" }, { status: 400 });
  }
  await setRoomListed(id, listed);
  return Response.json({ ok: true, listed });
}
