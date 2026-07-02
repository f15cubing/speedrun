"""Logistic regression + Platt (sigmoid) calibration — pure stdlib.

No numpy: the anki pyenv has none, and re-runnability wants zero heavy deps.
Batch gradient descent with optional L2; deterministic under a fixed seed.
"""
from __future__ import annotations

import math
import random


def sigmoid(z: float) -> float:
    if z >= 0:
        ez = math.exp(-z)
        return 1.0 / (1.0 + ez)
    ez = math.exp(z)
    return ez / (1.0 + ez)


class LogisticModel:
    def __init__(self) -> None:
        self.weights: list[float] = []
        self.bias: float = 0.0

    def fit(self, X, y, *, lr: float = 0.1, epochs: int = 2000, l2: float = 0.0, seed: int = 0) -> None:
        if not X:
            raise ValueError("no training rows")
        n_features = len(X[0])
        rng = random.Random(seed)
        # Deterministic tiny init (seeded) — keeps fit() reproducible.
        self.weights = [rng.uniform(-0.01, 0.01) for _ in range(n_features)]
        self.bias = 0.0
        n = len(X)
        for _ in range(epochs):
            grad_w = [0.0] * n_features
            grad_b = 0.0
            for xi, yi in zip(X, y):
                z = self.bias + sum(w * x for w, x in zip(self.weights, xi))
                err = sigmoid(z) - yi
                for j in range(n_features):
                    grad_w[j] += err * xi[j]
                grad_b += err
            for j in range(n_features):
                self.weights[j] -= lr * (grad_w[j] / n + l2 * self.weights[j])
            self.bias -= lr * (grad_b / n)

    def predict_proba_one(self, x) -> float:
        z = self.bias + sum(w * xi for w, xi in zip(self.weights, x))
        return sigmoid(z)


def platt_fit(scores, y, *, lr: float = 0.1, epochs: int = 2000, seed: int = 0) -> tuple[float, float]:
    """1-D logistic calibration: fit p = sigmoid(a*score + b)."""
    model = LogisticModel()
    model.fit([[s] for s in scores], y, lr=lr, epochs=epochs, seed=seed)
    return model.weights[0], model.bias


def platt_apply(a: float, b: float, score: float) -> float:
    return sigmoid(a * score + b)
