# SPDX-License-Identifier: AGPL-3.0-or-later
# Part of the GRE Math Speedrun fork of Anki (see repo LICENSE; credit: Anki / ankitects).
"""Deterministic lexical RAG retriever over the source-chapter passages.

A small, dependency-free TF-IDF cosine retriever. It is *lexical on purpose*: no
embedding model, no network, no randomness -> byte-stable results for a fixed
corpus and query, which is what "re-runnable" requires (PRD §11). It stands in for
a neural retriever at the same interface; swapping in embeddings later would not
change any downstream contract (provenance still anchors to a passage id).

The retriever's only job is to surface the passage(s) a card should ground itself
in. Whether the card's quote is *actually* in the retrieved passage is then
enforced verbatim by ``provenance.py`` — retrieval proposes, provenance disposes.
"""

from __future__ import annotations

import math
import re
from collections import Counter

import corpus

_TOKEN_RE = re.compile(r"[a-z0-9]+")

# Tiny stop-list: extremely common function words that carry no topical signal.
_STOP = frozenset(
    "a an the of to in on and or is are be by that this with for as at it its "
    "when where which than then from into over under not no".split()
)


def tokenize(text: str):
    return [t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOP]


class Retriever:
    """TF-IDF cosine retriever over a fixed passage list (deterministic)."""

    def __init__(self, passages=None):
        self.passages = list(passages if passages is not None else corpus.PASSAGES)
        self._df = Counter()
        self._tf = []  # parallel to self.passages: Counter of token -> count
        for p in self.passages:
            counts = Counter(tokenize(p.text))
            self._tf.append(counts)
            for term in counts:
                self._df[term] += 1
        n = max(len(self.passages), 1)
        # Smoothed idf so a term in every passage still contributes a little.
        self._idf = {t: math.log((n + 1) / (df + 1)) + 1.0 for t, df in self._df.items()}
        self._norms = [self._vector_norm(tf) for tf in self._tf]

    def _weighted(self, counts):
        return {t: c * self._idf.get(t, 0.0) for t, c in counts.items()}

    def _vector_norm(self, counts):
        return math.sqrt(sum(w * w for w in self._weighted(counts).values()))

    def retrieve(self, query: str, k: int = 3):
        """Return the top-``k`` ``(Passage, score)`` pairs, score descending.

        Empty/whitespace query -> ``[]``. Ties break by passage id (stable).
        """
        q_counts = Counter(tokenize(query))
        if not q_counts:
            return []
        q_weight = self._weighted(q_counts)
        q_norm = math.sqrt(sum(w * w for w in q_weight.values()))
        if q_norm == 0:
            # Query had only out-of-vocabulary terms.
            return [(p, 0.0) for p in self.passages[:k]]

        scored = []
        for passage, tf, p_norm in zip(self.passages, self._tf, self._norms):
            if p_norm == 0:
                scored.append((passage, 0.0))
                continue
            dot = 0.0
            p_weight = self._weighted(tf)
            for term, qw in q_weight.items():
                pw = p_weight.get(term)
                if pw:
                    dot += qw * pw
            scored.append((passage, dot / (p_norm * q_norm)))

        scored.sort(key=lambda item: (-item[1], item[0].id))
        return scored[:k]


DEFAULT = Retriever()


def retrieve(query: str, k: int = 3):
    """Convenience wrapper over the default corpus retriever."""
    return DEFAULT.retrieve(query, k=k)
