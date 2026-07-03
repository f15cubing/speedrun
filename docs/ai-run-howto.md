# How to run the AI card pipeline (for the demo)

> The AI system is a **build-time content pipeline** (PRD §9): it generates GRE-math
> flashcards from a source chapter with RAG + provenance + verification, and scores the
> batch against a pre-lodged gold-set gate. This is the "AI run" you show on camera.
>
> **Honesty posture (say it out loud): AI-off.** No live-model API key is wired in this
> build, so the full machinery runs on a **deterministic stub** standing in for the LLM.
> Every number below validates the **machinery** (RAG + CAS verify + abstention + the
> gate + McNemar), **not** a live model. Do not claim a live model — that's the whole
> point of the honesty framing.

---

## TL;DR — the two commands to run on camera

From the repo root (`/Users/felipecaicedo/Desktop/alpha/speedrun`):

```bash
# 1) Generate + verify + gate (writes pipeline/aicards/out/gate_report.{json,md})
make ai-gate

# 2) Beat-the-baseline (McNemar) + AI-off degradation proof
make ai-baseline
```

Both are **deterministic** (seed 42) and need only Python + SymPy. If your default
`python3` lacks SymPy, point the targets at the pipeline venv:

```bash
AI_PY=/Users/felipecaicedo/Desktop/alpha/speedrun/.venv/bin/python make ai-gate
AI_PY=/Users/felipecaicedo/Desktop/alpha/speedrun/.venv/bin/python make ai-baseline
```

(One-time venv, if needed: `python3 -m venv .venv && . .venv/bin/activate && pip install -r pipeline/requirements.txt`.)

Optional — run the 76-test suite live to prove the machinery is real:

```bash
make ai-gate-test
```

---

## What `make ai-gate` shows (and what to narrate)

It runs the pipeline on the stub, scores the pre-lodged gate, and runs the leakage
firewall. Expected output (seed 42):

- **`AI ACCESS: AI-off (no live model API key)`** ← read this out; it's the honest label.
- **50 candidates → 35 published · 5 human-review drafts · 10 abstained**
  (4 wrong-fact caught by SymPy CAS · 3 ungrounded dropped by provenance · 3 un-entailed).
- **fact-precision = 1.000** (≥ 0.98 ✓) — confirmed by an independent numeric-probe rater.
- **useful-yield = 0.64** (≥ 0.60 ✓).
- **Cohen's κ = 0.938 @ 98% agreement** (two raters).
- **FIREWALL / LEAKAGE: PASS** (8/8) · **GATE: PASSED**.

**Narration:** "This is our AI card pipeline. Every generated fact must carry a
**verbatim source quote** or it's dropped; every computational answer is **re-derived by
a computer-algebra system** — a wrong answer *cannot* publish; conceptual cards are
never auto-trusted, they're flagged for human review. It's scored against a gate whose
cutoffs were locked *before* scoring — fact-precision ≥ 0.98, useful-yield ≥ 0.60 — and
it passes. And it's honest: there's no live model here, so this validates the machinery,
not a model. Turning a real model on is a one-file change; nothing downstream moves."

## What `make ai-baseline` shows

The same shared SymPy targets run through two pipelines: **our AI arm**
(RAG + provenance + CAS + abstain) vs. a **naive baseline** (template/cloze, non-RAG, no
verify/abstain), scored by the same rater.

| arm | fact-precision | useful-yield |
|---|---|---|
| **AI pipeline** | **1.000** | **0.833** |
| baseline (naive) | 0.600 | 0.400 |

- Paired 2×2: b=30 (AI-only wins) · c=4 (baseline-only) → **McNemar exact p ≈ 6.2e-06**,
  favoring the AI arm; useful-yield-diff 90% CI **[0.300, 0.567]** (excludes 0).
- The baseline ships **24/60 wrong-fact cards**; the AI arm ships **0**.

**Narration:** "Does the extra machinery actually earn its keep? Against a naive
generator on the same problems, the RAG + verify + abstain pipeline beats it with
McNemar p ≈ 6-in-a-million, and it never ships a wrong fact while the baseline ships
dozens. That's the value of provenance + CAS + abstention."

## AI-off degradation (also in `make ai-baseline`)

With no model/network the pipeline **aborts cleanly — 0 cards, 0 unverified shipped** —
while the study/review deck and the `scoring/` layer keep working (they never call a
model). AI is a build-time step, never a runtime dependency. Good line for the close.

---

## Appendix — going live with a real model (EXPERIMENTAL, not demo-tested)

The live-model path is a **seam, not a finished feature.** `run_gate.py` currently
hard-selects the deterministic `StubBackend`, and `orchestrator.LlmBackend.plan()/build()`
raise `NotImplementedError` even with a key present. **Do not rely on this for today's
recording** — the AI-off machinery run above is the honest, working demo.

To actually wire a model later:

1. Set a key: `export OPENAI_API_KEY=…` (or `ANTHROPIC_API_KEY` / `AI_CARDS_LLM_KEY`).
2. Implement `LlmBackend.plan()` + `build(request, retrieved)` in
   `pipeline/aicards/orchestrator.py` to call the model with the retrieved passages and
   return a `cards.GeneratedCard` — **including** a SymPy-checkable `check` payload for
   computational cards (the same structure `StubBackend` builds), so the CAS verifier can
   re-derive it. Provenance, verification, and the gate are all model-agnostic and stay
   unchanged.
3. Add a `--live` flag in `run_gate.py` that selects `LlmBackend()` instead of the stub.
4. **Smoke-test it** (`--live` on a handful of cards) before trusting it on camera — an
   LLM that doesn't emit a valid `check` payload will simply abstain, which is safe but
   won't demo a live "published" card.

Until that's done and smoke-tested, keep the framing honest: **AI-off; machinery
validated, not a live model.**
