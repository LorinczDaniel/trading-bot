# Crypto strategy research — findings

**Date:** 2026-07-23
**Status:** Synthesized by hand from a deep-research run that was **stopped before its own synthesis phase**.

## Provenance and how much to trust this

The run completed: question decomposition, all 5 search angles, and claim extraction from **35 unique sources → 94 claims**. It completed only **4 of its planned adversarial verification votes** before being stopped.

**So: most claims below are UNVERIFIED by the adversarial pass.** They are extracted faithfully from named sources with direct quotes, but they have not been through the refutation step that was supposed to kill plausible-but-wrong findings. Treat source quality as the confidence signal — most are marked `primary` (peer-reviewed or working papers with full text), a few `blog`.

Raw harvest with every claim, quote, and source URL: `2026-07-23-crypto-strategy-research-RAW.md` in this directory.

One verification vote that *did* complete is important and is recorded below under cross-sectional momentum.

---

## The one finding that reframes our own result

Our scan killed almost everything and we attributed it to fees. The literature says the real variable is **turnover**, not fee level:

- A weekly-rebalanced cross-sectional strategy has a **breakeven one-way trading cost of 133–281 basis points** despite 79–111% weekly turnover. Binance taker is 10 bps. That is **13–28× headroom**.
- The CTREND strategy's breakeven is **1.41% per trade — roughly 14× Binance's fee** — at 68% weekly turnover.
- By contrast, hourly BTC signal-following fails at just **10 bps** even when the forecaster is XGBoost, LSTM, or iTransformer.

This maps exactly onto our own scan: 4h passed, 1h was marginal, 3m and 1m died. **Slow and cross-sectional is cost-tolerant; fast and single-asset is hopeless.** We were not unlucky with fees — we were testing in the regime where fees dominate by construction.

Our zero-fee result is also corroborated. Single technical rules on **Bitcoin specifically** fail out-of-sample: the best in-sample rule produced **negative** OOS returns on both BTC series tested (−0.10% and −0.91% annualized, negative Sharpe), while the same method stayed positive on LTC/XRP/ETH. And no single indicator is supposed to work — CTREND's whole mechanism is that the effect only appears when ~28 indicators are *aggregated cross-sectionally*.

---

## Tier 1 — test these next (cheap, fits the existing harness)

### 1. Cost-aware no-trade band
**Mechanism:** only take a trade when the predicted return magnitude exceeds a threshold derived from transaction costs. Sharply cuts turnover; "restores profitability in selected configurations."

This is the highest value-per-hour item on the list. It is orthogonal to which signal generates the forecast, it is a small change to `Trader.step`, and it is exactly the "fee-aware trade gate" already scoped as sub-project B.

**Important framing from the same paper:** there are two independent failure modes — a *predictability* problem and a *signal-to-trade conversion* problem. A strategy unprofitable at **zero** fees has a predictability problem no execution filter can fix. One profitable gross but not net has a conversion problem the filter *can* fix. Our MA/RSI on BTC is the former, so do not expect this filter to rescue it — but it should be in place before testing anything new.

### 2. Long-only time-series momentum on the market portfolio
**Result:** buy the market only when the trailing 28-day return sits in the top third of its own history, hold 5 days. Annualized **Sharpe 1.51 vs 0.85** for the market, net of 15 bps per trade, **invested only 48% of the time**. Nearly all lookback/hold pairs from 1–56 days beat the market after costs, so it is not a knife-edge parameter.

The outperformance came from **avoiding drawdowns**, not from higher returns.

**The authors disclaim their own headline** as an overfitted upper bound: the lookback/hold pair was chosen by scanning all combinations on the *same* full sample used to report performance, with no holdout. They call it "best-case" with data-snooping bias.

That disclaimer is precisely what our walk-forward harness exists to adjudicate. Long-only, single instrument, OHLCV only — this is directly testable with what we already have.

### 3. Weekly rebalancing as a design constraint
Not a strategy, a parameter. Everything that survives costs in this literature rebalances **weekly**, not hourly. Our current data cache and scan already support this; it mostly means testing on daily/weekly bars with multi-day holds rather than 1h–4h.

---

## Tier 2 — real edges, but each has a serious catch

### CTREND (cross-sectional ML on aggregated technical indicators)
**Result:** 3.87%/week gross (t=5.19, annualized Sharpe 1.94) over Apr 2015–May 2022 across 3,000+ coins; **net 2.90%/week at 30/40 bps**, still 2.35%/week at 50/60 bps. Restricted to the **100 largest coins** it still earns 3.40% gross, 1.90–2.45% net — so it is not a micro-cap artifact.

**Mechanism:** cross-sectional ranking of an aggregate of 28 technical indicators (RSI, stochastics, CCI, SMAs at 3/5/10/20/50/100/200 days, MACD, volume and volatility measures), combined via Fama-MacBeth forecasts selected by elastic net, rolling 52-week window, weekly rebalance.

**Catch:** it is long-short, and the crypto short leg is where these strategies die (see below). A long-only version captures a fraction. Also requires a multi-coin universe — a real change to the bot, which is single-symbol today.

### Cash-and-carry basis trade (fixed-expiry futures)
**Result:** futures-minus-spot basis averaged **~7% p.a.** Apr 2019–Jul 2024 (≈8% OKEx, 6.4% CME for 1-month BTC), with spikes above 40%. Roughly 10× S&P 500 carry.

**Why fees don't kill it:** a hold-to-maturity carry trader pays the spread **once at entry**, not per rebalance. Fee drag does not scale with holding period — the opposite of everything we tested.

**Mechanism (structural, not a pattern):** regulatory segmentation plus margin frictions, combined with leveraged demand from trend-chasing retail.

**Two serious catches.** (1) Not risk-free: the short-futures leg has ~17% monthly volatility, and at only 10× leverage it **would have been liquidated in over half of all months** in 2018–2024, because spot and futures legs aren't cross-margined. (2) It is being competed away — the January 2024 spot BTC ETF launch causally cut the basis by ~3pp across exchanges and ~5pp on CME (36% and 97% of the pre-event mean).

### Variance risk premium (short volatility)
**Result:** Bitcoin's VRP is **0.14 in annualized variance units** (Jul 2017–Dec 2022, Deribit), roughly an order of magnitude larger than the S&P's ~2%. Implied variance exceeded subsequent realized variance for essentially the entire sample, with about **one month of inversion** during the March 2020 crash.

**Mechanism:** option buyers systematically overpay for protection; you are selling insurance.

**Catch:** the paper *measures* the premium, it does not backtest a tradable strategy — no costs, no execution, no drawdown path. The blog-quality backtests that do exist model P&L on option mark price with **no fees, slippage, or spread anywhere**. And that single inversion month is the tail that eats the whole premium — which a walk-forward harness must be built to *capture*, not average away.

### Funding-rate carry (perp funding)
Weaker than expected, on the evidence we got. In one 8-day November-2025 sample the **mean funding rate was slightly negative** on both CEX (−1.91 bps) and DEX (−1.74 bps) per 8h — no persistent positive premium to harvest in the level. The exploitable dispersion was in cross-venue *spreads*, not the level.

And cross-venue funding-spread arbitrage tested badly: of the 20 largest opportunities, **only 8 of 20 were net profitable** after fees and slippage; average net P&L $22 per $20k of gross exposure (0.11%); **average Sharpe −7.40**. 19 of 20 showed reversal patterns and 12 of 20 hit forced exits, so it cannot be held passively.

Reusable cost model from that source: 0.05% taker, plus 0.1% slippage (liquid, OI rank <50) or 0.5% (illiquid), negligible gas on Solana/Arbitrum/Optimism. That is **$60 round-trip per $10k/side liquid, $220 illiquid** — a 20 bps spread must persist **3.7 days** just to break even.

Caveat: the 8-day window is very short and covers one market condition.

---

## Ruled out — do not spend time here

These are the cheap negatives, and they're the most valuable part of this research.

| Strategy | Why it's dead for us |
|---|---|
| **Triangular arbitrage** | Over one week of Binance tick data, 4,879 gross opportunities → **18 profitable**; total net **$12–30 for the week**. Needs ~**146 ms** end-to-end latency and a Tokyo-colocated server (4 ms vs 80 ms from Europe). **Cheaper fees do not save it**: 96.93% still unprofitable at VIP 9 — and VIP 9 needs $4bn/month volume. |
| **CEX-DEX arbitrage / MEV** | Winner-take-all and **consolidating**: three searchers captured ~73% of value, rising to ~90% by Q1 2025. Profits accrue to vertical integration with block builders — integrated searchers pass ~90% of revenue to their builder. It's an access edge, not a signal edge. |
| **Grid bots** | **Mathematically zero expected value** under a symmetric random walk — proven, not estimated — therefore negative after fees. The widely-cited "60–70% IRR" result is attributed *by its own authors* to bull-market beta, from a single in-sample parameter sweep, no walk-forward, arXiv preprint. |
| **Naive market making on perps** | The passive/maker variant of a profitable HFT signal produced **no statistically significant returns on any of five assets** tested. |
| **HFT microstructure** | Target is the **3-second-ahead** mid-price with 1–2 second holds on 1-second order-book data. Authors state results are an idealized upper bound with latency and queue position unmodeled. Not reachable from a ccxt REST bot. |
| **Plain cross-sectional momentum** | Median annualized Sharpe **0.83** across 55,296 research designs; significant in only **49%** of them; range −4.47 to +2.30. Restricted to Binance-perp-tradeable coins it **decays post-2022** to Sharpe 0.83 ≈ the market. The classic Liu-Tsyvinski-Wu result's "large" coins have a median market cap of **$8.17M** — microcaps by today's standards, not top-50 liquid coins. |
| **Any short leg** | Short-only momentum lost money at **20 of 21** parameter pairs **even with zero transaction costs**; most cross-sectional short legs were fully liquidated. Authors conclude market-neutral crypto momentum is **unattainable**. This is a direct argument against adding shorts, despite them being "on the table." |
| **Single technical rules on BTC** | Across 14,919 rules, breakeven costs of 7.88–147 bps against ~50 bps real-world cost; **no rule family had more than 49.5%** of rules clearing 50 bps. Only **5–6%** of rules beat buy-and-hold on return for BTC. |

**One completed verification vote** is worth quoting, because it makes the momentum picture *contested* rather than settled: Liu, Tsyvinski & Wu (*Journal of Finance* 77(2), 2022) do find cross-sectional momentum among three factors pricing the crypto cross-section. The verifier judged the negative claim **not refuted** (confidence: high) because Han et al. explicitly re-test LTW under transaction costs, tradability limits and daily mark-to-market that LTW omit, and LTW's universe includes sub-$1M-liquidity coins a retail bot cannot trade.

---

## Methodology warnings that bear on our harness

These change how we should *use* the scan, and several are things we'd have got wrong.

1. **Non-standard errors in crypto research exceed standard errors.** Varying ten routine methodological choices (data source, sample filters, portfolio construction) across 43 sorting variables moves measured performance *more than sampling noise does*. A single backtest carries less information than its t-statistic suggests. **Implication: test across a grid of universe/filter/weighting choices, not one fixed pipeline.**

2. **Use log returns for significance, not mean returns.** Of 21 momentum portfolios, 10 had mean-return t-stats above 2.0 but only **3** had mean *log*-return t-stats above 2.0 — and 6 portfolios with positive mean returns were liquidated or lost money. Our metrics use simple returns.

3. **The factor zoo collapses.** From 36 return-predictive crypto factors, only **2–3** are needed to drive all significant alphas to insignificance. Chasing a long list of signals mostly re-discovers the same exposures.

4. **Anomalies are regime-dependent and decaying** — concentrated in bull markets, attenuating over time. Backtests spanning 2014–2022 systematically overstate forward edge. **Recent-subsample performance is the binding test.** Our walk-forward gate is the right shape for this; we should weight late folds more heavily.

5. **What actually prices the crypto cross-section is liquidity.** The dominant surviving factors are turnover volatility, bid-ask spreads, and an on-chain new-address-to-price ratio — *no price-momentum or trend factor appears among them*. That means the priced return component is compensation for illiquidity and trading friction: **precisely what a taker-fee, market-order retail bot pays away rather than earns.** This is the deepest argument for switching to maker/limit orders.

6. **Beware alpha concentrated in inaccessible assets.** In one ML study the quintile producing the long-short alpha was **0.8–9.1% of aggregate market cap**, average constituent $100–600M, with alphas ~3× higher in the hardest-to-arbitrage tercile.

---

## Recommended next steps, in order

1. **Add the cost-aware no-trade band** to `Trader.step` and re-run the scan. Cheap, uses the harness as-is, and it's the mechanism the literature says converts gross edge into net.
2. **Test long-only time-series momentum on BTC** (28-day lookback / 5-day hold, and the surrounding grid) through walk-forward. This is the single most directly testable Tier-1 claim, and its authors' own data-snooping disclaimer is exactly what our harness adjudicates.
3. **Switch the broker to maker/limit orders.** Finding 5 above says the priced factor in crypto is liquidity provision — taker orders pay it, maker orders earn it. This changes the sign of a cost, not just its size.
4. **Only then** consider the multi-coin universe needed for CTREND-style cross-sectional work. It is the biggest architectural change (the bot is single-symbol today) and should wait until the cheap tests are done.
5. **Do not** build shorts, grid bots, triangular arbitrage, or anything latency-sensitive. The evidence against each is strong and cheap to accept.

## What this research did NOT establish

- No adversarial verification on 90+ of the 94 claims. Several headline numbers (CTREND's 3.87%/week especially) are large enough to warrant skepticism on principle.
- Nothing here was reproduced by us. Every Tier-1 and Tier-2 item is a *hypothesis to test with the harness*, not a result to trade.
- Current Binance fee tiers, maker/taker rates, and VIP thresholds were not confirmed against live documentation.
