import { useState } from "react";
import type { Dials, Result, FeedbackOut } from "../api";
import Slider from "./Slider";
import WeightBars from "./WeightBars";

type Props = {
  dials: Dials;
  onDials: (d: Dials) => void;
  result: Result | null;
  loading: boolean;
  feedback: FeedbackOut | null;
  onFeedback: (accepted: boolean) => void;
  onReset: () => void;
};

export default function AgentCard({ dials, onDials, result, loading, feedback, onFeedback, onReset }: Props) {
  const [showTrace, setShowTrace] = useState(false);
  const set = (patch: Partial<Dials>) => onDials({ ...dials, ...patch });
  const profile = feedback?.profile ?? result?.profile ?? null;
  const tradeoff = dials.k >= 0.5 ? "For the problem set due tonight." : "For the exam next month.";

  return (
    <section className="card p-5 flex flex-col gap-4 relative overflow-hidden">
      <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-blue-600 via-sky-400 to-indigo-400" />
      <header className="flex items-start justify-between gap-2">
        <div>
          <input
            value={dials.name}
            onChange={(e) => set({ name: e.target.value })}
            className="text-xl font-semibold tracking-tight bg-transparent border-b border-transparent focus:border-blue-400 outline-none"
            aria-label="Agent name"
          />
          <p className="text-xs text-slate-500 mt-0.5">{tradeoff}</p>
        </div>
        <button onClick={onReset} className="text-xs text-slate-400 hover:text-blue-700 transition">reset learning</button>
      </header>

      <div className="grid grid-cols-1 gap-2.5">
        <Slider left="Learn it" right="Answer now" symbol="k" value={dials.k} onChange={(k) => set({ k })} />
        <Slider left="Just tell me" right="Flag uncertainty" symbol="λ" value={dials.lam} onChange={(lam) => set({ lam })} />
        <Slider left="Surprise me" right="Consistent" symbol="β" value={dials.beta} onChange={(beta) => set({ beta })} />
        <Slider left="Assume" right="Ask first" symbol="ρ" value={dials.rho} onChange={(rho) => set({ rho })} />
      </div>

      <div className="min-h-[8rem] rounded-xl bg-blue-50/40 border border-blue-100 p-3.5 text-sm whitespace-pre-wrap leading-relaxed">
        {loading && <span className="text-slate-400">Scoring the shared draft pool…</span>}
        {!loading && !result && <span className="text-slate-400">Ask something. This agent picks from the same drafts as the other one.</span>}
        {!loading && result && result.ask_first && (
          <div className="mb-3 rounded-lg border border-indigo-200 bg-indigo-50 p-2.5 text-indigo-900">
            <div className="text-[11px] uppercase tracking-wider font-medium">Asks first</div>
            <div className="mt-0.5">{result.clarifying_question}</div>
            <div className="text-[11px] text-indigo-600 mt-1">{result.ask_reason}</div>
          </div>
        )}
        {!loading && result && <div>{result.answer}</div>}
      </div>

      {result && (
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="pill bg-blue-600 text-white">
            {Math.round(result.agreement.share * result.agreement.n)} of {result.agreement.n} drafts agree
          </span>
          <span className="pill bg-blue-50 text-blue-800 font-mono font-normal text-[11px]">
            margin {result.margins[result.chosen].toFixed(2)} · P {(result.probs[result.chosen] * 100).toFixed(0)}%
          </span>
          <button onClick={() => setShowTrace((s) => !s)} className="ml-auto text-blue-700 font-medium hover:underline">
            {showTrace ? "hide" : "why this draft?"}
          </button>
        </div>
      )}

      {result && showTrace && (
        <div className="rounded-xl border border-blue-100 bg-white p-3.5 space-y-3">
          <WeightBars title="what pushed this draft across the line (w·f per feature)" weights={result.contributions} />
          <div className="text-[11px] text-slate-500 font-mono">
            by margin:{" "}
            {result.margins
              .map((m, i) => ({ m, i }))
              .sort((a, b) => b.m - a.m)
              .map(({ m, i }) => `#${i + 1}:${m.toFixed(2)}`)
              .join("  ")}
          </div>
        </div>
      )}

      {result && (
        <div className="flex gap-2">
          <button onClick={() => onFeedback(true)} className="btn-primary flex-1 py-2.5 text-sm">Accept</button>
          <button onClick={() => onFeedback(false)} className="flex-1 rounded-xl border border-rose-200 bg-white text-rose-600 font-medium py-2.5 text-sm hover:bg-rose-50 transition">Reject</button>
        </div>
      )}

      {profile && (
        <div className="rounded-xl border border-blue-100 bg-white p-3.5 space-y-2">
          <div className="flex justify-between text-xs text-slate-500">
            <span>Profile drift after {profile.n_feedback} judgment{profile.n_feedback === 1 ? "" : "s"}</span>
            <span className="font-mono text-[11px]">η⁺ {profile.eta_pos.toFixed(2)} · η⁻ {profile.eta_neg.toFixed(2)}{feedback?.eta_refit ? " (re-fit)" : ""}</span>
          </div>
          <WeightBars title="learned correction to the hyperplane" weights={profile.w_learned_named} maxAbs={1} />
          {feedback && (
            <div className="text-xs text-slate-500">
              {feedback.step.surprised
                ? `That judgment was inside the margin, so the weights moved by η = ${feedback.step.eta.toFixed(2)}.`
                : "That judgment was already predicted; the weights did not move."}{" "}
              {feedback.support_vectors.length} of {feedback.n_events} past judgments are support vectors.
            </div>
          )}
        </div>
      )}
    </section>
  );
}
