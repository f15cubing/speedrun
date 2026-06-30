<!-- Raw sub-agent response. Captured: 2026-06-29. Round 1. -->
<!-- Prompt: prompts/06-sync-phone-companion.md | Critique: critiques/06-sync-phone-companion.md -->
<!-- Do not edit; this is the source record. -->

# Feasibility Report: Shared Rust Engine Flashcard App with Two-Way Offline Sync

**Scope:** One-week engineering feasibility, modeled on Anki/AnkiDroid (`ankitects/anki`, `ankidroid/Anki-Android`, `ankidroid/Anki-Android-Backend`). Confidence tags: **High** = confirmed in primary source/code; **Medium** = strong secondary source or maintainer statement; **Low/[inferred — verify in repo]** = reasoned from architecture, not seen verbatim.

---

## SECTION A — Anki Sync Protocol Overview

**Two HTTP endpoints.** The modern Rust sync exposes `/sync/` (collection sync, transactional, USN-based) and `/msync/` (media sync, file/hash-based). *Source: anki-cloud ADR citing `rslib/src/sync/`; type: secondary repo doc; confidence: High.*

**Collection endpoints/routes.** Observed against `sync.ankiweb.net`: `/sync/meta`, `/sync/start`, `/sync/applyChanges`, `/sync/chunk`, `/sync/applyChunk`, `/sync/sanityCheck2`, `/sync/finish`, plus `hostKey`, `upload`, `download`. Media: `/msync/begin`, `/msync/mediaChanges`. *Source: dsnopek/anki-sync-server PR #63 (captured live traffic), ankicommunity `sync_app.py` operations list `['meta','applyChanges','start','applyGraves','chunk','applyChunk','sanityCheck2','finish']` plus `valid_urls = ... + ['hostKey','upload','download']`; type: captured traffic + server source; confidence: High.* Documented modern sequence: `hostKey → meta → start → applyChanges ↔ getChanges → [chunks] → sanityCheck2 → finish`. *Source: anki-cloud ADR; type: secondary; confidence: Medium.*

**Module structure (`rslib/src/sync`).** Confirmed: top-level `rslib/src/sync/mod.rs` (`HttpSyncClient`); `rslib/src/sync/http_client.rs` (reqwest + protobuf); `rslib/src/sync/login.rs` (`SyncAuth`); `rslib/src/sync/collection/mod.rs` (`CollectionSyncer`); `rslib/src/sync/collection/download.rs` and `rslib/src/sync/collection/upload.rs` (one-way full sync); `rslib/src/sync/media/mod.rs` (`MediaSyncer`); `rslib/src/sync/http_server/` (self-hosted server handler layer). *Source: DeepWiki ankitects/anki (commit 57e67f84), anki-cloud ADR; type: secondary index of source; confidence: High for these paths.* Further per-phase files (e.g. `chunks.rs`, `graves.rs`, `sanity.rs`, `meta.rs`, `finish.rs`, `protocol.rs`, `request/`, `response.rs`, `version.rs`) are **[inferred — verify in repo]**; names match the documented sequence but were not directly enumerated.

**What gets synced.** Collection sync moves the SQLite collection database (`collection.anki2`): notes, cards, the review log (`revlog`), decks, deck config, note types (notetypes/fields/templates), tags, and `graves` (deletions). Media files sync separately via `/msync/` (hash-identified), with metadata in `collection.media.db`. *Source: AnkiDroid Database-Structure wiki + anki-cloud ADR (`<SYNC_BASE>/<username>/collection.anki2`, `collection.media.db`, `collection.media/`); type: wiki + repo doc; confidence: High.*

**USN (Update Sequence Numbers).** A monotonically increasing per-collection counter is stored per card/note/deck/revlog (`usn` column, indexed `ix_cards_usn` etc.). Client sends its last-known USN; server returns all changes since. A pending local change is stored with `usn = -1`; `usn < server_usn` means "pull." *Source: AnkiDroid schema wiki + DeepWiki citing `rslib/src/decks/mod.rs`; type: wiki + source index; confidence: High.*

**Incremental vs full sync.** Normal sync = incremental USN-diff merge. Full sync = one-way upload or download that replaces an entire side. The `col` row carries `scm` (schema modification time) and `ls` (last sync). When `scm > ls`, a normal merge is impossible and a full sync is forced. *Source: legacy `collection.py` `schemaChanged(): return self.scm > self.ls` (Rust ports this); AnkiDroid schema wiki comment "If server scm is different from the client scm a full-sync is required"; type: source + wiki; confidence: High (legacy)/Medium ([inferred — verify in repo] for the exact Rust `meta.rs` comparison).* Full sync also triggers on a `sanityCheck2` count mismatch (`SanityCheckFailed` = "Local/Server counts don't match"). *Source: DeepWiki citing `rslib/src/error/network.rs`; confidence: Medium.* The UI shows blue sync button = normal sync, red = full sync. *Source: Anki Manual syncing.html; confidence: High.*

---

## SECTION B — Conflict-Resolution Model + Proposed Winner Rule (most important)

**The crux finding — split behavior.** Anki does NOT do field-level merge of two independently-reviewed copies of a card. Instead it splits behavior by data type:

1. **`revlog` entries are unioned (both survive).** Each review log row's primary key `id` is the epoch-millisecond timestamp of the review, so two reviews from two devices have distinct IDs and both are appended. *Source: Anki Manual: "If the same card has been reviewed in two different locations, both reviews will be marked in the revision history"; AnkiDroid schema (revlog `id` = epoch-ms PK); type: official manual + schema; confidence: High.*

2. **Card scheduling state (due/interval/ease/queue) is last-writer-wins.** The card is "kept in the state it was when it was most recently answered." *Source: Anki Manual syncing.html#conflicts, quoted on forums by L.M.Sherlock; confidence: High.* Maintainer Damien Elmes (dae) confirmed directly on the forum: "When you change a card in multiple locations, the most recent change will win. It won't cause long term harm, but it's better to sync at the start and end of each session to avoid wasted work." *Source: forums.ankiweb.net thread 26442; type: maintainer statement; confidence: High.*

So: **revlog merges; scheduling state does not — one side wins by recency.** This resolves the ambiguity in the prompt: routine reviews/edits on different cards merge cleanly via USN; same-card reviews keep both log entries but only one scheduling outcome.

**True conflicts → forced one-way full sync.** Genuinely unmergeable divergence (schema changes like adding a field/removing a template, or a sanity-check count mismatch) is NOT resolved field-by-field. Anki warns and forces a one-way sync: "your decks here and on AnkiWeb differ in such a way that they can't be merged together, so it's necessary to overwrite the decks on one side." The user picks Upload (keep local) or Download (keep server); the losing side's divergent changes are discarded. *Source: Anki Manual syncing.html + `rslib/ftl/sync.ftl` strings (`sync-conflict`); type: manual + source strings; confidence: High.* A failed/interrupted sync can also force a one-way sync on the next attempt. *Source: dae via anki-android Google Group; confidence: Medium.*

**Mechanism summary.** Server is authoritative single-source-of-truth keyed by USN. Same-deck/same-card *reviews* merge (USN diff + revlog union + newer-mtime card state); structural divergence does not merge and falls back to whole-collection overwrite. The "newer mtime wins" at the card/note row level is consistent with `set_modified()` setting `mtime_secs = now()` in `rslib/src/decks/mod.rs`, but the exact card-merge function/comment is **[inferred — verify in repo].**

**How to confirm empirically:** stand up the self-hosted Rust sync server, review the same card offline on two clients, sync sequentially, then inspect: `SELECT count(*) FROM revlog WHERE cid=?` (expect both reviews) and the `cards` row (`due`, `ivl`, `factor`, `mod`, `usn`) to verify only the most-recently-answered state persists. (Procedure in Section D.)

### Proposed winner rule for the custom app
**Rule: "Latest-review-timestamp-wins for scheduling state; union of revlogs; deterministic device-ID tie-break."**

- **Scheduling state (due, interval, ease, queue, reps, lapses):** the copy whose most recent review (max revlog `id` for that card) is newest wins. Ties broken by a stable per-device ID (lexicographically lower device UUID wins) so the result is deterministic regardless of sync order.
- **Review log:** always take the union of all revlog rows across devices (dedup on the millisecond `id` + device salt). No review is ever lost.
- **Structural/schema changes:** detect via a schema-version/`scm`-equivalent; if both sides changed structurally, refuse silent merge and prompt the user to choose a winning side (mirror Anki).

**Why defensible:** (a) it matches Anki's proven, decade-tested model so behavior is predictable to power users; (b) revlog union preserves the audit trail and FSRS/SRS training data even when scheduling state is overwritten; (c) the device-ID tie-break removes Anki's one weakness (order-dependence / "last sync wins") and makes the outcome reproducible and testable; (d) it avoids the complexity and failure modes of CRDT field-merging that cannot be validated in a one-week build.

---

## SECTION C — Running the Same Rust Engine on a Phone

### Android (via AnkiDroid's `rsdroid`)
AnkiDroid consumes the upstream Rust `anki`/`rslib` backend through the **`ankidroid/Anki-Android-Backend`** repo (artifact namespace `net.ankiweb.rsdroid`). The build includes `anki` as a git submodule, compiles the Rust via a JNI bridge, and emits two artifacts: **`rsdroid.aar`** (Kotlin/Java backend code, web assets, and the Rust backend compiled for Android architectures) and **`rsdroid-testing.jar`** (host-platform build for Robolectric tests). Communication Java↔Rust is via Protocol Buffers. *Source: Anki-Android-Backend README + DeepWiki; type: repo doc; confidence: High.*

**What you get "for free":** the compiled Rust backend (`net.ankiweb.rsdroid.Backend`), the protobuf RPC interface, the SQLite-backed collection, scheduling/FSRS, AND **collection + media sync already working** (the same `rslib/src/sync` code). Toolchain: Android Studio, NDK (version pinned in `gradle/libs.versions.toml`), Rust targets auto-installed; build with `build-aar`/`build-robo` scripts; single-arch build is the default. *Source: Anki-Android-Backend README + PR #246 (dae); confidence: High.*

**Alternative — compile `rslib` yourself with NDK + cargo-ndk + UniFFI/hand-JNI.** Feasible but you reimplement everything AnkiDroid already solved: protobuf RPC plumbing, the SQLite open helper, sync wiring, multi-arch packaging. Effort is high and offers no engine advantage. **Recommendation: build on AnkiDroid's existing backend, not a from-scratch port.** *Confidence: High (effort comparison), Medium (exact effort numbers [inferred]).*

### iOS (realistic assessment)
There is **no open-source Anki iOS app** — AnkiMobile is closed-source, written by the lead developer of Anki/AnkiWeb (Damien Elmes), priced at **$24.99 one-time** (usable on up to 5 of your iOS devices), and is his primary funding source. The App Store listing states verbatim: "Sales of this app support the development of both the computer and mobile version, which is why the app is priced as a computer application. AnkiMobile was written by the lead developer of Anki and AnkiWeb, and it has been around since 2010." The Anki FAQ adds: "I have experimented with different price points in the past, and reducing the price resulted in a net decrease in income... For this reason, neither a price change nor a sale is likely in the foreseeable future." *Source: App Store listing + faqs.ankiweb.net + forums.ankiweb.net thread 51470; confidence: High.* So iOS gives you no reusable wrapper; you must build one.

**Path:** compile `rslib` for `aarch64-apple-ios` (+ `aarch64-apple-ios-sim`) as a static lib (`crate_type = ["staticlib"]`), generate Swift bindings via UniFFI (`uniffi-bindgen generate --language swift`) or cbindgen, package as an `.xcframework` via `xcodebuild -create-xcframework` (remembering to rename the generated `*FFI.modulemap` to `module.modulemap`), and drive the protobuf backend from Swift. *Source: multiple UniFFI/iOS guides (dev.to, boehs.org, strathweb); type: how-to; confidence: High for general toolchain.* But `rslib` is a large crate (SQLite, FSRS, sync, protobuf) — UniFFI does not auto-wrap its protobuf RPC surface, and you must also handle provisioning, signing, TestFlight/sideload, and on-device sync verification. **Blunt verdict: standing up the real engine + two-way sync on iOS in ONE WEEK is NOT realistic.** *Confidence: High (judgment).*

### Minimum viable "same engine on both" + grade ceiling
**Recommendation: Android via AnkiDroid's `rsdroid` backend (real shared `rslib`, sync works out of the box) + desktop Anki (same `rslib`).** This is honestly "the same Rust engine on both platforms" with working two-way sync, achievable in the week. The prompt notes that **no phone companion caps the grade at 70%**; shipping the Android client via `rsdroid` clears that ceiling. A from-scratch iOS port is high-risk and should be explicitly deferred. *Confidence: High.*

---

## SECTION D — Test Recipes

### 7b — Offline / Sync test
**Self-hosted server setup (built-in Rust sync server):**
```
cargo install --locked --git https://github.com/ankitects/anki.git --tag 25.02.5 anki-sync-server
# (replace 25.02.5 with the latest Anki version; protoc must be installed)
SYNC_USER1=user:pass SYNC_BASE=/path/to/serverdata anki-sync-server
```
Defaults if unset: `SYNC_HOST=0.0.0.0`, `SYNC_PORT=8080`, `SYNC_BASE=~/.syncserver`, `MAX_SYNC_PAYLOAD_MEGS=100`. Declare `SYNC_USER2`, `SYNC_USER3`, … for additional accounts. Point both clients at `http://<host>:<port>/` in Preferences → Sync. *Source: Anki Manual sync-server.html; confidence: High.* The server stores `<SYNC_BASE>/<username>/collection.anki2` (+ media); `SYNC_USER1` is mandatory. The server folder must be separate from any client's data folder.

**No-loss test (the merge case):** (1) Sync both clients clean. (2) Airplane-mode both. (3) On phone review 10 cards (deck slice A); on desktop review 10 *different* cards (deck slice B). (4) Reconnect; sync phone, then desktop, then phone again. (5) Verify: on each client `SELECT count(*) FROM revlog` increased by exactly 20 vs baseline, and 20 distinct cards advanced. Expect a clean USN merge, with none lost or double-counted.

**Same-card conflict test (must be constructed to be meaningful):** (1) Sync clean. (2) Offline, review the SAME card on both devices, answering differently (e.g. "Again" on phone, "Easy" on desktop), recording each device's wall-clock answer time. (3) Sync phone, then desktop. (4) Inspect: `SELECT count(*) FROM revlog WHERE cid=<id>` should show BOTH reviews; the `cards` row (`due`,`ivl`,`factor`,`mod`,`usn`) should equal the **most-recently-answered** device's outcome. **Risk flag:** if the divergence trips a schema/sanity issue, Anki forces a one-way full sync (whole-side overwrite) instead of merging — so keep the test to pure review divergence (no note-type/template edits) to demonstrate the *scheduling* winner rule rather than the full-sync fallback. *Source: Anki Manual conflicts + dae forum statement; confidence: High.*

### 7g — Crash / corruption test
**Procedure:** script-kill the app process (`kill -9` / `am force-stop`) mid-review across 20 trials at randomized points (during answer commit, during next-card fetch). After each kill, reopen and run the collection integrity check (Tools → Check Database); assert zero corrupted collections and a consistent revlog count (≤1 in-flight review may be rolled back, never partially written).

**Why it's safe — SQLite transactions + WAL.** Anki's storage layer wraps writes in transactions: the Rust backend uses `BEGIN IMMEDIATE` for writes via `rusqlite`, so an incomplete transaction is atomically rolled back on restart — no torn writes. *Source: DeepWiki Storage Layer citing `rslib/src/storage/sqlite.rs` ("Immediate transactions for write operations (BEGIN IMMEDIATE)"); type: source index; confidence: High.* The `open_or_create_collection_db` path sets PRAGMAs on open. WAL mode (`PRAGMA journal_mode=WAL`) gives atomic commit + crash recovery by replaying/truncating the `-wal` file; the anki-cloud ADR explicitly states the collection "requires random access, WAL, and file locking." *Source: anki-cloud ADR; type: secondary; confidence: Medium — the exact PRAGMA line in `sqlite.rs` is **[inferred — verify in repo]**.* **Graceful offline degradation:** with no network, the engine operates fully on local SQLite; sync simply returns a network error (`NetworkError::Offline`) and the UI shows "Cannot connect to AnkiWeb" without blocking study. *Source: DeepWiki `rslib/src/error/network.rs`; confidence: Medium.*

### 7h — Benchmark (`make bench`)
**Targets & percentiles:** measure p50/p95/worst-case for (a) button acknowledgment (answer card), (b) next-card fetch, (c) dashboard/deck-list load, (d) full-sync completion, all on a 50,000-card deck.

**Tooling:**
- **Engine-level latency:** Rust **Criterion** (the de-facto Rust micro-benchmark crate; current release 0.8.2, MSRV Rust 1.86). Configure `[dev-dependencies] criterion = { version = "0.8", features = ["html_reports"] }` and `[[bench]] name="..." harness=false`. It gives statistically rigorous percentiles and HTML reports — best for answer-card / next-card-fetch / deck-tree build, called directly against `rslib`'s public API. *Source: Criterion.rs book + crates.io; confidence: High.* Note Criterion can only hit the crate's public API; for internal functions use a custom timing harness. *Source: winterfell issue #264; confidence: Medium.*
- **End-to-end / sync:** a custom timing harness wrapping the protobuf backend RPC, or **hyperfine** for CLI-level full-sync timing; emit latency arrays and compute percentiles (sort; p95 = value at 0.95·N).
- **Synthetic 50k collection:** generate programmatically via the backend (add one note type, loop `add_note` 50,000×) or by SQL-inserting 50k `cards`/`notes` rows with valid `guid`/`usn`, then run the integrity check. Seed `revlog` for realistic sync payloads. (Keep the uncompressed collection under the 100 MB `MAX_SYNC_PAYLOAD_MEGS` default, or raise it, to benchmark full sync against the local server.)

`make bench` should: build release, generate (or restore) the 50k collection, run Criterion groups for engine ops, run the harness/hyperfine for sync, and print a p50/p95/worst table per target.

---

## Self-Confidence Summary
- **Section A (endpoints/modules):** High on endpoint names (captured traffic + server source) and top-level module paths; per-phase filenames inside `collection/` are **[inferred — verify in repo].**
- **Section B (conflict model):** High — directly backed by the Anki Manual and a verbatim Damien Elmes forum statement. The revlog-union-vs-scheduling-LWW split is confirmed; exact merge function names are [inferred].
- **Section C (phone):** High — AnkiDroid backend artifacts and AnkiMobile closed-source status/pricing are confirmed; the iOS one-week verdict is a well-grounded judgment.
- **Section D (tests):** High on sync-server setup and SQLite transaction safety; the WAL exact PRAGMA and some benchmark internals are partly [inferred].

## One-Line Recommendation
**Ship Android via AnkiDroid's existing `rsdroid` Rust backend (real shared `rslib`, two-way sync working out of the box) paired with desktop Anki on the same `rslib` — this is genuinely "the same Rust engine on both" and clears the 70% no-phone grade ceiling; defer the high-risk from-scratch iOS port.**
