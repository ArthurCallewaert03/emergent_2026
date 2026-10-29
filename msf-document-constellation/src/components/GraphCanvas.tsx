import { useEffect, useMemo, useRef, useState } from "react";
import type { DocNode, Edge } from "@/lib/graph";

interface Props {
  nodes: DocNode[];
  edges: Edge[];
  colors: Record<string, string>;
  alpha: Map<string, number>;
  selectedId: string | null;
  showEdges: boolean;
  focus: { id: string; n: number } | null;
  onSelect: (id: string | null) => void;
}

const WORLD = 1000;

export function GraphCanvas({ nodes, edges, colors, alpha, selectedId, showEdges, focus, onSelect }: Props) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const view = useRef({ k: 1, x: 0, y: 0 });
  const size = useRef({ w: 800, h: 600 });
  const [hover, setHover] = useState<{ n: DocNode; x: number; y: number } | null>(null);
  const drawRef = useRef<() => void>(() => {});

  // Scale precomputed coords into a world box; radius by sqrt(words).
  const layout = useMemo(() => {
    const xs = nodes.map((n) => n.x), ys = nodes.map((n) => n.y);
    const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys);
    const s = WORLD / Math.max(maxX - minX, maxY - minY, 1e-6);
    const maxW = Math.sqrt(Math.max(...nodes.map((n) => n.words), 1));
    const pos = new Map<string, { x: number; y: number; r: number; n: DocNode }>();
    for (const n of nodes)
      pos.set(n.id, {
        x: (n.x - (minX + maxX) / 2) * s,
        y: (n.y - (minY + maxY) / 2) * s,
        r: 2.5 + 7 * (Math.sqrt(n.words) / maxW),
        n,
      });
    return pos;
  }, [nodes]);

  const fit = () => {
    const { w, h } = size.current;
    const k = Math.min(w, h) / (WORLD * 1.1);
    view.current = { k, x: w / 2, y: h / 2 };
  };

  drawRef.current = () => {
    const c = canvasRef.current;
    if (!c) return;
    const ctx = c.getContext("2d")!;
    const dpr = window.devicePixelRatio || 1;
    const { w, h } = size.current;
    const { k, x, y } = view.current;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    ctx.setTransform(dpr * k, 0, 0, dpr * k, dpr * x, dpr * y);
    const edgeColor = getComputedStyle(c).getPropertyValue("--edge") || "gray";
    if (showEdges) {
      ctx.strokeStyle = edgeColor;
      ctx.lineWidth = 0.6 / k;
      for (const e of edges) {
        const a = layout.get(e.source), b = layout.get(e.target);
        if (!a || !b) continue;
        const na = alpha.get(e.source) ?? 1, nb = alpha.get(e.target) ?? 1;
        const sel = selectedId && (e.source === selectedId || e.target === selectedId);
        ctx.globalAlpha = Math.min(na, nb) * (sel ? 0.9 : 0.08 + 0.35 * e.weight);
        ctx.lineWidth = (sel ? 1.4 : 0.6) / k;
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.stroke();
      }
    }
    const rs = 1 / Math.sqrt(k);
    for (const p of layout.values()) {
      ctx.globalAlpha = alpha.get(p.n.id) ?? 1;
      ctx.fillStyle = colors[p.n.theme] ?? "#888";
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r * rs * 1.4, 0, Math.PI * 2);
      ctx.fill();
    }
    const s = selectedId && layout.get(selectedId);
    if (s) {
      ctx.globalAlpha = 1;
      ctx.strokeStyle = "#EE0000";
      ctx.lineWidth = 2.5 / k;
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r * rs * 1.4 + 4 / k, 0, Math.PI * 2);
      ctx.stroke();
    }
    ctx.globalAlpha = 1;
  };

  useEffect(() => drawRef.current());

  // Resize
  useEffect(() => {
    const wrap = wrapRef.current!, c = canvasRef.current!;
    let first = true;
    const ro = new ResizeObserver(() => {
      const r = wrap.getBoundingClientRect();
      size.current = { w: r.width, h: r.height };
      const dpr = window.devicePixelRatio || 1;
      c.width = r.width * dpr;
      c.height = r.height * dpr;
      c.style.width = r.width + "px";
      c.style.height = r.height + "px";
      if (first) { fit(); first = false; }
      drawRef.current();
    });
    ro.observe(wrap);
    return () => ro.disconnect();
  }, []);

  // Wheel zoom anchored at cursor
  useEffect(() => {
    const c = canvasRef.current!;
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      const dy = e.deltaY * (e.deltaMode === 1 ? 16 : e.deltaMode === 2 ? 100 : 1);
      const v = view.current;
      const next = Math.min(40, Math.max(0.05, v.k * Math.exp(-dy * 0.0015)));
      const r = c.getBoundingClientRect();
      const px = e.clientX - r.left, py = e.clientY - r.top, f = next / v.k;
      view.current = { k: next, x: px - (px - v.x) * f, y: py - (py - v.y) * f };
      drawRef.current();
    };
    c.addEventListener("wheel", onWheel, { passive: false });
    return () => c.removeEventListener("wheel", onWheel);
  }, []);

  // Centre on focus
  useEffect(() => {
    if (!focus) return;
    const p = layout.get(focus.id);
    if (!p) return;
    const start = { ...view.current };
    const k = Math.max(start.k, (Math.min(size.current.w, size.current.h) / WORLD) * 2.5);
    const end = { k, x: size.current.w / 2 - p.x * k, y: size.current.h / 2 - p.y * k };
    let raf = 0;
    const t0 = performance.now();
    const step = (t: number) => {
      const u = Math.min(1, (t - t0) / 450), e = 1 - Math.pow(1 - u, 3);
      view.current = { k: start.k + (end.k - start.k) * e, x: start.x + (end.x - start.x) * e, y: start.y + (end.y - start.y) * e };
      drawRef.current();
      if (u < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [focus, layout]);

  const hit = (cx: number, cy: number) => {
    const { k, x, y } = view.current;
    const wx = (cx - x) / k, wy = (cy - y) / k;
    let best: DocNode | null = null, bd = Infinity;
    const rs = 1 / Math.sqrt(k);
    for (const p of layout.values()) {
      const d = Math.hypot(p.x - wx, p.y - wy);
      const r = p.r * rs * 1.4 + 3 / k;
      if (d < r && d < bd) { bd = d; best = p.n; }
    }
    return best;
  };

  const drag = useRef<{ x: number; y: number; moved: boolean } | null>(null);

  return (
    <div ref={wrapRef} className="relative h-full w-full overflow-hidden bg-background">
      <canvas
        ref={canvasRef}
        className="block cursor-grab touch-none active:cursor-grabbing"
        onPointerDown={(e) => {
          drag.current = { x: e.clientX, y: e.clientY, moved: false };
          (e.target as HTMLElement).setPointerCapture(e.pointerId);
        }}
        onPointerMove={(e) => {
          const r = e.currentTarget.getBoundingClientRect();
          if (drag.current) {
            const dx = e.clientX - drag.current.x, dy = e.clientY - drag.current.y;
            if (Math.abs(dx) + Math.abs(dy) > 2) drag.current.moved = true;
            if (drag.current.moved) {
              view.current.x += dx;
              view.current.y += dy;
              drag.current.x = e.clientX;
              drag.current.y = e.clientY;
              setHover(null);
              drawRef.current();
              return;
            }
          }
          const n = hit(e.clientX - r.left, e.clientY - r.top);
          setHover(n ? { n, x: e.clientX - r.left, y: e.clientY - r.top } : null);
        }}
        onPointerUp={(e) => {
          const d = drag.current;
          drag.current = null;
          if (d && !d.moved) {
            const r = e.currentTarget.getBoundingClientRect();
            const n = hit(e.clientX - r.left, e.clientY - r.top);
            onSelect(n ? n.id : null);
          }
        }}
        onPointerLeave={() => setHover(null)}
      />
      {hover && (
        <div
          className="pointer-events-none absolute z-10 max-w-xs rounded-md border bg-popover px-3 py-2 text-xs shadow-lg"
          style={{ left: hover.x + 14, top: hover.y + 14 }}
        >
          <div className="font-medium text-foreground">{hover.n.title}</div>
          <div className="mt-1 text-muted-foreground">
             {hover.n.theme} · {hover.n.year ?? "Unknown year"}
          </div>
        </div>
      )}
      <div className="absolute bottom-4 right-4 flex flex-col overflow-hidden rounded-md border bg-card shadow-sm">
        {[
          ["+", 1.4],
          ["−", 1 / 1.4],
        ].map(([l, f]) => (
          <button
            key={l as string}
            className="h-8 w-8 text-foreground hover:bg-muted"
            onClick={() => {
              const v = view.current, { w, h } = size.current, k = v.k * (f as number);
              view.current = { k, x: w / 2 - (w / 2 - v.x) * (f as number), y: h / 2 - (h / 2 - v.y) * (f as number) };
              drawRef.current();
            }}
          >
            {l}
          </button>
        ))}
        <button className="h-8 w-8 border-t text-[10px] text-muted-foreground hover:bg-muted" onClick={() => { fit(); drawRef.current(); }}>
          fit
        </button>
      </div>
    </div>
  );
}
