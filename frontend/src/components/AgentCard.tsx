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
  const tradeoff = dials.k >= 0.5 ? "Optimised for the problem set due tonight." : "Optimised for the exam next month.";

  return (
    <section className="rounded-xl border border-stone-200 bg-white p-4 flex flex-col gap-4 shadow-sm">
      <header className="flex items-start justify-between gap-2">
        <div>
          <input
            value={dials.name}
            onChange={(e) => set({ name: e.target.value })}
            className="text-lg font-semibold bg-transparent border-b border-transparent focus:border-stone-400 outline-none"
            aria-label="Agent name"
          />
          <p className="text-xs text-stone-500">{tradeoff}</p>
        </div>
        <button onClick={onReset} className="text-xs text-stone-400 hover:text-stone-700 underline">reset learning</button>
      </header>

      <div className="grid grid-cols-1 gap-2">
        <Slider left="Learn it" right="Answer now" symbol="k" value={dials.k} onChange={(k) => set({ k })} />
        <Slider left="Just tell me" right="Flag uncertainty" symbol="λ" value={dials.lam} onChange={(lam) => set({ lam })} />
        <Slider left="Surprise me" right="Consistent" symbol="β" value={dials.beta} onChange={(beta) => set({ beta })} />
        <Slider left="Assume" right="Ask first" symbol="ρ" value={dials.rho} onChange={(rho) => set({ rho })} />
      </div>

      <div className="min-h-[8rem] rounded-lg bg-stone-50 border border-stone-100 p-3 text-sm whitespace-pre-wrap leading-relaxed">
        {loading && <span className="text-stone-400">Scoring the shared draft pool…</span>}
        {!loading && !result && <span className="text-stone-400">Ask something and this agent will pick from the same drafts as the other one.</span>}
        {!loading && result && result.ask_first && (
          <div className="mb-3 rounded-md border border-amber-300 bg-amber-50 p-2 text-amber-900">
            <div className="text-xs uppercase tracking-wide">Asks first</div>
            <div>{result.clarifying_question}</div>
            <div className="text-xs text-amber-700 mt-1">{result.ask_reason}</div>
          </div>
        )}
        {!loading && result && <div>{result.answer}</div>}
      </div>

      {result && (
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="rounded-full bg-stone-900 text-white px-2 py-0.5">
            {Math.round(result.agreement.share * result.agreement.n)} of {result.agreement.n} drafts agree
          </span>
          <span className="rounded-full bg-stone-100 px-2 py-0.5 font-mono">
            margin {result.margins[result.chosen].toFixed(2)} · P(pick) {(result.probs[result.chosen] * 100).toFixed(0)}%
          </span>
          <button onClick={() => setShowTrace((s) => !s)} className="ml-auto underline text-stone-500">
            {showTrace ? "hide" : "why this draft?"}
          </button>
        </div>
      )}

      {result && showTrace && (
        <div className="rounded-lg border border-stone-200 p-3 space-y-3">
          <WeightBars title="what pushed this draft across the line (w·f per feature)" weights={result.contributions} />
          <div className="text-xs text-stone-500 font-mono">
            drafts ranked by margin:{" "}
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
          <button onClick={() => onFeedback(true)} className="flex-1 rounded-md bg-emerald-600 text-white py-2 text-sm hover:bg-emerald-700">Accept</button>
          <button onClick={() => onFeedback(false)} className="flex-1 rounded-md bg-rose-600 text-white py-2 text-sm hover:bg-rose-700">Reject</button>
        </div>
      )}

      {profile && (
        <div className="rounded-lg border border-stone-200 p-3 space-y-2">
          <div className="flex justify-between text-xs text-stone-500">
            <span>Profile drift after {profile.n_feedback} judgment{profile.n_feedback === 1 ? "" : "s"}</span>
            <span className="font-mono">η⁺ {profile.eta_pos.toFixed(2)} · η⁻ {profile.eta_neg.toFixed(2)}{feedback?.eta_refit ? " (re-fit)" : ""}</span>
          </div>
          <WeightBars title="learned correction to the hyperplane" weights={profile.w_learned_named} maxAbs={1} />
          {feedback && (
            <div className="text-xs text-stone-500">
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
