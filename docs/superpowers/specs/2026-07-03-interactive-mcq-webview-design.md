# Interactive MCQ webview (card template) — Design Spec

> Make the "GRE Math MCQ" note type **interactive**: tappable A–E options with immediate
> correct/incorrect feedback + explanation reveal, rendered in Anki's card **webview** on
> **both** desktop and Android, grading on the normal **FSRS** loop. Fast lane
> (`pipeline/` + docs), no engine/submodule change. Dated 2026-07-03.

## Decisions (locked with owner)

- **Approach:** enhance the existing `MCQ_MODEL` card template (`pipeline/build_deck.py`)
  with HTML/CSS/JS. It travels *with* the deck → ships to desktop **and** AnkiDroid for
  free, renders in the reviewer's webview, grades natively on FSRS. **Not** a separate
  SvelteKit route (desktop-only, engine-lane, duplicates reviewer logic — rejected).
- **Grading (now):** **manual**. Tapping an option locks the choice, shows green/red +
  the correct option + the explanation; the user still presses the normal
  **Again/Hard/Good/Easy** button. Zero scheduler hacking → safe + identical on both
  platforms.
- **Grading (future, documented follow-up — NOT this change):** auto-answer via a reviewer
  JS hook — a **correct** tap lets FSRS schedule normally (Good), a **wrong** tap routes to
  **Again**. That touches the reviewer/answer path (engine lane, different-agent review);
  out of scope tonight.

## Global constraints

- **Fast lane.** Only `pipeline/` (the template string + tests) + docs. No `rslib`,
  `.proto`, FFI, or submodule pin bump tonight.
- **Deterministic + byte-stable build preserved.** The template is static markup; the
  card *content hash* (`cards_content_hash`) is computed from card data, not template
  HTML, so determinism is unaffected. `make deck-asset-check` stays green.
- **LaTeX preserved.** Option/question/explanation text is delimited LaTeX; the template
  must re-run MathJax typesetting on any content it reveals.
- **Self-study feedback is honest.** The correct index is embedded in the card (from
  `{{CorrectOption}}`) so the client can give instant feedback. This is a study aid, not a
  secure exam — Exam Mode (`gre-exam`) is the firewalled, key-withheld surface; the MCQ
  study card is deliberately open-book on the answer after you commit.

## 1. Component & data flow

```
Reviewer webview (desktop qt / AnkiDroid) renders the MCQ card template:
  FRONT  {{Question}} + A–E buttons (from {{OptionA..E}}), correct letter {{CorrectOption}} hidden
    │  user taps an option
    ▼
  JS: lock all buttons · mark tapped green/red · highlight correct · reveal {{Explanation}} · re-typeset MathJax
    │  user presses Again/Hard/Good/Easy (unchanged FSRS path)
    ▼
  BACK  {{FrontSide}} preserved (tapped state) + "Correct: X" + explanation + leaf tag
```

Single unit: the `MCQ_MODEL` template (qfmt/afmt/css) in `pipeline/build_deck.py`. Inputs
are the 9 existing fields (unchanged). No new fields, no new note type, no id change (the
model id stays `gre-speedrun::model::mcq-tagged::v1` so existing MCQ notes keep working).

## 2. Front template (qfmt)

- Render `{{Question}}`, then five `<button class="mcq-opt" data-i="0..4">` with `A. {{OptionA}}` … `E. {{OptionE}}`.
- Hidden `<span id="mcq-correct">{{CorrectOption}}</span>` (the letter) + a hidden explanation block `{{Explanation}}` revealed on tap.
- Inline JS (no external deps): on `click`, if not already answered → add `answered`, mark the clicked button `correct`/`wrong`, add `correct` to the true option, show the explanation, call `MathJax`/`typeset` if present. Idempotent + guarded so re-taps do nothing.
- Must degrade gracefully if JS is disabled (options still readable as text; the back side still shows the answer).

## 3. Back template (afmt)

`{{FrontSide}}` (keeps the answered state on the same card) + `<hr>` + `Correct: {{CorrectOption}}` + `{{Explanation}}` + the dimmed `{{LeafTag}}`. Re-typeset MathJax.

## 4. CSS

Extend the existing card CSS with `.mcq-opt` states (default / hover / `.correct` green / `.wrong` red / disabled after `.answered`). Tap targets ≥ 44px for the phone. Respect `.night-mode` (Anki toggles it) by using colors that read on both.

## 5. Testing (`pipeline/tests/test_mcq_notetype.py`, extended)

- **Template shape:** `MCQ_MODEL` qfmt contains five option placeholders + tappable
  `mcq-opt` buttons + a correct-answer hook + the interaction JS; afmt reveals the key +
  explanation.
- **No plaintext leak of the letter on the front *label*:** the visible A–E labels come
  from the option fields, and the correct letter appears only inside the hidden hook (so
  the rendered question doesn't announce the answer before a tap). (Assert the hidden
  element wraps `{{CorrectOption}}`.)
- **Existing invariants stay green:** 9 fields, one topic tag, `CorrectOption` matches
  index, content hash stable, MCQ count unchanged.
- All assertions are on the produced model/template strings + `load_all_cards` — pure,
  deterministic, no Anki runtime needed.

## 6. Manual GUI smoke (recorded)

Rebuild the deck (`python pipeline/build_deck.py --seed 42`), import into the running
desktop app, review an MCQ card: tap a right and a wrong option, confirm green/red +
explanation + LaTeX render, then grade with a normal ease button. (Android parity is
inherent to the template; verified opportunistically when the emulator is free — the deck
re-bundle into the app submodules + `GRE_DECK_VERSION` bump is the Sunday follow-up.)

## 7. Lane, risks, follow-ups

- **Lane:** fast lane (`pipeline/` template + tests + docs). No engine change.
- **Risks:** (a) reviewer MathJax hook name differs across surfaces → call the standard
  `globalThis.MathJax`/`typeset` defensively, guard with `typeof`. (b) template JS runs in
  both the desktop `qt` webview and AnkiDroid's — keep it vanilla ES5-safe, no modules.
- **Follow-ups (separate, engine-lane):** re-bundle the `.apkg` into `anki/` + `Anki-Android/`
  assets + bump `GRE_DECK_VERSION` (so existing installs re-import the interactive template);
  the **auto-grade** reviewer hook (right→FSRS, wrong→Again).

## 8. Acceptance criteria

- MCQ cards render five **tappable** options in the reviewer; tapping gives immediate
  correct/incorrect + explanation + correct-option highlight; LaTeX typesets.
- Grading is the unchanged FSRS ease path (manual).
- Deterministic byte-stable build preserved; all `test_mcq_notetype.py` assertions
  (existing + new) green; deck rebuilds through the coverage/verification gates.
- Ships via the deck to both apps (no engine/submodule change in this PR).
