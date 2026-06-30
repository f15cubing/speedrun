---
name: working-with-submodules
description: Use when initializing, updating, pinning, or troubleshooting the anki / Anki-Android (and later rsdroid / Anki-Android-Backend) git submodules — e.g. a fresh clone, bumping a pinned version, or a detached-HEAD / "modified submodule" surprise in git status.
---

# Working with Submodules

## Overview

This repo pins the upstream forks as **git submodules** (`anki/`, `Anki-Android/`, and later
`Anki-Android-Backend`/rsdroid). The outer repo stores only a **gitlink** — a pinned commit SHA —
per submodule, plus `.gitmodules`. Get the mechanics right or you'll commit the wrong pin or commit
edits that belong upstream.

## Quick reference

| Goal | Command |
|---|---|
| Fresh clone with everything | `git clone --recurse-submodules <url>` |
| Init/sync after a plain clone or pull | `git submodule update --init --recursive` |
| See pinned SHA vs working state | `git submodule status` |
| Snap a checkout back to its pin | `git submodule update --init --recursive` |

`--recursive` is **required**: rsdroid (`Anki-Android-Backend`) vendors `anki` as its own submodule.

## Bumping a pin (changing which upstream commit we use)

1. `cd <submodule>` → `git fetch` → `git checkout <tag-or-sha>`.
2. `cd ..` → `git add <submodule>` (this stages the new gitlink) → commit.
3. **In the same change**, update every place that records that submodule's pinned commit: the
   `Last verified against:` SHA in the relevant `docs/codebase/` area doc(s), `INDEX.md`, and
   `architecture.md`, plus the **"Pinned upstream versions"** line in `README.md`. (Required by
   `codebase-docs`.)
4. Re-run the touched area's checks (**REQUIRED:** use `building-and-testing`) — a pin bump can break
   the build.

## Gotchas — STOP

| Symptom | Reality / fix |
|---|---|
| `git status` shows a submodule as "modified (new commits)" you didn't intend | You moved its HEAD. Either intend it (bump flow above) or `git submodule update` to snap back to the pin. |
| You edited files *inside* a submodule | Those changes belong upstream, not in this repo. Don't `git add` them here. (Our planned engine change will live on a tracked fork; until then, don't commit inside the submodule dir.) |
| Submodule shows "detached HEAD" | Normal — submodules check out a specific commit, not a branch. Only a problem if you're trying to commit inside it. |
| `.gitmodules` URL changed but the checkout didn't | `git submodule sync --recursive` then `git submodule update --init --recursive`. |

## Don't

- Don't `git add` a submodule bump without bumping its docs' `Last verified against:` SHA in the same change.
- Don't commit work *inside* a submodule from this outer repo.
