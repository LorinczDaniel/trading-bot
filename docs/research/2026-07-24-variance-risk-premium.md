# Test 9: the variance risk premium — real, decaying, and tail-heavy

**Date:** 2026-07-24
**Question:** the last untested premium. Option buyers are said to overpay for protection,
so a seller of volatility collects the difference. Like the basis trade this pays for
bearing risk rather than for forecasting, so none of the eight prior negatives apply.

**Data:** Deribit's DVOL index (BTC 30-day implied volatility), **1,949 daily points,
2021-03-24 → 2026-07-24**, fetched over Deribit's public REST. Compared against the
volatility BTC actually realized over the following 30 days.

## The premium exists

| | mean | median |
|---|---|---|
| implied vol (DVOL) | 60.9 | 56.2 |
| realized vol (next 30 days) | 52.2 | 48.3 |
| **premium (IV − RV)** | **+8.8** | **+10.5** |

**Implied exceeded realized on 72.7% of days.** Options were, on average, priced about
nine volatility points above what the market subsequently delivered. The premium is real
and it is not small.

## But it decays, exactly like the carry did

| year | IV | RV | premium | % days IV > RV |
|---|---|---|---|---|
| 2021 | 91.8 | 73.7 | **+18.0** | 87.6% |
| 2022 | 73.6 | 61.4 | +12.2 | 66.8% |
| 2023 | 49.6 | 43.0 | +6.6 | 72.6% |
| 2024 | 57.7 | 50.5 | +7.2 | 73.2% |
| 2025 | 46.0 | 39.6 | +6.4 | 70.7% |
| **2026** | 45.8 | 46.5 | **−0.6** | 64.0% |

Same shape as the funding trade: large early, roughly a third of that by 2025, and
negative in the current year.

## The tail is the whole story

2026's negative average is not a gradual fade. It is one event:

| date | IV | RV | premium |
|---|---|---|---|
| 2026-01-28 | 38.0 | 83.2 | **−45.2** |
| 2026-01-27 | 38.2 | 83.2 | −45.0 |
| 2026-01-26 | 38.8 | 83.4 | −44.7 |
| 2026-01-24 | 38.3 | 80.7 | −42.4 |

In late January 2026 volatility was sold near 38 and realized above 80. Sixty-four percent
of 2026's days still showed a positive premium — the seller was right most of the time and
still finished the year behind.

**That is the defining property of short volatility, not a malfunction.** You collect small
premiums repeatedly and occasionally pay a very large claim. A crude variance-swap proxy
over the full sample gives a Sharpe of 1.48, and that number is *optimistic*: the
observations are 30-day overlapping windows, so they are heavily autocorrelated and the
effective sample is far smaller than 1,919.

## What this measurement does NOT establish

Important, because the premium looks harvestable and the gap between "premium exists" and
"strategy makes money" is where the cost lives:

- **This measures the premium, not a tradeable strategy.** Harvesting it means actually
  selling options — and Deribit option bid-ask spreads are commonly several volatility
  points wide. On a 2025-level premium of 6.4 points, spread alone could consume most of it.
- **No delta hedging is modelled.** A short option position is not delta-neutral; keeping
  it so requires continuous rebalancing in the underlying, which costs fees and bleeds in
  choppy markets.
- **No margin or assignment modelling.** Short options carry margin requirements that
  expand violently in exactly the scenarios that hurt, which is how short-vol books get
  force-closed at the worst moment.
- **Sharpe understates the risk here**, for the same reason it did on the basis trade: the
  hazard is tail-shaped, not volatility-shaped.

So the honest description is: **a real premium of ~6 volatility points in recent years,
gross of execution costs that plausibly consume most of it, with a documented tail that
erased a full year in a single month.**

## Reading

The VRP is genuinely there, which makes it the second real premium this project has found.
It is also worse than the basis trade on every axis that matters: smaller relative to its
costs, far more tail-exposed, harder to execute, and currently at zero.

Selling volatility with no hedging model, into a premium that has decayed to nothing this
year, on an instrument whose spreads could eat the entire edge, is not a trade worth
opening on this evidence.

## The pattern across three premium tests

| premium | historical | now | why it faded |
|---|---|---|---|
| perp funding (majors) | 11–14%/yr | ~3.3%/yr | spot ETFs gave institutions a cheaper long |
| funding-ranked basis | +8.11%/yr, Sharpe 6.20 | −1.6%/yr | same, plus capital competing for the carry |
| variance risk premium | +18 vol pts (2021) | −0.6 (2026) | volatility sellers arrived; the 2026 event |

Three independent premiums, all real, all measured, all compressed to roughly zero in the
current regime. That consistency is itself the finding: **retail-accessible crypto
premiums existed and have been arbitraged out over 2021–2026.** It is a much stronger
statement than any single negative, because the three have different mechanisms and
different participants and decayed anyway.

## What remains untested

- **Order book microstructure** — no history via the API, so testing it means collecting
  data forward for months before learning anything.
- **Open interest** — Binance serves only ~30 days, too short to backtest.
- **Cross-venue funding** — probed and effectively dead: Bybit 3.39%, OKX 3.35%,
  Gate 4.18%, Bitget 4.42%, KuCoin 1.48%, Hyperliquid 1.12%. No venue pays meaningfully
  more, so the decay is market-wide rather than Binance-specific.
- **Dated-futures term structure** — only 4 BTC contracts listed; a thin version of the
  carry already measured.
