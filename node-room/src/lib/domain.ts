import { nanoid } from "nanoid";

export const CONTRIBUTION_TAGS = [
  "question",
  "story",
  "challenge",
  "synthesis",
] as const;
export type ContributionTag = (typeof CONTRIBUTION_TAGS)[number];

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

export type KumuExportInput = {
  harvestTitle: string;
  nodeTitle: string;
  participants: string[];
};

function csvCell(value: string): string {
  // Quote when the cell contains a comma, quote, newline, or spaces; double inner quotes.
  if (/[",\n ]/.test(value)) return `"${value.replace(/"/g, '""')}"`;
  return value;
}

function csvRow(cells: string[]): string {
  return cells.map(csvCell).join(",");
}

export function buildKumuCsv(input: KumuExportInput): {
  elements: string;
  connections: string;
} {
  const elements = [
    csvRow(["Label", "Type"]),
    csvRow([input.harvestTitle, "Harvest"]),
  ].join("\n");

  const connectionRows = [csvRow(["From", "To", "Type"])];
  for (const person of input.participants) {
    connectionRows.push(csvRow([person, input.harvestTitle, "Harvested"]));
  }
  connectionRows.push(
    csvRow([input.harvestTitle, input.nodeTitle, "Harvested"])
  );
  const connections = connectionRows.join("\n");

  return { elements, connections };
}
