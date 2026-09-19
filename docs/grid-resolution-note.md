# Exact recovery and threshold-grid resolution

Exploratory derivation by Shivam Gupta, 2026-09-19. This is an elementary
certificate-complexity consequence, not an established novelty claim.

## Setting

Use the binary, monotone loss matrix and complete-row revelation model in
`partial-recalibration-note.md`. Unqueried rows are unrestricted monotone binary
rows ending in zero; no score-stability assumption or probabilistic shortcut is
available. Let n be the number of calibration rows and K the largest integer
with (K+1)/(n+1) <= alpha. Assume K >= 0. The full policy j is the first column
with at most K ones. This note concerns an interior policy, 0 < j < m-1.

Let D be the number of rows that change from one at j-1 to zero at j. Since j-1
fails and j passes, D >= 1. With no cached rows the minimum certificate size is

    C = max(n-K, K+1, n+1-D).

This is the no-cache specialization of the previously implemented two-witness
formula. A certificate needs n-K witnessed zeros at j and K+1 witnessed ones at
j-1. Exactly D rows can witness both. Choose as many shared witnesses as possible,
then complete each requirement. This attains the lower bound from counting the
two requirements and their overlap. The result is an oracle certificate size,
not the expected cost of finding that certificate online.

## Singleton-boundary corollary

If D=1, every row must be known. With c exactly cached rows, every one of the
n-c remaining rows must be revealed. To see this, the total number of ones drops
by exactly one across the boundary, so it must be K+1 before and K afterward.
There are exactly K+1 available one witnesses and n-K available zero witnesses.
Every required witness must be observed. Their union contains all n rows.

This statement applies to any fixed finite grid whose selected boundary has a
single loss transition. It does not assume that a data-dependent grid preserves
conformal validity. Distinct real-valued confidence scores alone do not force
D=1 on a coarse grid. A grid fine enough to isolate each loss transition does.
This recovers a familiar exact-order-statistic obstruction in this setting.

## Refinement monotonicity

Let a coarse grid be a subset of a fine grid, with the same endpoints and policy
semantics. Fix the actual full loss rows and an initial cache. The minimum exact
certificate size on the fine grid is at least that on the coarse grid.

Proof: for every fully specified monotone matrix, the first passing coarse policy
is the first coarse policy at or above the first passing fine policy. The same
holds for the final-policy fallback. Any row subset that fixes the fine answer
therefore fixes the coarse answer. Every compatible completion of the coarse
unknown rows extends to fine monotone rows, while retaining observed fine rows.
Thus a fine certificate is also a coarse certificate; minimizing proves the claim.

This is a statement about exact recovery. It does not imply that finer grids are
worse for prediction. With full information they can select a less conservative
threshold. The tradeoff is between policy resolution and certification effort.
It also does not compare algorithms under different statistical guarantees.

## Diagnostic plan

After the frozen pilot completes, replay nested, fixed grids with step sizes
0.05, 0.025, 0.0125, 0.00625, 0.003125, and 0.0015625 on [0.25,1], retaining the
initial 0 threshold and final 1.01 abstention threshold. Record reference policy,
boundary crossing count, full-information certificate cost, evaluation coverage,
and marginal shipped error at each alpha. No new model outputs are required.
This is a post-protocol exploratory diagnostic motivated by the derivation,
not a preregistered confirmatory experiment or a deployable oracle algorithm.

## Prior-work boundary

Costly sequential tests and certificates are established in stochastic Boolean
function evaluation and stochastic score classification (Gkenosis et al., ESA
2018, https://doi.org/10.4230/LIPIcs.ESA.2018.36). The connection is a reason to
avoid claiming generic exact certification as novel. A targeted literature
screen has not yet established a publishable gap for this specialization.
