type Props = { weights: Record<string, number>; title: string; maxAbs?: number };

export default function WeightBars({ weights, title, maxAbs }: Props) {
  const entries = Object.entries(weights);
  const m = maxAbs ?? Math.max(0.01, ...entries.map(([, v]) => Math.abs(v)));
  return (
    <div>
      <div className="text-xs uppercase tracking-wide text-stone-500 mb-1">{title}</div>
      <div className="space-y-1">
        {entries.map(([name, v]) => {
          const pct = Math.min(100, (Math.abs(v) / m) * 50);
          return (
            <div key={name} className="flex items-center gap-2 text-xs">
              <span className="w-28 text-stone-600 font-mono truncate">{name}</span>
              <div className="relative flex-1 h-3 bg-stone-100 rounded">
                <div className="absolute top-0 bottom-0 left-1/2 w-px bg-stone-300" />
                <div
                  className={`absolute top-0 bottom-0 rounded ${v >= 0 ? "bg-emerald-500" : "bg-rose-500"}`}
                  style={v >= 0 ? { left: "50%", width: `${pct}%` } : { right: "50%", width: `${pct}%` }}
                />
              </div>
              <span className="w-12 text-right font-mono text-stone-500">{v.toFixed(2)}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
