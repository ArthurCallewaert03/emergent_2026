# MSF Document Constellation

An interactive document knowledge graph for the D4GC 2026 research workspace.
Use it to find potentially related documents after identifying a useful source
with the [Document Navigator and RAG workflow](../README.md#research-workflow).
The goal is to move quickly from a specific finding to a broader set of sources
for further reading and research.

## Run locally

With Node.js and npm installed, run these commands from the repository root:

```powershell
cd msf-document-constellation
npm install
npm run dev
```

Open the URL printed by the development server. Run the Python Navigator in a
separate terminal using the [root setup instructions](../README.md#launch-the-document-navigator).

## Explore related documents

1. Select a document on the map, or append `/?doc=<document-id>` to the app's
   origin to open a document whose ID exists in the graph dataset.
2. Read its title, ID, metadata, and snippet in the detail panel.
3. Follow **Similar documents** to select and centre a connected document.
   This list is ordered by the supplied connection weight, highest first.
4. Narrow the map with theme, genre, language, country, and year filters.
   Search matches text in titles and snippets. Unknown publication years remain
   visible when filtering by year.
5. Use **Show connections** to toggle edges and **Reset filters** to clear the
   filters. Close the detail panel to leave the selected document's neighbourhood.

Filters dim nonmatching nodes. Selecting a document also dims nodes outside its
connected neighbourhood. The **Similar documents** list uses all supplied
neighbours of that document, independently of the map filters.

Use document IDs to find corresponding sources in
[`../data/corpus/Parsed/`](../data/corpus/Parsed/) and
[`../data/corpus/Original/`](../data/corpus/Original/), where present.
The graph displays metadata and snippets; original-source reading and RAG answers
are handled separately. Connections and visual proximity suggest research leads;
they do not establish that a document supports a particular answer.

## Graph data and integration

- [`src/lib/graph.ts`](src/lib/graph.ts) exports `DATA_URL`, using the URL stored
  in [`src/assets/knowledge_graph_msf.json.asset.json`](src/assets/knowledge_graph_msf.json.asset.json).
  The browser fetches this remote JSON when the map loads, requiring network access.
- The dataset supplies `meta`, document `nodes`, and weighted `edges`. Nodes include
  document IDs, titles, snippets, metadata, and precomputed `x`/`y` coordinates.
  Edges contain `source`, `target`, and `weight`; the app treats them as bidirectional.
- [`GraphCanvas.tsx`](src/components/GraphCanvas.tsx) renders those coordinates
  directly. The app does not calculate a new graph layout or similarity scores.
- The graph is a separate dataset from the Python corpus and enriched CSV. There
  is currently no automatic refresh pipeline, RAG service connection, or automatic
  transfer of graph neighbours into an answer's retrieved context. Document IDs
  provide the manual link between the two tools.
- To serve a full dataset locally, place a compatible JSON file under `public/data/`
  and set `DATA_URL` in `src/lib/graph.ts` to its public path, such as
  `/data/knowledge_graph_msf.json`. The included `public/data/msf-sample.json` is a
  sample, not an automatic fallback for the remote dataset.

## Development

Built with React, TypeScript, TanStack Start, Vite, and Tailwind CSS. Graph loading,
filtering, and navigation happen in the browser.

Run these commands inside `msf-document-constellation/`:

```powershell
npm run build
npm run preview
npm run test
npm run lint
```

The project was created with Lovable. See [AGENTS.md](AGENTS.md) for repository
guidance, including preserving published Git history when working with Lovable sync.
