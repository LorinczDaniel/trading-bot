# Test 2: cost-aware no-trade band on 4h MA — results

**Date:** 2026-07-24
**Claim under test:** research priority #1. Fee drag, not signal frequency, is what
kills these configurations; a band that refuses to act on hairline crossings should
convert gross edge into net edge.

**Pre-committed success bar** (owner decision, fixed *before* any code was written):
`4h ma` is the only configuration whose sole failing gate is `fee-drag` — trades 49,
churn 0.067, folds 4, posOOS 3/4, net +2.83% all already clear. Success = its full
verdict flips to PASS on a re-scan. Failure = fee drag falls but another gate breaks.

## Mechanic

`MACrossover(fast, slow, band)` widens the single crossing line into two: an entry must
clear `slow*(1+band)`, an exit must break `slow*(1-band)`. Both are tested as a *cross*
of the banded line, not as position relative to it, so a sustained trend does not
re-fire an entry every bar. `band=0.0` is the default and reproduces the unbanded
signals exactly, so every previously recorded measurement still stands.

The band rides in the `walk_forward_grid` closure alongside `trend_sma` rather than
joining the parameter grid: it is a fixed property of the configuration under test, not
a dimension to optimise. `scan_one` passes the same band to `build_strategy` and to
`make_strategy`, so a scan row still describes exactly one object.

## Result 1 — the success bar is met, at a knife edge

| band | trades | net | edge | feedrag | folds | posOOS | verdict |
|---|---|---|---|---|---|---|---|
| 0.000 | 49 | +2.83% | +1.49% | 0.75 | 4 | 3 | FAIL fee-drag |
| 0.002 | 42 | +3.65% | +2.31% | 0.52 | 4 | 3 | FAIL fee-drag |
| 0.003 | 38 | +4.73% | +3.38% | 0.36 | 4 | 3 | FAIL fee-drag |
| 0.004 | 36 | +4.51% | +3.17% | 0.36 | 4 | 3 | FAIL fee-drag |
| **0.005** | 33 | **+6.16%** | +4.82% | **0.24** | 4 | 3 | **PASS** |
| 0.006 | 33 | +3.59% | +2.24% | 0.42 | 4 | 3 | FAIL fee-drag |
| **0.007** | 33 | **+5.34%** | +4.00% | **0.28** | 3 | 2 | **PASS** |
| **0.008** | 31 | **+6.78%** | +5.44% | **0.21** | 3 | 2 | **PASS** |
| 0.009 | 30 | +5.46% | +4.11% | 0.25 | 3 | 1 | FAIL unstable |
| 0.010 | 29 | +6.37% | +5.02% | 0.21 | 3 | 1 | FAIL unstable |
| 0.020 | 26 | −4.21% | −5.55% | 0.24 | 2 | 1 | FAIL unstable |
| 0.030 | 15 | +0.06% | −1.28% | 1.66 | 1 | 1 | FAIL too-few-trades |

**Do not read the PASS rows as a validated result.** Bands 0.005, 0.006 and 0.007 all
make **the same 33 trades**, yet fee drag reads 0.24, 0.42 and 0.28 and the verdict goes
PASS, FAIL, PASS. A gate outcome that flips on a 0.001 change in a parameter — while the
trade count does not even move — is measuring noise around a threshold, not an edge.
Picking 0.005 because it passed on the same sample used to report it is precisely the
data-snooping this harness was built to adjudicate, and exactly what the tsmom paper was
criticised for in `2026-07-23-tsmom-test-results.md`.

The fee-drag response is not monotonic either (0.52, 0.36, 0.36, 0.24, 0.42, 0.28, 0.21,
0.25). The apparent monotonicity in a first coarse sweep (0.75 → 0.52 → 0.24 → 0.21) was
an artifact of the spacing.

## Result 2 — the robust part: direction, not magnitude

What *is* consistent across the whole plausible range is the sign of the effect.

**Every band from 0.002 to 0.010 improved net return over the unbanded +2.83%** — 3.65,
4.73, 4.51, 6.16, 3.59, 5.34, 6.78, 5.46, 6.37. Nine of nine. And every one of them cut
fee drag from 0.75 to somewhere in 0.21–0.52.

That breadth is the credible finding, and it is the same shape of evidence the tsmom test
treated as its one believable result: a mechanism that helps across a parameter range is
much harder to fake than a single tuned value. It supports the research claim that fee
drag was suppressing a real gross edge on this configuration.

It does **not** establish that any particular band is deployable.

## Result 3 — the band destroys the thing it needs

Widening the band thins trades, and thin trades starve the walk-forward folds:

- folds traded: 4 (band ≤ 0.006) → 3 (0.007–0.010) → 2 (0.020) → 1 (0.030) → 0 (0.050)
- `4h ma+trend`, which starts with only 24 trades, hits `insufficient-folds` at band
  0.002 and `too-few-trades` by 0.005. It cannot be measured this way at all.

This is the pre-registered failure mode ("thinner trades → folds/posOOS collapse"), and
it fires. Above roughly band 0.01 the configuration stops producing enough evidence to
judge, which caps how wide a band this harness can ever validate on 730 days of 4h bars.

## The theory-derived band, which is the one that was not snooped

Round-trip taker cost at fee 0.001 is 0.002. That is the only band value with an a-priori
justification rather than a fitted one, and it is the honest candidate:

> band 0.002 → net +3.65% (up from +2.83%), fee drag 0.52 (down from 0.75), **still FAIL
> fee-drag**.

So the non-snooped choice improves both numbers and still does not clear the gate.

## Reading

- The mechanism works in the direction the literature predicted, robustly in sign.
- The pass/fail verdict is not robust and must not be reported as a validated edge.
- No configuration is cleared to trade. The scan headline stays **0/16**.

## Next

The open question is no longer "does a band help" but "can a band be chosen without
snooping". The harness can answer it the same way it answered tsmom: select the band
in-sample per walk-forward fold and measure the selected band out-of-sample. If the
best-in-sample band jumps around per fold the way tsmom's lookback did, the band is a
fitting knob and should be fixed at the theory value (0.002) or abandoned. That test has
not been run.

Untouched by this work: maker/limit orders (priority #3), which change the *sign* of the
cost rather than its size, and are the larger lever if the fee is the real constraint.
