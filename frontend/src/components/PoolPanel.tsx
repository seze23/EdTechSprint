import { useState } from "react";
import type { Draft } from "../api";

export default function PoolPanel({ pool, source }: { pool: Draft[]; source: string }) {
  const [open, setOpen] = useState(false);
  return (
    <section className="rounded-xl border border-stone-200 bg-white p-4 shadow-sm">
      <button onClick={() => setOpen((o) => !o)} className="w-full flex justify-between text-sm">
        <span className="font-medium">The shared draft pool ({pool.length} drafts, source: {source})</span>
        <span className="text-stone-400">{open ? "hide" : "show"}</span>
      </button>
      {open && (
        <div className="mt-3 grid md:grid-cols-2 gap-3">
          {pool.map((d) => (
            <div key={d.idx} className="rounded-lg bg-stone-50 border border-stone-100 p-3 text-xs">
              <div className="font-semibold mb-1">Draft #{d.idx + 1} · final: <span className="font-mono">{d.final_answer || "—"}</span></div>
              <pre className="whitespace-pre-wrap font-sans text-stone-700 mb-2">{d.text}</pre>
              <div className="flex flex-wrap gap-1 font-mono text-[10px] text-stone-500">
                {Object.entries(d.features).map(([k, v]) => (
                  <span key={k} className="rounded bg-white border border-stone-200 px-1">{k}={v.toFixed(2)}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
