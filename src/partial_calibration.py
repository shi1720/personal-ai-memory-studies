"""Conservative partial evaluation of a finite-grid CRC reference.

An elementary interval algorithm, not a claim of a novel calibration theorem.
See docs/partial-recalibration-note.md for assumptions and limitations.
"""
from dataclasses import dataclass
import math


def validate_row(row, policies):
    if len(row) != policies:
        raise ValueError("Incorrect policy count")
    if any(not math.isfinite(v) or v < 0 or v > 1 for v in row):
        raise ValueError("Losses must be finite and in [0,1]")
    if any(a < b for a, b in zip(row, row[1:])):
        raise ValueError("Loss must be non-increasing across policies")
    if row[-1] != 0:
        raise ValueError("Last policy must be known zero-loss abstention")


def crc_policy(rows, alpha):
    if not rows or not rows[0]:
        raise ValueError("Non-empty calibration matrix required")
    if not 0 <= alpha < 1:
        raise ValueError("alpha must be in [0,1)")
    m = len(rows[0])
    for row in rows:
        validate_row(row, m)
    n = len(rows)
    for j in range(m):
        if (sum(row[j] for row in rows) + 1) / (n + 1) <= alpha:
            return j
    return m - 1


def shipped_loss_row(correct, confidence, thresholds):
    if not 0 <= confidence <= 1 or not math.isfinite(confidence):
        raise ValueError("Invalid confidence")
    if not thresholds or thresholds[-1] <= 1:
        raise ValueError("Last threshold must force abstention")
    if any(a >= b for a, b in zip(thresholds, thresholds[1:])):
        raise ValueError("Thresholds must be strictly increasing")
    return tuple(float(not correct and confidence >= t) for t in thresholds)


@dataclass(frozen=True)
class PolicyBounds:
    optimistic: int
    conservative: int

    @property
    def exact(self):
        return self.optimistic == self.conservative


class PartialCalibration:
    def __init__(self, n, policies, alpha, cached=None):
        if n <= 0 or policies <= 0:
            raise ValueError("Positive matrix dimensions required")
        if not 0 <= alpha < 1:
            raise ValueError("alpha must be in [0,1)")
        self.n, self.policies, self.alpha = n, policies, alpha
        self.lower = [(0.0,) * policies for _ in range(n)]
        self.upper = [(1.0,) * (policies - 1) + (0.0,) for _ in range(n)]
        self.known = set()
        self.recomputed = []
        for i, row in (cached or {}).items():
            self._set(i, row)
        self.cached_count = len(self.known)

    def _set(self, i, row):
        if not 0 <= i < self.n:
            raise IndexError(i)
        if i in self.known:
            raise ValueError("Row already known")
        row = tuple(row)
        validate_row(row, self.policies)
        if any(not lo <= value <= hi for lo, value, hi in zip(self.lower[i], row, self.upper[i])):
            raise ValueError("Revealed row violates prior bounds")
        self.lower[i] = self.upper[i] = row
        self.known.add(i)

    def reveal(self, i, row):
        self._set(i, row)
        self.recomputed.append(i)

    def bounds(self):
        return PolicyBounds(crc_policy(self.lower, self.alpha), crc_policy(self.upper, self.alpha))

    def next_row(self, priority=None):
        bounds = self.bounds()
        if bounds.exact:
            return None
        candidates = [i for i in range(self.n) if i not in self.known and
                      self.upper[i][bounds.optimistic] > self.lower[i][bounds.optimistic]]
        if not candidates:
            raise RuntimeError("Non-exact interval has no unresolved contributing row")
        # Priority must not read hidden new losses. A caller can supply a fixed
        # random ordering or priorities learned on separate development data.
        return max(candidates, key=lambda i: ((priority[i] if priority is not None else 0), -i))

    def run(self, evaluate_row, budget=None, priority=None):
        if budget is not None and budget < 0:
            raise ValueError("Budget cannot be negative")
        while budget is None or len(self.recomputed) < budget:
            i = self.next_row(priority)
            if i is None:
                break
            self.reveal(i, evaluate_row(i))
        bounds = self.bounds()
        return {"policy": bounds.conservative, "optimistic_policy": bounds.optimistic,
                "exact": bounds.exact, "reader_calls": len(self.recomputed),
                "cached_rows": self.cached_count, "recomputed_indices": list(self.recomputed)}
