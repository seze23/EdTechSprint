import { useState } from "react";
import type { Draft } from "../api";

export default function PoolPanel({ pool, source }: { pool: Draft[]; source: string }) {
  const [open, setOpen] = useState(false);
  return (
    <section className="card p-4">
      <button onClick={() => setOpen((o) => !o)} className="w-full flex justify-between items-center text-sm">
        <span className="font-semibold">The shared draft pool <span className="font-normal text-slate-500">· {pool.length} drafts · {source}</span></span>
        <span className="text-blue-600 text-xs font-medium">{open ? "hide" : "show"}</span>
      </button>
      {open && (
        <div className="mt-3 grid md:grid-cols-2 gap-3">
          {pool.map((d) => (
            <div key={d.idx} className="rounded-xl bg-blue-50/50 border border-blue-100 p-3 text-xs">
              <div className="font-semibold mb-1">Draft #{d.idx + 1} <span className="font-normal text-slate-500">· final:</span> <span className="font-mono text-[11px] text-blue-800">{d.final_answer || "—"}</span></div>
              <pre className="whitespace-pre-wrap font-sans text-slate-700 mb-2 leading-relaxed">{d.text}</pre>
              <div className="flex flex-wrap gap-1 font-mono text-[10px] text-slate-500">
                {Object.entries(d.features).map(([k, v]) => (
                  <span key={k} className="rounded-md bg-white border border-blue-100 px-1.5 py-0.5">{k}={v.toFixed(2)}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
