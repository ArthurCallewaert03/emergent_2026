import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { GraphCanvas } from "@/components/GraphCanvas";
import { DATA_URL, buildNeighbours, nodeMatches, themeColors, type Filters, type GraphData } from "@/lib/graph";

export const Route = createFileRoute("/")({
  validateSearch: (s: Record<string, unknown>): { doc?: string } => (typeof s["doc"] === "string" ? { doc: s["doc"] } : {}),
  head: () => ({
    meta: [
      { title: "MSF Knowledge Graph" },
      { name: "description", content: "Interactive map of Médecins Sans Frontières documents, where similar documents sit close together." },
      { property: "og:title", content: "MSF Knowledge Graph" },
      { property: "og:description", content: "Explore MSF documents by theme, genre, language, country and year." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: App,
});

function App() {
  const { doc } = Route.useSearch();
  const navigate = Route.useNavigate();
  const [data, setData] = useState<GraphData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(DATA_URL)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then(setData)
      .catch((e) => setError(String(e)));
  }, []);

  if (error) return <div className="p-8 text-destructive">Could not load data: {error}</div>;
  if (!data) return <div className="flex h-screen items-center justify-center text-muted-foreground">Loading map…</div>;
  return <Explorer data={data} doc={doc} setDoc={(id) => navigate({ search: id ? { doc: id } : {}, replace: true })} />;
}

function Explorer({ data, doc, setDoc }: { data: GraphData; doc: string | undefined; setDoc: (id: string | null) => void }) {
  const colors = useMemo(() => themeColors(data.meta.themes), [data]);
  const byId = useMemo(() => new Map(data.nodes.map((n) => [n.id, n])), [data]);
  const neighbours = useMemo(() => buildNeighbours(data.edges), [data]);
  const yearBounds = useMemo((): [number, number] => {
    const ys = data.nodes.flatMap((n) => n.year === null ? [] : [n.year]);
    return ys.length ? [Math.min(...ys), Math.max(...ys)] : [0, 0];
  }, [data]);
  const allCountries = useMemo(() => [...new Set(data.nodes.flatMap((n) => n.countries))].sort(), [data]);
  const empty: Filters = { themes: [], genres: [], languages: [], countries: [], years: yearBounds, search: "" };
  const [f, setF] = useState<Filters>(empty);
  const [showEdges, setShowEdges] = useState(true);
  const [focus, setFocus] = useState<{ id: string; n: number } | null>(null);
  const selectedId = doc && byId.has(doc) ? doc : null;

  // Deep link on load: centre the document from ?doc=
  useEffect(() => {
    if (selectedId) setFocus({ id: selectedId, n: Date.now() });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const matching = useMemo(() => new Set(data.nodes.filter((n) => nodeMatches(n, f)).map((n) => n.id)), [data, f]);
  const alpha = useMemo(() => {
    const m = new Map<string, number>();
    const hood = selectedId ? new Set([selectedId, ...(neighbours.get(selectedId) ?? []).map((x) => x.id)]) : null;
    for (const n of data.nodes) {
      let a = matching.has(n.id) ? 1 : 0.1;
      if (hood && !hood.has(n.id)) a = Math.min(a, 0.1);
      m.set(n.id, a);
    }
    return m;
  }, [data, matching, selectedId, neighbours]);

  const count = (key: "theme" | "genre") => {
    const c: Record<string, number> = {};
    for (const n of data.nodes) c[n[key]] = (c[n[key]] ?? 0) + 1;
    return c;
  };
  const themeCounts = useMemo(() => count("theme"), [data]);
  const genreCounts = useMemo(() => count("genre"), [data]);
  const toggle = (k: "themes" | "genres" | "languages" | "countries", v: string) =>
    setF((p) => ({ ...p, [k]: p[k].includes(v) ? p[k].filter((x) => x !== v) : [...p[k], v] }));

  const select = (id: string | null, centre = false) => {
    setDoc(id);
    if (id && centre) setFocus({ id, n: Date.now() });
  };
  const sel = selectedId ? byId.get(selectedId)! : null;

  return (
    <div className="flex h-screen flex-col bg-background text-foreground">
      <header className="flex items-center gap-6 border-b px-5 py-3">
        <div className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-full bg-primary" />
          <h1 className="text-lg font-semibold tracking-tight">MSF Knowledge Graph</h1>
        </div>
        <input
          value={f.search}
          onChange={(e) => setF({ ...f, search: e.target.value })}
          placeholder="Search titles and text…"
          className="h-9 w-full max-w-md rounded-md border border-input bg-background px-3 text-sm outline-none focus:border-ring"
        />
        <div className="ml-auto whitespace-nowrap text-sm text-muted-foreground">
          showing <span className="font-medium text-foreground">{matching.size}</span> of {data.nodes.length} documents
        </div>
      </header>

      <div className="flex min-h-0 flex-1">
        <aside className="w-72 shrink-0 space-y-6 overflow-y-auto border-r bg-sidebar p-4 text-sm">
          <Section title="Theme">
            {data.meta.themes.map((t) => (
              <Check key={t} checked={f.themes.includes(t)} onChange={() => toggle("themes", t)}>
                <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: colors[t] }} />
                <span className="flex-1">{t}</span>
                <span className="text-xs text-muted-foreground">{themeCounts[t] ?? 0}</span>
              </Check>
            ))}
          </Section>
          <Section title="Genre">
            {data.meta.genres.map((g) => (
              <Check key={g} checked={f.genres.includes(g)} onChange={() => toggle("genres", g)}>
                <span className="flex-1">{g}</span>
                <span className="text-xs text-muted-foreground">{genreCounts[g] ?? 0}</span>
              </Check>
            ))}
          </Section>
          <Section title="Language">
            <div className="flex flex-wrap gap-2">
              {data.meta.languages.map((l) => (
                <button
                  key={l}
                  onClick={() => toggle("languages", l)}
                  className={`rounded-full border px-3 py-1 text-xs uppercase ${f.languages.includes(l) ? "border-primary bg-accent text-accent-foreground" : "hover:bg-muted"}`}
                >
                  {l}
                </button>
              ))}
            </div>
          </Section>
          <CountryFilter all={allCountries} selected={f.countries} toggle={(c) => toggle("countries", c)} />
          <Section title={`Year: ${f.years[0]} – ${f.years[1]}`}>
            <input type="range" className="w-full accent-primary" min={yearBounds[0]} max={yearBounds[1]} value={f.years[0]}
              onChange={(e) => setF({ ...f, years: [Math.min(+e.target.value, f.years[1]), f.years[1]] })} />
            <input type="range" className="w-full accent-primary" min={yearBounds[0]} max={yearBounds[1]} value={f.years[1]}
              onChange={(e) => setF({ ...f, years: [f.years[0], Math.max(+e.target.value, f.years[0])] })} />
          </Section>
          <label className="flex items-center gap-2">
            <input type="checkbox" className="accent-primary" checked={showEdges} onChange={(e) => setShowEdges(e.target.checked)} />
            Show connections
          </label>
          <button onClick={() => setF(empty)} className="w-full rounded-md border px-3 py-2 font-medium hover:border-primary hover:text-primary">
            Reset filters
          </button>
        </aside>

        <main className="min-w-0 flex-1">
          <GraphCanvas nodes={data.nodes} edges={data.edges} colors={colors} alpha={alpha} selectedId={selectedId}
            showEdges={showEdges} focus={focus} onSelect={(id) => select(id)} />
        </main>

        {sel && (
          <aside className="w-96 shrink-0 overflow-y-auto border-l p-5 text-sm">
            <div className="flex items-start justify-between gap-3">
              <h2 className="text-base font-semibold leading-snug">{sel.title}</h2>
              <button onClick={() => select(null)} className="text-muted-foreground hover:text-foreground" aria-label="Close">✕</button>
            </div>
            <div className="mt-1 font-mono text-xs text-muted-foreground">{sel.id}</div>
            <dl className="mt-4 grid grid-cols-2 gap-y-2">
              <dt className="text-muted-foreground">Genre</dt><dd>{sel.genre}</dd>
              <dt className="text-muted-foreground">Language</dt><dd className="uppercase">{sel.language}</dd>
               <dt className="text-muted-foreground">Year</dt><dd>{sel.year ?? "Unknown"}</dd>
              <dt className="text-muted-foreground">Words</dt><dd>{sel.words.toLocaleString()}</dd>
            </dl>
            <Tags label="Themes" items={sel.themes} colors={colors} />
            <Tags label="Countries" items={sel.countries} />
            <p className="mt-4 leading-relaxed text-muted-foreground">{sel.snippet}</p>
            <h3 className="mt-6 mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Similar documents</h3>
            <ul className="space-y-1">
              {(neighbours.get(sel.id) ?? []).map(({ id, weight }) => {
                const n = byId.get(id);
                if (!n) return null;
                return (
                  <li key={id}>
                    <button onClick={() => select(id, true)} className="flex w-full items-start gap-2 rounded-md p-2 text-left hover:bg-muted">
                      <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full" style={{ background: colors[n.theme] }} />
                       <span className="flex-1">{n.title}<span className="block text-xs text-muted-foreground">{n.theme} · {n.year ?? "Unknown year"}</span></span>
                      <span className="text-xs tabular-nums text-muted-foreground">{weight.toFixed(2)}</span>
                    </button>
                  </li>
                );
              })}
            </ul>
          </aside>
        )}
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">{title}</h3>
      <div className="space-y-1">{children}</div>
    </div>
  );
}

function Check({ checked, onChange, children }: { checked: boolean; onChange: () => void; children: React.ReactNode }) {
  return (
    <label className="flex cursor-pointer items-center gap-2 rounded px-1 py-0.5 hover:bg-muted">
      <input type="checkbox" className="accent-primary" checked={checked} onChange={onChange} />
      {children}
    </label>
  );
}

function CountryFilter({ all, selected, toggle }: { all: string[]; selected: string[]; toggle: (c: string) => void }) {
  const [q, setQ] = useState("");
  const list = all.filter((c) => c.toLowerCase().includes(q.toLowerCase()));
  return (
    <Section title={`Country${selected.length ? ` (${selected.length})` : ""}`}>
      <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Find a country…"
        className="mb-1 h-8 w-full rounded-md border border-input bg-background px-2 text-sm outline-none focus:border-ring" />
      <div className="max-h-44 overflow-y-auto">
        {list.map((c) => (
          <Check key={c} checked={selected.includes(c)} onChange={() => toggle(c)}>{c}</Check>
        ))}
      </div>
    </Section>
  );
}

function Tags({ label, items, colors }: { label: string; items: string[]; colors?: Record<string, string> }) {
  return (
    <div className="mt-4">
      <div className="mb-1 text-xs text-muted-foreground">{label}</div>
      <div className="flex flex-wrap gap-1.5">
        {items.map((t) => (
          <span key={t} className="inline-flex items-center gap-1.5 rounded-full border bg-secondary px-2.5 py-0.5 text-xs">
            {colors && <span className="h-2 w-2 rounded-full" style={{ background: colors[t] }} />}
            {t}
          </span>
        ))}
      </div>
    </div>
  );
}
