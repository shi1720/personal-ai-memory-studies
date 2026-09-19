"""Full-information certificate-size diagnostic. Never an acquisition policy."""
from partial_calibration import crc_policy, validate_row


def integer_loss_budget(n, alpha):
    # Match the reference's floating-point inequality exactly at integer totals.
    # Avoid floor(alpha*(n+1)-1) accidentally rounding across a boundary.
    return max((k for k in range(n + 1) if (k + 1) / (n + 1) <= alpha), default=-1)


def oracle_certificate_cost(rows, alpha, cached_indices=()):
    """Minimum additional exact row revelations, using the hidden full matrix.

    Purely a post-hoc diagnostic of the interval information model. Reporting
    this as achievable online would leak the outputs the algorithm seeks to save.
    """
    j = crc_policy(rows, alpha)
    n, m = len(rows), len(rows[0])
    for row in rows:
        validate_row(row, m)
        if any(value not in (0, 1) for value in row):
            raise ValueError("Binary losses required")
    cached = set(cached_indices)
    if not cached.issubset(range(n)):
        raise ValueError("Invalid cached row index")
    k = integer_loss_budget(n, alpha)
    if k < 0:
        return {"policy": j, "calls": 0, "zero_witnesses_needed": 0, "one_witnesses_needed": 0,
                "dual_witnesses_available": 0, "integer_loss_budget": k}
    zeros = (max(0, n - k - sum(rows[i][j] == 0 for i in cached)) if j < m-1 else 0)
    ones = (max(0, k + 1 - sum(rows[i][j-1] == 1 for i in cached)) if j > 0 else 0)
    dual = (sum(rows[i][j-1] == 1 and rows[i][j] == 0 for i in range(n) if i not in cached)
            if 0 < j < m-1 else 0)
    calls = max(zeros, ones, zeros + ones - dual)
    return {"policy": j, "calls": calls, "zero_witnesses_needed": zeros,
            "one_witnesses_needed": ones, "dual_witnesses_available": dual, "integer_loss_budget": k}
