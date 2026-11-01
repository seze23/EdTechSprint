# Decision-Profile Agents: Neuromorphic Tie and Proof of Concept

Oct 28, 2026 · @syd

## The idea in one paragraph

An AI agent should have a decision profile instead of  a hidden default to promote interpretability and ensure human alignment. The profile is a small set of parameters that computational neuroscience has already shown to be real, measurable, and different from one individual to the next: how steeply the agent discounts future value, how much it weighs a loss against a gain, how deterministic its choices are, and how much it pays to seek information before acting. The proof of concept is a study tool where two agents answer the same homework prompt under two profiles, the student sees the fast answer and the explanation side by side, sets the decision-making engine parameter dial, and the profile is re-fit from what they accept and reject.

## What "neuromorphic" means here, and what it does not

The tie is algorithmic. Strictly, neuromorphic computing means chips (or at least popularly this is what people understand it to be) built to mimic neural structure: spiking neurons, event-driven signalling, memristive synapses (Intel Loihi, SpiNNaker, IBM TrueNorth). This project does not run on that hardware and should not claim to.

The decision algorithm inside the agent is the one the **mammalian reward circuit** implements, with the parameters the brain actually varies. Three specific links hold.

1. Temporal-difference reinforcement learning is not an analogy for dopamine; midbrain dopamine neurons fire a reward-prediction error that matches the TD error term (Schultz, Dayan & Montague, 1997). The agent updates value estimates with the same error signal.
2. **The parameters are the brain's, and they vary per individual.** Learning rate, inverse temperature, loss aversion, temporal discounting, and exploration bonus are each recoverable from choice behavior in humans, non human primates, and rodents. Each cognitive function has a candidate neural circuit/brain region, and each differs reliably across individuals and states. The agent inherits the parameters and the variation.
3. **Context gates the decision.** Wu, Litwin-Kumar, Shadlen & Axel result (Neuron, 2020); The agent's profile/decision-making strategy is held context. **The same prompt yields a different output depending on it.**

If a reviewer presses on the word, the honest substitute is "brain-derived decision computation." Running the selector on spiking hardware is possible later (reinforcement learning on Loihi exists) but is not part of this project.

## The decision model in the brain

Five parameters, each identifiable from behavior alone, each with a circuit and a literature. These are the only parameters the agent exposes; everything else is fixed.

| Parameter | What it controls in behavior | How it is measured | Candidate circuit | Key references |
| --- | --- | --- | --- | --- |
| Learning rates η⁺ / η⁻ | How much a better-than-expected vs. worse-than-expected outcome shifts the value of an option | Fit to trial-by-trial choices in bandit and gambling tasks | Dopamine prediction error acting on striatal D1 (go) and D2 (no-go) pathways | Schultz, Dayan & Montague 1997; Frank's OpAL model; Lefebvre et al. 2017 |
| Inverse temperature β | How deterministic choice is given the value difference between options | Softmax fit to choice probabilities; separable from η with enough trials | Striatal and prefrontal gain; reduced in some clinical states | Daw et al. 2006; Niv et al. 2012 |
| Loss aversion λ | How much a loss weighs relative to an equal gain | Mixed-gamble acceptance tasks; prospect-theory fit | Amygdala and ventral striatum; modulated by reappraisal | Tom et al. 2007; Sokol-Hessner et al. 2009 |
| Temporal discounting k | How steeply future value is discounted | Intertemporal-choice tasks; hyperbolic fit | Ventral striatum and vmPFC track discounted value | Kable & Glimcher 2007 |
| Directed exploration (information bonus) | Willingness to choose an uncertain option to learn about it, distinct from random choice | Horizon task separates information-seeking from β | Frontopolar cortex and rostrolateral PFC | Wilson et al. 2014; Gershman 2018 |

Two results from my own data motivate the design. First, on the rGT the parameters are not interchangeable: residuals on two option-value parameters are bimodal and η⁺ trajectories differ by sex, so a single average profile would misdescribe most animals. Second, the parameters trade off against each other during fitting (β against η in particular), which is why the agent exposes four as sliders and fits the fifth from feedback rather than letting a user set all five.

A caution from the literature: Collins and colleagues have shown that working memory contributes to what bandit tasks label "reinforcement learning," so a fitted η partly absorbs a memory process the model does not name. For the agent this is a feature (the profile should absorb the user's short-horizon behavior) but it means η should be reported as a behavioral parameter, not a claim about mechanism.

## The same model inside an agent

The rGT pipeline runs the model backward: observe choices, recover parameters. The agent runs it forward: given parameters, choose. Nothing in the equations changes; only what is known and what is solved for.

The agent's choice is over candidate outputs rather than levers. For a prompt, the system draws N drafts from the language model, scores each draft on a few deterministic features, converts those features into a value through the profile's parameters, and chooses by softmax. Feedback (accept or reject) is the reward, and the profile's feature weights update by η.

```latex
U_i = \sum_j w_j f_{ij}, \qquad P(i) = \frac{e^{\beta U_i}}{\sum_k e^{\beta U_k}}, \qquad w_j \leftarrow w_j + \eta^{\pm}\,(r - \hat r)\, f_{ij}
```

| Brain parameter | What it becomes in the agent | What the student sees |
| --- | --- | --- |
| Temporal discounting k | Weight on features that pay off now (final answer up front, short) vs. later (worked steps, a check for understanding) | "Answer now ↔ Learn it" |
| Loss aversion λ | Penalty on low agreement among candidates; above a threshold the agent hedges or shows the disagreement rather than asserting | "Just tell me ↔ Flag uncertainty" |
| Inverse temperature β | Sharpness of the softmax over candidate values; low β varies, high β converges | "Consistent ↔ Surprise me" |
| Information bonus | Probability of asking one clarifying question before answering when candidates diverge | "Assume ↔ Ask first" |
| Learning rates η⁺ / η⁻ | How much an accept vs. a reject shifts the feature weights | Not a slider; shown as profile drift over a session |

The features are cheap and deterministic so the choice is auditable: token length, number of explanation steps, position of the final answer, count of hedges, count of questions asked, whether a self-check was performed, and for math the extracted final answer. Agreement is the fraction of candidates sharing the modal final answer. Two profiles that see the same N drafts and choose differently are the demonstration that the divergence is a decision, not a prompt trick.

## **The proof of concept: a study tool with two agents**

A student types one homework prompt and gets two answers from two agents with different profiles, side by side, each labelled with the tradeoff it is making.

- **Sprint** (working name): high k, low λ, high β. Final answer first, short, no hedging. Optimized for the problem set due tonight.
- **Coach** (working name): low k, high λ, information bonus on. Worked steps, a check for understanding, a clarifying question when the candidates disagree. Optimized for the exam next month.
- Each agent card shows four sliders and the current parameter values. The student can move them, rename the agents, or add a third.
- Each answer carries an agreement score ("4 of 5 drafts agree") instead of a confidence claim.
- Under each answer: accept or reject. Over a session, the profile card shows how the student's feedback has moved η-weighted feature weights.
- Pricing and terms are stated in the interface: one flat price, cancel in one click, no steps gated behind a paywall.

The student is told going in that the two agents are deliberately different. That disclosure is the product, not a disclaimer: the only tradeoff that matters in a study tool (answer now vs. understand later) is made explicit and handed to the person it belongs to.

Education is the first application because the buyer is reachable this week (classmates with problem sets due), the demo is legible in thirty seconds, and the discount-rate slider is a complete product thesis on its own. Healthcare triage (the loss-aversion slider on a clinical agent) and legal intake are later verticals with the same engine and a different feature map.

## System architecture and the learning loop

&#91;embedded content: selector architecture · one pool, two profiles, one feedback loop\]

Both selectors see the same N drafts. The divergence between Sprint and Coach is therefore a difference in valuation, not in generation, and every choice is reproducible from the logged feature vectors and parameters.

Everything below here is a massive WIP:

- **Stack.** FastAPI backend; SQLite logging every prompt, candidate, feature vector, selection, and feedback event; a Haiku-class model for drafts at temperature \~0.9; a deterministic Python feature extractor; `sympy` for a numeric sanity check on math where possible; a single-page frontend; a Stripe payment link. No auth beyond a magic link, no mobile.
- **Cost.** Input tokens are identical for both agents; output tokens scale with N per agent. N = 4 for the demo, N = 3 if latency bites.
- **Learning loop.** Accept or reject is the reward. The profile's feature weights move by η⁺ on accept and η⁻ on reject; η is fit per student from the log rather than set. After five interactions the profile card shows the drift, which is the visible claim that the tool adapts.
- **Auditability.** Because the features are deterministic and the selection is a softmax over logged values, any output can be traced to the drafts it beat and the parameters that decided it. That is the property no hated study tool has.

## Why it survives the market

Students hate AI study tools for reasons that are consistent across 1-star reviews and surveys, and almost none of them are about AI being bad at teaching. Every hated tool hides a tradeoff. This product's premise is the one tradeoff that matters, made explicit.

| What students hate | Evidence | How the design answers it |
| --- | --- | --- |
| Confident wrong answers | Top complaint across tutor apps (\~27% of 1-star reviews); accuracy is the top AI concern for 74% of students and 73% of teachers | Agreement score across N drafts shown on every answer; high-λ profile hedges or shows the disagreement |
| Bait-and-paywall: free scan, steps locked, weekly auto-charge, no refund | \~30% of negative education-app reviews are about subscriptions; Gauth sits at 2.1/5 on independent review sites | One flat price (free as a demo for now); cancel in one click, no gated steps, stated in the interface |
| Answer machines that call themselves tutors | "The AI tutor doesn't seem to have a plan for me"; students repeat the same error for weeks | The teach-vs-answer tradeoff is labelled on each agent and set by the student |
| Fake adaptivity | "Adaptive learning often feels like random content selection" | η is fit from the student's own accepts and rejects; drift is shown, not asserted |
| Shame and mixed messages | 55.8% of 8,021 surveyed students name scepticism as their main emotion about AI; 8 in 10 Gen Z think faster AI makes learning harder; 5% feel aware of their institution's guidelines | Positioned as a study tool that tells you which mode you are in, so a student can choose to learn and prove it |
| "Responsible mode" as a toggle | ChatGPT Study Mode can be switched off in one click; critics say it rearranges behavior without addressing hallucination or overreliance | Both modes are always visible; the choice is the interface, not a hidden setting |

The willingness-to-pay question is open and is the point of the week. Sources for the table are listed at the end.

**Market and ed tech**

- [Gauth vs Question AI: 5 AI tutor apps ranked by 1-star reviews](https://unstar.app/blog/gauth-question-ai-answer-ai-studdy-brainly-ai-homework-tutor-apps-ranked-2026)
- [Education app reviews: what students and teachers complain about](https://unstar.app/blog/education-learning-app-reviews-what-students-teachers-complain-about-2026)
- [Gauth AI review 2026](https://www.myengineeringbuddy.com/blog/gauth-reviews-alternatives-pricing-offerings-in-2026/)
- [AI is making students more paranoid — Up Learn survey](https://www.yorkshirepost.co.uk/must-read/ai-in-schools-concerns-9010850)
- [Students hate AI, and they can't stop using it](https://leonfurze.com/2026/05/29/students-hate-ai-and-they-cant-stop-using-it/)
- [Gen Z growing more cautious about AI in education — Walton/Gallup](https://www.meritalkslg.com/?p=27483)
- [ChatGPT Study Mode: mixed reactions](https://www.datastudios.org/post/chatgpt-s-new-study-mode-mixed-reactions-among-students-teachers-and-tech-users)
- [DiCerbo, Cheng & Whitmer (2026), Applying Evidence-Centered Design to automated evals of AI-powered assessment systems, AIME-Con](https://aclanthology.org/2026.aimecon-wip.42.pdf)
- [What is an AI agent registry — Atlan](https://atlan.com/know/ai-agent/what-is-an-ai-agent-registry/)
- [Every AI agent registry in 2026, compared](https://dev.to/aiiaro/every-ai-agent-registry-in-2026-compared-122o)
- [That's a wrap: the YC x Medplum hackathon (Lamina)](https://www.medplum.com/blog/yc-medplum-hackathon-2026-recap)
