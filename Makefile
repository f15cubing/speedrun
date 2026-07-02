# GRE fork — task shortcuts. (make bench lands here later, PRD §11.)
SHELL := /bin/bash

# The bundled study deck asset, shipped inside both apps for first-run auto-import.
DECK_APKG := pipeline/dist/gre-study-deck.apkg
DESKTOP_ASSET := anki/qt/aqt/gre/data/gre-study-deck.apkg
ANDROID_ASSET := Anki-Android/AnkiDroid/src/main/assets/gre-study-deck.apkg

.PHONY: sync-server sync-smoke deck-asset deck-asset-check

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
