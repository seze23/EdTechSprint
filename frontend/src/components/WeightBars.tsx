type Props = { weights: Record<string, number>; title: string; maxAbs?: number };

export default function WeightBars({ weights, title, maxAbs }: Props) {
  const entries = Object.entries(weights);
  const m = maxAbs ?? Math.max(0.01, ...entries.map(([, v]) => Math.abs(v)));
  return (
    <div>
      <div className="text-[11px] uppercase tracking-wider text-slate-500 mb-1.5">{title}</div>
      <div className="space-y-1">
        {entries.map(([name, v]) => {
          const pct = Math.min(100, (Math.abs(v) / m) * 50);
          return (
            <div key={name} className="flex items-center gap-2 text-xs">
              <span className="w-28 text-slate-600 font-mono text-[11px] truncate">{name}</span>
              <div className="relative flex-1 h-2.5 bg-blue-50 rounded-full overflow-hidden">
                <div className="absolute top-0 bottom-0 left-1/2 w-px bg-blue-200" />
                <div
                  className={`absolute top-0 bottom-0 rounded-full ${v >= 0 ? "bg-gradient-to-r from-blue-500 to-sky-400" : "bg-gradient-to-l from-rose-400 to-pink-300"}`}
                  style={v >= 0 ? { left: "50%", width: `${pct}%` } : { right: "50%", width: `${pct}%` }}
                />
              </div>
              <span className="w-12 text-right font-mono text-[11px] text-slate-500">{v.toFixed(2)}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
