import { nanoid } from "nanoid";

export const CONTRIBUTION_TAGS = [
  "question",
  "story",
  "challenge",
  "synthesis",
] as const;
export type ContributionTag = (typeof CONTRIBUTION_TAGS)[number];

// Display labels and point-of-use definitions for the contribution kinds.
// Single source of truth: the composer chips and the /about page both read
// these, so a wording change stays consistent across the app.
export const TAG_LABELS: Record<ContributionTag, string> = {
  question: "Question",
  story: "Story",
  challenge: "Challenge",
  synthesis: "Synthesis",
};

export const TAG_DEFINITIONS: Record<ContributionTag, string> = {
  question: "something you are opening for the group",
  story: "something from your own experience",
  challenge: "a push against an idea on the table",
  synthesis: "pulling threads together",
};

export function isValidTag(value: unknown): value is ContributionTag {
  return (
    typeof value === "string" &&
    (CONTRIBUTION_TAGS as readonly string[]).includes(value)
  );
}

export function generateToken(): string {
  return nanoid(); // 21 url-safe chars by default
}

const MENTION_RE = /(^|[^A-Za-z0-9_@])@claude\b/i;
export function mentionsClaude(body: string): boolean {
  return MENTION_RE.test(body);
}

export const WEAVE_THRESHOLD = 4;
export const POLL_INTERVAL_MS = 5000;
export const CLAUDE_COOLDOWN_MS = 20000;

export function shouldWeave(humanMessagesSinceLastClaude: number): boolean {
  return humanMessagesSinceLastClaude >= WEAVE_THRESHOLD;
}

// What crosses the room boundary is the conversation's anonymized shape, never
// the participants. Per Megan Ducote's Community Legibility Spec, a community
// reports "an anonymized, aggregate shape" carrying "the shape of activity,
// never the content, and never participant identities" (Local Assembly,
// doi.org/10.6084/m9.figshare.32772147; Dual-Ledger Authentication,
// doi.org/10.6084/m9.figshare.32576631). See hybrid-dialogue#2. So the export
// carries the harvest, the node, the tags present as theme nodes (with counts),
// and the time it was captured. No display names, no message bodies.
export type KumuExportInput = {
  harvestTitle: string;
  nodeTitle: string;
  tagCounts: Partial<Record<ContributionTag, number>>;
  capturedAt?: string;
};

function csvCell(value: string): string {
  // Quote when the cell contains a comma, quote, newline, or spaces; double inner quotes.
  if (/[",\n ]/.test(value)) return `"${value.replace(/"/g, '""')}"`;
  return value;
}

function csvRow(cells: string[]): string {
  return cells.map(csvCell).join(",");
}

function tagLabel(tag: ContributionTag): string {
  return TAG_LABELS[tag];
}

export function buildKumuCsv(input: KumuExportInput): {
  elements: string;
  connections: string;
} {
  const captured = input.capturedAt ?? "";
  const elementRows = [
    csvRow(["Label", "Type", "Count", "Captured"]),
    csvRow([input.harvestTitle, "Harvest", "", captured]),
    csvRow([input.nodeTitle, "Node", "", ""]),
  ];

  const connectionRows = [csvRow(["From", "To", "Type"])];
  for (const tag of CONTRIBUTION_TAGS) {
    const count = input.tagCounts[tag] ?? 0;
    if (count <= 0) continue;
    const label = tagLabel(tag);
    elementRows.push(csvRow([label, "Theme", String(count), ""]));
    connectionRows.push(csvRow([label, input.harvestTitle, "Surfaced"]));
  }
  connectionRows.push(csvRow([input.harvestTitle, input.nodeTitle, "Harvested"]));

  return {
    elements: elementRows.join("\n"),
    connections: connectionRows.join("\n"),
  };
}
