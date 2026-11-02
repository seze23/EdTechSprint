# The selector as a support vector machine

The spec's selector was a softmax over a linear utility. Keeping the softmax, the
cleanest interpretable version of that utility is an SVM decision function. This
note says exactly what was stitched together and what each dial does to it.

## Agreement is a cluster share, not a string match

Numeric final answers agree when they are numerically equal. Prose answers agree
when their content tokens (lower-cased, stop words and parentheticals removed,
lightly stemmed) overlap with containment ≥ 0.6. Drafts are clustered by
union-find and each draft's `agreement` is its cluster's share of the pool. No
model call, so the number is reproducible from the logged text.

## One hyperplane per agent

Every draft `i` gets a deterministic feature vector `f_i` in roughly `[0,1]^9`
(`backend/app/features.py`). A profile is a hyperplane `(w, b)`. The utility of a
draft is its signed distance to that hyperplane, the SVM margin:

    margin_i = w · f_i + b
    w = w_prior(k, λ, ρ) + w_learned

Drafts on the positive side are ones this student is predicted to accept.

| Dial | What it does to the hyperplane |
| --- | --- |
| k (discount) | `w_prior` puts `2k` on pay-off-now features (`answer_first`, `brevity`) and `2(1−k)` on pay-off-later features (`n_steps`, `self_check`, `understanding`) |
| λ (loss aversion) | weight on `agreement` is `0.5 + 2.5λ`; weight on `hedges` is `2(λ − 0.5)`, so low λ punishes hedging and high λ rewards it |
| β (inverse temperature) | sharpness of the softmax over margins, `P(i) ∝ exp(β · margin_i)`; mapped to `[0.5, 12]` on a log scale |
| ρ (information bonus) | width of an uncertainty band, `0.5ρ`, in units of normalised margin: if the separation between the best and second-best draft along the normal, `(m₁ − m₂) / ‖w‖`, is inside the band and the pool disagrees on the answer, the agent asks one clarifying question first |

`math_ok` carries a fixed weight of 1.5 for every profile. Correctness is not a dial.

## Learning is the hinge loss with two learning rates

On accept (`y = +1`) or reject (`y = −1`) of the chosen draft:

    if y · margin < 1:                      # inside the margin or on the wrong side
        w_learned ← (1 − η_y·0.01) w_learned + η_y · y · f
        b         ← b + η_y · y
    else:
        w_learned ← (1 − η_y·0.01) w_learned   # already predicted; only shrink

This is Pegasos-style SGD on a linear SVM. The spec's reward-prediction-error
flavour is the `if`: an outcome only moves the weights when it was surprising.
`η⁺` and `η⁻` are the asymmetric learning rates from the rGT model.

## η is fit, not set

After five judgments, `(η⁺, η⁻)` is chosen from a grid by replaying the student's
own log from the dial prior and maximising the log-likelihood of their
accept/reject sequence under `P(accept) = σ(margin)`. Same procedure as fitting a
rodent's choice sequence, with the student's verdicts as the choices. The frontend
reports the re-fit when it happens.

## Interpretation, which is the point

* **Why this draft:** the per-feature contributions `w_j · f_ij` sum to the margin.
  The UI shows them as signed bars.
* **Which past judgments matter:** the logged events with `y · margin ≤ 1` under the
  current hyperplane are the support vectors. Everything else could be deleted
  without moving the boundary. The UI reports how many there are.
* **Divergence is valuation, not generation:** both agents score the same pool, so
  a different pick is a different hyperplane, nothing else. Every pick is
  reproducible from the logged feature vectors, dials and seed.

## What this is not

Not a kernel SVM, not a batch QP solve, not neuromorphic hardware. It is a linear
margin classifier updated online with brain-derived parameters. If a reviewer
presses, say "online linear SVM with asymmetric learning rates and a softmax policy".
