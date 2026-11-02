import { useEffect, useState } from "react";
import { ask, health, resetProfile, sendFeedback, type AskOut, type Dials, type FeedbackOut } from "./api";
import AgentCard from "./components/AgentCard";
import PoolPanel from "./components/PoolPanel";

const DEFAULTS: Dials[] = [
  { id: "sprint", name: "Sprint", k: 0.9, lam: 0.15, beta: 0.85, rho: 0.0 },
  { id: "coach", name: "Coach", k: 0.15, lam: 0.85, beta: 0.5, rho: 0.7 },
];

const STRIPE_LINK = (import.meta.env.VITE_STRIPE_LINK as string | undefined) ?? "#";

export default function App() {
  const [dials, setDials] = useState<Dials[]>(DEFAULTS);
  const [prompt, setPrompt] = useState("Solve 3x + 7 = 22 for x");
  const [out, setOut] = useState<AskOut | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<Record<string, FeedbackOut | null>>({});
  const [status, setStatus] = useState<{ ok: boolean; mock_mode: boolean; model: string; db: string } | null>(null);

  useEffect(() => { health().then(setStatus).catch(() => setStatus(null)); }, []);

  async function run() {
    setLoading(true); setError(null); setFeedback({});
    try { setOut(await ask(prompt, dials)); }
    catch (e) { setError((e as Error).message); }
    finally { setLoading(false); }
  }

  async function judge(profileId: string, accepted: boolean) {
    if (!out) return;
    const r = out.results.find((x) => x.profile.id === profileId);
    if (!r) return;
    try { setFeedback((f) => ({ ...f, [profileId]: null })); const fb = await sendFeedback(out.prompt_id, profileId, r.chosen, accepted); setFeedback((f) => ({ ...f, [profileId]: fb })); }
    catch (e) { setError((e as Error).message); }
  }

  async function reset(profileId: string) {
    await resetProfile(profileId);
    setFeedback((f) => ({ ...f, [profileId]: null }));
  }

  function addAgent() {
    const n = dials.length + 1;
    setDials([...dials, { id: `agent${n}`, name: `Agent ${n}`, k: 0.5, lam: 0.5, beta: 0.5, rho: 0.3 }]);
  }

  return (
    <main className="max-w-6xl mx-auto px-4 py-10 space-y-6">
      <header className="space-y-2">
        <h1 className="text-3xl md:text-4xl font-bold tracking-tight bg-gradient-to-r from-blue-800 via-blue-600 to-sky-500 bg-clip-text text-transparent">Two agents, one prompt.</h1>
        <p className="text-sm text-slate-600 max-w-2xl">
          Both agents read the same drafts. They differ only in how they value them. <strong>They are deliberately different</strong>:
          one is tuned for the problem set due tonight, the other for the exam next month. You set the dials, and each accept or reject
          moves that agent's decision boundary.
        </p>
        <div className="text-xs text-slate-500">
          {status === null && <span className="text-rose-600 font-medium">Backend not reachable. Start it with <code>uvicorn app.main:app --reload</code> in <code>backend/</code>.</span>}
          {status && `${status.mock_mode ? "Mock mode: canned drafts, no API credits used." : `Drafts from ${status.model}.`} Log store: ${status.db}.`}
        </div>
      </header>

      <form onSubmit={(e) => { e.preventDefault(); run(); }} className="flex gap-2">
        <input
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          className="flex-1 rounded-xl border border-blue-200 bg-white/90 px-4 py-2.5 text-sm shadow-card focus:outline-none focus:ring-2 focus:ring-blue-400"
          placeholder="Paste a homework prompt"
        />
        <button type="submit" disabled={loading || !prompt.trim()} className="btn-primary px-5 py-2.5 text-sm">
          {loading ? "Thinking…" : "Ask both"}
        </button>
      </form>
      {error && <div className="text-sm text-rose-700 bg-rose-50 border border-rose-200 rounded-xl p-3">{error}</div>}

      <div className={`grid gap-4 ${dials.length > 2 ? "md:grid-cols-3" : "md:grid-cols-2"}`}>
        {dials.map((d, i) => (
          <AgentCard
            key={d.id}
            dials={d}
            onDials={(nd) => setDials(dials.map((x, j) => (j === i ? nd : x)))}
            result={out?.results.find((r) => r.profile.id === d.id) ?? null}
            loading={loading}
            feedback={feedback[d.id] ?? null}
            onFeedback={(a) => judge(d.id, a)}
            onReset={() => reset(d.id)}
          />
        ))}
      </div>
      {dials.length < 3 && (
        <button onClick={addAgent} className="text-sm text-blue-700 font-medium hover:underline">+ add a third agent</button>
      )}

      {out && <PoolPanel pool={out.pool} source={out.source} />}

      <footer className="card p-4 text-sm text-slate-600 flex flex-wrap items-center gap-3">
        <span className="font-semibold text-slate-900">One flat price.</span>
        <span>Cancel in one click. No steps behind a paywall. Free while this is a demo.</span>
        <a href={STRIPE_LINK} className="btn-ghost ml-auto px-3 py-1.5 text-sm">Support the build</a>
      </footer>
    </main>
  );
}
