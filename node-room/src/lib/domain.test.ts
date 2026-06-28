import { describe, expect, test } from "vitest";
import {
  CONTRIBUTION_TAGS,
  isValidTag,
  generateToken,
  mentionsClaude,
  shouldWeave,
  WEAVE_THRESHOLD,
  buildKumuCsv,
} from "./domain";

describe("tags", () => {
  test("valid tags pass", () => {
    for (const t of CONTRIBUTION_TAGS) expect(isValidTag(t)).toBe(true);
  });
  test("invalid tags fail", () => {
    expect(isValidTag("idea")).toBe(false);
    expect(isValidTag(null)).toBe(false);
    expect(isValidTag(undefined)).toBe(false);
  });
});

describe("generateToken", () => {
  test("is 21 url-safe chars and unique", () => {
    const a = generateToken();
    const b = generateToken();
    expect(a).toMatch(/^[A-Za-z0-9_-]{21}$/);
    expect(a).not.toBe(b);
  });
});

describe("mentionsClaude", () => {
  test("detects @claude case-insensitively", () => {
    expect(mentionsClaude("hey @claude what do you think?")).toBe(true);
    expect(mentionsClaude("@Claude")).toBe(true);
    expect(mentionsClaude("ask @CLAUDE here")).toBe(true);
  });
  test("ignores when absent or embedded", () => {
    expect(mentionsClaude("no mention here")).toBe(false);
    expect(mentionsClaude("email claude@example.com")).toBe(false);
  });
});

describe("shouldWeave", () => {
  test("weaves at threshold, not before", () => {
    expect(shouldWeave(WEAVE_THRESHOLD - 1)).toBe(false);
    expect(shouldWeave(WEAVE_THRESHOLD)).toBe(true);
    expect(shouldWeave(WEAVE_THRESHOLD + 1)).toBe(true);
  });
});

describe("buildKumuCsv", () => {
  const out = buildKumuCsv({
    harvestTitle: "Trust, said plainly",
    nodeTitle: "What does trust require?",
    tagCounts: { question: 2, story: 1 },
    capturedAt: "2026-06-28",
  });
  test("elements carry the harvest, node, and a theme row per present tag", () => {
    expect(out.elements).toContain("Label,Type,Count,Captured");
    expect(out.elements).toContain('"Trust, said plainly",Harvest,,2026-06-28');
    expect(out.elements).toContain('"What does trust require?",Node,,');
    expect(out.elements).toContain("Question,Theme,2,");
    expect(out.elements).toContain("Story,Theme,1,");
  });
  test("absent tags are omitted", () => {
    expect(out.elements).not.toContain("Challenge");
    expect(out.elements).not.toContain("Synthesis");
  });
  test("connections link present themes to the harvest and the harvest to the node", () => {
    expect(out.connections).toContain("From,To,Type");
    expect(out.connections).toContain('Question,"Trust, said plainly",Surfaced');
    expect(out.connections).toContain('Story,"Trust, said plainly",Surfaced');
    expect(out.connections).toContain(
      '"Trust, said plainly","What does trust require?",Harvested'
    );
  });
  test("no participant identities cross the boundary", () => {
    const both = out.elements + out.connections;
    expect(both).not.toContain("Ana");
    expect(both).not.toContain("Rijon");
  });
});
