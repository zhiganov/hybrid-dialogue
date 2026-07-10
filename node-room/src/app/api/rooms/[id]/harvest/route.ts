import type { NextRequest } from "next/server";
import { finalizeHarvest, getAllMessages, getHarvest, saveHarvestDraft } from "@/lib/rooms";
import { requireDesigner } from "@/lib/designer";
import { rateLimit } from "@/lib/ratelimit";
import { harvestDraft } from "@/lib/claude";

export async function POST(req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const gate = await requireDesigner(req, id);
  if ("error" in gate) return gate.error;
  if (!rateLimit(`harvest:${id}`, 12, 60 * 60 * 1000)) {
    return Response.json(
      { error: "rate_limited", message: "The harvest has been generated several times in the last hour. Please wait a little before generating again." },
      { status: 429 }
    );
  }
  const all = await getAllMessages(id);
  const draft = await harvestDraft(gate.room, all);
  const harvest = await saveHarvestDraft(id, draft);
  return Response.json({ harvest });
}

export async function PUT(req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const gate = await requireDesigner(req, id);
  if ("error" in gate) return gate.error;
  const { body, finalize } = (await req.json()) ?? {};
  if (typeof body !== "string") return Response.json({ error: "body is required" }, { status: 400 });
  const harvest = finalize ? await finalizeHarvest(id, body) : await saveHarvestDraft(id, body);
  return Response.json({ harvest });
}

export async function GET(req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const gate = await requireDesigner(req, id);
  if ("error" in gate) return gate.error;
  const harvest = await getHarvest(id);
  return Response.json({ harvest });
}
