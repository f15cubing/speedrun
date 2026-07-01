# W4 — Sync Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up a self-hosted `anki-sync-server` running our fork's engine, wire desktop Anki + the AnkiDroid emulator to it, and prove a card + its review state round-trips desktop↔Android with no corruption — the Wednesday sync foundation.

**Architecture:** A committed one-command launcher starts the server from the desktop build's Python (`python -m anki.syncserver`, engine `f15cubing/anki@ea3acae`). Two proofs: a re-runnable **headless pylib round-trip** (two collections ↔ the server, asserting a reviewed note + revlog + scheduling cross and `quick_check` stays ok), and the **live desktop↔Android** round-trip captured as evidence. All new files live in the outer repo — nothing under `anki/` changes, so this is **fast lane**.

**Tech Stack:** Anki's built-in Rust sync server (via pylib `python -m anki.syncserver`), pylib `Collection` sync API (`sync_login`/`sync_collection`/`full_upload_or_download`), Bash, Make, Python 3, an Android emulator + `adb`, the desktop Anki fork build.

## Global Constraints

- **No engine/collection code changes** — nothing under `anki/` (no `rslib`, no proto/FFI, no submodule pin). If a change would reach `anki/rslib/src/sync/`, STOP: that flips to engine lane. (Spec §6.)
- **Self-hosted only; never point a client at AnkiWeb.** Set the custom sync URL *before* first login on each client. (Spec §Global.)
- **Server data dir + credentials are gitignored.** Committed creds are local throwaways: `SYNC_USER1=greuser:grepass` (NOT a secret). (Spec §2, §Global.)
- **Pin server engine == both clients == `f15cubing/anki@ea3acae`.** A patch-version skew can force a full sync / protocol error. (Spec §Global.)
- **Endpoints:** desktop → `http://127.0.0.1:8080/`; Android emulator → `http://10.0.2.2:8080/` (emulator alias for the host loopback); `SYNC_PORT=8080`; the server **panics without `SYNC_USER1`**. (Spec §1, §3.)
- **Foundation only.** No 10+10 no-loss matrix, no same-card conflict demo (7b), no crash/offline (7g). The D3 device-UUID tie-break is **documented, not implemented**. (Spec §Decisions, §10.)
- **Read RPCs never return `OpChanges`** — n/a here (no RPC added). Never blend the three scores (no scoring surface in W4).
- **Spec:** `docs/superpowers/specs/2026-07-01-w4-sync-foundation-design.md`.

## Environment (known facts for this machine)

- Repo root (this worktree): `/Users/felipecaicedo/Desktop/alpha/speedrun-worktrees/w4-sync`; branch `agent/w4-sync-foundation`.
- The desktop **Anki fork build** provides both `$FORK_PY` (the interpreter with our compiled `anki`/`_rsbridge`) and the GUI app. Expected `$FORK_PY` ≈ `anki/out/pyenv/bin/python`; **confirm at execution** and record the real path in `docs/codebase/sync.md`. If the build is absent, rebuild the desktop fork first (`.cursor/skills/building-and-testing`).
- The **Android emulator** `anki_test` (arm64-v8a, API 35) with our AnkiDroid debug build (`com.ichi2.anki.debug`) is already installed (W3). `ANDROID_HOME=/Users/felipecaicedo/Library/Android/sdk`; `adb` on `PATH` via `$ANDROID_HOME/platform-tools`.
- The seeded GRE deck: `python pipeline/build_deck.py --seed 42` → `pipeline/dist/gre-study-deck.apkg` (already importable; used as the sync payload).
- Lane: **fast lane** — self-review checklist, no separate reviewer agent, no submodule/engine edits.

---

## File Structure

**New (outer repo):**
- `sync/run-sync-server.sh` — launcher: resolve `$FORK_PY`, set `SYNC_*` env, `exec python -m anki.syncserver`.
- `sync/.env.example` — documents the local-only creds + optional `FORK_PY`/`SYNC_PORT` overrides.
- `sync/roundtrip_smoke.py` — headless two-collection round-trip regression (the automated proof).
- `Makefile` (root, created) — `sync-server` + `sync-smoke` targets.
- `docs/codebase/sync.md` — runbook: topology, exact verified commands, both clients' config, the honest D3 rule, gotchas.
- `docs/evidence/w4-sync/` — live desktop↔Android round-trip screenshots + Check-Database results.

**Modified (outer repo):**
- `.gitignore` — ignore `sync/.sync-data/`, `sync/.env`, `docs/evidence/w4-sync/*.tmp`.
- `docs/codebase/INDEX.md` — move "Sync conflict rules" Planned → Built-foundation (+ `sync.md`).
- `docs/STATUS.md`, `docs/execution-plan.md` — record the PR; check the Wednesday sync-foundation box.

**Untouched:** everything under `anki/`, `Anki-Android/`, `Anki-Android-Backend/`, `pipeline/`.

---

## Task 1: Sync-server launcher + `make sync-server` + gitignore

**Goal/deliverable:** one documented command starts the pinned self-hosted server on our engine.

**Files:**
- Create: `sync/run-sync-server.sh`, `sync/.env.example`, root `Makefile`
- Modify: `.gitignore`

**Interfaces:**
- Produces: a running server on `:8080` with account `greuser:grepass`; `$FORK_PY` resolution reused by Task 2.

- [ ] **Step 1: Write the launcher `sync/run-sync-server.sh`**

```bash
#!/usr/bin/env bash
# GRE fork — launch a self-hosted Anki sync server on OUR engine (f15cubing/anki@ea3acae).
# W4 foundation (PRD §10 / D3). LOCAL TEST HARNESS ONLY — never expose publicly.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Local overrides (gitignored) win; otherwise the committed defaults below apply.
if [[ -f "$REPO_ROOT/sync/.env" ]]; then set -a; source "$REPO_ROOT/sync/.env"; set +a; fi

# Local-only throwaway credentials (NOT a secret). Override via sync/.env.
: "${SYNC_USER1:=greuser:grepass}"
: "${SYNC_HOST:=0.0.0.0}"
: "${SYNC_PORT:=8080}"
: "${SYNC_BASE:=$REPO_ROOT/sync/.sync-data}"
export SYNC_USER1 SYNC_HOST SYNC_PORT SYNC_BASE

# Resolve the desktop build's Python (the interpreter with our compiled `anki` = _rsbridge).
FORK_PY="${FORK_PY:-$REPO_ROOT/anki/out/pyenv/bin/python}"
if [[ ! -x "$FORK_PY" ]]; then
  echo "ERROR: desktop-build Python not found at: $FORK_PY" >&2
  echo "Build the desktop fork (.cursor/skills/building-and-testing) or set FORK_PY in sync/.env." >&2
  exit 1
fi
if ! "$FORK_PY" -c 'import anki, anki._backend' 2>/dev/null; then
  echo "ERROR: $FORK_PY cannot import our built 'anki' (_rsbridge missing). Rebuild the desktop fork." >&2
  exit 1
fi

mkdir -p "$SYNC_BASE"
echo "anki-sync-server  (engine f15cubing/anki@ea3acae)"
echo "  data dir : $SYNC_BASE"
echo "  desktop  : http://127.0.0.1:${SYNC_PORT}/"
echo "  emulator : http://10.0.2.2:${SYNC_PORT}/"
echo "  account  : ${SYNC_USER1%%:*}"
exec env RUST_LOG="${RUST_LOG:-anki=info}" "$FORK_PY" -m anki.syncserver
```

- [ ] **Step 2: Write `sync/.env.example`**

```bash
# GRE fork — local sync-server config. Copy to sync/.env (gitignored) to override.
# These are LOCAL THROWAWAY credentials for the self-hosted test server — NOT secrets.
SYNC_USER1=greuser:grepass
# SYNC_PORT=8080
# SYNC_HOST=0.0.0.0
# Absolute path to the desktop build's Python (with our compiled `anki`):
# FORK_PY=/Users/felipecaicedo/Desktop/alpha/speedrun-worktrees/w4-sync/anki/out/pyenv/bin/python
```

- [ ] **Step 3: Write the root `Makefile`**

```make
# GRE fork — task shortcuts. (make bench lands here later, PRD §11.)
SHELL := /bin/bash

.PHONY: sync-server sync-smoke

sync-server: ## Start the self-hosted Anki sync server on our engine (foreground; Ctrl-C to stop).
	@sync/run-sync-server.sh

sync-smoke: ## Headless desktop-collection sync round-trip (server must already be running).
	@FORK_PY="$${FORK_PY:-anki/out/pyenv/bin/python}"; \
	"$$FORK_PY" sync/roundtrip_smoke.py
```

- [ ] **Step 4: Make the launcher executable + append `.gitignore`**

Run:
```bash
chmod +x sync/run-sync-server.sh
cat >> .gitignore <<'EOF'

# W4 sync foundation — local server data + creds (never commit)
sync/.sync-data/
sync/.env
docs/evidence/w4-sync/*.tmp
EOF
```

- [ ] **Step 5: Verify the server starts and listens**

Run (terminal A): `make sync-server`
Expected: prints the banner (desktop/emulator URLs, account `greuser`) and a `RUST_LOG` line indicating it is serving on `0.0.0.0:8080`; the process stays in the foreground.

Run (terminal B):
```bash
curl -sS -o /dev/null -w "sync-server HTTP %{http_code}\n" http://127.0.0.1:8080/
```
Expected: a numeric HTTP code (e.g. `404` for `GET /`), which proves the port is listening (NOT `curl: (7) connection refused`). Then stop the server in terminal A with Ctrl-C.

> If Step 5 fails because `$FORK_PY` isn't found, the desktop fork build must be (re)built first — do that (or set `FORK_PY` in `sync/.env`) before continuing. This is the spec's Risk #1.

- [ ] **Step 6: Commit**

```bash
git add sync/run-sync-server.sh sync/.env.example Makefile .gitignore
git commit -m "feat(w4): one-command self-hosted anki-sync-server launcher"
```

---

## Task 2: Headless pylib round-trip smoke (`sync/roundtrip_smoke.py`)

**Goal/deliverable:** an automated, re-runnable proof that a reviewed, tagged note crosses A → server → B with revlog + scheduling intact and `quick_check` ok on both — the CI-able regression.

**Files:**
- Create: `sync/roundtrip_smoke.py`
- Modify: `Makefile` (the `sync-smoke` target already added in Task 1 runs it)

**Interfaces:**
- Consumes: a running server from Task 1 (`http://127.0.0.1:8080/`, account `greuser:grepass`); `$FORK_PY`.
- Produces: exit 0 on success, non-zero + a diagnostic on any mismatch.

- [ ] **Step 1: Write the failing smoke script**

Note the pylib sync handshake (verified against `anki/qt/aqt/sync.py`): `sync_collection(auth, sync_media=False)` performs a normal sync inline and returns `out.required`; if it is not `NO_CHANGES` a full sync is required, resolved with `full_upload_or_download(auth=..., server_usn=None, upload=<bool>)`. Enum: `NO_CHANGES=0, NORMAL_SYNC=1, FULL_SYNC=2, FULL_DOWNLOAD=3, FULL_UPLOAD=4`.

```python
#!/usr/bin/env python3
"""GRE fork — headless sync round-trip smoke (W4 foundation).

Proves the self-hosted server + Anki sync protocol move a reviewed, topic-tagged
note from collection A -> server -> collection B with revlog + scheduling intact
and `pragma quick_check` = ok on both. Run OUR desktop-build Python:

    make sync-server            # terminal A (leave running)
    make sync-smoke             # terminal B  (or: $FORK_PY sync/roundtrip_smoke.py)

Exits non-zero on any mismatch. LOCAL TEST ONLY (creds are throwaways).
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from anki.collection import Collection

ENDPOINT = "http://127.0.0.1:8080/"
USER, PASSWORD = "greuser", "grepass"
TAG = "topic::calculus::integral_single"
FRONT = "w4-sync-smoke-front"


def _sync(col: Collection, *, prefer_upload: bool) -> None:
    """One sync; if a full sync is required (empty-server first contact), resolve it
    in the intended direction."""
    auth = col.sync_login(USER, PASSWORD, ENDPOINT)
    out = col.sync_collection(auth, False)  # sync_media=False
    if out.required == out.NO_CHANGES:
        return
    if out.required == out.FULL_UPLOAD:
        upload = True
    elif out.required == out.FULL_DOWNLOAD:
        upload = False
    else:  # FULL_SYNC (ambiguous) — use our controlled direction
        upload = prefer_upload
    col.full_upload_or_download(auth=auth, server_usn=None, upload=upload)


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="w4-sync-"))
    a = Collection(str(tmp / "a.anki2"))
    b = Collection(str(tmp / "b.anki2"))
    try:
        # A: add a tagged note and review its card once (creates a revlog row + schedules it).
        note = a.new_note(a.models.by_name("Basic"))
        note["Front"], note["Back"] = FRONT, "back"
        note.tags = [TAG]
        a.add_note(note, 1)  # deck 1 = Default
        card = a.sched.getCard()
        assert card is not None, "no card queued to review on A"
        a.sched.answerCard(card, 3)  # 3 = Good
        reps_a = a.db.scalar("select count() from revlog")
        assert reps_a >= 1, f"expected a revlog row on A, got {reps_a}"

        # A -> server (full upload; server starts empty), then server -> B (full download).
        _sync(a, prefer_upload=True)
        _sync(b, prefer_upload=False)

        # B must now have the note, its card, and the revlog row; both DBs stay clean.
        n_notes = b.db.scalar("select count() from notes where flds like ?", f"{FRONT}%")
        n_revlog = b.db.scalar("select count() from revlog")
        n_cards = b.db.scalar(
            "select count() from cards c join notes n on c.nid=n.id where n.flds like ?",
            f"{FRONT}%",
        )
        assert n_notes == 1, f"note did not cross to B (notes={n_notes})"
        assert n_cards >= 1, f"card did not cross to B (cards={n_cards})"
        assert n_revlog >= 1, f"revlog did not cross to B (revlog={n_revlog})"
        for name, col in (("A", a), ("B", b)):
            qc = col.db.scalar("pragma quick_check")
            assert qc == "ok", f"quick_check on {name} = {qc!r}"

        print(f"OK: note+card+revlog crossed A->server->B; quick_check ok (revlog A={reps_a}, B={n_revlog})")
        return 0
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    finally:
        a.close()
        b.close()


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run it to verify it FAILS with no server running**

Run: `$FORK_PY sync/roundtrip_smoke.py` (with the server stopped)
Expected: a non-zero exit — a connection/sync error (the server isn't up). This confirms the script really talks to the server rather than passing vacuously.

- [ ] **Step 3: Start the server, then run the smoke to verify it PASSES**

Run (terminal A): `make sync-server`
Run (terminal B): `make sync-smoke`
Expected: `OK: note+card+revlog crossed A->server->B; quick_check ok (...)` and exit 0.

> If `sync_collection` returns `FULL_SYNC`/`NORMAL_SYNC` unexpectedly for B, that's handled by `_sync` (B forces download). If the note fails to cross, re-run against a fresh `SYNC_BASE` (`rm -rf sync/.sync-data`) — a stale server DB from a prior run can leave the account non-empty and change the first-contact direction.

- [ ] **Step 4: Make executable + commit**

```bash
chmod +x sync/roundtrip_smoke.py
git add sync/roundtrip_smoke.py
git commit -m "test(w4): headless pylib sync round-trip smoke (note+revlog cross, quick_check ok)"
```

---

## Task 3: Live desktop↔Android round-trip + evidence

**Goal/deliverable:** the real cross-device proof — a card + review state syncs desktop↔Android through our server, both directions, with Check Database clean on both. This is a manual/`adb`-driven gate (like the W3 on-device gate); capture screenshots.

**Files:**
- Create: `docs/evidence/w4-sync/*.png` (curated, small)

**Interfaces:**
- Consumes: Task 1 server running; the desktop fork GUI app; the `anki_test` emulator + AnkiDroid; the seeded deck imported on both (from W3 the emulator already has "GRE Math Subject Test").

- [ ] **Step 1: Ensure prerequisites are live**

Run:
```bash
export ANDROID_HOME="$HOME/Library/Android/sdk"; export PATH="$ANDROID_HOME/platform-tools:$PATH"
adb devices                        # expect: emulator-5554  device
mkdir -p docs/evidence/w4-sync
make sync-server                   # in its own terminal; leave running
```
Expected: emulator online; server serving. Launch the desktop fork app (per `building-and-testing`).

- [ ] **Step 2: Point desktop at the local server and upload**

In the desktop app: Preferences ▸ Syncing ▸ *Self-hosted sync server* = `http://127.0.0.1:8080/`. Ensure the seeded GRE deck is loaded (import `pipeline/dist/gre-study-deck.apkg` if needed). Review one card, then Sync. Because the server is empty, choose **Upload** if prompted.
Expected: "Sync complete." Screenshot the sync-complete state → `docs/evidence/w4-sync/01-desktop-synced.png`.

- [ ] **Step 3: Point AnkiDroid at the local server and download**

On the emulator: AnkiDroid ▸ Settings ▸ Sync ▸ custom sync server; set collection + media URL = `http://10.0.2.2:8080/`; log in as `greuser`/`grepass`; Sync (choose **Download** if prompted, since the phone hasn't synced yet). Capture:
```bash
adb exec-out screencap -p > docs/evidence/w4-sync/02-android-synced.png
```
Expected: the deck + the desktop's just-reviewed card state appear on Android (the card you reviewed on desktop shows its updated due/interval).

- [ ] **Step 4: Reverse direction (Android → desktop)**

On AnkiDroid: review a *different* card, then Sync (uploads). On desktop: Sync (downloads).
Capture the Android post-review sync and the desktop-after-download state:
```bash
adb exec-out screencap -p > docs/evidence/w4-sync/03-android-reviewed-synced.png
```
Screenshot the desktop reflecting the Android change → `docs/evidence/w4-sync/04-desktop-after-download.png`.
Expected: the Android review lands on desktop — proving two-way sync foundation.

- [ ] **Step 5: No-corruption guard on both clients**

Desktop: Tools ▸ Check Database → screenshot the "collection ok / rebuilt" result → `docs/evidence/w4-sync/05-desktop-checkdb.png`.
AnkiDroid: overflow ▸ Check ▸ Check database → OK → capture:
```bash
adb exec-out screencap -p > docs/evidence/w4-sync/06-android-checkdb.png
```
Expected: both report no corruption ("Database rebuilt and optimized" on Android; "ok" on desktop).

- [ ] **Step 6: Curate + commit evidence**

Keep the six storytelling shots above (delete any extra navigation captures). Then:
```bash
git add docs/evidence/w4-sync
git commit -m "docs(w4): live desktop<->Android sync round-trip evidence (no corruption)"
```

> Fallback (only if the desktop GUI build is unavailable in-budget): run `roundtrip_smoke.py`'s collection **A** as the "desktop" side against the live AnkiDroid (A uploads → AnkiDroid downloads → review on AnkiDroid → A downloads). Note the substitution honestly in `sync.md`; the GUI round-trip remains the target.

---

## Task 4: Runbook `docs/codebase/sync.md` + INDEX/STATUS/execution-plan + PR

**Goal/deliverable:** capture the verified commands + the honest conflict rule, flip the docs to "foundation built," and open the fast-lane PR.

**Files:**
- Create: `docs/codebase/sync.md`
- Modify: `docs/codebase/INDEX.md`, `docs/STATUS.md`, `docs/execution-plan.md`

**Interfaces:**
- Consumes: the verified commands/paths from Tasks 1–3 (real `$FORK_PY` path, the working URLs).

- [ ] **Step 1: Write `docs/codebase/sync.md`** using the module-doc template
  (`.cursor/skills/codebase-docs/module-doc-template.md`). It MUST contain:
  - **Topology** (the §1 diagram) + the exact **verified** launch command and the real resolved `$FORK_PY` path.
  - **Client config:** desktop `127.0.0.1:8080` (Preferences ▸ Syncing) and AnkiDroid `10.0.2.2:8080` (Settings ▸ Sync ▸ custom sync server); "set the URL before first login; never leave it blank."
  - **The two proofs:** `make sync-smoke` (automated) and the `docs/evidence/w4-sync/` live round-trip.
  - **Conflict rule (honest, spec §5):** revlog **union** (stock, holds) · card scheduling **LWW by mod time** (stock, holds) · device-UUID tie-break **DEFERRED** (Thursday demo made deterministic by controlling sync order + recording UUIDs) · structural divergence → **forced full sync** (so the Thursday conflict demo must be pure review divergence).
  - **Gotchas:** `10.0.2.2` (not `127.0.0.1`) from the emulator; empty-server first-contact = full upload then download; `SYNC_USER1` required; `rm -rf sync/.sync-data` to reset; keep server engine == clients == `ea3acae`.
  - **Last verified against:** `f15cubing/anki@ea3acae`.

- [ ] **Step 2: Update `docs/codebase/INDEX.md`**

Move the Planned row *"Sync conflict rules …"* into the Built table:
```
| Sync foundation (self-hosted server + conflict rule, W4) | `docs/codebase/sync.md` | `sync/run-sync-server.sh`, `sync/roundtrip_smoke.py`, root `Makefile` (`sync-server`/`sync-smoke`); server engine `anki@ea3acae` | `f15cubing/anki@ea3acae` |
```
Remove the now-built entry from the "Planned areas" table (leave the conflict-*implementation* note for Thursday if desired).

- [ ] **Step 3: Update `docs/STATUS.md`**

Bump "Last updated"; add a **Done** entry for this PR (sync foundation: launcher + headless smoke + live desktop↔Android round-trip + `sync.md`); replace the "In flight" placeholder with W4 done → next is Thursday (7b full two-way proof + 7g crash/offline).

- [ ] **Step 4: Update `docs/execution-plan.md`**

Check the Wednesday **Sync foundation** box:
```
- [x] Conflict rule documented (PRD D3). Stand up `anki-sync-server` (pinned tag). Manual sync smoke test. — **W4:** `make sync-server` (engine `ea3acae`); headless `roundtrip_smoke.py` green; live desktop↔Android round-trip with Check-DB clean (`docs/evidence/w4-sync/`); rule in `docs/codebase/sync.md`. 7b/7g deferred to Thursday.
```

- [ ] **Step 5: Commit the docs**

```bash
git add docs/codebase/sync.md docs/codebase/INDEX.md docs/STATUS.md docs/execution-plan.md
git commit -m "docs(w4): sync runbook + INDEX/STATUS/execution-plan (foundation built)"
```

- [ ] **Step 6: Self-review (fast lane) + open the PR**

Verify against `.cursor/skills/shipping-changes/pr-checklist.md` fast-lane checklist: non-engine ✓, on a branch ✓, `make sync-smoke` passed + evidence attached ✓, docs updated ✓, intent note ✓, STATUS updated ✓. Then:
```bash
git push -u origin agent/w4-sync-foundation
gh pr create --base main --head agent/w4-sync-foundation \
  --title "W4: sync foundation — self-hosted anki-sync-server + desktop↔Android round-trip" \
  --body "$(cat <<'EOF'
## What & why (fast lane)
Stand up a pinned self-hosted anki-sync-server on our engine (ea3acae) and prove a card + review state round-trips desktop↔Android with no corruption — the Wednesday sync foundation. No engine/submodule changes.

## Area(s) touched
`sync/`, root `Makefile`, `docs/codebase/sync.md` + INDEX/STATUS/execution-plan, `docs/evidence/w4-sync/` — engine/Rust PR? no

## Docs updated
`docs/codebase/sync.md` (new), INDEX (Planned→Built), STATUS, execution-plan (Wednesday sync box).

## Test evidence
`make sync-smoke` green (note+revlog cross A→server→B, quick_check ok); live desktop↔Android round-trip both directions with Check-Database clean on both (`docs/evidence/w4-sync/`).

## Engine/Rust extra gate
N/A — no engine code; conflict rule documented (device-UUID tie-break deferred), 7b/7g are Thursday.
EOF
)"
```
Expected: PR URL printed. Fast lane → self-merge permitted after the checklist passes.

---

## Self-Review (plan vs. spec)

- **Spec coverage:** §1 topology → Task 1 + sync.md (Task 4.1); §2 components → Tasks 1–4 (every file mapped); §3 recipe → Task 1 + Task 3; §4.1 headless proof → Task 2; §4.2 live proof → Task 3; §5 conflict rule → Task 4.1; §6 fast lane → Task 4.6; §7 risks (FORK_PY, 10.0.2.2, first-sync direction, SYNC_USER1, media off, stale data dir) → Task 1 Step 5 note, Task 2 Step 3 note, Task 3 steps; §8 tests → Tasks 2–3; §9 acceptance → all; §10 out-of-scope → honored (no 7b/7g/engine change). No gaps.
- **Placeholder scan:** none — full script, launcher, Makefile, and commands are inline.
- **Type/name consistency:** `$FORK_PY`, `SYNC_USER1/HOST/PORT/BASE`, `greuser:grepass`, endpoints `127.0.0.1`/`10.0.2.2:8080`, and the `sync_login`/`sync_collection`/`full_upload_or_download` + `getCard`/`answerCard`/`add_note(note, 1)` APIs match the spec and the verified pylib signatures throughout.
