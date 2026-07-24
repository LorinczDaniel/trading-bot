# Equities: setup, the blocker, and the comparison this project could not make

**Date:** 2026-07-24
**What was built:** `data/equity.py`, an equity provider writing the project's standard
lowercase-OHLCV parquet with a tz-naive index, so `scan`, `simulate`, `cross_sectional`
and `panel` all run on stocks unchanged. 263 tests pass.

Verified end-to-end: the crypto gates ran on eight tickers with no code modification.

## The blocker, measured before anything was designed on top of it

**yfinance does not serve delisted tickers.** Probed directly — LEHMQ (Lehman), ENRNQ
(Enron), SIVBQ (SVB), FTCH (Farfetch), BBBYQ (Bed Bath & Beyond) all return **empty**.

This is *worse* than the crypto situation, where Binance kept serving delisted coins and a
survivorship-free universe was reconstructible.

| | permitted | forbidden |
|---|---|---|
| index and single-name time-series | **yes** — SPY to 1993, AAPL to 1980, XOM/KO to 1962 | |
| cross-sectional stock selection | | **no** — this is exactly the defect that produced a +573% result which collapsed to −99.7% once membership went point-in-time |

Index *membership* history is reconstructible; the *prices* of names that left are not, and
that is the half that matters. Honest cross-sectional equity work needs a survivorship-free
source (CRSP, Norgate, Sharadar) — those cost money. Until then any stock-picking backtest
on this provider measures survivors only and must say so.

**The good news is real though:** deep history directly addresses the evidence floor that
was the binding constraint on crypto. `1d ma` on BTC passed every gate only because BTC has
nine years of data; SPY has thirty-three and XOM has sixty-four.

## The comparison the project owed itself

`2026-07-24-if-the-goal-is-returns.md` recorded this as an open gap: *"No equity index was
benchmarked, and on a risk-adjusted basis a broad index fund may well dominate."* Now
measurable. Matched windows, and annualized correctly per asset class — equities at 252
periods/year, crypto at 365, or the Sharpe comparison is wrong by 1.20x in crypto's favour.

### Over BTC's full history (8.9 years, same window)

| | annualized | Sharpe | max DD | % of days >20% below peak |
|---|---|---|---|---|
| SPY | 15.04% | **0.84** | **−33.7%** | **2.5%** |
| QQQ | 20.26% | **0.91** | −35.1% | 11.6% |
| BTC | **35.59%** | 0.79 | −83.2% | **71.7%** |

BTC won on raw return and **lost on every risk measure**. The last column is the one to sit
with: holding BTC meant being more than a fifth underwater on **seven days in ten**. For
SPY it was one day in forty.

### Last 5 years

| | annualized | Sharpe | max DD |
|---|---|---|---|
| SPY | 12.38% | **0.77** | **−24.5%** |
| BTC | 13.68% | 0.51 | −76.6% |

Nearly identical return. Two-thirds the Sharpe, three times the drawdown.

### Risk-matched — the decisive framing

BTC's annualized volatility is **67.3%** against SPY's **18.8%**, so BTC is 3.6x the risk.
To run a BTC position at SPY's risk level you would hold **28% BTC and 72% cash**.

That sleeve returned **14.03%/yr with a −34.4% max drawdown.**
SPY returned **15.04%/yr with a −33.7% max drawdown.**

**Risk-matched, they are the same thing.** BTC's extra return over the period was
compensation for volatility, not evidence of a superior asset — and that leverage is
available to anyone through position sizing. This is the same conclusion the leverage
document reached from the other direction: leverage moves you along a line, it does not
lift you off it.

QQQ, meanwhile, beat both on Sharpe in the full window.

## The gates on equities: same pattern as crypto

Running `scan_one` on eight tickers since 2010, two strategies each:

**7 of 16 passed** (versus 0 of 16 on crypto). But every passing configuration lost
enormously to simply holding the stock — SPY `1d ma` returned +12.30% where SPY itself
returned +772%. The `edge` column reads −658% for SPY, −3,180% for AAPL, −60,666% for NVDA.

So the gates pass more often on equities purely because fee drag is lower and history is
longer — not because the strategies work. **The finding transfers exactly: technical timing
underperforms holding, in both asset classes.** The difference is that in equities, holding
is a genuinely good risk-adjusted bet.

## What this means for the stated goal

The evidence now supports something it could not support this morning: **a broad equity
index dominates BTC on risk-adjusted terms**, and the gap in drawdown experience
(2.5% vs 71.7% of days underwater by 20%) is the difference between a position a person can
actually hold and one they are likely to abandon at the worst moment.

Caveats worth keeping: 2017–2026 was a strong equity period; SPY's 33% drawdown is real and
was fast; and none of this is a forecast. But the comparison is now measured rather than
assumed, which is what was missing.

## Next, if equities continue

1. **Do not build cross-sectional stock selection on this data source.** It would reproduce
   a known error with known consequences.
2. Index-level and single-name work is fully supported today.
3. If cross-sectional becomes the goal, buy survivorship-free data first. That is a
   purchasing decision, not an engineering one.
