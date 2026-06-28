import type { NextRequest } from "next/server";
import { getAllMessages, getHarvest } from "@/lib/rooms";
import { requireFacilitator } from "@/lib/facilitator";
import { buildKumuCsv } from "@/lib/domain";
import type { ContributionTag } from "@/lib/domain";

export async function GET(req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const gate = await requireFacilitator(req, id);
  if ("error" in gate) return gate.error;

  const harvest = await getHarvest(id);
  if (!harvest) return Response.json({ error: "no harvest yet" }, { status: 400 });

  // First line of the harvest, stripped of markdown the model tends to emit
  // (heading hashes, a leading "**Title:**" label, stray bold), so the Kumu
  // node label reads as plain prose.
  const title =
    harvest.body
      .split("\n")[0]
      .replace(/^#+\s*/, "")
      .replace(/^\*\*\s*title\s*:?\s*\*\*\s*:?\s*/i, "")
      .replace(/\*\*/g, "")
      .trim()
      .slice(0, 120) || "Harvest";

  // Anonymized shape: tally the tags human contributions carried, never who said
  // what. Display names and message bodies stay in the room (hybrid-dialogue#2).
  const tagCounts: Partial<Record<ContributionTag, number>> = {};
  for (const m of await getAllMessages(id)) {
    if (m.authorType === "human" && m.contributionTag) {
      tagCounts[m.contributionTag] = (tagCounts[m.contributionTag] ?? 0) + 1;
    }
  }

  const { elements, connections } = buildKumuCsv({
    harvestTitle: title,
    nodeTitle: gate.room.nodeTitle,
    tagCounts,
    capturedAt: (harvest.finalizedAt ?? new Date().toISOString()).slice(0, 10),
  });

  const csv = `# Elements\n${elements}\n\n# Connections\n${connections}\n`;
  return new Response(csv, {
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": `attachment; filename="kumu-${id}.csv"`,
    },
  });
}
