# Test 4: does `1d ma` generalise beyond BTC?

**Date:** 2026-07-24
**Claim under test:** `1d ma` is the only configuration that has ever cleared all six
gates (`2026-07-24-daily-bars-and-the-evidence-floor.md`). Was that a property of the
rule, or of Bitcoin? The multi-coin fetch makes this answerable for free.

**Method:** the existing single-asset `scan_one` run over every cached daily symbol with
≥300 bars, same parameters as the BTC scan (pinned (20,50), warmup 50, 4 splits, fee
0.001).

## Result — 1 of 22 coins passes, and all 21 failures are the same failure

| reason | count |
|---|---|
| too-few-trades | **21** |
| anything else | 0 |

Not one coin failed on churn, fee drag, stability or net return. Every single rejection is
the trade-count gate.

The cause is arithmetic, not behavioural. BTC has 3,264 daily bars (8.9 years); almost
every other symbol has 1,500 (4.1 years, Binance's pagination limit from today). At the
~3.6 trades/year this rule generates, 4.1 years buys about 15 trades against a gate of 20.

> trades per coin: min 2, **median 15**, max 36 — gate is 20.

**BTC passes because it is old, not because it is different.** That is the single
cleanest statement of the evidence floor identified in the previous test, and it is now
shown to be universal rather than BTC-specific.

## The part that does generalise: cost

Fee drag across the 22 coins sits at **0.02–0.21** for 18 of them (gate: 0.30). The
exceptions are informative rather than contradictory: SOL 1.05, USD1 1.14, SUI 0.31,
ZEC 0.21.

So the turnover thesis holds across the whole cross-section, not just on BTC. At daily
rebalancing the cost problem that killed sixteen configurations is simply gone.

## The part that does not generalise: edge

This is where honesty matters more than the headline.

- **12 of 22 coins have positive net return, 10 negative.** That is a coin flip.
- **Median net return is +2.08% over roughly 4 years** — about 0.5%/year.

Best: DEXE +35.14%, BTC +26.55%, FTT +25.02%, DOGE +19.71%.
Worst: AVAX −11.39%, WLD −6.53%, NEAR −6.47%, VANA −6.32%.

A median of half a percent per year, with the sign split near 50/50, is not a mechanism
producing returns. It is what noise looks like after costs have stopped eating it.

**So the correct reading of the BTC PASS is now much weaker than it looked.** `1d ma` on
BTC returned +26.55% over 8.9 years while BTC itself returned ~1385%. Across 22 coins the
same rule produces a coin-flip distribution centred near zero. BTC's result sits in the
upper tail of that distribution — which is exactly what one expects when the best of 22
noisy draws is selected and reported.

## What this implies for the cross-sectional build

Two things point in opposite directions and both should be recorded before building:

**For:** the evidence floor is now proven universal, and pooling is the only escape from
it that does not require either more history (unavailable) or more turnover (fatal). At 15
trades per coin, a portfolio ranking across 20 coins has a few hundred position-decisions
to be judged on while each individual holding stays slow and cheap. The argument derived
in the last test survives contact with data.

**Against:** the per-coin distribution gives no reason to believe there is a signal to
pool. Pooling noise produces a better-measured zero, not an edge. The honest expectation
for the cross-sectional test just moved *down*, not up.

Both remain worth knowing. A better-measured zero is a real result — it would close the
prediction branch with evidence rather than leaving it open on a technicality, which is
what the whole harness exists to do.

## Incidental finding: the universe filter has a denylist hole

`USD1/USDT` appears in the results with fee drag 1.14 and net −0.60%: it is a stablecoin
churning on noise around $1.00, precisely the pollution stablecoins were supposed to be
excluded to prevent. `RLUSD/USDT` and `XAUT/USDT` (a gold-backed token) were also fetched.

`data/universe.py` excludes stablecoins by an `EXCLUDED_BASES` name list, and new ones
keep being issued. This is the same fragility already rejected for the redenomination
screen in `2026-07-24-multi-coin-data-integrity.md`:

> A denylist alone would be fragile: it only catches the renames we already know about,
> and the whole point of a universe of thousands of coins is that we do not know them all.

The same objection applies to stablecoins and was not applied consistently. Fixed by
screening structurally on realized volatility in the panel, where the price data actually
lives — a stablecoin is identifiable by what it does, not by what it is called.

Verified against the real cache:

```
in:  32 symbols
out: 29 symbols
dropped:
  RLUSD/USDT     stablecoin (daily vol 0.0218%)
  U/USDT         stablecoin (daily vol 0.0206%)
  USD1/USDT      stablecoin (daily vol 0.0359%)

lowest volatility among the KEPT symbols:
  XAUT/USDT      1.2819%      <- tokenized gold: real asset, correctly kept
  BNB/USDT       2.7901%
  BTC/USDT       3.5207%
```

The separation is two orders of magnitude — pegs at 0.02–0.04%, the least volatile real
asset at 1.28% — so the 0.5% threshold sits in a wide empty gap rather than on a
boundary that needs defending. It also caught `U/USDT`, which was not on any list I would
have thought to write, which is the entire argument for structural screens over denylists.

Two limits recorded rather than papered over: a stablecoin that *breaks* its peg has
genuine post-collapse volatility and passes the screen (defensible — after the break it is
a real, dying asset, and dying assets are what a survivorship-free universe must keep);
and the screen refuses to judge series shorter than 30 bars, because a few days of quiet
drift is indistinguishable from a peg and guessing wrong would drop a real coin.
