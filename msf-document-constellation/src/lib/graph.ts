import datasetAsset from "@/assets/knowledge_graph_msf.json.asset.json";

export const DATA_URL = datasetAsset.url;

export interface DocNode {
  id: string;
  title: string;
  genre: string;
  language: string;
  theme: string;
  themes: string[];
  countries: string[];
  year: number | null;
  words: number;
  x: number;
  y: number;
  snippet: string;
}
export interface Edge {
  source: string;
  target: string;
  weight: number;
}
export interface GraphData {
  meta: { themes: string[]; genres: string[]; languages: string[] };
  nodes: DocNode[];
  edges: Edge[];
}

export interface Filters {
  themes: string[];
  genres: string[];
  languages: string[];
  countries: string[];
  years: [number, number];
  search: string;
}

// Categorical palette for themes (data-viz colours, used on the canvas only).
const PALETTE = [
  "#1f77b4", "#2ca02c", "#ff7f0e", "#9467bd", "#8c564b", "#17becf",
  "#bcbd22", "#e377c2", "#7f7f7f", "#4e79a7", "#59a14f", "#b07aa1",
  "#f28e2b", "#76b7b2", "#edc948", "#9c755f",
];
export function themeColors(themes: string[]): Record<string, string> {
  const m: Record<string, string> = {};
  themes.forEach((t, i) => (m[t] = PALETTE[i % PALETTE.length] ?? "#7f7f7f"));
  return m;
}

export function nodeMatches(n: DocNode, f: Filters): boolean {
  if (f.themes.length && !f.themes.includes(n.theme)) return false;
  if (f.genres.length && !f.genres.includes(n.genre)) return false;
  if (f.languages.length && !f.languages.includes(n.language)) return false;
  if (f.countries.length && !n.countries.some((c) => f.countries.includes(c))) return false;
  // Unknown dates stay visible rather than being interpreted as year zero.
  if (n.year !== null && (n.year < f.years[0] || n.year > f.years[1])) return false;
  const q = f.search.trim().toLowerCase();
  if (q && !n.title.toLowerCase().includes(q) && !n.snippet.toLowerCase().includes(q)) return false;
  return true;
}

export function buildNeighbours(edges: Edge[]) {
  const m = new Map<string, { id: string; weight: number }[]>();
  for (const e of edges) {
    if (!m.has(e.source)) m.set(e.source, []);
    if (!m.has(e.target)) m.set(e.target, []);
    m.get(e.source)!.push({ id: e.target, weight: e.weight });
    m.get(e.target)!.push({ id: e.source, weight: e.weight });
  }
  for (const l of m.values()) l.sort((a, b) => b.weight - a.weight);
  return m;
}
