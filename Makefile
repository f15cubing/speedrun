# GRE fork — task shortcuts.
SHELL := /bin/bash

# The bundled study deck asset, shipped inside both apps for first-run auto-import.
DECK_APKG := pipeline/dist/gre-study-deck.apkg
DESKTOP_ASSET := anki/qt/aqt/gre/data/gre-study-deck.apkg
ANDROID_ASSET := Anki-Android/AnkiDroid/src/main/assets/gre-study-deck.apkg

# Quantitative proofs (Block D). Bench runs the REAL engine via the built pylib;
# calibration/paraphrase are pure-stdlib scoring + the eval bank (charts need the
# proofs venv). Override FORK_ANKI / BENCH_CARDS / BENCH_ITERS as needed.
FORK_ANKI := $(if $(FORK_ANKI),$(FORK_ANKI),/Users/felipecaicedo/Desktop/alpha/speedrun/anki)
BENCH_CARDS := 50000
BENCH_ITERS := 300

.PHONY: sync-server sync-smoke sync-up sync-status sync-verify sync-down sync-reset sync-urls sync-doctor sync-server-7b sync-7b crash-7g deck-asset deck-asset-check score-eval interleave-report ai-gate ai-gate-test ai-baseline bench proofs deck-leakage-audit giveup-audit deck-report scorecard-validate ablation-analysis

sync-server: ## Start the self-hosted Anki sync server on our engine (foreground; Ctrl-C to stop).
	@sync/run-sync-server.sh

sync-smoke: ## Headless desktop-collection sync round-trip (server must already be running).
	@FORK_ANKI="$${FORK_ANKI:-/Users/felipecaicedo/Desktop/alpha/speedrun/anki}"; \
	FORK_PY="$${FORK_PY:-$$FORK_ANKI/out/pyenv/bin/python}"; \
	PYTHONPATH="$$FORK_ANKI/out/pylib$${PYTHONPATH:+:$$PYTHONPATH}" "$$FORK_PY" sync/roundtrip_smoke.py

sync-up: ## One command: preflight + start the sync server in the background + health-check + status card.
	@sync/sync.sh up

sync-status: ## Report sync server state (pid/port/health/data dir/engine buildhash).
	@sync/sync.sh status

sync-verify: ## Ensure the server is up, then run the headless round-trip proof (PASS/FAIL).
	@sync/sync.sh verify

sync-down: ## Stop the background sync server (ARGS=--reset also wipes the data dir).
	@sync/sync.sh down $(ARGS)

sync-reset: ## Wipe the local server data dir for a clean first-contact (ARGS=--yes to skip confirm).
	@sync/sync.sh reset $(ARGS)

sync-urls: ## Print copy-paste desktop + emulator client config (ARGS=--set-desktop/--emulator).
	@sync/sync.sh urls $(ARGS)

sync-doctor: ## Preflight checklist only (build/creds/port/emulator) — no start.
	@sync/sync.sh doctor

sync-server-7b: ## Start a self-hosted sync server on :8090 with a fresh 7b-only data dir (foreground; Ctrl-C to stop).
	@rm -rf "$(CURDIR)/sync/.sync-data-7b"; \
	FORK_ANKI="$${FORK_ANKI:-/Users/felipecaicedo/Desktop/alpha/speedrun/anki}" \
	SYNC_PORT=8090 SYNC_BASE="$(CURDIR)/sync/.sync-data-7b" sync/run-sync-server.sh

sync-7b: ## Two-way sync proof (7b): 10+10 no-loss + same-card conflict (server on :8090 must be running).
	@FORK_ANKI="$${FORK_ANKI:-/Users/felipecaicedo/Desktop/alpha/speedrun/anki}"; \
	FORK_PY="$${FORK_PY:-$$FORK_ANKI/out/pyenv/bin/python}"; \
	SYNC_ENDPOINT="$${SYNC_ENDPOINT:-http://127.0.0.1:8090/}" \
	PYTHONPATH="$$FORK_ANKI/out/pylib$${PYTHONPATH:+:$$PYTHONPATH}" "$$FORK_PY" sync/two_way_sync_7b.py

crash-7g: ## Crash-durability proof (7g): SIGKILL mid-review x20 -> quick_check/integrity_check ok, no revlog loss.
	@FORK_ANKI="$${FORK_ANKI:-/Users/felipecaicedo/Desktop/alpha/speedrun/anki}"; \
	FORK_PY="$${FORK_PY:-$$FORK_ANKI/out/pyenv/bin/python}"; \
	PYTHONPATH="$$FORK_ANKI/out/pylib$${PYTHONPATH:+:$$PYTHONPATH}" "$$FORK_PY" robustness/crash_test_7g.py

deck-asset: ## Rebuild the study deck and refresh the bundled app assets (desktop + AnkiDroid).
	python pipeline/build_deck.py --seed 42
	@mkdir -p "$$(dirname $(DESKTOP_ASSET))" "$$(dirname $(ANDROID_ASSET))"
	cp $(DECK_APKG) $(DESKTOP_ASSET)
	cp $(DECK_APKG) $(ANDROID_ASSET)
	@echo "deck sha256:"; shasum -a 256 $(DECK_APKG) $(DESKTOP_ASSET) $(ANDROID_ASSET)
	@echo "NOTE: bump GRE_DECK_VERSION in both apps' importers when the deck content changes."

deck-asset-check: ## Fail if the committed app assets drift from the pipeline output (byte-identical).
	python pipeline/build_deck.py --seed 42
	@a=$$(shasum -a 256 $(DECK_APKG) | awk '{print $$1}'); \
	 d=$$(shasum -a 256 $(DESKTOP_ASSET) 2>/dev/null | awk '{print $$1}'); \
	 n=$$(shasum -a 256 $(ANDROID_ASSET) 2>/dev/null | awk '{print $$1}'); \
	 if [ "$$a" = "$$d" ] && [ "$$a" = "$$n" ]; then echo "deck assets in sync ($$a)"; \
	 else echo "DRIFT: pipeline=$$a desktop=$$d android=$$n — run 'make deck-asset'"; exit 1; fi

score-eval: ## Simulate + fit + validate the scoring models; emit metrics + sample scorecard.
	@PYTHONPATH=. python3 scoring/eval_cli.py --seed 42 --students 40 --out scoring/out

interleave-report: ## Interleaving metrics (adjacency dispersion + FSRS displacement) on the seeded deck (PRD §8/D5).
	@IL_PY="$${IL_PY:-python3}"; PYTHONPATH=pipeline "$$IL_PY" pipeline/run_interleave_report.py --seed 42
deck-leakage-audit: ## Publish the study-deck<->eval-bank residual leakage rate (PRD §11; read-only on the held-out bank).
	@LK_PY="$${LK_PY:-python3}"; PYTHONPATH=pipeline:eval/bank "$$LK_PY" pipeline/run_leakage_audit.py --seed 42 --strict
deck-report: ## Study-deck quality report + integrity GATE (distinct options / valid key / required fields).
	@DR_PY="$${DR_PY:-python3}"; PYTHONPATH=pipeline "$$DR_PY" pipeline/run_deck_report.py --seed 42 --strict
scorecard-validate: ## Validate the synced gre_scorecard honesty contract (no bare Readiness number; scores never blended; PRD §7c/D2).
	@SC_PY="$${SC_PY:-python3}"; PYTHONPATH=. "$$SC_PY" proofs/validate_scorecard.py \
		proofs/tests/fixtures/scorecard_gated.json proofs/tests/fixtures/scorecard_shown.json
ablation-analysis: ## Pre-registered interleaving ablation analysis (TOST + 90% CI + honest-null; PRD D5/App. B). Stdlib-only.
	@AB_PY="$${AB_PY:-python3}"; PYTHONPATH=. "$$AB_PY" ablation/analysis.py --seed 42

ai-gate: ## Run the AI card pipeline + gold-set gate (deterministic stub; AI-off, PRD §9).
	@AI_PY="$${AI_PY:-python3}"; PYTHONPATH=pipeline:pipeline/aicards "$$AI_PY" pipeline/aicards/run_gate.py --seed 42

ai-gate-test: ## Run the AI card pipeline test suite (fast; needs pipeline/requirements.txt).
	@AI_PY="$${AI_PY:-python3}"; "$$AI_PY" -m pytest pipeline/aicards/tests -q

ai-baseline: ## Beat-the-baseline (McNemar) + AI-off degradation proofs (deterministic, PRD §9).
	@AI_PY="$${AI_PY:-python3}"; PYTHONPATH=pipeline:pipeline/aicards "$$AI_PY" pipeline/aicards/run_baseline.py --seed 42

bench: ## Latency bench of the mastery-query RPC at 50k cards (p50/p95/worst) via the built engine.
	@PYTHONPATH="$(FORK_ANKI)/out/pylib:." "$(FORK_ANKI)/out/pyenv/bin/python" \
		proofs/bench_mastery.py --cards $(BENCH_CARDS) --iters $(BENCH_ITERS) --seed 42

proofs: ## Memory calibration chart + paraphrase results (needs .venv-proofs: pyyaml+matplotlib).
	@if [ ! -x .venv-proofs/bin/python ]; then \
		echo "creating .venv-proofs (pyyaml+matplotlib)"; \
		python3 -m venv .venv-proofs && .venv-proofs/bin/pip -q install pyyaml matplotlib; fi
	@PYTHONPATH=. .venv-proofs/bin/python proofs/calibration.py --seed 42
	@PYTHONPATH=.:eval/bank:pipeline .venv-proofs/bin/python proofs/paraphrase.py --seed 42

giveup-audit: ## D2 give-up-rule evidence audit: prove Readiness is gated w/ no bare number (PRD §7c). Stdlib-only.
	@GU_PY="$${GU_PY:-python3}"; PYTHONPATH=. "$$GU_PY" proofs/giveup_audit.py --seed 42 --out docs/evidence/proofs/giveup_audit.json
