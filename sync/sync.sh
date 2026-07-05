#!/usr/bin/env bash
# GRE fork — sync operator control tool for the self-hosted Anki sync server.
#   up · status · verify · down · reset · urls · doctor
# LOCAL TEST HARNESS ONLY — never expose publicly. Fast lane, no engine change.
# Companion doc: docs/codebase/sync.md ("Operating sync").
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Local overrides (gitignored) win; otherwise the committed defaults below apply.
if [[ -f "$REPO_ROOT/sync/.env" ]]; then set -a; source "$REPO_ROOT/sync/.env"; set +a; fi

: "${SYNC_USER1:=greuser:grepass}"
: "${SYNC_PORT:=8080}"
: "${SYNC_BASE:=$REPO_ROOT/sync/.sync-data}"
: "${FORK_ANKI:=/Users/felipecaicedo/Desktop/alpha/speedrun/anki}"
FORK_PY="${FORK_PY:-$FORK_ANKI/out/pyenv/bin/python}"
export SYNC_USER1 SYNC_PORT SYNC_BASE FORK_ANKI

RUN_DIR="$REPO_ROOT/sync/.run"
PID_FILE="$RUN_DIR/server.pid"
LOG_FILE="$RUN_DIR/server.log"
PYLIB="$FORK_ANKI/out/pylib"

ACCOUNT="${SYNC_USER1%%:*}"
PASSWORD="${SYNC_USER1#*:}"
DESKTOP_URL="http://127.0.0.1:${SYNC_PORT}/"
EMULATOR_URL="http://10.0.2.2:${SYNC_PORT}/"

if [[ -t 1 ]]; then C_G=$'\033[32m'; C_Y=$'\033[33m'; C_R=$'\033[31m'; C_0=$'\033[0m'; else C_G=""; C_Y=""; C_R=""; C_0=""; fi
say()  { printf '%s\n' "$*"; }
ok()   { printf '  %s✓%s %s\n' "$C_G" "$C_0" "$*"; }
warn() { printf '  %s!%s %s\n' "$C_Y" "$C_0" "$*"; }
bad()  { printf '  %s✗%s %s\n' "$C_R" "$C_0" "$*" >&2; }

port_pid() { lsof -tiTCP:"$SYNC_PORT" -sTCP:LISTEN 2>/dev/null | head -n1; }

running_pid() {
  [[ -f "$PID_FILE" ]] || return 1
  local pid; pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null && { printf '%s' "$pid"; return 0; }
  return 1
}

http_ok() {  # any HTTP response (incl. 404) == serving; connection refused == down
  if command -v curl >/dev/null 2>&1; then
    curl -sS -o /dev/null -m 2 "$DESKTOP_URL" >/dev/null 2>&1
    return $?
  fi
  "$FORK_PY" - "$SYNC_PORT" <<'PY' >/dev/null 2>&1
import sys, urllib.request, urllib.error
port = sys.argv[1]
try:
    urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=2)
except urllib.error.HTTPError:
    sys.exit(0)
except Exception:
    sys.exit(1)
sys.exit(0)
PY
}

engine_build() {
  PYTHONPATH="$PYLIB${PYTHONPATH:+:$PYTHONPATH}" "$FORK_PY" - <<'PY' 2>/dev/null || printf 'unknown'
import anki.buildinfo as b
print(f"anki {getattr(b, 'version', '?')}  (buildhash {getattr(b, 'buildhash', '?')})", end="")
PY
}

status_card() {
  local pid="$1" uptime
  uptime="$(ps -o etime= -p "$pid" 2>/dev/null | tr -d ' ' || true)"
  say ""
  say "sync server UP  (pid $pid, port $SYNC_PORT, uptime ${uptime:-0s})"
  say "  engine   : $(engine_build)"
  say "  data dir : $SYNC_BASE"
  say "  account  : $ACCOUNT"
  say "  desktop  : $DESKTOP_URL   -> Preferences > Syncing > self-hosted sync server URL"
  say "  emulator : $EMULATOR_URL   -> AnkiDroid > Settings > Sync > custom sync server"
  say "  first contact: whoever syncs FIRST must UPLOAD (empty server => full sync); the other DOWNLOADS."
  say "  next: make sync-verify  |  make sync-status  |  make sync-down"
}

cmd_doctor() {
  local fail=0
  say "sync doctor -- preflight ($DESKTOP_URL)"
  if PYTHONPATH="$PYLIB${PYTHONPATH:+:$PYTHONPATH}" "$FORK_PY" -c 'import anki, anki.buildinfo, anki.syncserver' 2>/dev/null; then
    ok "engine build importable ($(engine_build))"
  else
    bad "engine build not importable (FORK_PY=$FORK_PY)"
    say "      fix: cd \"$FORK_ANKI\" && ./ninja pylib qt   (or set FORK_ANKI/FORK_PY in sync/.env)"
    fail=1
  fi
  if [[ -n "${SYNC_USER1:-}" ]]; then ok "SYNC_USER1 set (account: $ACCOUNT)"; else bad "SYNC_USER1 unset -- server would panic"; fail=1; fi
  local lp ours; lp="$(port_pid || true)"; ours="$(running_pid || true)"
  if [[ -z "$lp" ]]; then ok "port $SYNC_PORT free"
  elif [[ -n "$ours" && "$lp" == "$ours" ]]; then ok "port $SYNC_PORT held by our server (pid $lp)"
  else bad "port $SYNC_PORT in use by a foreign process (pid $lp) -- stop it or set SYNC_PORT"; fail=1; fi
  if command -v adb >/dev/null 2>&1 && [[ -n "$(adb devices 2>/dev/null | awk 'NR>1 && $2=="device"{print $1; exit}')" ]]; then
    ok "adb device present -- emulator syncs to $EMULATOR_URL"
  else
    warn "no adb device -- emulator config is manual (AnkiDroid custom sync URL = $EMULATOR_URL)"
  fi
  return $fail
}

cmd_up() {
  local pid
  if pid="$(running_pid)"; then
    if http_ok; then say "sync server already UP (pid $pid)"; status_card "$pid"; return 0; fi
    warn "stale/starting pid $pid not serving -- cleaning up"; kill "$pid" 2>/dev/null || true; rm -f "$PID_FILE"
  fi
  cmd_doctor || { bad "preflight failed -- not starting"; return 1; }
  mkdir -p "$RUN_DIR" "$SYNC_BASE"
  say "starting sync server (background) ..."
  RUST_LOG="${RUST_LOG:-anki=info}" nohup "$REPO_ROOT/sync/run-sync-server.sh" >"$LOG_FILE" 2>&1 &
  local newpid=$!
  printf '%s' "$newpid" >"$PID_FILE"
  local i
  for ((i = 0; i < 20; i++)); do
    if ! kill -0 "$newpid" 2>/dev/null; then
      bad "server exited during startup -- last log lines:"; tail -n 15 "$LOG_FILE" >&2 2>/dev/null || true
      rm -f "$PID_FILE"; return 1
    fi
    if http_ok; then status_card "$newpid"; return 0; fi
    sleep 0.5
  done
  bad "server did not become healthy within ~10s -- last log lines:"; tail -n 15 "$LOG_FILE" >&2 2>/dev/null || true
  return 1
}

cmd_status() {
  local pid
  if pid="$(running_pid)"; then
    if http_ok; then status_card "$pid"; return 0; fi
    warn "pid $pid alive but not serving on $SYNC_PORT (starting up or wedged); see $LOG_FILE"; return 1
  fi
  local lp; lp="$(port_pid || true)"
  if [[ -n "$lp" ]]; then warn "no tracked server, but port $SYNC_PORT held by pid $lp (foreign)"; return 1; fi
  say "sync server DOWN (no tracked pid; port $SYNC_PORT free)"; return 1
}

do_reset() {
  local yes=0; [[ "${1:-}" == "--yes" ]] && yes=1
  if running_pid >/dev/null 2>&1; then bad "server is up -- run 'make sync-down' first"; return 1; fi
  if (( ! yes )); then
    read -r -p "wipe $SYNC_BASE ? [y/N] " ans || true
    [[ "${ans:-}" == "y" || "${ans:-}" == "Y" ]] || { say "reset aborted"; return 0; }
  fi
  rm -rf "$SYNC_BASE"; say "reset: wiped $SYNC_BASE (fresh first-contact on next sync)"
}

cmd_down() {
  local reset=0; [[ "${1:-}" == "--reset" ]] && reset=1
  local pid
  if pid="$(running_pid)"; then
    kill "$pid" 2>/dev/null || true
    local i; for ((i = 0; i < 10; i++)); do kill -0 "$pid" 2>/dev/null || break; sleep 0.3; done
    kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null || true
    rm -f "$PID_FILE"; say "sync server stopped (pid $pid)"
  else
    rm -f "$PID_FILE" 2>/dev/null || true; say "no tracked sync server running"
  fi
  (( reset )) && do_reset --yes || true
  return 0
}

set_desktop_url() {
  say "desktop auto-config (best-effort):"
  warn "the desktop sync URL lives in Anki's pickled profile (needs the app's own Preferences dialog)"
  say "      set it once by hand: Anki > Preferences > Syncing > self-hosted sync server = $DESKTOP_URL, then log in as $ACCOUNT"
}

set_emulator_url() {
  say "emulator auto-config (best-effort):"
  if ! command -v adb >/dev/null 2>&1; then
    warn "adb not found -- set it by hand: AnkiDroid > Settings > Sync > custom sync server = $EMULATOR_URL"; return 0
  fi
  local dev; dev="$(adb devices 2>/dev/null | awk 'NR>1 && $2=="device"{print $1; exit}')"
  if [[ -z "$dev" ]]; then
    warn "no running emulator/device -- set it by hand: custom sync server = $EMULATOR_URL"; return 0
  fi
  if adb -s "$dev" shell run-as com.ichi2.anki true >/dev/null 2>&1; then
    warn "run-as available on $dev, but AnkiDroid's sync-URL pref keys are version-specific"
    say "      set it in-app once: Settings > Sync > custom sync server = $EMULATOR_URL"
    say "      verify host reachability: adb -s $dev shell 'ping -c1 10.0.2.2'"
  else
    warn "com.ichi2.anki not debuggable via run-as on $dev -- set it in-app: custom sync server = $EMULATOR_URL"
  fi
  return 0
}

cmd_urls() {
  local set_desktop=0 do_emu=0 a
  for a in "$@"; do case "$a" in --set-desktop) set_desktop=1 ;; --emulator) do_emu=1 ;; esac; done
  say "sync client config"
  say "  account : $ACCOUNT   password: $PASSWORD"
  say "  desktop : $DESKTOP_URL"
  say "            Preferences > Syncing > self-hosted sync server URL = $DESKTOP_URL   (set BEFORE first login)"
  say "  emulator: $EMULATOR_URL"
  say "            AnkiDroid > Settings > Sync > Custom sync server > Sync URL = $EMULATOR_URL   (10.0.2.2, not 127.0.0.1)"
  say "  first contact: whoever syncs FIRST must UPLOAD; the other DOWNLOADS."
  (( set_desktop )) && { say ""; set_desktop_url; }
  (( do_emu )) && { say ""; set_emulator_url; }
  return 0
}

cmd_verify() {
  running_pid >/dev/null 2>&1 || { say "server not up -- starting it first"; cmd_up || return 1; }
  say "running headless round-trip proof against $DESKTOP_URL ..."
  local rc=0
  SYNC_ENDPOINT="$DESKTOP_URL" SYNC_PORT="$SYNC_PORT" SYNC_USER="$ACCOUNT" SYNC_PASSWORD="$PASSWORD" \
    PYTHONPATH="$PYLIB${PYTHONPATH:+:$PYTHONPATH}" "$FORK_PY" "$REPO_ROOT/sync/roundtrip_smoke.py" || rc=$?
  if (( rc == 0 )); then say "PASS: headless sync round-trip"; else bad "FAIL: headless sync round-trip (rc=$rc)"; fi
  return $rc
}

usage() {
  cat <<EOF
sync operator control tool -- self-hosted Anki sync server (LOCAL TEST HARNESS ONLY)

usage: sync/sync.sh <command> [flags]
       make sync-up | sync-status | sync-verify | sync-down | sync-reset | sync-urls | sync-doctor

commands:
  up        preflight + start server in background + wait until healthy + status card
  status    report server state (pid / port / health / data dir / engine buildhash)
  verify    ensure up, then run the headless round-trip proof (PASS/FAIL)
  down      stop the background server  ( --reset also wipes data )
  reset     wipe the data dir for a clean first-contact  ( --yes to skip confirm )
  urls      print copy-paste client config  ( --set-desktop / --emulator best-effort )
  doctor    preflight checklist only (build / creds / port / emulator)

env (or sync/.env): SYNC_PORT=$SYNC_PORT  SYNC_USER1=$ACCOUNT:***  SYNC_BASE  FORK_ANKI  FORK_PY
EOF
}

cmd="${1:-}"; shift || true
case "$cmd" in
  up)     cmd_up "$@" ;;
  status) cmd_status "$@" ;;
  verify) cmd_verify "$@" ;;
  down)   cmd_down "$@" ;;
  reset)  do_reset "${1:-}" ;;
  urls)   cmd_urls "$@" ;;
  doctor) cmd_doctor "$@" ;;
  -h | --help | help) usage; exit 0 ;;
  "") usage; exit 2 ;;
  *) say "unknown command: $cmd"; usage; exit 2 ;;
esac
