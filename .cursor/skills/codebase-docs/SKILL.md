---
name: codebase-docs
description: Use when about to read, modify, or add code anywhere in the Anki fork — before editing any module, when navigating an unfamiliar area of the large codebase, or when documentation may be stale. Covers where codebase docs live, how to find the docs relevant to the files you are touching, and the requirement to read them before changing code and update them in the same change.
---

# Codebase Docs

## Overview

This is a large fork. **Read the doc for an area before you change it, and update that doc in the same change.** Docs record the commit SHA they were last verified against, so staleness is detectable. Never edit a module "blind."

## Where docs live

- **Central map:** `docs/codebase/architecture.md` — how the whole fork fits together.
- **Index:** `docs/codebase/INDEX.md` — area → doc file → code paths → last-verified SHA.
- **Co-located docs:** `<area>.md` (or `AGENTS.md`) inside key code directories. A co-located doc is **authoritative** for its directory.

## Find the relevant docs

1. Open `docs/codebase/INDEX.md`.
2. Map the files you are about to touch → their doc(s).
3. If a co-located doc exists in that directory, prefer it — it is authoritative.

## Read before you change (REQUIRED)

Read the area's doc(s) **before** editing. They carry invariants the code alone won't tell you (e.g. "this read path must not return `OpChanges`").

If no doc exists for an area you must change, **create a stub from `module-doc-template.md` as part of your PR.** Missing docs are not an excuse to skip — they are a task to do.

## Update after you change (REQUIRED)

Any change to behavior, public interface, or file layout updates the corresponding doc(s) **in the same PR**, and bumps the `Last verified against:` SHA.

This is enforced: "relevant docs updated" is a base-gate item the reviewer checks in the `shipping-changes` skill. A PR that changes behavior without touching docs gets blocked.

## Templates

- Module/area doc → `module-doc-template.md`
- Central architecture map → `architecture-template.md`

## Red flags — STOP

| Thought | Reality |
|---|---|
| "I'll update the docs in a follow-up PR." | No — same PR. Behavior and its doc travel together. |
| "This area has no doc, so I'll just skip docs." | No — create a stub from the template in this PR. |
| "I read the code, the doc is optional." | No — read the doc; it carries invariants the code doesn't state. |
| "Small change, docs can't be stale." | Bump the `Last verified against:` SHA so the next agent can trust it. |
