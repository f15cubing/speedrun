"""Study-deck ↔ eval-bank leakage self-audit (PRD §11).

Publishes a **residual leakage rate**: the fraction of held-out eval items whose
`(question, answer)` also appears in the study deck. That is the dangerous kind of
leakage — the same *item* in both corpora — and "leaked test data → that score → 0" is a
hard ceiling. Today the repo only has an exact `(stem, answer)` firewall
(`eval/bank/loader.assert_firewall`, a boolean); this extends it to the layered scan PRD
§11 asks for (exact → normalised → n-gram/Jaccard) and *quantifies* the result.

**Read-only + non-contaminating.** This module is a pure function of two card lists and
**never reads or writes** the eval bank itself — the CLI (`run_leakage_audit.py`) loads
both corpora via their existing read-only loaders and passes them in. It exists to
*protect* the leakage isolation, not to modify the held-out bank.

**Honest framing (important).** The study deck and the authored eval bank are *both*
generated from GRE-math templates (e.g. "Give the antiderivative (omit + C): ∫…"), so
high n-gram / Jaccard overlap between *stems* is **expected structural similarity, not
leakage** — two different items that share a template but differ in parameters. Only an
identical normalised `(question, answer)` is leakage. The near-duplicate layers are
reported for **human adjudication** (PRD §11's 0.75–0.90 band), never counted as leakage.

Scope: PRD §11 layers 1–3 (exact, normalised, 13-gram / token-Jaccard). Embedding-cosine
(layer 4) + MinHash/LSH for scale are a documented phase-2 follow-up.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

NGRAM_N = 13
JACCARD_THRESHOLD = 0.75


def normalize(text) -> str:
    """Collapse whitespace, strip, lowercase (mirrors `eval.bank.loader._normalize`)."""
    return re.sub(r"\s+", " ", str(text).strip().lower())


def tokens(text) -> list[str]:
    return normalize(text).split()


def word_ngrams(text, n: int = NGRAM_N) -> set[str]:
    """Set of `n`-word shingles; empty when the text has fewer than `n` tokens."""
    ts = tokens(text)
    if len(ts) < n:
        return set()
    return {" ".join(ts[i : i + n]) for i in range(len(ts) - n + 1)}


def jaccard(a: set[str], b: set[str]) -> float:
    """Jaccard similarity of two token/shingle sets (0..1); empty∪empty → 0.0."""
    union = a | b
    return len(a & b) / len(union) if union else 0.0


def card_stem(card) -> str:
    return card["question"] if card.get("format") == "mcq" else card.get("front", "")


def card_answer(card) -> str:
    if card.get("format") == "mcq":
        return card["options"][card["correct_index"]]
    return card.get("back", "")


def eval_stem(item) -> str:
    return item["question"]


def eval_answer(item) -> str:
    return item["options"][item["correct_index"]]


@dataclass
class LeakageReport:
    total_eval: int
    exact_qa: list[str] = field(default_factory=list)        # LEAKAGE: (stem, answer) both match
    stem_only: list[str] = field(default_factory=list)       # same stem, different answer (review)
    shared_13gram: list[str] = field(default_factory=list)   # shares a 13-word shingle (review)
    high_jaccard: list[dict] = field(default_factory=list)   # stem token-Jaccard > threshold (review)
    max_jaccard: float = 0.0
    max_jaccard_eval_id: str | None = None
    ngram_n: int = NGRAM_N
    jaccard_threshold: float = JACCARD_THRESHOLD

    @property
    def residual_leakage_rate(self) -> float:
        """The publishable number: fraction of eval items that truly leak (exact QA)."""
        return (len(self.exact_qa) / self.total_eval) if self.total_eval else 0.0

    def as_dict(self) -> dict:
        return {
            "total_eval": self.total_eval,
            "residual_leakage_rate": round(self.residual_leakage_rate, 6),
            "exact_qa_collisions": sorted(self.exact_qa),
            "stem_only_collisions": sorted(self.stem_only),
            "shared_13gram_flags": sorted(self.shared_13gram),
            "high_jaccard_flags": sorted(self.high_jaccard, key=lambda h: -h["jaccard"]),
            "max_jaccard": round(self.max_jaccard, 4),
            "max_jaccard_eval_id": self.max_jaccard_eval_id,
            "ngram_n": self.ngram_n,
            "jaccard_threshold": self.jaccard_threshold,
        }


def scan_leakage(
    study_cards,
    eval_items,
    *,
    ngram_n: int = NGRAM_N,
    jaccard_threshold: float = JACCARD_THRESHOLD,
) -> LeakageReport:
    """Scan every eval item against the whole study deck across the §11 layers."""
    study_qa = set()
    study_stems_norm = set()
    study_ngrams: set[str] = set()
    study_token_sets: list[set[str]] = []
    for card in study_cards:
        stem, answer = card_stem(card), card_answer(card)
        study_qa.add((normalize(stem), normalize(answer)))
        study_stems_norm.add(normalize(stem))
        study_ngrams |= word_ngrams(stem, ngram_n)
        study_token_sets.append(set(tokens(stem)))

    report = LeakageReport(
        total_eval=len(eval_items), ngram_n=ngram_n, jaccard_threshold=jaccard_threshold
    )
    for item in eval_items:
        eid = item["id"]
        stem, answer = eval_stem(item), eval_answer(item)
        nstem, nans = normalize(stem), normalize(answer)

        if (nstem, nans) in study_qa:
            report.exact_qa.append(eid)
        elif nstem in study_stems_norm:
            report.stem_only.append(eid)

        item_ngrams = word_ngrams(stem, ngram_n)
        if item_ngrams & study_ngrams:
            report.shared_13gram.append(eid)

        item_tokens = set(tokens(stem))
        best = 0.0
        for st in study_token_sets:
            j = jaccard(item_tokens, st)
            if j > best:
                best = j
                if best == 1.0:
                    break
        if best > report.max_jaccard:
            report.max_jaccard = best
            report.max_jaccard_eval_id = eid
        if best > jaccard_threshold:
            report.high_jaccard.append({"eval_id": eid, "jaccard": round(best, 4)})

    return report


def assert_no_leakage(report: LeakageReport) -> None:
    """Hard gate: raise if any eval item truly leaks (exact QA collision)."""
    if report.exact_qa:
        raise AssertionError(
            "leakage: {} eval item(s) share (question, answer) with the study deck: {}".format(
                len(report.exact_qa), sorted(report.exact_qa)
            )
        )


def format_report(report: LeakageReport) -> str:
    d = report.as_dict()
    lines = [
        "Study-deck <-> eval-bank leakage audit (PRD §11)",
        "  eval items scanned      : {}".format(d["total_eval"]),
        "  RESIDUAL LEAKAGE RATE   : {:.4f}  ({} exact (question,answer) collisions)".format(
            d["residual_leakage_rate"], len(d["exact_qa_collisions"])
        ),
        "  stem-only collisions    : {} (same stem, different answer -- review)".format(
            len(d["stem_only_collisions"])
        ),
        "  shared 13-gram flags    : {} (structural template overlap -- review)".format(
            len(d["shared_13gram_flags"])
        ),
        "  token-Jaccard > {:.2f}     : {} near-duplicate flag(s); max Jaccard {:.3f}{}".format(
            d["jaccard_threshold"],
            len(d["high_jaccard_flags"]),
            d["max_jaccard"],
            " ({})".format(d["max_jaccard_eval_id"]) if d["max_jaccard_eval_id"] else "",
        ),
        "  note: shared templates make high Jaccard EXPECTED, not leakage; only exact",
        "        (question,answer) collisions count toward the residual leakage rate.",
    ]
    return "\n".join(lines) + "\n"
