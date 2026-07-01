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

# Resolve the desktop fork's COMPLETE build. VERIFIED 2026-07-01: the importable engine is the
# primary worktree's build (its out/pylib carries generated buildinfo + _rsbridge). This
# worktree's own anki/out is only partially built. Override FORK_ANKI/FORK_PY in sync/.env.
: "${FORK_ANKI:=/Users/felipecaicedo/Desktop/alpha/speedrun/anki}"
FORK_PY="${FORK_PY:-$FORK_ANKI/out/pyenv/bin/python}"
export PYTHONPATH="$FORK_ANKI/out/pylib${PYTHONPATH:+:$PYTHONPATH}"
if [[ ! -x "$FORK_PY" ]]; then
  echo "ERROR: desktop-build Python not found at: $FORK_PY" >&2
  echo "Build the desktop fork (cd \$FORK_ANKI && ./ninja pylib qt) or set FORK_ANKI/FORK_PY in sync/.env." >&2
  exit 1
fi
if ! "$FORK_PY" -c 'import anki, anki.buildinfo, anki.syncserver' 2>/dev/null; then
  echo "ERROR: $FORK_PY cannot import our built 'anki' (buildinfo/_rsbridge missing on PYTHONPATH=$PYTHONPATH)." >&2
  echo "Rebuild the desktop fork: cd \$FORK_ANKI && ./ninja pylib qt" >&2
  exit 1
fi

mkdir -p "$SYNC_BASE"
echo "anki-sync-server  (engine f15cubing/anki@ea3acae, via $FORK_ANKI/out/pylib)"
echo "  data dir : $SYNC_BASE"
echo "  desktop  : http://127.0.0.1:${SYNC_PORT}/"
echo "  emulator : http://10.0.2.2:${SYNC_PORT}/"
echo "  account  : ${SYNC_USER1%%:*}"
exec env RUST_LOG="${RUST_LOG:-anki=info}" "$FORK_PY" -m anki.syncserver
