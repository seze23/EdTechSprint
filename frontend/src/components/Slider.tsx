type Props = { left: string; right: string; value: number; onChange: (v: number) => void; symbol: string };

export default function Slider({ left, right, value, onChange, symbol }: Props) {
  return (
    <label className="block text-xs">
      <div className="flex justify-between items-baseline text-slate-500">
        <span className="font-medium text-slate-600">{left}</span>
        <span className="font-mono text-[11px] text-blue-700/80">{symbol} = {value.toFixed(2)}</span>
        <span className="font-medium text-slate-600">{right}</span>
      </div>
      <input
        type="range" min={0} max={1} step={0.05} value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full"
      />
    </label>
  );
}
