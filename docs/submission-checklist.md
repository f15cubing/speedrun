# Submission checklist & packaging runbook (Sunday)

> The single "what to build, verify, and hand in" runbook for the **Sunday 2026-07-05, 10:59 PM CT**
> deadline. Pairs with `docs/execution-plan.md` (Day 6 — Sunday) and the **Sat/Sun buffer** section of
> `docs/STATUS.md` (the CUT-FIRST spillover to clear first).
>
> **Legend:** ✅ = merged / verified in-repo (re-runnable now) · 🧑 = **human-gated** (needs a person
> at the keyboard, a signing key, or a clean device — cannot be finished headless in this environment).
> Pinned engine: `f15cubing/anki@6d05314` (Anki 25.09.4); Android forks
> `f15cubing/Anki-Android@c6d02501` + `f15cubing/Anki-Android-Backend@3dc30c2` (rsdroid, built locally).

---

## 0. Clear the CUT-FIRST buffer first

Per `docs/STATUS.md` § *Sat/Sun buffer (CUT-FIRST spillover)* — none of these blocks a passing
submission, but clear what you can:

- 🧑 **Demo recording** — the 3–5 min Sunday cut (`docs/demo-plan.md`). Needs live capture.
- 🧑/⏳ **AI live-model run** — only if a live-model API key lands: `make ai-gate` with a real backend
  (seam `orchestrator.LlmBackend`). Otherwise ship **AI-off** (machinery validated; do not overclaim).
- ⏳ **Ablation run** — optional; interleaving instrumentation isn't built. The pre-registration
  stands (PRD Appendix B), so a documented **"not yet run"** is honest and scores.
- 🧑 **Block C Android leg** — optional on-device crash/sync round when the emulator is free; the
  device durability is already covered by W3 + W4.

---

## 1. Desktop — build the installer & verify on a clean machine

**Dev run (sanity, from repo root):**

```bash
cd anki && ./run          # compiles + launches the desktop app (first run is slow)
```

**Package (wheels → installer):**

```bash
cd anki
./tools/build             # builds the Python wheels (anki + aqt) under anki/out/wheels/
```

- ✅ The engine + app build from source in-repo (`./run`, `./ninja check`).
- 🧑 **Clean-machine verification (required, recorded):** on a machine that has *never* built Anki,
  install the produced wheels into a fresh venv (`pip install anki/out/wheels/*.whl`) — or the
  platform bundle if you produce one — launch it, confirm the GRE deck **auto-imports on first run**,
  open the **GRE dashboard** (three separated scores; Readiness gated with the evidence panel), and
  **record** the install + launch. A clean-machine failure caps the grade at 50% (hard ceiling).
- Note: full native OS bundles (`.dmg`/`.exe`/AppImage) use Anki's platform packaging on top of the
  wheels; the wheels + `./run` are the re-runnable baseline. See `README.md` → "Run the desktop app".

## 2. Android — build & sign the APK, verify on a clean device

**Build the backend (bundles our engine) + the APK (from repo root, `.androidenv` sourced):**

```bash
cd Anki-Android-Backend && ./build.sh && cd ..      # rsdroid; logs "Anki commit: ea3acae…"
cd Anki-Android && ./gradlew assembleFullRelease     # release APK (unsigned by default)
```

- ✅ Debug APK builds on our local backend; `librsdroid.so` loads; the read-only 3-score panel opens
  (Task 7); first-run auto-import verified on the emulator (see `docs/evidence/task7-android/`).
- 🧑 **Signing (required for a real release):** create/point to a keystore and sign the release APK
  (`apksigner`/Gradle signing config, keystore **never committed**). The signing key is a human-held
  secret — this cannot be done headless here.
- 🧑 **Clean-device verification (required, recorded):** install the **signed** APK on a fresh
  emulator/device, run a real FSRS review, open **DeckPicker overflow → "GRE readiness"** (three
  scores, read-only, Readiness gated), sync with the desktop, and **Check database → "rebuilt and
  optimized."** **Record** it. A clean-device failure caps the grade at 50% (hard ceiling).

## 3. AI off/on posture

- ✅ **AI-off is the shipped posture:** `make ai-gate` passes on the deterministic stub
  (fact-precision **1.000** · useful-yield **0.64** · κ **0.938**); `make ai-baseline` beats the
  non-RAG baseline (McNemar **p ≈ 6e-6**). Both apps run and score with **no model / no network**
  (`run_pipeline_safe` aborts cleanly; `scoring/` never imports a model/network client).
- 🧑/⏳ **Live model:** a one-file seam (`orchestrator.LlmBackend`) — run only if a key is available.
  When describing AI, say **"AI-off; validates the machinery, not a live model."** Do not overclaim.

---

## 4. Hard-ceiling checklist (must all hold — see PRD §3 / project-spec §11)

| Ceiling | Status | Evidence |
|---|---|---|
| **Real read-only Rust engine change** exists (never `OpChanges`, never `transact`, undo intact) | ✅ | W1 mastery query (PR #7); read-only-invariant test; `docs/progress-and-rust-change.md`, `docs/codebase/rslib.md` |
| **Phone shares one engine + syncs** | ✅ | rsdroid rebuilt from our fork (W3, PR #12); self-hosted two-way sync (W4) + 7b (PR #36) |
| **Re-runnable test setup** (pinned deps, seeded, one command each) | ✅ | `make bench` · `make proofs` · `make ai-gate` · `make crash-7g` · `make sync-7b` |
| **Held-out testing** (no leaked ETS items) | ✅ | Authored eval bank (firewalled, drift-guarded); AI firewall PASS (canary/ETS/OCW-free) |
| **No ETS item reuse** in training or eval | ✅ | Original RAG source chapter; leakage firewall off the committed canary GUID |
| **Readiness never a bare number** (range + full evidence panel + give-up rule) | ✅ | Desktop adapter (Task 6) + phone panel (Task 7); a bare number is an **auto-fail** |
| **Three scores never blended** | ✅ | Memory / Performance / Readiness separate on both surfaces |
| **Both apps run on a clean device** (AI off) | 🧑 | **Must record on Sunday** — desktop wheels install + signed APK install (§1, §2) |

---

## 5. Deliverables to hand in (project-spec §12 / PRD §15)

| # | Deliverable | Status | Where |
|---|---|---|---|
| 1 | **Public GitHub repo** — AGPL-3.0-or-later + Anki credit, exam stated up front, build instructions (both platforms), architecture overview, Rust-change note + files touched + merge-difficulty | ✅ (push final on Sun) | `README.md`, `LICENSE`, `docs/codebase/architecture.md`, `docs/progress-and-rust-change.md` |
| 2 | **Demo video (3–5 min)** — review → Rust change → phone↔desktop sync → three scores with ranges → AI → test results | 🧑 record | Script: `docs/demo-plan.md` (Sunday cut) |
| 3 | **Three model descriptions** (one page each: memory, performance, readiness incl. give-up rule) | ✅ | `docs/models/{memory,performance,readiness}.md` |
| 4 | **Brainlift** | ✅ (already complete — do not rewrite) | `research/brainlift.md` |

**Final steps (Sunday):** push the repo public, attach the recorded demo, link the three model docs +
Brainlift, tick the hard-ceiling table above, then **submit by 10:59 PM CT.**

---

Last verified against: `f15cubing/anki@6d05314` (Anki 25.09.4); Android `f15cubing/Anki-Android@c6d02501`.
