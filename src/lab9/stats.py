"""Statistics students implement (M2 judge calibration, M4 paired bootstrap).

Rules: a judge is a classifier -- measure it like one. A higher mean is not
"better" until the paired CI of the difference excludes 0.
Reference values to self-check are in tests/test_lab9_stats.py.
"""

from __future__ import annotations

from collections.abc import Sequence

POS = "FAIL"   # the judge's job is to FIND failures, so FAIL is the positive class


def _is_fail(label: str) -> bool:
    return str(label).strip().upper() == POS


def _paired(human: Sequence[str], judge: Sequence[str]) -> list[tuple[bool, bool]]:
    """(human says FAIL, judge says FAIL) per row. Unequal lengths would silently drop rows in zip()."""
    if len(human) != len(judge):
        raise ValueError(f"human has {len(human)} labels, judge has {len(judge)}")
    return [(_is_fail(h), _is_fail(j)) for h, j in zip(human, judge)]


def confusion(human: Sequence[str], judge: Sequence[str]) -> dict[str, int]:
    """tp/fp/fn/tn with FAIL as positive."""
    c = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    for h_fail, j_fail in _paired(human, judge):
        if j_fail:
            c["tp" if h_fail else "fp"] += 1     # judge flagged it: a real failure, or a false alarm
        else:
            c["fn" if h_fail else "tn"] += 1     # judge let it pass: a missed failure, or a correct pass
    return c


def precision_recall(human: Sequence[str], judge: Sequence[str]) -> tuple[float, float]:
    c = confusion(human, judge)
    precision = c["tp"] / (c["tp"] + c["fp"]) if c["tp"] + c["fp"] else 0.0
    recall = c["tp"] / (c["tp"] + c["fn"]) if c["tp"] + c["fn"] else 0.0
    return precision, recall


def cohen_kappa(human: Sequence[str], judge: Sequence[str]) -> float:
    """kappa = (p_o - p_e) / (1 - p_e). Raise ValueError when undefined (p_e == 1):
    a constant judge has no signal and must FAIL calibration, not pass on a technicality."""
    pairs = _paired(human, judge)
    n = len(pairs)
    if n == 0:
        raise ValueError("kappa undefined: no labels")
    p_o = sum(h == j for h, j in pairs) / n                  # observed agreement
    h_fail = sum(h for h, _ in pairs) / n
    j_fail = sum(j for _, j in pairs) / n
    p_e = h_fail * j_fail + (1 - h_fail) * (1 - j_fail)     # agreement expected by chance alone
    if p_e == 1:
        raise ValueError("kappa undefined: both raters give one constant label")
    return (p_o - p_e) / (1 - p_e)


def rogan_gladen(observed_rate: float, sensitivity: float, specificity: float) -> float:
    """Correct an observed failure rate for judge error; clip to [0, 1]."""
    denom = sensitivity + specificity - 1
    if denom <= 0:
        raise ValueError("Rogan-Gladen undefined: the judge is no better than chance (sens + spec <= 1)")
    return min(1.0, max(0.0, (observed_rate + specificity - 1) / denom))


def paired_bootstrap(a: Sequence[float], b: Sequence[float], *, n_resamples: int = 1000,
                     rng: int = 2027, confidence: float = 0.95) -> tuple[float, float, float]:
    """a[i], b[i] = per-item mean over seeds, SAME items, SAME order.
    Return (mean(a)-mean(b), lo, hi) with scipy.stats.bootstrap(paired=True, method="percentile",
    rng=numpy.random.default_rng(rng)). If a == b everywhere return (0.0, 0.0, 0.0)."""
    # Imported here, not at module top: Lab 8's CI collects these tests with only Lab 8 dependencies.
    import numpy as np
    from scipy.stats import bootstrap

    a_arr, b_arr = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if a_arr.shape != b_arr.shape or a_arr.ndim != 1:
        raise ValueError(f"paired samples need the same items in the same order: {a_arr.shape} vs {b_arr.shape}")
    if a_arr.size == 0:
        raise ValueError("paired bootstrap needs at least one item")
    if np.array_equal(a_arr, b_arr):
        return (0.0, 0.0, 0.0)
    diff = float(a_arr.mean() - b_arr.mean())
    if a_arr.size == 1:
        # One item: every resample is that same item, so the bootstrap distribution is the point itself.
        return (diff, diff, diff)

    def mean_diff(x, y, axis=-1):
        return x.mean(axis=axis) - y.mean(axis=axis)

    # paired=True resamples ITEM indices and keeps a[i] with b[i]: each item is compared with itself.
    res = bootstrap((a_arr, b_arr), mean_diff, paired=True, vectorized=True,
                    n_resamples=n_resamples, confidence_level=confidence, method="percentile",
                    rng=np.random.default_rng(rng))
    return (diff, float(res.confidence_interval.low), float(res.confidence_interval.high))


def pass_at_k(n: int, c: int, k: int) -> float:
    """Probability that AT LEAST ONE of k trials drawn from n (c of them passing) passes.
    Unbiased estimator (Chen et al. 2021): 1 - C(n-c, k) / C(n, k). Raise ValueError if k > n."""
    # TODO M6
    raise NotImplementedError


def pass_hat_k(n: int, c: int, k: int) -> float:
    """pass^k (tau-bench, Yao et al. 2024): probability that ALL k trials drawn from n pass.
    Unbiased estimator: C(c, k) / C(n, k). Raise ValueError if k > n.
    pass^k <= pass@1 <= pass@k; a reliable agent keeps pass^k close to pass@1."""
    # TODO M6
    raise NotImplementedError
