# The `overfit` gate stopped measuring overfitting when the scan pinned its params

**Date:** 2026-07-24
**Status:** RESOLVED. Owner chose to replace the gate; shipped in `57be959` as
gate 5 `unstable` (majority of traded folds positive out-of-sample), with a dated
amendment in `docs/superpowers/specs/2026-07-23-measurement-harness-design.md`.
The full 16-configuration scan was re-run afterwards and returns **0/16**, with
`4h ma+trend` the single row failing on `unstable`; every other row still fails
earlier on `churn` or `fee-drag`, so no other verdict moved.

## What prompted this

`docs/research/2026-07-23-tsmom-test-results.md` recorded a gate limitation in passing:
the `overfit` gate fires only when `avg_is > 0 AND avg_oos < 0`, so a strategy carried
by one lucky fold slips through. The obvious tightening — require a *majority* of folds
positive out-of-sample — turns out to interact with commit `12e0e61` (the pin-params
fix) in a way that changes what the gate means, not just how strict it is.

## Finding 1 — with pinned params, `avg_is` vs `avg_oos` cannot detect overfitting

`scan_one` pins walk-forward to a single-entry grid (`pinned_grid = [default_params(name)]`)
so that every gate judges the same configuration the headline metrics were measured on.
That was the right fix for `trades`, `net_return` and `fee_drag`.

But the `overfit` gate reads `avg_is` and `avg_oos`, and those only mean "in-sample" and
"out-of-sample" *when a selection happens*. With a one-entry grid, `walk_forward`'s
optimizer loop (`walkforward.py:47-55`) has nothing to choose between: `best_params` is
always the pinned tuple. Nothing is fitted, so nothing can be over-fitted.

What the two numbers actually compare is the *same fixed strategy* on two sets of time
windows offset by one fold.

## Finding 2 — the fold windows overlap by construction

`walkforward.py:43-45`:

```python
is_slice  = df.iloc[k * fold : (k + 1) * fold]
oos_slice = df.iloc[(k + 1) * fold : oos_end]
```

Fold *k*'s out-of-sample slice **is** fold *k+1*'s in-sample slice — the same rows. With
pinned params the returns are therefore identical, which the measured data confirms
exactly (BTC/USDT 4h `ma`, pinned (20,50), 4 splits):

| fold | in-sample | out-of-sample |
|---|---|---|
| 0 | +3.7267% | +0.6199% |
| 1 | **+0.6199%** | +2.7352% |
| 2 | **+2.7352%** | −4.6035% |
| 3 | **−4.6035%** | +1.2041% |

Each fold's in-sample return repeats the previous fold's out-of-sample return.

Consequently, when all folds are valid, `avg_is` averages windows {0,1,2,3} and `avg_oos`
averages windows {1,2,3,4}, so the reported `oos_gap` collapses to:

```
oos_gap = (first_window_return - last_window_return) / n_folds
```

Checked against the data above: (0.037267 − 0.012041) / 4 = **0.0063065**, and
`avg_is − avg_oos` = 0.0061957 − (−0.000111) = **0.0063067**. Identical.

**`oos_gap` on a pinned scan row is "did the first window beat the last window, divided
by four."** It is not an overfitting measure.

## Finding 3 — the tightening would flip the headline

The single passing configuration, `4h ma+trend`, pinned to (20,50):

| fold | valid | oos trades | in-sample | out-of-sample |
|---|---|---|---|---|
| 0 | yes | 3 | +2.6975% | **+1.2862%** |
| 1 | no | 0 | — | — |
| 2 | yes | 1 | +2.1861% | **−0.9883%** |
| 3 | no | 0 | — | — |

Two traded folds, one positive out-of-sample and one negative, on **four out-of-sample
trades in total**. `avg_oos = +0.1490%` is the average of those two. A
majority-positive-OOS rule fails it (1 of 2 is not a majority), taking the delivered
headline from **1/16 to 0/16**.

For contrast, `4h ma` has 4 valid folds and 3 positive out-of-sample — it would *pass* a
majority rule while *failing* the current `avg_oos < 0` rule. The two rules disagree in
opposite directions on the only two net-positive configs in the scan. (`4h ma` fails
`fee-drag` at 0.75 well before either rule is reached, so this changes no verdict today.)

## What this does not undermine

- The pin-params fix itself is still correct. Unpinning would put the cost and return
  gates back to judging a different object than the headline row.
- The 0/16 and 1/16 findings for every *other* gate stand untouched.
- `cli.py walkforward` still re-optimizes over the full grid, so the genuine
  "does selecting params on this family hold up" question is still answerable there.

## The decision this leaves open

For a *pinned* configuration the meaningful question is temporal stability — does this
one fixed config hold up across successive windows — not parameter overfitting. That
argues for replacing the gate rather than tightening it, and renaming it (`unstable`)
so the label stops claiming something it cannot measure.

Any such change is a **tightening** (it can only turn PASS into FAIL), but unlike the
`net > 0` amendment it **does** change the delivered result, so it needs the same ritual:
owner decision plus a dated amendment in
`docs/superpowers/specs/2026-07-23-measurement-harness-design.md`.

## Reproduction

`walk_forward` on cached `BTC/USDT` 4h, `n_splits=4`, `warmup=50`, `fee=0.001`,
`risk_per_trade=0.01`, `stop_loss_pct=0.05`, grid pinned to `[default_params(name)]` —
i.e. exactly what `scan_one` runs.
