# Test 8: the funding-ranked basis strategy — found it, and watched it die

**Date:** 2026-07-24
**Question:** the majors' basis decayed because spot ETFs gave institutions cheaper long
exposure. That mechanism is asset-specific. Coins with no ETF should still pay — and
retail leverage concentrates in exactly those.

**Universe:** 327 assets with both a spot leg and a perp funding series, **81 of them
delisted**. Delisted perps are included deliberately; Binance still serves their funding
history, and leaving them out is the survivorship error this project keeps finding.

## First: high funding predicts death, and it is not subtle

Rank every perp by funding over a period, then count which later delisted:

| ranked over | top-quintile death rate | bottom-quintile | overall |
|---|---|---|---|
| 2024 H1 | **45.8%** | 14.6% | 25.0% |
| 2024 H2 | **54.7%** | 26.4% | 32.1% |
| 2025 H1 | **55.4%** | 42.9% | 36.4% |

Over half the top-quintile funding payers were delisted within about eighteen months. The
highest payers among the dead — 42 (32.4%), 1000WHY (30.4%), DAM (30.0%), RVV (28.6%) —
are precisely what a naive funding screen selects. **High altcoin funding is substantially
compensation for the coin dying.**

## But delta-neutrality hedges exactly that

The obvious inference — "so the yield is fake" — turns out to be wrong, and the direct
test says so. Running cash-and-carry on the coins that actually died:

| | fraction of assets profitable | median max drawdown |
|---|---|---|
| **delisted coins** | **69.1%** | −8.8% |
| surviving coins | 61.9% | −10.4% |

The dead coins were the *better* trade. That is what delta-neutral means: as the price goes
to zero the spot leg's loss is the short perp's gain, and the funding accrues throughout.
Death is hedged. The residual tail is real but narrow — worst case ALPACA at −88%
annualized — and the median outcome is fine.

This is worth stating plainly because the intuition points the wrong way: the risk that
makes altcoin funding high is the risk this particular structure neutralises.

## The strategy, judged properly

Rank by trailing funding at each rebalance using only past data, take the top N with
positive carry, equal-weight, run cash-and-carry on each, 3x target leverage, rebalance
weekly, fees on every adjustment.

| window | return | annualized | Sharpe | max DD |
|---|---|---|---|---|
| full, 2021-06 → | +24.58% | +4.37% | 2.93 | −4.4% |
| 2021–2023 | +8.99% | +4.41% | 4.90 | −0.5% |
| **2023–2025** | +16.85% | **+8.11%** | **6.20** | −1.4% |
| last 24 months | +6.74% | +3.32% | 2.13 | −2.5% |
| **last 12 months** | −1.56% | **−1.56%** | **−0.54** | −4.0% |
| **last 6 months** | −3.41% | **−6.80%** | **−1.85** | −4.4% |

**It worked, genuinely and for years.** Sharpe 6.20 at +8.11% annualized over 2023–2025,
with a 1.4% maximum drawdown, is a better risk-adjusted result than anything else in this
project by a wide margin — holding BTC managed Sharpe 0.79 with an 83% drawdown.

**And it is now negative.** Not marginal — negative across the entire parameter grid:

| top N | lookback 14 | 30 | 60 |
|---|---|---|---|
| 5 | −8.48% | −6.75% | −5.10% |
| 10 | −4.20% | −1.56% | −1.10% |
| 20 | −3.31% | −0.11% | −0.18% |

Nine of nine settings at or below zero on the last twelve months. This is not a knife-edge
parameter failure of the kind that killed the cost band; the whole surface has sunk.

## Why

Funding itself has collapsed, and it is measurable rather than inferred:

- BTC funding: 11.67% over full history → 3.43% last 12m → 3.35% last 3m
- Pre/post the January 2024 spot ETF: BTC 14.45% → 6.92%, ETH −11.24pp, XRP −13.82pp
- **Surviving perps' median funding over their last 180 days is −2.59% — negative**

The trade paid because leveraged longs paid to be long. ETFs gave institutions a cheaper
long, and enough capital ran this carry that perps no longer pay for it. The edge was
competed away, and the competition is visible directly in the price of the thing being
harvested.

## What this establishes

**A real, measurable edge existed in retail-accessible crypto, and this harness found it,
measured it honestly, and dated its death.** That is a different outcome from the six
predictive tests, which found nothing that was ever there.

Recorded for future reference, because the mechanism may recur:

- The carry is real whenever perp funding is persistently positive. It is a cash flow, not
  a forecast, so it does not depend on predicting anything.
- It requires **cross-margin**. At 3x isolated, every major was liquidated in 2020–21.
- Delta-neutrality hedges coin death, which is counterintuitive and empirically confirmed.
- The binding risks are structural and invisible to Sharpe: exchange failure (FTX killed
  people running exactly this), auto-deleveraging, liquidation on rebalance lag.
- **Watch the funding rate directly.** It is the strategy's own price. When it falls below
  the risk-free rate plus a counterparty premium, stop.

## Honest bottom line

Asked to find a strategy that beats holding, I found one that did — +8.11% annualized at
Sharpe 6.20, market-neutral, through 2025 — and the same measurement shows it stopped
paying roughly twelve months ago.

Deploying it today would be trading a strategy whose edge is documented to have
disappeared, in exchange for exchange counterparty risk. The monitoring rule matters more
than the strategy: **if BTC funding returns durably above ~8–10% annualized, this becomes
worth building.** Until then it is a watchlist item, not a position.

## Adjacent, untested

Funding is now *negative* on many alts, meaning longs are paid. The mirror trade (long
perp, short spot) would harvest that — but shorting spot requires a margin borrow whose
cost typically exceeds the negative funding, and the project's research already ruled out
short legs on independent evidence. Not pursued.

The remaining untested premium is the variance risk premium on options, where the
harvested research claims BTC's is roughly an order of magnitude above the S&P's.
