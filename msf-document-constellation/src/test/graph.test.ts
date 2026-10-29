import { describe, expect, it } from "vitest";
import { nodeMatches, type DocNode, type Filters } from "@/lib/graph";

const node: DocNode = {
  id: "D054bcedd1a", title: "Document", genre: "Statement", language: "en",
  theme: "Other / general", themes: [], countries: [], year: null,
  words: 198, x: 0.7936, y: 1.077, snippet: "",
};
const filters: Filters = {
  themes: [], genres: [], languages: [], countries: [], years: [1973, 2026], search: "",
};

describe("Real dataset dates", () => {
  it("keeps undated documents visible without treating null as year zero", () => {
    expect(nodeMatches(node, filters)).toBe(true);
  });
  it("still filters known dates outside the selected years", () => {
    expect(nodeMatches({ ...node, year: 2013 }, { ...filters, years: [2020, 2026] })).toBe(false);
  });
});