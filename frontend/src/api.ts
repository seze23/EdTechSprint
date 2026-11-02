export const API_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000";

export type Dials = { id: string; name: string; k: number; lam: number; beta: number; rho: number };

export type ProfileOut = Dials & {
  eta_pos: number;
  eta_neg: number;
  b: number;
  n_feedback: number;
  w_prior: Record<string, number>;
  w_total: Record<string, number>;
  w_learned_named: Record<string, number>;
  inverse_temperature: number;
};

export type Draft = { idx: number; text: string; final_answer: string; features: Record<string, number> };

export type Result = {
  profile: ProfileOut;
  chosen: number;
  answer: string;
  final_answer: string;
  agreement: { share: number; n: number };
  margins: number[];
  normalised_margins: number[];
  probs: number[];
  ask_first: boolean;
  ask_reason: string;
  clarifying_question: string | null;
  contributions: Record<string, number>;
};

export type AskOut = { prompt_id: number; source: string; features: string[]; pool: Draft[]; results: Result[] };

export type FeedbackOut = {
  profile: ProfileOut;
  step: { surprised: boolean; margin_before: number; y: number; eta: number; delta_w: Record<string, number> };
  eta_refit: boolean;
  n_events: number;
  support_vectors: number[];
};

async function post<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`${path}: ${r.status} ${await r.text()}`);
  return r.json();
}

export const ask = (prompt: string, profiles: Dials[]) => post<AskOut>("/ask", { prompt, profiles });
export const sendFeedback = (prompt_id: number, profile_id: string, draft_idx: number, accepted: boolean) =>
  post<FeedbackOut>("/feedback", { prompt_id, profile_id, draft_idx, accepted });
export const resetProfile = (id: string) => post<{ profile: ProfileOut }>(`/profile/${id}/reset`, {});
export const health = () => fetch(`${API_URL}/health`).then((r) => r.json() as Promise<{ ok: boolean; mock_mode: boolean; model: string; db: string }>);
