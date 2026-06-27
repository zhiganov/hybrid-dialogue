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
    participants: ["Ana", "Rijon"],
  });
  test("elements has the harvest row typed Harvest", () => {
    expect(out.elements).toContain("Label,Type");
    expect(out.elements).toContain('"Trust, said plainly",Harvest');
  });
  test("connections links each person to the harvest and the harvest to the node", () => {
    expect(out.connections).toContain("From,To,Type");
    expect(out.connections).toContain('Ana,"Trust, said plainly",Harvested');
    expect(out.connections).toContain('Rijon,"Trust, said plainly",Harvested');
    expect(out.connections).toContain(
      '"Trust, said plainly","What does trust require?",Harvested'
    );
  });
});
