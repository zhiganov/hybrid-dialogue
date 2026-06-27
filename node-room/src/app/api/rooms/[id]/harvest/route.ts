import type { NextRequest } from "next/server";
import { finalizeHarvest, getAllMessages, getHarvest, saveHarvestDraft } from "@/lib/rooms";
import { requireFacilitator } from "@/lib/facilitator";
import { harvestDraft } from "@/lib/claude";

export async function POST(req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const gate = await requireFacilitator(req, id);
  if ("error" in gate) return gate.error;
  const all = await getAllMessages(id);
  const draft = await harvestDraft(gate.room, all);
  const harvest = await saveHarvestDraft(id, draft);
  return Response.json({ harvest });
}

export async function PUT(req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const gate = await requireFacilitator(req, id);
  if ("error" in gate) return gate.error;
  const { body, finalize } = (await req.json()) ?? {};
  if (typeof body !== "string") return Response.json({ error: "body is required" }, { status: 400 });
  const harvest = finalize ? await finalizeHarvest(id, body) : await saveHarvestDraft(id, body);
  return Response.json({ harvest });
}

export async function GET(req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const gate = await requireFacilitator(req, id);
  if ("error" in gate) return gate.error;
  const harvest = await getHarvest(id);
  return Response.json({ harvest });
}
