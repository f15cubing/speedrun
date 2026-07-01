# GRE fork — task shortcuts. (make bench lands here later, PRD §11.)
SHELL := /bin/bash

.PHONY: sync-server sync-smoke

sync-server: ## Start the self-hosted Anki sync server on our engine (foreground; Ctrl-C to stop).
	@sync/run-sync-server.sh

sync-smoke: ## Headless desktop-collection sync round-trip (server must already be running).
	@FORK_ANKI="$${FORK_ANKI:-/Users/felipecaicedo/Desktop/alpha/speedrun/anki}"; \
	FORK_PY="$${FORK_PY:-$$FORK_ANKI/out/pyenv/bin/python}"; \
	PYTHONPATH="$$FORK_ANKI/out/pylib$${PYTHONPATH:+:$$PYTHONPATH}" "$$FORK_PY" sync/roundtrip_smoke.py
