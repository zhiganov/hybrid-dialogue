import type { NextRequest } from "next/server";
import { getAllMessages, getHarvest } from "@/lib/rooms";
import { requireFacilitator } from "@/lib/facilitator";
import { buildKumuCsv } from "@/lib/domain";

export async function GET(req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const gate = await requireFacilitator(req, id);
  if ("error" in gate) return gate.error;

  const harvest = await getHarvest(id);
  if (!harvest) return Response.json({ error: "no harvest yet" }, { status: 400 });

  const title = harvest.body.split("\n")[0].replace(/^#+\s*/, "").slice(0, 120) || "Harvest";
  const participants = Array.from(
    new Set(
      (await getAllMessages(id))
        .filter((m) => m.authorType === "human" && m.authorName)
        .map((m) => m.authorName as string)
    )
  );

  const { elements, connections } = buildKumuCsv({
    harvestTitle: title,
    nodeTitle: gate.room.nodeTitle,
    participants,
  });

  const csv = `# Elements\n${elements}\n\n# Connections\n${connections}\n`;
  return new Response(csv, {
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": `attachment; filename="kumu-${id}.csv"`,
    },
  });
}
