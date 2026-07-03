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

.PHONY: sync-server sync-smoke deck-asset deck-asset-check score-eval ai-gate ai-gate-test ai-baseline bench proofs

sync-server: ## Start the self-hosted Anki sync server on our engine (foreground; Ctrl-C to stop).
	@sync/run-sync-server.sh

sync-smoke: ## Headless desktop-collection sync round-trip (server must already be running).
	@FORK_ANKI="$${FORK_ANKI:-/Users/felipecaicedo/Desktop/alpha/speedrun/anki}"; \
	FORK_PY="$${FORK_PY:-$$FORK_ANKI/out/pyenv/bin/python}"; \
	PYTHONPATH="$$FORK_ANKI/out/pylib$${PYTHONPATH:+:$$PYTHONPATH}" "$$FORK_PY" sync/roundtrip_smoke.py

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
