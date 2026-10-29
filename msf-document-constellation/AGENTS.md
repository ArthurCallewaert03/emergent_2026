<!-- LOVABLE:BEGIN -->
> [!IMPORTANT]
> This project is connected to [Lovable](https://lovable.dev). Avoid rewriting
> published git history — force pushing, or rebasing/amending/squashing commits
> that are already pushed — as it rewrites history on Lovable's side and the
> user will likely lose their project history.
>
> Commits you push to the connected branch sync back to Lovable and show up in
> the editor, so keep the branch in a working state.
<!-- LOVABLE:END -->

- The map is a custom canvas renderer (src/components/GraphCanvas.tsx) using precomputed x/y; no force layout, so positions match the data file.
- Data source URL lives only in DATA_URL in src/lib/graph.ts; the app is fully client-side with no backend.
