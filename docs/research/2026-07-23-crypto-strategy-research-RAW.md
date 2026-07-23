# Crypto strategy research — RAW harvested output (INCOMPLETE RUN)
Harvested 2026-07-23 from a deep-research workflow stopped before synthesis.
Completed: scope=1, search angles=6, sources with extracted claims=19, verification votes=6.
**The adversarial verification phase was only partly done — treat unverified claims as UNVERIFIED.**

## Question & angles
**Question:** Which crypto trading strategies have credible evidence of edge that survives out-of-sample testing AND realistic trading costs, for a solo retail trader running a Python bot?

**Decomposition rationale:** Decompose by the structural mechanism that could make an edge persist (risk premium, liquidity provision, forced flows, venue segmentation), giving the user's two priority families — funding/basis carry and cross-sectional momentum — dedicated slots, and adding the one named mechanism they flagged but no other angle covers (variance risk premium / options selling). Two further angles carry the skeptical load: a negative-findings query aimed at retail-promoted strategies they have NOT already personally falsified (grid bots, DCA, social sentiment, the crypto factor zoo's multiple-testing problem), and an overfitting-focused query on the most fragile family (on-chain/ML alpha), plus a practitioner angle on which edges retail can still capture without HFT infrastructure in 2026.

- {"label": "Academic — cross-sectional momentum & the crypto factor zoo", "query": "cross-sectional cryptocurrency momentum factor returns net of transaction costs out-of-sample replication coin universe", "rationale": "User's flagged priority family. Targets peer-reviewed and replication work on multi-coin momentum/reversal/size factors specifically reporting net-of-cost and post-publication out-of-sample performance, rather than raw backtest Sharpes."}
- {"label": "Academic/mechanism — funding-rate carry and perpetual basis", "query": "perpetual futures funding rate carry basis trade cryptocurrency risk premium empirical study net returns leverage costs", "rationale": "User's other flagged family. Seeks the structural explanation (leverage demand premium, forced liquidation flows) plus realistic net returns after funding, taker fees, and margin/borrow costs — the numbers needed to size a testable harness."}
- {"label": "Risk premium — variance/vol selling on crypto options", "query": "bitcoin ethereum variance risk premium options selling delta hedged returns Deribit empirical evidence transaction costs", "rationale": "Options are explicitly in scope and 'risk premium' is a mechanism the user named, but no other angle covers the volatility premium. Distinct academically-grounded edge with a very different cost/margin structure and tail-risk profile worth ruling in or out early."}
- {"label": "Contrarian/negative — retail strategies shown not to work", "query": "grid trading bots DCA social sentiment signals crypto backtest overfitting multiple testing deflated Sharpe ratio evidence they fail", "rationale": "Explicit request for cheap negative findings. Deliberately avoids MA/RSI-on-BTC (already empirically killed) and targets the retail-promoted set the user has not tested, plus the data-snooping literature for judging any published claim."}
- {"label": "Practitioner/infrastructure — what a solo trader can still capture in 2026", "query": "retail algorithmic crypto market making maker rebates order flow imbalance latency requirements alpha decay 2026 what still works", "rationale": "Separates liquidity-provision and segmentation edges that survive at retail latency from those requiring colocation, large capital, or institutional venue access. Also covers CEX/DEX arbitrage and MEV competition realities."}
- {"label": "Skeptical — on-chain, order book, and ML alpha claims", "query": "on-chain metrics exchange flows machine learning cryptocurrency return prediction out-of-sample net of fees does it survive", "rationale": "The most overfit-prone family and the widest data-acquisition cost. Framed skeptically to surface honest replications, survivorship/look-ahead critiques, and data-vendor cost realities rather than vendor marketing."}

## Sources found

### Han, Kang & Ryu — Time-Series and Cross-Sectional Momentum in the Cryptocurrency Market: A Comprehensive Analysis under Realistic Assumptions (SSRN 4675565; free full text + internet appendix)
- URL: https://acfr.aut.ac.nz/__data/assets/pdf_file/0009/918729/Time_Series_and_Cross_Sectional_Momentum_in_the_Cryptocurrency_Market_with_IA.pdf
- Relevance: high

The single most decision-relevant paper for this angle, and largely a NEGATIVE finding. Its explicit thesis is that prior crypto momentum studies 'disregard important real-world considerations and inadequately assess performance.' Once transaction costs and intraday/daily price fluctuation (i.e. margin liquidation of the short leg) are modelled, 'many momentum portfolios are liquidated and many with statistically significant returns earn insignificant profits.' Headline conclusion: evidence of TIME-SERIES momentum is strong, evidence of CROSS-SECTIONAL momentum is WEAK, and the effect is concentrated among large winners — losers rebound and inflict significant losses, which is precisely what kills a long-short CS-momentum book. Directly tempers the user's suspicion that cross-sectional momentum is one of the two most promising families: the academic evidence says the time-series/trend variant survives realistic assumptions better than the cross-sectional one. Note: do NOT anchor on the ~37.8% annualized top-quintile figure circulating from blog write-ups (starkiller.capital) — that is a gross, pre-cost number and is not this paper's net conclusion. Free full text with internet appendix makes the portfolio construction (lookbacks, rebalance frequency, universe filters) directly replicable in a walk-forward harness.

### Liu, Tsyvinski & Wu — Common Risk Factors in Cryptocurrency (Journal of Finance, 2022)
- URL: https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.13119
- Relevance: high

The canonical peer-reviewed anchor for the whole crypto factor literature and the reference point every replication paper below measures against. Finds that three factors — cryptocurrency market, size, and momentum — capture the cross-section of expected crypto returns, i.e. a crypto analogue of Fama-French. Published in the Journal of Finance (top-3 journal), so it clears the 'peer-reviewed, not a blog claim' bar the user set. Critical caveat for a solo retail trader: the paper's mandate is asset-pricing (explaining the cross-section), not net-of-cost tradability — its long-short portfolios are formed on a broad coin universe including small/illiquid names where realistic spreads and exchange access are the binding constraint. Use this to define the factor construction (market cap deciles, 1–4 week momentum lookbacks, weekly rebalance) that the user's harness should test, then apply the cost models from the other papers here rather than trusting the headline alphas.

### Crypto factor zoo (.Zip) — Finance Research Letters, 2026
- URL: https://www.sciencedirect.com/science/article/abs/pii/S1057521926000645
- Relevance: high

The dedicated replication study the user's angle calls for, and the newest (2026). Replicates a comprehensive set of 36 return-predictive crypto factors under a single explicit selection protocol, then asks how many priced dimensions actually exist. Punchline: just TWO TO THREE factors eliminate all significant portfolio alphas — i.e. the 'crypto factor zoo' is overwhelmingly redundant and most published signals carry no unique information once you control for a small core. The surviving/most influential dimensions are turnover volatility, bid-ask spreads, and blockchain-native metrics such as the new-address-to-price ratio — note that two of the three are LIQUIDITY/COST proxies, strongly implying much of the reported cross-sectional alpha is compensation for trading in illiquid coins the user cannot cheaply trade. This is the single cheapest way to rule out dozens of candidate signals before testing any of them, which is exactly the 'rule things out cheaply' request.

### A Trend Factor for the Cross Section of Cryptocurrency Returns — Journal of Financial and Quantitative Analysis (free full-text PDF)
- URL: https://unipub.lib.uni-corvinus.hu/11621/1/a-trend-factor-for-the-cross-section-of-cryptocurrency-returns.pdf
- Relevance: high

The strongest POSITIVE, testable-in-weeks result found. Peer-reviewed in JFQA (top-tier), and it explicitly reports that the trend factor SURVIVES the impact of transaction costs and — crucially for a solo retail trader — PERSISTS IN BIG AND LIQUID COINS, not just the illiquid microcap tail where most crypto anomalies live and where retail execution is impossible. This is the key differentiator from the generic factor-zoo results. Mechanism is a moving-average-trend signal aggregated across multiple lookback horizons and cross-sectionally ranked, which is a natural generalisation of the user's already-built MA machinery: instead of one MA crossover on one symbol, rank a liquid multi-coin universe on a combined multi-horizon trend score and go long the top / short the bottom. Also reconciles with the Han/Kang/Ryu finding above — trend (time-series-flavoured) beating pure cross-sectional momentum. Free full text means the exact signal construction is available for direct implementation in the walk-forward harness.

### Cryptocurrency Anomalies and Economic Constraints — International Review of Financial Analysis, 2024
- URL: https://www.sciencedirect.com/science/article/abs/pii/S1057521924001509
- Relevance: high

Answers the user's question #2 and #3 most directly: WHICH crypto anomalies actually survive real trading costs, and at what turnover. Finds trading costs 'severely hamper the profitability of anomaly strategies' but with UNEVEN impact — size and volume portfolios have moderate turnover of roughly 10–16% per week and continue to generate substantial profits after transaction costs, while higher-turnover signals do not. The turnover figure is the load-bearing number: at ~10-16% weekly turnover on Binance's 0.1% taker rate, fee drag is roughly an order of magnitude below what the user measured on 3m/1h MA crossovers, which is the structural reason weekly-rebalanced cross-sectional factors can clear costs where intraday timing cannot. Also argues low liquidity (which raises transaction costs) is itself what allows these anomalies to PERSIST — a genuine structural/limits-to-arbitrage reason for the edge rather than 'it backtested well', but simultaneously a warning that the edge lives where the user's execution is worst.

### Non-standard Errors in the Cryptocurrency World — Finance Research Letters, 2024
- URL: https://www.sciencedirect.com/science/article/abs/pii/S1057521924000383
- Relevance: medium

The overfitting/researcher-degrees-of-freedom check the user explicitly asked for ('flag anything where the published evidence looks like overfitting or survivorship bias'). Applies the 'non-standard errors' methodology — multiple independent research teams given the same crypto data and the same hypotheses — to quantify how much reported crypto results vary purely from defensible differences in universe construction, delisting/survivorship handling, return winsorisation, and price-source choice. Directly relevant because the crypto cross-section is unusually fragile to these choices: dead-coin and delisting treatment alone can flip the sign of a long-short momentum portfolio, and most published crypto factor papers draw from CoinMarketCap/CoinGecko snapshots that are survivorship-contaminated. Read this as the prior to apply to every headline Sharpe in the four papers above, and as the justification for the user's own instinct to pre-commit thresholds and share one simulation path across backtest/walk-forward/live.

### Han, Kang & Ryu — Time-Series and Cross-Sectional Momentum in the Cryptocurrency Market: A Comprehensive Analysis under Realistic Assumptions
- URL: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4675565
- Relevance: high

Directly targets one of the two families you flagged. The paper's stated contribution is that prior crypto-momentum studies ignore real-world frictions; once transaction costs, forced liquidation and intraday price fluctuation are imposed, 'many momentum portfolios are liquidated and many with statistically significant returns earn insignificant profits.' Headline split is the actionable part: evidence for TIME-SERIES momentum is strong, evidence for CROSS-SECTIONAL momentum is WEAK. That is a direct partial negative on cross-sectional momentum across a coin universe, and it points you toward per-asset trend rather than rank-and-rotate. Its friction model (costs + liquidation + realistic fills) is also a template you can copy into your walk-forward harness. Note: SSRN/AUT mirrors returned 403 to automated fetch — findings above are from indexed abstract text, so read the full PDF before relying on magnitudes. Open-access mirror also exists at acfr.aut.ac.nz (PDF, bot-blocked) and ResearchGate.

### The Two-Tiered Structure of Cryptocurrency Funding Rate Markets (Mathematics, MDPI)
- URL: https://www.mdpi.com/2227-7390/14/2/346
- Relevance: high

The most useful net-of-cost reality check I found on funding-rate carry, your other suspected family. Key numbers: ~17% of observations show economically significant funding/basis spreads (>=20bp), but only ~40% of the TOP opportunities are still positive after transaction costs and spread reversals — i.e. the raw funding screen massively overstates capturable edge, and the killer is not just fees but mean-reversion of the spread while you are in the trade. Also documents the segmentation mechanism that would let the edge persist: CEX venues dominate price discovery with ~61% higher integration than DEXs, with information flowing CEX->DEX and zero reverse causality, meaning DEX-perp funding is the slower, more mispriced tier. Practitioner read: the structural story (long-biased perp speculators pay carry) is real, but a naive 'short perp / long spot on Binance' harvest is close to competed away; the residual is in the second tier. Directly testable with funding-rate history in your harness.

### Measuring CEX-DEX Extracted Value and Searcher Profitability: The Darkest of the MEV Dark Forest (AFT 2025)
- URL: https://arxiv.org/abs/2507.13023
- Relevance: high

Verified by fetch. The definitive 'do not bother' evidence for CEX/DEX arbitrage and MEV as a solo-trader strategy. Over Aug 2023–Mar 2025 it identifies 8.7M candidate CEX-DEX arbitrage transactions and attributes $233.8M extracted to just 19 major searchers across 7.2M arbitrages — and THREE searchers captured three-quarters of both volume and extracted value. Critically, profitability is shown to be a function of a searcher's INTEGRATION LEVEL WITH BLOCK BUILDERS, including exclusive searcher-builder relationships; vertically integrated builder-searchers are more profitable than previously estimated. This is a structural, not a skill, barrier: without a builder relationship and colocated latency the residual margin is negligible. Use this to permanently deprioritise CEX/DEX arb, cross-venue latency arb, and MEV from your roadmap.

### Wish or reality? On the exploitability of triangular arbitrage in cryptocurrency markets (Finance Research Letters)
- URL: https://www.sciencedirect.com/science/article/pii/S154461232401537X
- Relevance: high

Peer-reviewed negative finding on the single most heavily promoted 'risk-free' retail crypto strategy. Using high-frequency Binance data (BTC/LTC/USD triangles) the authors find thousands of apparent opportunities (4,879 in the cited sample) but conclude they are not exploitable once transaction costs and, crucially, LIMITED ORDER BOOK DEPTH at the quoted prices are accounted for — average triangular cycles run only ~0.05–0.15%, below round-trip taker cost. The title is literal: the opportunities are a data artifact of stale/top-of-book quotes, not capturable P&L. Rules out intra-exchange triangular arb (which is the version usually pitched to retail precisely because it avoids withdrawal delay and transfer risk) without you spending weeks building it. Fetch was 403-blocked (ScienceDirect paywall); findings from indexed abstract.

### Hudson & Urquhart — Technical Trading and Cryptocurrencies (open-access repository copy)
- URL: https://centaur.reading.ac.uk/85715/8/Hudson-Urquhart2019_Article_TechnicalTradingAndCryptocurre.pdf
- Relevance: high

Independent corroboration of your own empirical null on MA/RSI timing, at far larger scale than 16 configs. This literature tests on the order of ~15,000 technical trading rules (MA, filter, support/resistance, channel breakout, OBV) across major cryptocurrencies with explicit DATA-SNOOPING adjustment (White's Reality Check / Hansen SPA), which is the correction your 16-config gated scan approximates but does not formally implement. Related work in the same cluster reports mean Sharpe collapsing from ~0.66 in-sample to ~0.06 out-of-sample, no predictability for Bitcoin specifically out-of-sample (some remaining in smaller alts), and returns that do not survive modest transaction costs. Practical takeaway: your finding that 4h MA+trend passed marginally on 2 folds is almost certainly the survivor of a multiple-testing problem — treat it as noise, and do not spend more cycles enumerating price-only rule variants on BTC. Repository PDF returned a bot-challenge to automated fetch but is publicly readable in a browser.

### Explainable Patterns in Cryptocurrency Microstructure (arXiv 2602.00776)
- URL: https://arxiv.org/html/2602.00776v1
- Relevance: medium

Answers the 'is order-flow alpha reachable at retail latency?' question, which is the core of the infrastructure angle. Verified by fetch: order flow imbalance and queue imbalance are statistically significant price predictors, but predictability lives at SECONDS-TO-MINUTES horizons and the paper's own framing is that converting it to P&L requires execution fast enough to beat the price adjustment; spreads, fees and slippage erode the theoretical return at ultra-short horizons, and retail participants on conventional venues face latency/cost disadvantages that eliminate many identified patterns. This is consistent with your measured fee-drag of up to 14x on 3-minute configs — the sub-hourly band is structurally hostile to a taker-order retail bot. Corollary for scoping: any signal you find at 1m/3m is only investable if you can quote passively (maker) rather than cross the spread, and Binance's negative-fee tiers require ~$100M/month volume, so maker rebates are out of reach; at best you get maker-fee (not rebate) economics.

### Risk Premia in the Bitcoin Market (Almeida, Grith, Miftachov & Wang, arXiv 2410.15195, rev. Aug 2025)
- URL: https://arxiv.org/abs/2410.15195
- Relevance: high

The strongest academic evidence that a BTC variance risk premium exists and is structurally large. Built from Deribit option-implied risk-neutral densities: 'Bitcoin is much more volatile and has a higher variance risk premium than the S&P 500.' Critically for a testable strategy, it finds BVRP is regime-dependent — HIGH in low-volatility regimes, COMPRESSED in high-volatility states — which implies a naive always-short-vol rule harvests premium exactly when it is thinnest and pays out when it is richest. That regime split is directly implementable as a walk-forward-testable conditioning variable. Caveat for the user: this documents the premium's existence and size, not its capturability net of spreads, fees, and hedging costs.

### Bitcoin Options: Finding Edge in Four Years of Volatility Regimes (Deribit Insights)
- URL: https://insights.deribit.com/industry/bitcoin-options-finding-edge-in-four-years-of-volatility-regimes/
- Relevance: high

The most directly actionable source: an actual systematic short-straddle backtest on Deribit BTC options, May 2019–Dec 2022. Claims 30d implied vol exceeded 30d realized vol ~70% of the time, uses a 2.5% price-move rehedge threshold (not continuous delta hedging) specifically to suppress transaction costs, and reports optimal blends of ~90% strategy/10% spot for weeklies vs ~30%/70% for monthlies. TWO decision-critical caveats: (1) it computes P&L from MARK prices and openly concedes this 'is not entirely realistic in practice' — so the headline risk-adjusted numbers are an upper bound that ignores the bid-ask spread, which on crypto options is the dominant cost, not the fee; (2) the cost structure is fundamentally different from the user's failed spot strategies — Deribit options are ~0.00% maker / ~0.03% taker (of underlying, capped vs premium), versus the 0.1% Binance spot taker that produced their 0.78 fee-drag. This is a practitioner blog, not peer-reviewed.

### The Bitcoin VIX and Its Variance Risk Premium — Alexander & Imeraj (Journal of Alternative Investments, 2021)
- URL: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3383734
- Relevance: high

The foundational peer-reviewed paper on crypto VRP; built the BVIN index (CBOE VIX methodology) from ~7 million Deribit option prices sampled every 15 minutes, and is the first to study the term structure of fair-value BTC variance swap rates — i.e., it tells you WHICH maturity to sell. The single most important line for the user's purposes is the reported finding that the Bitcoin VRP SPIKES BEFORE large positive or negative returns. That is the tell that this premium is compensation for jump/tail risk rather than a mispricing: the payoff profile is many small wins punctuated by rare large losses, which is precisely the shape that a short backtest window and a Sharpe-ratio gate will misprice. Gives a concrete, replicable index construction the user could rebuild from Deribit's public API.

### Illiquidity Premium and Crypto Option Returns — Atanasova et al. (full PDF; published as 'Aggregate illiquidity and crypto option returns', Finance Research Letters 85, 2025)
- URL: https://acfr.aut.ac.nz/__data/assets/pdf_file/0006/969378/950002_Atanasova_Illiquidity-Premium-and-Crypto-Option-Returns.pdf
- Relevance: high

Answers the user's cost-structure question with transaction-level Deribit data (Jan 2020–Jul 2024) rather than mark prices. The paper reports that a one-standard-deviation rise in option illiquidity raises DAILY delta-hedged returns by roughly 0.07% for calls and 0.06% for puts, and attributes this to market makers demanding an illiquidity premium to offset hedging and rebalancing costs when they hold net-long inventory. Mechanistically important: it says a meaningful slice of the apparent short-vol edge is really a liquidity-provision premium — which means a retail taker crossing the spread is PAYING that premium rather than earning it, and only resting maker orders capture it. Also gives an empirical handle on when spreads widen (negative dealer gamma inventory), i.e., when execution assumptions in a backtest will be most wrong. Peer-reviewed; figures quoted are the paper's claims, not independently reverified here.

### Jump Risk Premia in the Presence of Clustered Jumps — Liu, Packham & Sepp (arXiv 2510.21297, Oct 2025)
- URL: https://arxiv.org/abs/2510.21297
- Relevance: medium

Uniquely bridges the user's two priority families. Fits a bivariate Hawkes jump model to BTC options and extracts separate POSITIVE and NEGATIVE jump risk premia, then shows those inferred premia have predictive power for BOTH the performance of delta-hedged option strategies AND the cost of carry in BTC futures — i.e., one option-implied signal that speaks to short-vol timing and to funding/basis carry simultaneously. Co-authored by Artur Sepp, a crypto-vol practitioner, so the modelling is execution-aware. Decision value: it argues the crypto vol premium is dominated by jump compensation with sign-switching skew (crypto skew flips positive in bull sentiment, unlike equities), which explains why equity-derived short-vol intuitions transfer badly. Implementation difficulty is the highest in this set — Hawkes-process calibration is well beyond a walk-forward MA-crossover harness.

### Quantifying Risks of DeFi Options Vaults — IV League DAO
- URL: https://medium.com/iv-league-dao/quantifying-risks-of-defi-options-vaults-bb18950a29ed
- Relevance: medium

The honest negative finding the user explicitly asked for, covering the retail-accessible packaged version of this trade (DeFi option vaults / automated covered calls and cash-secured puts). Reports that index volatility-harvesting has consistently UNDERPERFORMED simple buy-and-hold over ~5 years and that DOVs inherit this; DOV return distributions have long left tails, and a handful of tail events — not gradual decay — drive the underperformance. Also names the structural flaw: vaults sell volatility indiscriminately on a fixed schedule regardless of whether the premium is rich, which is exactly the naive rule the Almeida regime evidence warns against. A cited example shows a covered-SOL strategy leaving a holder with ~0.30 SOL from 1 SOL in coin terms. Practitioner/DAO blog, NOT peer-reviewed — treat the numbers as illustrative, but the mechanism (path-dependent left tail, coin-denominated loss vs USD-denominated gain) is the cheap ruling-out the user wanted.

### Borri, Liu, Tsyvinski & Wu — Cryptocurrency as an Investable Asset Class: Coming of Age (arXiv 2510.14435, rev. Mar 2026)
- URL: https://arxiv.org/abs/2510.14435
- Relevance: high

The single most on-target source for 'is the edge still alive.' Constructs the crypto carry trade explicitly as short perpetual / long spot and reports annualized Sharpe of 6.45 over the full 2020-2025 sample, falling to 4.06 from 2024 and turning NEGATIVE in 2025 — direct decay evidence against sizing a harness off full-sample numbers. Profit is attributed mostly to the funding rate itself: mean return ~8%/yr at only ~0.8% volatility (which is why the raw Sharpe looks absurd, and why costs/liquidation tails dominate the real distribution). Caveat the user should note: the paper does not explicitly model transaction costs for the carry leg. Same paper also covers the user's second flagged family — crypto-size, crypto-momentum (past two-week returns) and crypto-value (price-to-new-address) span the cross-section; short-horizon momentum long-short earns 0.026 weekly (t=3.89), while long-horizon momentum, volatility, volume and beta 'continue not to generate significant average returns in the recent sample' — a ready-made negative-findings list. Free full text; authored by the Liu/Tsyvinski group behind the canonical crypto factor literature. Full HTML at arxiv.org/html/2510.14435v2.

### Schmeling, Schrimpf & Todorov — Crypto Carry (BIS Working Paper No. 1087; published in Management Science, 2026)
- URL: https://www.bis.org/publ/work1087.pdf
- Relevance: high

The canonical MECHANISM paper the user asked for — a structural reason the edge exists rather than 'it backtested well.' Documents carry (futures-minus-spot) reaching over 40% per annum with large time variation, and traces it to exactly two forces: (i) demand from smaller, trend-chasing retail investors buying leveraged long exposure, and (ii) limited deployment of arbitrage capital due to regulatory and margin frictions. Key friction for sizing a real trade: absence of cross-margining between spot and futures on regulated venues (on CME you cannot post spot BTC as collateral, so arbitrageurs fund the position twice) — this is the capital-efficiency constraint that determines whether a solo trader's realized return resembles the headline carry. Concludes structural limits to arbitrage amplify price inefficiencies. Free full-text BIS PDF; peer-reviewed version is Management Science 2026, doi 10.1287/mnsc.2024.05069.

### Exploring Risk and Return Profiles of Funding Rate Arbitrage on CEX and DEX (ScienceDirect / Digital Business, 2025)
- URL: https://www.sciencedirect.com/science/article/pii/S2096720925000818
- Relevance: high

The most directly retail-implementable net-return study found. Scrutinizes funding rate arbitrage in perpetual futures across centralized venues (Binance, BitMEX) and decentralized ones (ApolloX, Drift), covering BTC, ETH, XRP, BNB and SOL — i.e. the exact venue/instrument set a ccxt bot can reach. Reports that funding rate arbitrage returns are essentially uncorrelated with HODL, which is the diversification argument for adding it to a long-only bot. Critically for harness design, it finds that introducing leverage into the trade significantly raises liquidation risk plus penalty fees, and that funding cost expressed as a percentage of MARGIN can push a position toward liquidation even when the underlying price barely moves — the failure mode a naive delta-neutral backtest will miss. Note: the ScienceDirect page returned HTTP 403 to automated fetch, so the specifics above come from indexed abstract/summary text; the user should pull the PDF manually to extract the exact fee and slippage assumptions before trusting any headline APY.

### Ackerer, Hugonnier & Jermann — Perpetual Futures Pricing (Mathematical Finance, 2026)
- URL: https://finance.wharton.upenn.edu/~jermann/AHJ-main-10.pdf
- Relevance: medium

Theory rather than empirics — include for correctly specifying the harness, NOT for expected returns. Derives the no-arbitrage pricing relation for non-expiring perpetual contracts and what the funding rate must equal to tether perp price to spot, which is the equation a simulator needs to accrue funding correctly (8h vs 4h vs 12h payment schedules, three daily UTC checkpoints on most venues). Useful for getting the sign convention and accrual timing right — longs pay shorts when perp trades above spot — and for understanding why perps carry less basis risk than dated quarterly futures. Contains no net-of-cost backtest, no Sharpe ratios, and nothing about retail feasibility; do not expect testable return figures from it. Free author PDF; the Wiley version is doi 10.1111/mafi.70018.

### Mallory — Implied ETF Carry Rates and the Limits of Arbitrage in Segmented Bitcoin Markets (arXiv, May 2026)
- URL: https://arxiv.org/html/2605.29309
- Relevance: low

Included mainly as a RULE-OUT signal. Reinforces the segmentation mechanism with fresh 2026 evidence: a persistent wedge between carry implied by IBIT options (via put-call parity on BlackRock's daily holdings) and matched CME bitcoin futures, mean 2.58 pp and median 2.52 pp annualized, ranging -4.77% to +10.42% across 386 observations, wider at longer tenors (2.94% vs 2.22%). Cause is segmented collateral and margin systems that prevent treating hedged positions as integrated — the same no-cross-margining friction as the BIS paper. But the instruments are US-listed ETF options and CME futures: institutional venues a solo trader running ccxt against Binance cannot access, and the 2.5% gross wedge would not survive retail commissions and margin costs anyway. Read it for why the premium persists, not as a strategy to implement.

### Microstructure alpha: hierarchical learning and cross-asset transfer in cryptocurrency markets (Frontiers in Blockchain, 2026)
- URL: https://www.frontiersin.org/journals/blockchain/articles/10.3389/fbloc.2026.1811716/full
- Relevance: high

The single strongest rule-out for the order-book/microstructure ML family, and it is a negative finding by the authors' own admission (verified by fetching the paper, not just the title). 3.4M minute-level observations, 6 coins, Binance spot AND perpetual futures, Aug 2025-Feb 2026. All 12 microstructure features pass stability selection, but OLS gains only ~1.23% R-squared over a random walk. Deployed as strategies at Binance VIP-0 fees, ALL net Sharpe ratios are deeply negative, roughly -52 to -18 across venues and models -- and this includes their own proposed hierarchical/transfer-learning method, not just naive baselines. Their concluding words: 'the information is far too weak to overcome Binance VIP-0 frictions at a 5-min holding horizon,' because '288 round trips per day' at '20 bps per round trip' overwhelms the edge 'by orders of magnitude.' Authors explicitly position the work as 'diagnostic rather than prescriptive.' Also delivers the key leakage critique: LightGBM shows 35.9% in-sample R-squared vs 0.2% out-of-sample under naive splits, and collapses to -10.94% (worse than random walk) under purged/embargoed CV with a 5-min purge and 60-min embargo. Directly generalizes the user's own empirical finding (fee drag of 14 at 3-minute bars) and tells them not to spend weeks on order-book alpha or high-frequency ML.

### Machine Learning-Based Bitcoin Trading Under Transaction Costs: Evidence From Walk-Forward Forecasting (arXiv 2606.00060)
- URL: https://arxiv.org/html/2606.00060
- Relevance: high

Closest published analogue to the user's own harness, and it reaches a similar conclusion. ~70,000 hourly BTC/USDT bars (2018-2026, Binance futures), XGBoost vs LSTM vs iTransformer, evaluated on a 27-fold rolling walk-forward (12mo train / 3mo validation / 3mo test, advancing quarterly). Naive sign-rule ML strategies collapse at 10 bps costs: XGBoost long-only -64.00% annualized, iTransformer long-short -98.62% annualized. A cost-aware execution filter (trade only when expected move exceeds a lambda multiple of round-trip cost) restores XGBoost to 65.40% annualized / Sharpe 1.09 by cutting turnover from 10,619 to 251 trades -- but the honest caveat is decisive: bootstrap-corrected Sharpe tests do NOT reject equality with buy-and-hold. The paper's real contribution is 'execution discipline,' not alpha. Two directly testable takeaways for the user: (1) the walk-forward protocol is a template they can copy, (2) a signal-magnitude-vs-cost trade gate is the single highest-leverage cheap experiment given their measured fee drag, but they should benchmark against buy-and-hold with a bootstrap test or they will fool themselves.

### Introducing Point-in-Time Data: Addressing the Mutability of On-chain Metrics (Glassnode)
- URL: https://insights.glassnode.com/introducing-point-in-time-data
- Relevance: high

The on-chain data vendor itself documenting that its own historical metrics carry look-ahead bias -- an unusually credible source for a skeptical read because it cuts against the vendor's marketing. Exchange balances, entity-tagged flows and similar metrics are RETROACTIVELY REVISED as address-clustering and entity-labelling improve, so the value shown today for a past date is not what was published then. Glassnode ran the same simple BTC exchange-balance strategy (long when the 5-day MA of Binance BTC balance falls below the 14-day MA, exit on reversal) on revised vs immutable point-in-time data, Jan 2024-Mar 2026, $1,000 capital, identical 0.1% fees: the revised-data version roughly matched buy-and-hold, while the point-in-time version missed the Nov 2024 and Mar 2025 rallies and came in considerably lower. Practical consequence for the user: ANY on-chain backtest built on a standard vendor API is contaminated unless the vendor serves point-in-time variants -- and Glassnode gates PiT behind its Professional tier, so the data-acquisition cost is real and recurring. Strong argument for deprioritizing the on-chain family until PiT data is budgeted for.

### Machine learning and the cross-section of cryptocurrency returns (International Review of Financial Analysis)
- URL: https://www.sciencedirect.com/science/article/abs/pii/S1057521924001765
- Relevance: high

Directly addresses one of the two families the user flagged as most relevant (cross-sectional momentum across a coin universe), and is the main POSITIVE peer-reviewed claim surfaced. The paper reports that ML predicts the cross-section of crypto returns, with the dominant predictors being price level, past alpha, illiquidity and momentum, and CLAIMS profitability persists despite high turnover and transaction costs. Treat as a claim to be replicated, not a settled result -- direct verification was blocked (HTTP 403 paywall), so details come from search indexing. Two specific skeptical flags before the user builds on it: (1) ILLIQUIDITY appearing among the top predictors is the classic tell that returns concentrate in small, thinly-traded coins where the modelled cost assumption almost never matches realized slippage for a market order; (2) crypto cross-sectional studies are acutely exposed to survivorship bias because delisted and collapsed tokens routinely drop out of vendor universes. Testable cheaply: rebuild the universe from a point-in-time listing snapshot including dead coins, and re-run with liquidity-tiered slippage rather than a flat fee.

### Return and Volatility Forecasting Using On-Chain Flows in Cryptocurrency Markets (Chi, Chu & Hao, arXiv 2411.06327)
- URL: https://arxiv.org/abs/2411.06327
- Relevance: medium

The strongest academic statement of the on-chain exchange-flow claim, useful as the steelman to test against the Glassnode look-ahead critique above. Studies BTC, ETH and USDT net exchange inflows 2017-2023 at 1-6 hour horizons -- notably matching the user's existing 1h/4h data cadence. Headline claims: USDT net inflows to exchanges POSITIVELY predict BTC and ETH returns and negatively predict volatility; ETH net inflows NEGATIVELY predict ETH returns and volatility at all intraday intervals; BTC net inflows are mixed for returns. Skeptical caveats worth passing on: the abstract states neither out-of-sample results nor transaction-cost accounting, and the profitability assessment is routed through ETH OPTION strategies rather than a plain spot/perp signal -- which quietly changes the cost structure and is not something the user's current market-order spot harness can reproduce. Also uses conventionally revised on-chain history, so the Glassnode PiT contamination applies. Sensible cheap test: USDT exchange-inflow as a single filter on a 4h signal, with the honest expectation that the effect is a volatility/regime signal rather than a tradable return edge.

### Exploring Microstructural Dynamics in Cryptocurrency Limit Order Books: Better Inputs Matter More Than Stacking Another Hidden Layer (arXiv 2506.05764)
- URL: https://arxiv.org/abs/2506.05764
- Relevance: medium

Cheap ruling-out for the deep-learning-on-order-books family, which is where most retail ML enthusiasm and most data spend goes. Benchmarks logistic regression and XGBoost against deep architectures (DeepLOB, Conv1D+LSTM) on BTC/USDT limit-order-book snapshots, comparing out-of-sample accuracy, inference latency and noise robustness. Finding: the SIMPLE models match or exceed the deep networks while being faster and interpretable -- apparent gains from added hidden layers are largely attributable to data preprocessing and feature engineering, not model capacity. Complements the Frontiers paper: that one shows the LOB signal is too weak to beat retail fees at all; this one shows that even the statistical accuracy attributed to deep models is mostly a preprocessing artifact. Combined implication for a solo trader: buying tick-level LOB data and building a DeepLOB pipeline is very likely wasted capital and weeks, and the correct prior is that any published deep-LOB result should be assumed non-replicable until shown otherwise under purged CV and realistic fees.

### Testing the Applicability of the Technical Trading Strategy in the Cryptocurrency Market
- URL: https://pubs.sciepub.com/jfe/11/4/2/index.html
- Relevance: high

VERIFIED by fetching the paper. The closest published analogue to the user's own harness, and it reaches the same negative conclusion. Tests EMAC, RSI, Bollinger Bands and MACD on BTC/USDT and ETH/USDT, Aug 2017–Oct 2023, split in-sample/out-of-sample at 20 Dec 2021, with White's Reality Check bootstrap plus a stepwise test to control data snooping across 83+ strategy variants. Headline: the best BTC EMAC rule returned 116.0% annualized in-sample but only 3.6% out-of-sample and statistically insignificant; the authors conclude 'previously profitable technical approaches, observed prior to December 2021, generally failed to generate profits during the subsequent out-of-sample period.' Costs modelled were only 0.001 slippage + 0.0003 commission — far cheaper than the user's 0.1% taker rate — and results were still negative OOS, which independently corroborates the user's finding that zero-fee MA/RSI on BTC is still a loser. Cheap rule-out: MA/RSI/MACD/Bollinger timing on BTC and ETH is a dead family, not a fee problem.

### Machine Learning-Based Bitcoin Trading Under Transaction Costs: Evidence From Walk-Forward Forecasting
- URL: https://arxiv.org/abs/2606.00060
- Relevance: high

VERIFIED by fetching the paper. Directly transferable: ~70,000 hourly BTC/USDT observations 2018–2026, walk-forward evaluation, 10 bps per position change as the effective cost (fees + spread + slippage) — nearly identical to the user's setup and cost assumption. Findings, honestly reported: ML forecasts contain measurable signal but naive sign-based strategies collapse entirely once costs are applied. A cost-aware execution filter that suppresses weak signals restores profitability only by cutting turnover >97% (10,619 trades down to 251); the best XGBoost config then shows 65.4% annualized return, Sharpe 1.09, but with a −67.4% max drawdown. Critically: 'None of the reported cost-aware strategies significantly outperforms buy-and-hold in Sharpe-ratio terms after Holm correction.' This is the strongest cheap rule-out for the whole ML-on-price-history family — the achievable result is beta plus enormous drawdown, not alpha. It also supplies a directly reusable design lesson: turnover suppression, not model architecture, is the dominant lever.

### The Probability of Backtest Overfitting (Bailey, Borwein, López de Prado, Zhu)
- URL: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253
- Relevance: high

The methodological tool that applies directly to the user's own scan of 16 configurations and to every published claim in this report. Introduces PBO, which measures whether a selection process is conducive to overfitting by testing whether the config chosen as best in-sample tends to underperform the median of all trials out-of-sample. The companion result (in 'Pseudo-mathematics and Financial Charlatanism', Notices of the AMS, 2014) is the actionable one: with only a few years of data, a small number of trials is enough to manufacture an impressive in-sample Sharpe from pure noise. This is exactly the lens to apply to the user's single surviving 4h MA+trend-filter config: 1 winner out of 16 pre-committed trials, 24 trades, +0.15% out-of-sample on 2 walk-forward folds is precisely the signature PBO is designed to flag as selection noise rather than edge. Use it as the gate before spending weeks on any new family.

### The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting and Non-Normality (Bailey & López de Prado)
- URL: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551
- Relevance: high

The correction to apply once PBO has flagged the problem, and the single cheapest filter for judging the published crypto strategy literature. DSR adjusts an observed Sharpe for two inflation sources the user's harness currently does not account for: (1) selection bias under multiple testing — when N variants are tried and the best kept, the max Sharpe is inflated even if all N are pure noise; and (2) non-normal returns, correcting via skewness and kurtosis, which matters acutely in crypto where returns are heavily fat-tailed. Practical value here is twofold: bolt DSR onto the existing gated scan so the pre-committed threshold accounts for the number of configs tested, and use it to discount any paper in this space that reports a raw Sharpe without disclosing how many specifications were searched — which is most of them.

### Dynamic Grid Trading Strategy: From Zero Expectation to Market Outperformance
- URL: https://arxiv.org/abs/2506.11921
- Relevance: high

VERIFIED abstract. The cleanest available rule-out for grid bots — the most heavily retail-promoted family the user has not tested, and one where the vendor literature (Bitsgap, 3Commas, Pionex) is pure marketing. The paper's own analytical starting point is the negative finding: 'Starting with an analysis of the expected value of the traditional grid strategy, we show that under simple assumptions, its expected return is essentially zero.' Zero expectancy gross means strictly negative net of a 0.2% round trip — and grid bots are high-turnover by construction, so the fee-drag ratio the user already measured would be brutal. Structurally, a grid is a short-volatility/short-gamma position with no premium collected: it harvests small wins in a range and holds an unhedged losing position when price trends out. Read the paper's own proposal skeptically too — the DGT variant is backtested on a single Jan-2021–Jul-2024 BTC/ETH minute-data window with no out-of-sample split reported in the abstract, which is exactly the overfitting signature the user asked to have flagged. Verdict: skip grid and martingale/DCA-averaging bots without testing them.

### Technical trading and cryptocurrencies (Hudson & Urquhart, Annals of Operations Research 2021)
- URL: https://link.springer.com/article/10.1007/s10479-019-03357-1
- Relevance: medium

INCLUDED AS A CLAIM TO DISTRUST, not as supporting evidence. This is the most-cited 'technical analysis works in crypto' paper — ~15,000 rules across five rule classes on two Bitcoin markets and three other coins, reporting significant predictability and profitability for every rule class, with break-even transaction costs said to exceed those actually found in crypto markets. Expect other researchers to surface it as positive evidence; it should be discounted for three reasons. (1) Regime/period bias: published online Aug 2019, so its sample ends around 2018 — entirely inside crypto's secular bull run and entirely before the user's test window. (2) Benchmark choice: 'profitability' is measured against a cash/zero benchmark, not against buy-and-hold, so any long-biased rule in a violent bull market clears the bar almost trivially — the arXiv walk-forward paper above shows the result flips once buy-and-hold is the benchmark and Holm correction is applied. (3) It has already been falsified out-of-sample twice: by the sciepub study's post-Dec-2021 test, and by the user's own harness. Useful mainly as a worked example of how a large, competently data-snooping-controlled study can still produce a conclusion that does not survive the next regime.


## Extracted claims by source

### Source 1 — quality: primary | published: 2024 (International Review of Financial Analysis, Vol. 94, article 103218; DOI 10.1016/j.irfa.2024.103218)

**[central]** Cross-sectional momentum DOES survive in the liquid, large-cap segment of the crypto universe (unlike size/volume anomalies), but its net profitability is materially eroded by trading costs, and most of its alpha comes from the SHORT leg — meaning a long-only implementation captures only a fraction of the documented effect. This is directly falsifiable in a walk-forward harness: build a long-only large-cap cross-sectional momentum book with realistic taker fees and check whether alpha survives.

> Conversely, the momentum effect prevails in larger cryptocurrencies but incurs substantial trading costs and extracts alphas largely from short positions.

**[central]** The documented size and volume (illiquidity/volume) anomalies in the crypto cross-section are artifacts of micro-cap coins that are too small to trade at any meaningful size — i.e., they are not economically exploitable and should be ruled out cheaply rather than tested. This predicts that replicating size/volume factor sorts while excluding micro-caps (or applying a realistic liquidity/market-cap floor) will kill the effect.

> We find that size and volume anomalies originate from micro-cap coins of negligible economic importance.

**[central]** Crypto anomaly returns are regime-dependent and decaying: abnormal returns are concentrated in bull markets and attenuate over the sample period. This implies backtests spanning 2014–2022-era crypto bull runs systematically overstate forward-looking edge, and that any anomaly's recent-subsample performance is the binding test — a direct warning that headline factor-zoo results are period-specific rather than structural.

> Most abnormal returns occur primarily in bull markets and fade over time.

**[supporting]** The authors prescribe a specific evaluation protocol for deciding whether a crypto anomaly is genuinely tradable: restrict to long positions, explicitly model transaction costs, exclude/handle hard-to-trade coins, and weight recent-period performance. This is a concrete, adoptable specification for a walk-forward harness's gating criteria.

> Therefore, protocols for identifying tradable cryptocurrency anomalies should focus on long positions, account for transaction costs, consider hard-to-trade coins, and emphasize performance in recent years.

**[tangential]** The paper's premise is that the crypto 'factor zoo' of documented cross-sectional return predictors is large and growing, but that whether any of it converts into realizable trading profit was an open question requiring separate testing under economic constraints — i.e., published crypto anomaly alphas should be treated as gross-of-constraint statistical findings, not as strategy performance.

> The asset pricing literature documents a growing list of predictable patterns in the cross-section of cryptocurrency returns. But can they be forged into viable trading profits?

### Source 2 — quality: primary | published: 2024-12-07 (available online; accepted 22 Nov 2024). Issued in Finance Research Letters Vol. 73, 2025, art. 106508. DOI 10.1016/j.frl.2024.106508

**[central]** Triangular arbitrage on Binance spot (USDT->BTC->LTC->USDT) is NOT exploitable by a retail trader net of fees: over one full week of tick data, 4,879 gross opportunities collapsed to just 18 profitable ones at the regular fee tier, and total net profit for the entire week was only $12.43-$30.42 depending on execution assumption. This rules out the strategy family for a solo Python bot on economic grounds, not just latency grounds.

> For regular traders, a small subset of 18 opportunities remains profitable after accounting for transaction costs. For example, traders could realize a total of 2 percent if these opportunities are taken immediately. In a best-case scenario, this sum of relative returns increases to 3 percent. The depth of the order book further restricts the quantities that could be traded. Since the average tradable amount is 4,070.86 U.S. Dollar for the 18 opportunities, this results in marginal arbitrage profits between 12.43 U.S. Dollar and 17.73 U.S. Dollar for the entire week.

**[central]** The strategy has a hard latency budget of ~146 milliseconds end-to-end for the full three-leg execution before expected value turns negative from slippage; the authors needed a Tokyo-colocated server to get 4ms quote latency, versus 80ms from Europe. A retail ccxt/REST bot cannot meet this, so the barrier is infrastructure a solo trader cannot obtain.

> Consequently, a regular trader has to execute trades on average within a maximum of 146 milliseconds, based on the data. In order to reduce the risk of slippage, the strategy must be implemented that, if the arbitrage opportunity is recognized, trading should take place within these 146 milliseconds in order to avoid making a loss on average. This result emphasizes the location advantage in high-frequency trading.

**[central]** Lowering fees does not rescue the strategy: 96.93% of the 4,879 opportunities were unprofitable even at Binance's cheapest VIP 9 tier (0.054% total across all three legs, i.e. BNB-discounted taker fees), and the best-case VIP 9 net profit of $170.76 for the week requires $4bn/month trading volume to qualify for. This is direct evidence that a fee-tier or rebate strategy cannot convert a sub-threshold gross edge into a real one.

> 96.93 percent of the triangular arbitrage opportunities are not even profitable for VIP 9 traders... However, if we relate this finding to the condition that those market participants need at least a trading turnover of 4 billion U.S. dollars per month, the possible profit is negligible. In summary, our results indicate that transaction costs and order book depth restrict possible profits in such a way that market participants could not archive a risk-free return on cryptocurrency markets.

**[supporting]** The gross edge is an order of magnitude below the retail fee floor and evaporates in under a second: 88.89% of opportunities had gross returns of 0-0.025% (versus ~0.225% three-leg round-trip cost for a regular trader), and ~65% lasted one second or less, with 57.90% under 0.5 seconds. Signal magnitude, not just cost, is the binding constraint.

> The majority (4,337 observations) have a return between 0 percent and 0.025 percent. But we find three observations with a return larger than 0.5 percent. Simultaneously, approximately 65 percent of these arbitrage opportunities are very short and last one second or less, while 767 observations (15.72 percent) exhibit a relatively long duration of more than 5 seconds.

**[supporting]** Profit in this strategy is capacity-capped by top-of-book depth rather than scaling with capital: the average tradable notional across profitable opportunities was $4,070.86 and the majority of opportunities permitted only $0-500 of tradable value, with the LTC/BTC cross-rate being the binding leg in roughly half of cases. Unlike directional strategies where P&L and fees scale together, here adding capital cannot increase profit.

> we assume, that a trader only trades those quantities for which there are supply/demand quantities in the order book at the underlying ask and bid prices. Under this assumption, the lowest quantity offered/demanded is relevant in each case, as this is the limiting factor.

### Source 3 — quality: primary | published: 2024 (International Review of Financial Analysis, Vol. 92, article 103106; DOI 10.1016/j.irfa.2024.103106)

**[central]** Cross-sectional size and momentum factors in crypto survive massive researcher-degrees-of-freedom testing: they remain robust across the 20,736 alternative research designs the authors generated, meaning these two specific factors are not artifacts of p-hacking or a single lucky specification. NOTE: this is robustness-to-specification, NOT a claim that the edge survives fees/slippage or is tradable out-of-sample net of costs.

> Notwithstanding the above, the most prominent cryptocurrency factors, such as size and momentum, remain consistently robust across numerous specifications.

**[central]** Non-standard errors (variation in results caused purely by defensible methodological choices) in cryptocurrency portfolio research are larger than those in equity markets AND larger than the standard errors themselves — implying that for most crypto 'anomalies', the choice of data source, sample filters, and portfolio-construction rules moves the measured performance more than statistical sampling noise does. A single backtest of a crypto factor therefore carries less information than its t-statistic suggests.

> The non-standard errors in cryptocurrency studies not only surpass those in the stock market but also clearly exceed standard errors—though varying considerably across coin characteristics.

**[supporting]** Restricting the coin universe to exclude or down-weight the smallest-capitalization coins measurably reduces non-standard errors, i.e. produces more specification-stable results. Corollary for a retail bot: much of the fragile, specification-dependent signal lives in micro-cap coins that are also the least tradable net of spread and slippage, so a large-cap-restricted universe is both more robust and more realistic.

> Lastly, we find that reducing the influence of the smallest coins effectively decreases the non-standard errors.

**[central]** The instability is driven by choices a practitioner would consider trivial — the authors varied ten common decisions across data sources, sample preparation, and portfolio construction over 43 sorting variables, and found large dispersion in resulting portfolio performance. This is direct evidence that a crypto cross-sectional backtest must be tested across a grid of universe/filter/weighting choices, not one fixed pipeline, before its edge is believed.

> We examine ten prevalent decisions related to data sources, sample preparation, and portfolio construction, generating 20,736 research designs for 43 sorting variables. Our findings reveal remarkable variation in portfolio performance tied to seemingly trivial choices.

**[tangential]** The paper is peer-reviewed work published in the International Review of Financial Analysis (Vol. 92, article 103106, 2024, DOI 10.1016/j.irfa.2024.103106) by Fieberg, Günther, Poddig, and Zaremba, and is explicitly framed as a data-mining / p-hacking robustness study rather than a strategy-promotion paper — its keywords include 'Data mining' and 'P-hacking'.

> Keywords: Cryptocurrency markets; Non-standard errors; Portfolio sorts; Data mining; P-hacking; Risk factors; Anomalies; Asset pricing models; Factor investing; Portfolio construction

### Source 4 — quality: primary | published: 2025-07-17 (v1; v3 revised 2025-08-03; accepted at AFT 2025)

**[supporting]** CEX-DEX arbitrage is a real but small and extremely concentrated value pool: 19 major searchers extracted $233.8M gross over 19 months (Aug 2023-Mar 2025) across 7,203,560 arbitrages (~$32 gross extracted value per arbitrage, before builder payments and hedging costs) — this is a competed-for pie, not an open opportunity.

> 233.8M USD extracted by 19 major CEX-DEX searchers from 7,203,560 identified CEX-DEX arbitrages

**[central]** The strategy is winner-take-all and concentration is INCREASING, not decreasing: three searchers captured ~73% of cumulative extracted value over the full period, rising to roughly 90% by Q1 2025 — direct evidence that a new entrant is not competing into a fragmenting market but a consolidating one.

> three leading searchers capturing 170.8M USD, representing approximately 73% of the total cumulative extracted value ... intensifying to around 90% of the extracted value by Q1 2025

**[central]** The paper explicitly names structural barriers to entry that a solo retail Python-bot trader cannot satisfy: capital requirements, low-latency infrastructure, inventory risk, and block-inclusion uncertainty, reinforced by economies of scale favoring incumbents. This rules out CEX-DEX arbitrage as a testable near-term strategy family for this user.

> capital requirements, low-latency infrastructure, inventory risk, and uncertainty of block inclusion

**[central]** Profits accrue to vertical integration with block builders, not to the arbitrage signal itself: SCP is integrated with builder beaverbuild and Wintermute with rsync, and integrated searchers transfer nearly 90% of arbitrage revenue directly to their integrated builder. Without an exclusive builder relationship, the residual economics are worse, so the edge is an access/structure edge unavailable to outsiders.

> SCP and Wintermute transfer nearly 90% of their arbitrage revenue directly to their integrated builder

**[supporting]** Net margins per trade are razor-thin — median trade PnL for the dominant integrated searchers is only a few dollars above zero, and 80% of exclusive/integrated searchers' trades net under $10 — meaning the strategy only works at industrial trade counts (millions of arbs) and any incremental cost (fees, gas, hedging slippage) wipes out the edge, mirroring the user's own fee-drag finding.

> 80% of exclusive and integrated searchers' trades net fewer than 10 USD

### Source 5 — quality: primary | published: 2025 (© The Author(s), 2025, Cambridge University Press; DOI 10.1017/S0022109024000747; study sample period Apr. 2015 – May 2022)

**[central]** A weekly-rebalanced, value-weighted long-short quintile strategy on an ML-aggregated technical signal (CTREND) across 3,000+ coins earned 3.87%/week gross (t=5.19, annualized Sharpe 1.94) over Apr 2015–May 2022, and SURVIVED realistic costs: net 2.90%/week at 30bps long / 40bps short, still 2.35%/week at 50/60bps. The breakeven transaction cost is 1.41% per trade — roughly 14x Binance's 0.1% taker fee — despite 68% weekly portfolio turnover.

> the portfolio turnover is substantial, reaching 68% per week, indicating that an investor must replace a considerable fraction weekly. However, the gross portfolio returns exceed these implementation costs, and the net payoffs on the long-short CTREND strategy range between 2.90% (t-stat = 3.89) and 2.35% (t-stat = 3.16), depending on the assumed transaction cost rate. Furthermore, the BETC rate, at which the mean net return is erased to 0, equals 1.41%. Even if the fee was as high as 0.88%, the strategy's profit would remain significant at the 5% level.

**[central]** The edge is NOT a micro-cap illiquidity artifact: restricted to the 100 largest coins each week it still earns 3.40%/week gross and 2.45%–1.90%/week net of costs, all statistically significant; restricted to the 10% largest coins the long-short return is 2.51%/week with CCAPM and LTW alphas above 2%. This makes it tradeable on a major-exchange coin universe rather than requiring obscure listings.

> A CTREND factor based on the largest 100 cryptocurrencies earns between 2.45% and 1.90% per week--all statistically significant. Although the CTREND strategy requires intense trading and frequent portfolio rebalancing, it remains resilient despite high transaction costs.

**[central]** The mechanism is CROSS-SECTIONAL ranking of an aggregate of 28 technical indicators (RSI, stochastics, CCI, 3/5/10/20/50/100/200-day SMAs scaled by price, MACD, volume SMAs and volume MACD, volatility measures), combined via univariate Fama-MacBeth forecasts selected by an elastic net, estimated on a rolling 52-week window and rebalanced weekly. No single indicator produces the effect — which is consistent with single-indicator time-series MA/RSI rules on one coin failing.

> it does not derive from a single technical indicator but rather aggregates information across multiple technical signals. […] The model parameters are estimated using a fixed rolling window of 52 weeks, and these parameters are then used to predict returns for the following week.

**[central]** Plain cross-sectional momentum (CMOM, the Liu-Tsyvinski-Wu momentum factor) is materially weaker and fragile: across 55,296 alternative research designs its median annualized Sharpe is only 0.83, it is statistically significant in just 49% of designs, its maximum Sharpe is 2.30 and its minimum is -4.47, and CTREND renders the momentum effect insignificant in spanning tests. CTREND by contrast is significantly positive in 79% of designs.

> The maximum Sharpe ratio of the CMOM factor is 2.30, and the minimum is -4.47. The median Sharpe ratio of CMOM is only 0.83, thus considerably lower than that of CTREND. […] using the Lo (2002) Sharpe ratio test, the CTREND factor achieves a significant positive Sharpe ratio (5% level) in 79% of all combinations

**[supporting]** Fragility flags a replicator must respect: (a) the sample ends May 2022, and profitability already halved across subperiods (4.47%/week first half vs 3.26%/week second half); (b) the headline Sharpe of 1.94 sits at the upper edge of the design distribution whose median is 1.34, and the extreme Sharpes up to 10.92 come specifically from equal-weighting plus removing the $1m market-cap filter (i.e. tiny illiquid coins); (c) the signal is short-lived — moving from weekly to 2-week rebalancing cuts weekly returns by 1.5 percentage points to 2.34%, and significance dies beyond a 4-week holding period; (d) adding a 1-trading-day implementation lag reduces profitability.

> Even with 2-week rebalancing, the average weekly returns drop by 1.5 percentage points to reach 2.34%. The mean returns remain significant at the 5% level as long as the holding periods do not exceed 4 weeks. […] the combination of equal-weighting and turning off the market capitalization filter of 1 million USD yields extreme Sharpe ratios as high as 10.92.

### Source 6 — quality: primary | published: 2024-03-02 (PDF version date; SSRN working paper no. 4675565, first posted December 2023). Sample period: 28 Dec 2013 - 28 Aug 2023 for the main tests; Binance futures robustness test runs 12 Feb 2020 - 17 Nov 2023.

**[central]** Long-only TIME-SERIES momentum on the crypto market portfolio survives realistic transaction costs and beats buy-and-hold. Buying the market only when the trailing 28-day return sits in the top third of its own history, holding 5 days, produced an annualized Sharpe of 1.51 vs 0.85 for the market, net of 15bps per trade, while being invested only 48% of the time. Nearly all lookback/holding pairs tested (1-56 days) beat the market after costs, i.e. the result is not a single knife-edge parameter. Directly testable in a walk-forward harness on daily/4h BTC or a market-cap index, long-only, which matches the user's current setup.

> Remarkably, all long-only portfolios exhibit superior performance compared to the market portfolio in terms of the Sharpe ratio and the cumulative return. Even after accounting for the transaction costs, all long-only portfolios, except for the (7, 7) portfolio, outperform the market. The superior performance mainly results from the reduced risk as evidenced by the low standard deviations and MDDs compared to those of the market. The (28, 5) portfolio yields the highest Sharpe ratio of 1.51 and a cumulative return of 36,686%, which are significantly higher than those of the market, 0.85 and 2,696%. It holds a position for 48% of the sample period.

**[central]** The SHORT side of crypto momentum destroys value and should not be built. Short-only time-series momentum portfolios lost money at 20 of 21 tested parameter pairs even with ZERO transaction costs, and most cross-sectional short-only legs were fully liquidated during the sample. The authors conclude a market-neutral long/short momentum strategy is not achievable in crypto. This argues against the user adding shorts or perpetual-futures leverage to a momentum strategy, despite shorts being 'on the table'.

> Contrary to the long-only portfolios, the short-only portfolios yield unfavorable outcomes. All the portfolios but the (21, 7) portfolio make losses at the end of the sample period even without transaction costs. It appears that time-series momentum is almost non-existent when the market is bearish. Consequently, the long-short portfolios underperform their long-only counterparts. Adding short positions only erodes the mean return without reducing the risk. [...] A momentum-based long-short strategy that can generate steady, market-neutral profits appears unattainable.

**[central]** CROSS-SECTIONAL momentum across a coin universe has weak evidence, and the standard t-test of mean returns systematically overstates it. Of 21 pre-selected (already cherry-picked as best-in-regression) lookback/holding pairs, 5 were fully liquidated and only 6 beat the market. Ten portfolios had mean-return t-stats above 2.0 but only three had mean LOG-return t-stats above 2.0, and six portfolios with positive mean returns were liquidated or actually lost money. Falsifiable methodological rule for the user's harness: with fat-tailed crypto returns, evaluate compounded/log return, never mean simple return.

> Among 21 cross-sectional momentum portfolios of selected look-back and holding periods, five are liquidated during the sample period and only six outperform the market. [...] Ten portfolios yield a positive mean return with a t-statistic greater than 2.0, but only three of them have a mean log return with a t-statistic greater than 2.0. Moreover, six portfolios with a positive mean return are either liquidated or earn a negative profit. These results demonstrate the inadequacy of the mean return as a long-term profitability indicator.

**[central]** When the universe is restricted to what a retail trader can actually trade and short (coins listed on Binance perpetual futures, Feb 2020 - Nov 2023), cross-sectional momentum largely decays: profits are concentrated before 2022 and post-2022 performance is mediocre, and the strategy that was best on the full CoinMarketCap universe, (14, 7), falls to a Sharpe of 0.83, roughly matching the market. The authors explicitly label this an indication that their own and other crypto momentum findings may be fragile. This is direct evidence the cross-sectional momentum edge is at least partly competed away in the modern (post-2021) regime.

> Most long-short portfolios earn profits and six of them outperform the market. [...] Nevertheless, the cumulative returns in Figure 11 reveal that most profits are accrued prior to 2022, and the performance thereafter is mediocre. This result aligns with the previous observation that a cross-sectional momentum portfolio formed of the top 5% does not perform well since 2021. The previous best strategy, (14, 7), performs comparably to the market with a Sharpe ratio of 0.83, whereas the (1, 7) strategy with the lowest MDD now has the highest MDD of 78.7%. This inconsistency reveals the potential unreliability and fragility of the findings in this paper, and perhaps in many other papers on cryptocurrency.

**[supporting]** An empirically calibrated all-in retail cost assumption for Binance is 15bps per trade (fee + half-spread/tick + slippage), decomposed as: 10bps spot fee / 4.5bps futures fee for non-VIP users, 3.26bps average relative tick size in futures, and 1.53bps average measured slippage derived from 15,661,698 actual Binance futures market orders. A long/short portfolio therefore pays up to 0.6% per rebalance. This gives the user a defensible, source-backed cost model to plug into the harness instead of guessing, and confirms round-trip costs of ~0.2-0.3% for spot are realistic, not conservative.

> We assume a transaction cost of 15 basis points (bps) for every trade. At the time of writing this article, Binance, the leading cryptocurrency exchange, charges a fee of 10 bps to regular users in the spot market and 4.5 bps in the futures market, and the average tick size relative to the price is 3.26 bps in the futures market. From 15,661,698 records of actual market orders in the Binance futures market during the period from June 24, 2023 to August 20, 2023, we find that the minimum, maximum, and average slippage per coin are respectively 0.01, 11.81, and 1.53 bps.

### Source 7 — quality: primary | published: 2026 — International Review of Financial Analysis, Vol. 113 (2026), art. 105137. NOTE: the source title supplied listed 'Finance Research Letters', but the PII prefix S1057-5219 and the RePEc record both confirm the journal is International Review of Financial Analysis. Authors: Aleksander Mercik, Adam Zaremba, Ender Demir.

**[central]** In the crypto cross-section, the 'factor zoo' collapses almost entirely: from a set of 36 return-predictive crypto factors, only two to three factors are needed to drive all significant portfolio alphas to insignificance. Testable implication: most published crypto factors (including many momentum/reversal variants) are redundant, so a solo trader chasing a long list of cross-sectional signals is likely re-discovering the same 2-3 underlying exposures.

> Using a comprehensive set of 36 return-predictive factors, we find that just two to three factors can eliminate all significant portfolio alphas.

**[central]** The factors that survive selection are liquidity-related, and this is robust rather than a specification artifact — it holds across weighting schemes, model specifications, and sub-periods. Implication for a retail bot: the priced dimension of the crypto cross-section is compensation for illiquidity/trading friction, i.e. precisely the return component a taker-fee, market-order retail trader pays away rather than earns.

> Liquidity-related variables dominate the selection process, appearing consistently across weighting schemes, model specifications, and periods.

**[central]** The specific dominant factors are turnover volatility, bid-ask spreads, and the blockchain-native new-address-to-price ratio. Notably, no price-momentum or trend factor appears in the abstract's list of most influential factors — the survivors are microstructure/liquidity proxies and an on-chain fundamental ratio. This is direct evidence against cross-sectional price momentum being the primary independent driver of the crypto cross-section, and it points to on-chain data (address growth) and spread/turnover data as the higher-value inputs to collect.

> The most influential factors include turnover volatility, bid–ask spreads, and blockchain-native metrics such as the new-address-to-price ratio.

**[supporting]** The evidence comes from applying Swade et al. (2024)'s alpha-based iterative factor-selection method (an equity-market methodology, GRS-test based) to crypto for the first time — meaning the result is an asset-pricing spanning finding about which factors explain returns, not a demonstration that any of these factors is tradable net of realistic costs by a retail participant. Checkable: the abstract states no net-of-fee Sharpe, turnover, or capacity figure.

> we are the first to apply the alpha-based, iterative factor selection methodology of Swade et al. (2024), initially developed for equities, to the cryptocurrency market

### Source 8 — quality: primary | published: 2023-12-26 (SSRN posting date; this working-paper version covers data through 2023-08-28)

**[central]** Long-only TIME-SERIES momentum on the crypto market portfolio survives realistic transaction costs and beats buy-and-hold: the best (28-day lookback, 5-day hold) variant earned an annualized Sharpe of 1.51 vs 0.85 for the market, while holding a position only 48% of the time — the outperformance came from avoiding drawdowns, not from higher returns. Every long-only lookback/hold pair tested except (7,7) beat the market NET of 15bps-per-trade costs.

> Remarkably, all long-only portfolios exhibit superior performance compared to the market portfolio in terms of the Sharpe ratio and the cumulative return. Even after accounting for the transaction costs, all long-only portfolios, except for the (7, 7) portfolio, outperform the market. The superior performance mainly results from the reduced risk as evidenced by the low standard deviations and MDDs compared to those of the market. The (28, 5) portfolio yields the highest Sharpe ratio of 1.51 and a cumulative return of 36,686%, which are significantly higher than those of the market, 0.85 and 2,696%. It holds a position for 48% of the sample period.

**[central]** CROSS-SECTIONAL momentum across a coin universe is weak and largely illusory once assessed properly: of 21 long-short portfolios built from regression-selected optimal lookback/hold pairs, 5 were fully LIQUIDATED during the sample and only 6 beat the market. Critically, statistical significance of the MEAN return does not imply profitability — 10 portfolios had mean-return t-stats above 2.0 but only 3 had mean LOG-return t-stats above 2.0, and 6 portfolios with positive mean returns either got liquidated or lost money outright.

> In contrast to time-series momentum, evidence of cross-sectional momentum is weak. Among 21 cross-sectional momentum portfolios of selected look-back and holding periods, five are liquidated during the sample period and only six outperform the market. ... Ten portfolios yield a positive mean return with a t-statistic greater than 2.0, but only three of them have a mean log return with a t-statistic greater than 2.0. Moreover, six portfolios with a positive mean return are either liquidated or earn a negative profit. These results demonstrate the inadequacy of the mean return as a long-term profitability indicator.

**[central]** The SHORT leg is where crypto momentum strategies die — short-only momentum portfolios lost money even with ZERO transaction costs (all but one of the time-series variants ended the sample at a loss), so adding shorts to build a market-neutral momentum book strictly degrades the strategy. The authors conclude a stable market-neutral crypto momentum strategy is unattainable.

> Contrary to the long-only portfolios, the short-only portfolios yield unfavorable outcomes. All the portfolios but the (21, 7) portfolio make losses at the end of the sample period even without transaction costs. It appears that time-series momentum is almost non-existent when the market is bearish. Consequently, the long-short portfolios underperform their long-only counterparts. Adding short positions only erodes the mean return without reducing the risk.

**[supporting]** The paper's cost calibration is a directly reusable benchmark for a retail Binance bot: 15bps per trade, built bottom-up from actual Binance fees (10bps spot / 4.5bps futures for regular non-VIP users), a 3.26bps average relative tick size, and measured slippage of 1.53bps average (max 11.81bps) from 15.7 million real futures market orders. The authors describe 15bps as a LOWER bound, since their measured order sizes averaged only $56 (0.02% of daily volume).

> We assume a transaction cost of 15 basis points (bps) for every trade. At the time of writing this article, Binance, the leading cryptocurrency exchange, charges a fee of 10 bps to regular users in the spot market and 4.5 bps in the futures market, and the average tick size relative to the price is 3.26 bps in the futures market. From 15,661,698 records of actual market orders in the Binance futures market during the period from June 24, 2023 to August 20, 2023, we find that the minimum, maximum, and average slippage per coin are respectively 0.01, 11.81, and 1.53 bps. The order sizes are very small compared to the daily trading volume: 56 USD or 0.02% of the daily trading volume on average.

**[central]** The authors explicitly disclaim their own headline numbers as an overfitted upper bound: the lookback/holding pairs were chosen by scanning all combinations from 1 to 56 days on the SAME full sample (Dec 2013 - Aug 2023) used to report performance, with no out-of-sample holdout. They label the results a 'best-case scenario' with data-snooping bias, and note the max achievable Sharpe (~1.5) is below what equity ML strategies achieve (>2.0).

> Furthermore, it is important to note that we introduce a data-snooping bias by examining various pairs of look-back and holding periods, and the findings in this paper should be considered a best-case scenario.

### Source 9 — quality: primary | published: 2024-10-19 (submitted); v2 revised 2025-08-01

**[central]** Bitcoin carries a large, positive variance risk premium (VRP) of 0.14 in annualized variance units over July 2017–Dec 2022 Deribit options, roughly an order of magnitude larger than the S&P 500's (~2%). A positive VRP means option buyers systematically overpay for variance protection, which is the structural (risk-premium / insurance-provision) basis for a short-volatility or variance-swap-selling edge in crypto. CAVEAT: the paper measures the premium; it does NOT backtest a tradable short-vol strategy, report its Sharpe, or net it of bid-ask spreads, margin, or delta-hedging costs.

> The corresponding variance risk premium is 0.14, much higher than that of the S&P 500 Index—approximately 2%

**[central]** The premium is persistent, not episodic: option-implied variance (BVIX squared) exceeded subsequent realized variance for essentially the entire 2017–2022 sample, with only about one month of inversion during the March 2020 crash. This is the persistence condition a systematic variance seller needs — and it simultaneously identifies the tail-loss regime (a single crash month wipes out the sign), which is exactly what a walk-forward harness must be built to capture rather than average away.

> Generally, BVIXt² remains above RVt, except for about a month in 2020 when RV approached 500%.

**[supporting]** The VRP is counter-intuitively LARGER in the low-volatility regime (0.17) than in the high-volatility regime (0.12), where risk-neutral vs physical monthly annualized variances are 0.46 vs 0.29 (LV) and 0.86 vs 0.74 (HV). This falsifies the naive 'sell vol when IV is high' rule: the compensation per unit of risk is best in calm markets, and selling into high-vol regimes gives you the worst premium alongside the largest tail exposure. A regime-conditional short-vol filter is therefore testable and should be signed opposite to intuition.

> Surprisingly, the low volatility cluster is characterized by a higher VRP of 0.17 compared to the high volatility cluster of 0.12, suggesting a potential disconnect between variance and VRP.

**[supporting]** Deribit option trading fees are 0.03% of the underlying notional (0.0003 BTC per contract), capped at 12.5% of the option's value. This is a materially different cost structure from the user's spot problem: fees scale with UNDERLYING notional rather than with the option premium collected, so cheap far-OTM options can hit the 12.5% cap and fee drag on a short-premium book is driven by contracts traded and premium collected per contract, not by P&L magnitude. Any short-vol backtest must model fees per-contract-on-notional, not as a percentage of trade value.

> The trading fees on Deribit are 0.03% of the underlying or 0.0003 Bitcoin per option contract, capped at 12.5% of the contract's value.

**[supporting]** Bitcoin's equity-like premium is earned disproportionately in the RIGHT tail: monthly returns of +20% to +60% contribute 38.66% of the Bitcoin premium while returns of -60% to -20% contribute 28.53% — unlike the S&P 500, whose premium comes mostly from mildly negative returns. Bitcoin's own annualized Sharpe is ~0.8, about twice the S&P 500's. Implication: strategies that truncate crypto upside (covered calls, short calls, call-side strangles, and by extension any long-only timing rule that is out of the market during melt-ups) forfeit the largest single source of the asset's return — a direct structural explanation for why the user's MA/RSI timing rules underperform buy-and-hold even at zero fees.

> We find that negative monthly returns between -60% and -20% and positive returns ranging from 20% to 60% contribute 28.53% and 38.66%, respectively of the BP.

### Source 10 — quality: primary | published: 2019 (Annals of Operations Research, DOI 10.1007/s10479-019-03357-1, © The Author(s) 2019, open access; appeared in print as vol. 297, pp. 191-220, 2021)

**[central]** Technical trading rules that were the single best in-sample performer produced NEGATIVE out-of-sample returns and negative Sharpe/Sortino ratios for BOTH Bitcoin price series (CoinDesk best rule: -0.10% annualized, Sharpe -0.0502; Bitstamp best rule: -0.91% annualized, Sharpe -0.0641) over the pure out-of-sample window of January-June 2018, while the three altcoins (Litecoin +7.75%/Sharpe 1.36, Ripple +5.46%/Sharpe 0.74, Ethereum +6.31%/Sharpe 1.19) stayed positive. The authors attribute Bitcoin's failure to it being the most liquid and most-watched coin, i.e. the most efficient.

> In the out-of-sample periods, we find negative annualized returns, Sharpe ratios and Sortino ratios for both Bitcoin prices. However, the three other cryptocurrencies show positive out-of-sample returns, as well as positive Sharpe and Sortino ratios. This indicates that Bitcoin may not be profitable to trade using technical analysis in an out-of-sample setting... Bitcoin may be the least profitable cryptocurrency in the out-of-sample setting Bitcoin was the first cryptocurrency created as well as the most liquid and therefore attracts more attention from investors. The relatively large number of investors investors that are attracted to Bitcoin means that profitable trading strategies may be more difficult to find as the market becomes more efficient.

**[central]** Across 14,919 rules, the average breakeven (round-trip-equivalent) transaction cost that would zero out profits ranges from only 7.88 bps to 147.56 bps, with Bitcoin's best families topping out at 66.41 bps (CoinDesk) and 57.51 bps (Bitstamp), against a reference real-world Bitcoin transaction cost of ~50 bps. Critically, in Table 6 NO rule-family/coin cell had more than 49.52% of its rules clearing the 50 bps hurdle (CoinDesk 0.00-36.06%, Bitstamp 0.95-28.15%, Litecoin 0.21-25.81%, Ripple 3.49-34.04%, Ethereum 0.11-49.52%) - so the MAJORITY of tested rules are unprofitable at realistic costs, despite the paper's own optimistic framing.

> The breakeven transaction costs range 7.88 basis points for the support-resistance rule in Litecoin to 147.56 basis points for the filter rule in Ethereum. If we focus on CoinDesk and Bitstamp, the breakeven transaction costs are as high as 66.41 and 57.51 basis points respectively. Lintilhac and Tourin (2017) report that the transaction costs for Bitcoin is around 50 basis points and therefore also in Table 6 we report the percentage of technical trading rules that offer breakeven transaction costs greater than 50 basis points.

**[central]** Only a small minority of the 14,919 technical trading rules beat simple buy-and-hold on raw annualized return: 6.12% for CoinDesk Bitcoin, 4.96% for Bitstamp Bitcoin, 11.49% for Litecoin, 15.69% for Ripple, 9.01% for Ethereum (Table 7). The paper's positive case for technical trading rests entirely on risk-adjusted/drawdown metrics (e.g. 32.83% of rules beat B&H on annualized Sortino for CoinDesk, 51.26% for Litecoin), not on outperforming buy-and-hold in return terms.

> For each cryptocurrency, we see that only a small proportion of rules generate annualized returns greater than the buy-and-hold strategy. However once we examine the risk-adjusted metrics, we find that substantially more technical trading rules offer returns greater than the buy-and-hold strategy, especially for the annualized Sortino and Calmar ratios, which both capture downside risk. This indicates that employing technical trading rules avoids the large, severe and lengthy drawdowns associated with cryptocurrencies

**[supporting]** Data-snooping corrections materially cut the surviving rule count: before correction 27.96-58.64% of rules were significant at 5%, but after Bonferroni/Holm/Benjamini-Hochberg/Benjamini-Yekutieli adjustment (applied on top of 1,000-replication stationary-bootstrap p-values following Sullivan et al. 1999) only 20.35% (Ripple) to 50.41% (CoinDesk, BH) remained. Bonferroni/Holm/BY figures cluster at 20-34%, so roughly half to two-thirds of nominally significant rules were data-snooping artifacts.

> Finally, we implement four popular adjustments of multiple hypothesis testing to safeguard against data-snooping bias and find that a large proportion of rules are still statistically significant, ranging from 20.35% of total rules to a high of 50.41%.

**[supporting]** The evidence base is thin in ways that limit transfer to 2026: only DAILY data is used (no intraday), the in-sample period runs from coin inception to 31 December 2017 - i.e. almost entirely the historic crypto bull run, with all five series showing positive skew - and the 'pure' out-of-sample test is a single best-performing rule per coin over just six months (H1 2018). Positions are long/short/flat with no risk-free interest earned when flat.

> we study CoinDesk's Bitcoin price from 18th July 2010, Bitstamp from 1st December 2012, Litecoin from 28th April 2013, 28th April 2013, Ripple from 4th August 2013 and Ethereum from 7th August 2015. All prices end on 31st December 2017... The first draft of this paper employed data up to 31st December 2017, but since then, there has been a huge drop in the value of cryptocurrencies, with the price hovering around $6500 in early July 2018. therefore we can offer a pure out-of-sample analysis

### Source 11 — quality: blog | published: 2023-01-24

**[central]** A persistent variance risk premium exists in BTC options: 30-day implied volatility exceeded 30-day realized volatility roughly 70% of the time from April 2019 onward, which is the structural mechanism behind short-vol/option-selling strategies and is directly checkable against public Deribit IV and BTC realized-vol series.

> Since April 2019, the implied volatility for 30-day BTC options has been greater than 30-day realized volatility for nearly 70% of the time.

**[central]** The backtests supporting these vol-selling results model P&L on the option mark price with no transaction costs, fees, slippage, or bid-ask spread quantified anywhere — so the reported profitability is a gross, pre-cost figure and cannot be treated as evidence of net-of-cost edge.

> The mark option price will be used to calculate P&L. This is not entirely realistic in practice.

**[supporting]** The variance risk premium is regime-dependent rather than constant: it averages about +15 vol points when the term structure is in contango, but turns negative and noisier in backwardation — implying a term-structure state filter is required and that naive always-short-vol will bleed during backwardation regimes.

> When the term structure is in Contango, the VRP has a mean of about +15pts

**[supporting]** Delta-hedged short straddles on BTC, hedged only after a 2.5% move in the index, were profitable across the 2019-04 to 2022-12 sample including market crashes, with the best risk-adjusted portfolio allocating roughly 90% to the weekly-straddle strategy and 10% to spot BTC (monthly straddles saturated at ~30% allocation).

> the model will hedge only after the index price moves past a certain threshold...we'll set our threshold to hedging the delta after every 2.5% change in BTC price.

**[supporting]** The event-driven long-volatility sub-strategy (buying vol into FOMC/CPI prints) is not statistically supportable: fewer than 15 trades per backtest, which the authors themselves say is too small to conclude the effect persists — a concrete example of a crypto-options edge claim that should be ruled out cheaply rather than tested.

> It should be noted that there have been less than 15 trades for each individual backtest. Therefore, the small sample size makes it too early to conclude whether this strategy will continue to work in practice.

### Source 12 — quality: primary | published: 2026-02 (arXiv v1; HTML build dated 2026-01-31; data through 2025-10-12)

**[central]** The paper's reported crypto microstructure profits are explicitly an idealized upper bound: latency, queue position and network jitter are not modeled, so the results do not demonstrate an edge achievable by a non-colocated trader. This is the single most important caveat for a solo retail Python bot.

> Latency is not explicitly modeled; results should be interpreted as an upper bound in the fastest regime.

**[central]** The predictive target is the 3-second-ahead mid-price log return, with typical holding periods of one to two seconds on 1-second Binance Futures order-book data — an HFT-regime strategy, not something a Python/ccxt REST bot on 1m-4h bars can execute.

> Our prediction target is the logarithmic return of the mid price over a short horizon, specifically: r_{t→t+3s} = log(mid_{t+3s}/mid_t)

**[central]** The passive market-making (maker) variant of the same signal produces no statistically significant returns on any of the five assets tested — a clean negative finding against naive retail market-making on crypto perps, and BTC maker returns of 2.93%/yr with IR 5.47 are not significant.

> For maker strategies, all p-values exceed 0.05, so the null hypothesis of zero mean returns cannot be rejected for any asset in the maker backtest.

**[supporting]** Even in the latency-free upper-bound regime, the aggressive (taker) strategy is significant on only 3 of 5 assets, and annualized returns are modest and wildly dispersed (BTC 13%, ROSE 7.00%, ETC 5.78%, ENJ 4.06%, LTC 0.07%); the paper never states the taker fee rate used nor discloses turnover, so the net-of-cost figure is not verifiable.

> Optional proportional costs can be introduced to reflect taker fees; we report gross and fee adjusted returns using taker fee.

**[supporting]** The infrastructure requirement is concrete and large: 1-second-frequency Binance Futures perpetual order book AND trade data spanning Jan 2022 - Oct 2025, from which order flow imbalance, bid-ask spread and VWAP-to-mid deviation are the dominant features. Signal construction requires book depth, not OHLCV bars.

> The data is sourced from Binance Futures perpetual contract order books and trades on 1-second frequency starting from January 1st, 2022 up to October 12th, 2025.

### Source 13 — quality: primary | published: 2026-01-20

**[central]** CROSS-VENUE FUNDING SPREAD ARBITRAGE (not the classic long-spot/short-perp carry trade): in delta-neutral simulations of the 20 largest funding-rate spread opportunities — long the perp on the lowest-rate exchange, short on the highest-rate exchange, $10,000 per side — only 8 of 20 were net profitable after fees and slippage, average net P&L was $22 per portfolio (0.11% on $20k of gross exposure), and average Sharpe was -7.40 with even the best portfolio at -2.73. Note this measures the CEX-vs-DEX funding DIFFERENTIAL, a different mechanism from single-venue funding carry.

> Under our conservative forced exit protocol (spread < 0 bps), eight portfolios generate positive net returns while twelve incur losses (Table 9). The best performer AIA yields $1,433 profit over 2 days. Average net P&L across all 20 portfolios is $22. ... Average Sharpe ratio is -7.40; even the best performing portfolio (AIA) achieves a Sharpe of just -2.73.

**[central]** Explicit, directly reusable cost model and breakeven arithmetic for any funding-rate strategy: 0.05% taker fee (conservative; observed range 0.01-0.05%), plus slippage of 0.1% for liquid pairs (OI rank < 50) and 0.5% for illiquid pairs, plus negligible DEX gas (<$0.01 on Solana/Arbitrum/Optimism). That is $60 round-trip per $10k/side in liquid markets and $220 in illiquid ones — meaning a 20 bps (8h-equivalent) spread must persist 3.7 days just to break even.

> Consider that a 20 bps spread with this trade size accrues just $0.042 per minute ($10,000 × 20 bps/10000/480), requiring 5263 min (3.7 days) to generate enough funding to cover transaction costs.

**[central]** Funding-spread positions cannot be held passively: 19 of 20 top opportunities (95%) exhibited reversal patterns where the two exchanges swapped relative funding positions, and 12 of 20 hit a forced exit when the spread turned negative. The strategy therefore requires real-time (sub-hourly) spread monitoring and automated unwinding, not a set-and-forget harness — and reported profitability is explicitly described as highly sensitive to the exit threshold chosen (-0, -5, or -10 bps).

> When we classify convergence patterns, 95% of portfolios (19 of 20) exhibit reversal patterns where exchanges swap funding rate positions. Forced exits occurred for 12 of 20 portfolios when spreads turned negative.

**[supporting]** OVERFITTING / SURVIVORSHIP FLAG: the profitability evidence rests on only 8 days of data (8-15 November 2025), an ex-post selection of the top 20 spread opportunities, and profits concentrated in illiquid microcap symbols (AIA, PARTI, KAVA, MERL, 0G, GODS, LAYER) — precisely the names carrying the paper's own 0.5% slippage assumption. 84% of significant spreads occur at the CEX-DEX boundary and essentially none between DEXs, so the opportunity set is not accessible without multi-venue (including on-chain) execution.

> Most of these opportunities (84%) involve CEX-DEX pairings (average 52.4 bps, persisting 91% of observation time); roughly 16% involve CEX-CEX pairs (47.2 bps, 92% duration), while essentially no DEX-DEX opportunities appear

**[central]** CARRY-LEVEL EVIDENCE (most relevant to the classic funding-carry trade): during the sample window the MEAN funding rate was near zero and slightly NEGATIVE on both venue types — CEX -1.91 bps and DEX -1.74 bps per 8h, with interquartile ranges of only 1.20 and 1.60 bps. In other words there was no persistent positive funding premium to harvest in the cross-section average; the exploitable dispersion showed up in cross-platform spreads, not in the level of funding. (Caveat: 8-day window only, during a November 2025 drawdown when negative funding is expected.)

> CEX observations (27.9M, representing 78% of the sample) and DEX observations (7.8M, 22%) exhibit similar mean rates (CEX: −1.91 bps, DEX: −1.74 bps, difference 0.18 bps, p < 0.001), though the economic magnitude of this difference appears negligible. ... Market frictions appear to manifest in cross-platform spreads, not in average levels.

### Source 14 — quality: primary | published: Journal of Finance, Vol. 77, No. 2 (April 2022), pp. 1133-1177. The Wiley page at the task URL returned HTTP 402 (paywalled); all quotes above were extracted from the openly available and fully verifiable earlier version, NBER Working Paper No. 25882, May 2019 (https://www.nber.org/system/files/working_papers/w25882/w25882.pdf), sample period 2014-2018. The published JF version has a longer sample and reports ten (not nine) successful characteristics, so specific figures may differ.

**[central]** In a 2014-2018 panel of 1,707 coins (CoinMarketCap, >$1M market cap), only 9 of 25 equity-style price/volume characteristics produced statistically significant weekly long-short returns, and all 9 are spanned by a three-factor model (crypto market, size, momentum). The surviving momentum signals are SHORT-horizon only: 1-, 2-, 3-, and 4-week formation with WEEKLY rebalancing, earning 2.7%, 3.3%, 4.1%, and 2.5% raw weekly excess returns respectively. NOTE: figures are from the May 2019 NBER WP; the published JF 2022 version reports TEN successful characteristics on a longer sample, so do not cite these numbers as the JF numbers.

> We find that the returns of the zero-investment strategies are statistically significant for 9 out of the 25 factors. Specifically, these are: market capitalization, price, and maximum price; one-, two-, three-, and four-week momentum; dollar volume; and standard deviation of dollar volume. ... (2.7 percent for one-week momentum, 3.3 percent for two-week momentum, 4.1 percent for three-week momentum, and 2.5 percent for four-week momentum strategies)

**[central]** Crypto cross-sectional momentum is concentrated in the LARGER half of the sampled universe (4.2% weekly, significant) and is absent in the smaller half (0.6% weekly, insignificant) - the opposite of equity momentum. CRITICAL SCOPE CAVEAT: 'large' here means above the sample median market cap of $8.17M, or the >$10M cutoff used in Panel E - i.e. microcaps by 2026 standards, two-to-three orders of magnitude below Binance mega-cap perps. The paper does NOT show that momentum works among today's top-50 liquid coins, and 4.2%/week (>800%/yr) is a gross-of-cost, capacity-constrained number.

> We find that the long-short momentum strategy in the below median size group only generates 0.6 percent weekly returns which is not statistically significant. In contrast, the long-short momentum strategy in the above median size group generates statistically significant 4.2 percent weekly returns. This implies that the momentum strategy works better for the larger coins in the cryptocurrency market. This is in sharp contrast to the equity market where momentum strategies work better among smaller stocks

**[central]** All reported returns are GROSS of trading costs and assume shortability the authors concede does not exist - the paper performs no transaction-cost, spread, or slippage adjustment anywhere. This matters acutely because the universe is mostly untradeable: median coin market cap is $8.17M and median daily dollar volume is only $103,890, so weekly rebalancing of quintile portfolios across ~1,500 coins is not implementable at retail without spreads/impact that plausibly exceed the 2.5-4.1% weekly gross edge.

> Of course, this strategy does not take into account trading costs and the feasibility of short selling. ... The mean (median) market capitalization in the sample is 356.71 (8.17) million dollars. The mean (median) daily dollar volume in our sample is 18,305.83 (103.89) thousand dollars.

**[supporting]** The retail-implementable variant of the momentum trade - long the winner quintile, short Bitcoin instead of shorting illiquid alts - DEGRADES the result: one-, two-, and four-week momentum lose statistical significance under the short-BTC substitution. Three-week momentum is notably NOT listed among those that lose significance, suggesting the 3-week/weekly-rebalance config is the one plausibly testable as long-alts/short-BTC-perp. (Table 12 column alignment was corrupted in text extraction, so the 3-week row could not be independently verified beyond the authors' prose.)

> The exceptions are the momentum factors for which the lowest quintiles behave differently from Bitcoin. As a result, the mean returns of the one-, two-, and four-week momentum strategies are no longer statistically significant, and the returns to the Bitcoin zero-investment strategies are somewhat different.

**[supporting]** Crypto momentum's significance is weighting-dependent and therefore fragile: in Fama-MacBeth regressions (which weight observations roughly equally) the momentum factors are NOT statistically significant, unlike in the value-weighted portfolio sorts - the authors themselves attribute the discrepancy to value- vs equal-weighting. Combined with a single in-sample 2014-2018 window and no out-of-sample or walk-forward validation reported, the momentum result should be treated as a hypothesis to test, not an established net-of-cost edge. (Size-related factors, by contrast, were individually significant in Fama-MacBeth.)

> Panel D shows that the momentum factors are not statistically significant in the Fama-MacBeth regressions. This is different from what we have found in the previous section for the value-weighted portfolio strategies. A potential reason for this discrepancy is that, in essence, the Fama-MacBeth regressions consider each observation equally and thus are close to strategies formed on equally weighted portfolios.

### Source 15 — quality: primary | published: 2026-05-19 (arXiv submission date; arXiv ID 2606.00060, announced June 2026)

**[central]** On hourly BTC-USDT (~70,000 observations, 2018-2026, 27-fold walk-forward), XGBoost, LSTM and iTransformer all produced positive GROSS trading performance in selected configurations, but naive sign-based (trade-on-every-signal-flip) strategies all fail once a 10 bps transaction cost is imposed. This directly corroborates the user's own finding that fee drag dominates high-frequency signal-following on BTC — and shows it holds even for modern ML forecasters, not just MA/RSI rules.

> All three models produce positive gross trading performance in selected configurations, but naive sign-based strategies fail once transaction costs of ten basis points are imposed.

**[central]** The paper's central mechanism is a cost-aware execution filter: only take a trade when the predicted return magnitude exceeds a transaction-cost-derived threshold. This sharply reduces turnover and 'restores profitability in selected configurations'. This is a cheap, directly testable modification to an existing harness — a signal-magnitude/no-trade band gate applied on top of any existing signal — and is orthogonal to which model generates the forecast. (Note: the abstract as printed says the filter 'prevents trades only when the forecast magnitude exceeds' the threshold, which is almost certainly a typo for 'permits'; the stated effect of reducing turnover only makes sense under the 'permits' reading.)

> A cost-aware execution filter, which prevents trades only when the forecast magnitude exceeds a transaction-cost-based threshold, sharply reduces turnover and restores profitability in selected configurations.

**[supporting]** The headline result — a long-only XGBoost strategy with >65% annualised return and Sharpe >1 — is reported as the maximum over a configuration search ('the strongest'), and every positive result in the abstract is hedged with 'in selected configurations'. Combined with the authors' own admission that bootstrap tests do not establish statistical dominance, this headline number should be treated as a selection-biased upper bound, not an expected out-of-sample return. It is NOT evidence that a retail bot can earn 65%/yr on hourly BTC ML forecasts.

> The strongest long-only XGBoost strategy produces annualised returns above 65% with a Sharpe ratio above one.

**[supporting]** Model architecture and modelling choices are NOT the binding constraint: XGBoost was only 'descriptively' stronger than LSTM/iTransformer with no formal statistical dominance, EGARCH-derived volatility features gave no uniformly robust gains, technical indicators helped only in selected cases, and loss-function/model-selection effects were 'secondary and statistically fragile'. Implication for a solo retail trader: effort spent on fancier ML architectures or richer feature sets on hourly BTC returns has low expected payoff relative to effort spent on execution/turnover control.

> Additional tests show that technical indicators improve performance in selected cases, EGARCH-derived features do not provide uniformly robust gains, and XGBoost is descriptively stronger than the neural alternatives, although bootstrap evidence does not support formal statistical dominance. Loss-function and model-selection effects are secondary and statistically fragile.

**[central]** The paper's stated overall conclusion is that hourly crypto predictability is weak AND that signal-to-trade conversion (turnover/execution) is an independent, first-order obstacle — i.e. two separate failure modes must both be fixed. This reframes the user's negative scan result: a strategy that is unprofitable at zero fees has a predictability problem that no execution filter can fix, whereas one profitable gross but not net has a conversion problem the cost-threshold filter can address.

> The results show that the main obstacle in hourly cryptocurrency trading is not only weak predictability, but also the way forecasts are converted into trades.

### Source 16 — quality: primary | published: 2023-04 (BIS WP No. 1087, April 2023); revised version dated October 1, 2025; forthcoming/published in Management Science 2026

**[central]** Crypto futures carry (futures-minus-spot basis) averaged roughly 7% p.a. across exchanges from April 2019 to July 2024 — about 8% on OKEx and 6.4% on CME for 1-month BTC, with spikes above 40% p.a. — roughly 10x the carry of the S&P 500 and >12x that of US Treasuries. This is the gross, pre-cost size of the cash-and-carry edge in fixed-expiry crypto futures.

> From April 2019 to July 2024, the average annualized carry across exchanges was approximately 7% p.a. In theory, a cash-and-carry arbitrage trader could earn this return by buying the cryptocurrency in the spot market and simultaneously selling a futures contract. By holding the spot position until the futures contract expires, the trader locks in the price difference and earns a return that is (in the absence of frictions) fully hedged against movements in the underlying asset and thus appears risk-free.

**[central]** Transaction costs are an order of magnitude too small to explain (or erase) the crypto basis: spot BTC bid-ask spreads are under 0.2% on most crypto-native exchanges and exchange trading fees run 0.10%-0.25% of notional, versus a ~7% p.a. carry. Critically, a hold-to-maturity carry trader pays the spread only once at entry, not on every rebalance — so unlike high-turnover timing strategies, fee drag does not scale with holding period.

> Bid-ask spreads on spot bitcoin are much smaller than crypto carry and less than 0.2% for most crypto-native exchanges (Makarov and Schoar (2020)). Average bid-ask spreads for futures are also small relative to the size of crypto carry and are less than 3% for CME futures in our sample period. In addition, note that the carry trader does not incur bid-ask spread costs if she holds the position until maturity but only if she chooses to liquidate the position prematurely. Exchange trading fees are also too small to explain the large magnitude of crypto carry ... Makarov and Schoar (2020) estimate these to range from 0.25% of the amount traded to 0.1%, which is much less than the size of crypto carry.

**[central]** The cash-and-carry trade is NOT risk-free in practice: the short-futures leg has a mean excess return of 2-3% per month but ~17% monthly volatility, and at only 10x leverage (far below exchange maxima) the futures leg would have been liquidated in over half of all months in the 2018-2024 sample. The binding constraint is margin/funding risk from the absence of cross-margining between the spot and futures legs, not the headline spread.

> the analysis reveals that, assuming a leverage of 10 (which is significantly lower than the maximum leverage offered by most exchanges, as shown in Table A.1), the futures leg of the strategy would have been liquidated in over half of the months in our sample. These findings highlight the substantial risks associated with the futures leg of the cash-and-carry strategy, particularly when it is not protected by cross-margining, despite its high average return.

**[central]** The carry exists because of structural limits to arbitrage (regulatory segmentation plus margin frictions) combined with leveraged demand from small trend-chasing retail traders — and it shrinks measurably when those frictions are relaxed. The January 2024 spot BTC ETF launch causally cut the basis by ~3 percentage points across exchanges and a further ~5pp on CME, i.e. 36% and 97% of the pre-event mean basis. This implies the historical ~7% edge is being competed away as institutional arbitrage capital enters.

> in a DiD setting, we show that the introduction of the ETF significantly decreased crypto carry across exchanges by about three percentage points and by an additional five percentage points on the CME. In economic terms, these are very large declines of 36% and 97% of the mean crypto carry, respectively. This result provides causal evidence that margining frictions, which are central to our limits to arbitrage story, have an important bearing on crypto carry.

**[supporting]** Perpetual futures are a structurally different (and weaker-anchored) carry instrument than the fixed-expiry contracts this paper studies: perps typically trade at positive funding (longs pay shorts) and a short-perp carry trade has been shown to generate high Sharpe ratios, but perps have no expiry to force spot-futures convergence, so the arbitrage is not self-liquidating and basis divergence can persist indefinitely.

> He et al. (2022) document that perpetual futures allow investors to use leverage and typically trade at a positive funding rate, that is, the long side pays the short side. Christin et al. (2022) also use perpetual futures' eight-hour funding periods to show that cryptocurrency exchanges facilitate leverage for long-side traders and that a carry trade that is short perpetual futures generates high Sharpe ratios. Our paper provides a different perspective on basis trades, since we study fixed-date contracts with proper price convergence of spot and futures on the settlement date. ... In contrast to fixed-maturity futures, perpetual ones are not guaranteed to converge to the spot price, since the contracts have no expiration date to strictly enforce arbitrage.

### Source 17 — quality: primary | published: 2025-06-13

**[central]** Traditional grid trading has a mathematically zero expected value: the authors prove that under a symmetric 50/50 random walk with grid size k and a finite number of grid levels, E(grid strategy) = 0, so after transaction fees the strategy is a negative-expectancy proposition. This is a cheap, principled ruling-out of grid bots, one of the most heavily promoted retail crypto strategies (Binance/OKX/Pionex all ship built-in grid bots).

> Grid trading has become a widely used trading technique in recent years. However, our research reveals that without any insight into market trends, the expected value of grid trading is effectively zero. This means that investors face a high risk of losing money after taking transaction fees into consideration.

**[supporting]** The zero-expectancy result is confirmed empirically on BTC/ETH 1-minute data (Jan 2021-Jul 2024): with fees switched off the grid strategy's IRR oscillates around a flat level with no drift, and turning fees on shifts it down, with smaller grid sizes (i.e. higher trade frequency) hurt most. This is the same structure as the user's own finding that fee drag scales with trade frequency (0.78 at 1h vs ~14 at 3m) while the underlying edge is zero.

> Without considering fees (represented by the blue line), the IRR fluctuates at a consistent level, aligning with our earlier calculation that the expected value of the grid strategy is zero. Next, after considering fees (represented by the red line), as with the DGT strategy results, we observe that a smaller grid size experiences lower volatility but is more susceptible to transaction fees

**[central]** The paper's headline 'market outperformance' claim (DGT strategy, 60-70% IRR) is attributed by the authors themselves to bull-market beta rather than to strategy edge, and rests on a single in-sample sweep of grid parameters over one historical window (Jan 2021-Jul 2024, BTC/ETH) with no held-out or walk-forward validation reported. It is an arXiv preprint (v1, June 2025), not peer-reviewed. Treat DGT as a long-only, long-biased accumulation heuristic tested through a large crypto bull market, not as demonstrated alpha.

> the IRR of our strategy remains consistently positive throughout the backtesting period, reaching as high as 60-70%. This strong performance is largely due to the significant rise in cryptocurrency prices in recent years, which is highly favorable for spot grid trading.

**[supporting]** The benchmark traditional-grid comparison uses grid boundaries chosen with look-ahead knowledge of the realised price range (BTC upper 80,000 / lower 10,000; ETH 5,000 / 500 'perfectly contain' the 2021-2024 path), so even the baseline it beats is an optimistically-specified one that could not have been configured ex ante.

> Figure 7 shows the IRR for a grid strategy where the upper and lower limits perfectly contain the cryptocurrency price from 2021 to July 2024. For BTC, the upper limit is 80, 000, and the lower limit is 10, 000. For ETH, the upper limit is 5, 000, and the lower limit is 500.

**[supporting]** All results assume every grid fill is a maker fill at 0.0008 (8 bps, OKX Level 1 maker), i.e. 16 bps round trip on limit orders only. A retail trader paying Binance's 0.1% taker rate (20 bps round trip, the user's current cost basis) faces roughly 25% higher cost per round trip than modelled, and grid strategies cannot in practice guarantee maker fills on fast moves - so the published net-of-cost numbers are an upper bound.

> Additionally, we account for transaction fees, applying a fee of 0.0008, which corresponds to the Level 1 maker fee on OKX.

### Source 18 — quality: primary | published: 2025-08-01

**[central]** The headline funding-rate-arbitrage result (115.9% over six months) is an UPPER BOUND across 60 evaluated scenarios paired with the MINIMUM loss (1.92%), not an average or a distribution. The abstract reports no net-of-transaction-cost figures (no taker/maker fees, slippage, gas, or borrow costs), no out-of-sample or walk-forward validation, and no per-scenario dispersion. Treat 115.9%/6mo as a best-case gross number, not an expected net return.

> Evaluation of 60 arbitrage scenarios underscores the potential range of returns, positioning funding rate arbitrage as a stable yet rewarding alternative to HODL strategies. This study presents evidence that funding rate arbitrage can generate substantial returns—up to 115.9% over six months—while keeping possible losses to a minimal 1.92%.

**[central]** The paper names an explicit STRUCTURAL mechanism for the edge rather than a backtested pattern: the funding rate is a contractually mandated periodic cash transfer between longs and shorts whose purpose is to tether the perpetual price to spot. A delta-neutral position (short perp / long spot, or the reverse) harvests this payment as carry, so the return source is a market-design feature, not a price-prediction signal.

> A pivotal mechanism in this market is the funding rate, a periodic payment between buyers (longs) and sellers (shorts) in perpetual futures contracts to keep the contract price close to the market value of the asset.

**[supporting]** Funding-rate arbitrage returns are reported as UNCORRELATED with buy-and-hold (HODL) crypto returns, making it a diversifier rather than a levered beta proxy. This is directly testable: a bot can compute the correlation of its realised carry P&L against BTC spot returns over the same window and should find it near zero if the paper's finding replicates.

> Empirical analysis of arbitrage strategies, contrasted with the Hold-On-for-Dear-Life (HODL) approach, uncovers diversification benefits as funding rate arbitrage exhibits no correlation with HODL strategies.

**[supporting]** The study's venue and asset scope is directly reachable by a solo retail trader: two CEXs (Binance, BitMEX) and two DEX perp venues (ApolloX, Drift), on five liquid majors (BTC, ETH, XRP, BNB, SOL). No colocation, HFT latency, or institutional venue access is invoked — the strategy is specified at a granularity (periodic funding payments, typically 8-hourly) that a Python/ccxt bot can execute.

> leveraging data from major exchanges such as Binance and Bitmex, alongside decentralized platforms like ApolloX and Drift. Key assets, including BTC, ETH, XRP, BNB, and SOL are examined.

**[tangential]** The perpetual futures market traded is described as exceeding $100 billion per day in volume, implying that venue capacity and liquidity are not the binding constraint for a small retail participant running funding-rate carry — the binding constraints are instead fees, funding-rate sign persistence, and execution/basis risk.

> Perpetual futures, non-expiring swap contracts, dominate cryptocurrency markets with over $100 billion in daily trades.

### Source 19 — quality: primary | published: 2024-03-01 (International Review of Financial Analysis, Volume 94, article 103244; DOI 10.1016/j.irfa.2024.103244). Working paper version read in full is dated 6 December 2022 (SSRN 4295427).

**[central]** A weekly-rebalanced cross-sectional ML long-short strategy over ~574 coins (Jul 2017-Jul 2022) survives realistic trading costs, but conservative variable costs (dynamically estimated Corwin-Schultz/Abdi-Ranaldo bid-ask spread + 10bps flat fee) consume ~60% of gross profits; the best model (COMB, an equal-weight combination of 10 ML forecasts) nets 2.89% per WEEK, while PLS and SVM are rendered statistically insignificant. Treat the magnitude with heavy skepticism: the reported gross annualized Sharpe ratios of 2.73 (PLS) to 5.37 (COMB) are far above the 2.45 Gu et al. report for US equities and are not plausibly attainable — this is the single strongest overfitting/feasibility red flag in the paper.

> the strategies lose about 60% of their gross profits on average. Furthermore, the mean returns on two long-short portfolios--PLS and SVM--are rendered insignificant. Nevertheless, most algorithms survive--continuing to produce sizeable and significant profits. Our top performer, the COMB strategy, generates an average weekly net return of 2.89% (t-stat = 5.54).

**[central]** Weekly cross-sectional selection is roughly 10-25x more cost-tolerant than high-frequency timing: despite one-sided weekly turnover of 78.6% (LASSO) to 110.8% (SVM) — 83.9% for the top COMB model — the breakeven one-way trading cost is 133 to 281 basis points. This is directly falsifiable against the user's own finding that fee drag killed 3-minute configs: at a 0.1% Binance taker fee, a weekly-rebalanced cross-sectional strategy would need to lose >13x more to costs before breaking even, meaning fee drag is a survivable tax at weekly horizons rather than the dominant term.

> The breakeven trading costs range between 133 (SVM) and 281 (COMB) basis points. These numbers are far beyond the conservative trading costs assumptions in Babiak et al. (2022); thus, they promise a potentially successful portfolio implementation.

**[central]** The alpha is concentrated in assets a retail trader effectively cannot access: the quintile that is the primary source of the long-short alpha represents only 0.8% (COMB) to 9.1% (NN1) of aggregate crypto market capitalization, and less than 1% for almost half the strategies, with average constituent market caps of only $100-600M. Alphas in the highest-limits-to-arbitrage tercile are roughly three times those in the easiest-to-trade tercile. NOTE: the Dec-2022 preprint attributes this to the SHORT leg (making it infeasible via borrow constraints), whereas the published 2024 abstract attributes returns to the LONG leg — either way, the concentration in illiquid microcaps is stable across both versions and is the binding practical constraint.

> the bottom quintile--the primary source of alphas in the long-short strategies--accounts for between 0.8% (COMB) and 9.1% (NN1) of the market. Notably, this subset does not capture more than 1% of the aggregate cryptocurrency capitalization for almost half the strategies.

**[central]** The predictive signal requires NO on-chain, order-book, funding-rate, or sentiment data — the top predictors among 34 tested characteristics are all derivable from OHLCV price/volume history alone (idiosyncratic volatility, CAPM alpha, maximum daily return, nominal price, value at risk, distance to 90-day high; grouped: past returns, volatility, liquidity). The published 2024 abstract lists a slightly different but equally simple set (market price, past alpha, illiquidity, momentum). This makes the strategy family cheaply testable in a walk-forward harness within weeks using only ccxt daily/weekly bars across a multi-coin universe.

> cryptocurrency returns are determined by a handful of uncomplicated signals--including idiosyncratic volatility, CAPM alpha, maximum daily return, nominal price, value at risk, and distance to a 90-day high. Notably, all these variables originate from simple data types--such as prices and returns. Moreover, when predictors are grouped into general economic categories, what matters the most are past returns, volatility, and liquidity.

**[central]** VERSION CONFLICT bearing directly on whether this edge is alive in 2026 and testable long-only. The Dec-2022 preprint (full text verified) reports alpha coming from the short leg and DECAYING ~30% between the first half (Jan 2018-Apr 2020) and second half (Apr 2020-Jul 2022) of the sample, plus 30-58.83% maximum drawdowns. The published 2024 IRFA version reverses both, claiming long-leg origin and persistence. The published abstract could not be verified by direct fetch (ScienceDirect/SSRN/ResearchGate all 403; Semantic Scholar and Crossref return null abstracts) and is quoted here as returned consistently by search. If the published long-leg version is correct, a long-only cross-sectional strategy is viable for this user; if the preprint is correct, the strategy is a short-microcap trade the user cannot execute. This must be resolved before building on the paper.

> Contrary to the stock market, abnormal returns in cryptocurrencies originate from the long leg of the trade and persist over time. [published 2024 abstract via search] — vs. preprint: "machine learning alphas predominantly come from the short legs of long-short strategies" and "their sheer size has declined by about 30%"


## Verification votes completed

- refuted=False confidence=high
  - evidence: I could not WebFetch the PDF (HTTP 403), so I downloaded it via curl with a browser user-agent and ran pdftotext. The file is genuine: PDF v1.5, 116 pages, 9,191,880 bytes. Every element of the claim is VERBATIM in the source.

1. QUOTE FIDELITY — exact, lines 159-170 of extracted text, p.5-6: "In contrast to time-series momentum, evidence of cross-sectional momentum is weak. Among 21 cross-sectional momentum portfolios of selected look-back and holding periods, five are liquidated during the sample period and only six outperform the market. [...] Ten portfolios yield a positive mean return with a t-statistic greater than 2.0, but only three of them have a mean log return with a t-statistic greater than 2.0. Moreover, six portfolios with a positive mean return are either liquidated or earn a negative profit. These results demonstrate the inadequacy of the mean return as a long-term profitability indicator." Not a paraphrase, not truncated misleadingly. The abstract independently states: "Evidence of time-series momentum is strong, whereas evidence of cross-sectional momentum is weak" and "The t-test of the mean return is insufficient to test profitability."

2. THE "CHERRY-PICKED AS BEST-IN-REGRESSION" PARENTHETICAL IS THE STRONGEST-VERIFIED PART, not an overreach. p.45: "we select three holding periods for each look-back period up to 28 days, which have the highest t-statistics in Table 13. [...] Using this criterion, we choose 21 pairs: (1,7), (1,14), (1,21), (3,14), (3,21)
  - counterSource: Liu, Tsyvinski & Wu, "Common Risk Factors in Cryptocurrency," Journal of Finance 77(2), 2022, pp.1133-1177 (https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.13119) — peer-reviewed, top-3 journal, finds cross-sectional momentum IS one of three factors pricing the crypto cross-section, with 1-, 2-, 3-, 4-, and 1-to-4-week look-backs generating "significantly positive returns." This makes the literature CONTESTED, not settled. However it does not refute the claim: (a) Han et al. explicitly cite and engage LTW (p.3) and their whole contribution is re-testing it under transaction costs, tradability limits, and daily mark-to-market that LTW omit; (b) LTW's universe includes sub-$1M-liquidity coins a retail bot cannot trade; (c) independent papers cited on the same page — Grobys & Sapkota (2019) and Dong et al. (2022) — ALSO find crypto cross-sectional momentum insignificant, so "weak evidence" is corroborated by three sources, not one.

- refuted=False confidence=medium
  - evidence: VERIFICATION METHOD: WebFetch returned HTTP 403 on both the AUT PDF and SSRN, so I downloaded the PDF via curl with a browser UA (9.19 MB, 116 pages) and extracted text with pdftotext -layout. The passage sits at extracted lines 2464-2476.

WHAT IS CONFIRMED VERBATIM (all load-bearing assertions):
1. Section heading is literally "5.3.2 Binance futures". Body: "we test the cross-sectional momentum strategy using the coins listed on the Binance futures market... The dataset contains 239 unique coins and spans the period from September 8, 2019 to November 17, 2023... the backtesting period commences on February 12, 2020."
2. The supporting quote is word-for-word accurate, including "most profits are accrued prior to 2022, and the performance thereafter is mediocre", "The previous best strategy, (14, 7), performs comparably to the market with a Sharpe ratio of 0.83", "the (1, 7) strategy with the lowest MDD now has the highest MDD of 78.7%", and "This inconsistency reveals the potential unreliability and fragility of the findings in this paper, and perhaps in many other papers on cryptocurrency." No fabrication.
3. "full CoinMarketCap universe" is correct: line 437, "Our data include all available cryptocurrencies in CoinMarketCap." And the paper itself calls (14,7) "The previous best strategy", so that characterization is the authors', not the claimant's.
4. Results ARE net of costs, strengthening the claim: Table 21 caption states "A transaction cost of 15 bps is assumed." The 
  - counterSource: No credible contradicting source found. Two targeted searches for post-2022 evidence that crypto cross-sectional momentum survives on a tradable/Binance-perp universe returned only weak counters: a ResearchGate preprint, "Momentum Trading in Cryptocurrencies: A Comparative Study of Time-Series and Cross-Sectional Strategies" (https://www.researchgate.net/publication/406476873), claiming XS momentum "limited losses" in 2022-2023 and "modest positive returns" in 2024-2025 — but it covers only 8 large-cap coins, is a non-peer-reviewed preprint, and does not report net-of-cost Sharpes, so it does not rebut. The strongest internal counterweight is inside the source itself (see evidence, item 5).

- refuted=False confidence=high
  - evidence: VERIFIED AGAINST PRIMARY SOURCE. I downloaded NBER WP 25882 (https://www.nber.org/system/files/working_papers/w25882/w25882.pdf), extracted text with pdftotext, and read the relevant sections. Every element of the claim is verbatim-supported.

1) SAMPLE (2014-2018, 1,707 coins, CoinMarketCap, >$1M mcap) — CONFIRMED. Section 2: "We collect trading data of all cryptocurrencies available from Coinmarketcap.com... Our sample includes 1,707 coins from the beginning of 2014 to the end of 2018. The trading volume data became available in the last week of 2013, and thus our sample period starts from the beginning of 2014... We further exclude coins with market capitalizations of less than $1,000,000." Coin count grows "from 109 in 2014 to 1,583 in 2018"; the 1,707 is the full-sample/market-return universe.

2) "9 of 25" — CONFIRMED verbatim: "We hence investigate 25 factors, which we present in Table 2" and "We find that the returns of the zero-investment strategies are statistically significant for 9 out of the 25 factors. Specifically, these are: market capitalization, price, and maximum price; one-, two-, three-, and four-week momentum; dollar volume; and standard deviation of dollar volume." (3+4+1+1 = 9, arithmetic checks.)

3) "equity-style price/volume characteristics" — CONFIRMED as fair paraphrase: "we consider a comprehensive list of the established factors in the cross-section of stock returns, compiled by Feng et al. (2017) and Chen and Zimmermann (2018)... we select all 
  - counterSource: I searched specifically for refutations and found qualifying literature, but none that disputes what the paper reports. (1) "Cryptocurrency anomalies and economic constraints" (Int. Review of Financial Analysis, 2024, https://www.sciencedirect.com/science/article/abs/pii/S1057521924001509) finds size and volume anomalies originate in micro-cap coins of negligible economic importance, and that screening out the smallest/least-liquid coins changes results — i.e. it attacks ECONOMIC significance and implementability, not the statistical estimates. (2) "Cryptocurrency momentum has (not) its moments" (Financial Markets and Portfolio Management, 2025, https://link.springer.com/article/10.1007/s11408-025-00474-9) reports crypto momentum suffers severe crashes, that a single coin can render momentum portfolio returns insignificant, and that momentum is concentrated in large caps — a robustness qualification. (3) Some later work reports short-term reversal rather than momentum in more recent samples, which is an out-of-sample persistence concern for 2014-2018 findings, not a challenge to the paper's reported figures. Both (1) and (2) were paywalled (403 / IDP redirect) so I relied on search-result abstracts for them; the core claim itself was verified directly from the full primary PDF text, so this does not weaken the verdict. Net: the descriptive claim stands; its practical tradeability is separately and legitimately contested.

- refuted=False confidence=high
  - evidence: VERBATIM VERIFICATION (primary source obtained directly). WebFetch got 403, so I downloaded the PDF via curl (116 pages, v1.5) and extracted text with pdftotext. Every number in the claim matches the paper word-for-word.

Paper: Chulwoo Han, Byeongguk Kang, Jehyeon Ryu, "Time-Series and Cross-Sectional Momentum in the Cryptocurrency Market: A Comprehensive Analysis under Realistic Assumptions" (SSRN 4675565, Dec 2023; ACFR seminar version with Internet Appendix).

Line-by-line matches in the extracted text:
- Abstract (l.15-17): "many momentum portfolios are liquidated and many with statistically significant returns earn insignificant profits. The t-test of the mean return is insufficient to test profitability. Evidence of time-series momentum is strong, whereas evidence of cross-sectional momentum is weak."
- l.160-170 (exact match to the supplied quote): "Among 21 cross-sectional momentum portfolios of selected look-back and holding periods, five are liquidated during the sample period and only six outperform the market. ... Ten portfolios yield a positive mean return with a t-statistic greater than 2.0, but only three of them have a mean log return with a t-statistic greater than 2.0. Moreover, six portfolios with a positive mean return are either liquidated or earn a negative profit."
- The claim's parenthetical "already cherry-picked as best-in-regression" is directly supported at l.1747: "even though we select the best 21 pairs from the regression analysis, only eight o
  - counterSource: Liu, Tsyvinski & Wu, "Common Risk Factors in Cryptocurrency," Journal of Finance 77(2):1133-1177 (2022) — peer-reviewed, documents a crypto cross-sectional momentum factor (CMOM), which superficially contradicts "weak evidence." It fails as a refutation because it assumes frictionless trading with no liquidation modeling and no interim mark-to-market, the exact deficiencies Han et al. quantify. Second checked source, Drogen/Hoffstein/Otte (SSRN 4322637), claims the edge but reports out-of-sample top-quintile returns of -2.35% annualized vs +69.17% in-sample, corroborating the claim instead.

- refuted=True confidence=high
  - evidence: I downloaded and extracted the full 116-page primary PDF (saved at C:\Users\DNIELL~1\AppData\Local\Temp\claude\--wsl-localhost-Ubuntu-home-daniellorincz-personal-trading-bot\1cc3c6a1-cd80-4d34-885e-78fae748eae0\scratchpad\mom.pdf / mom.txt). The narrow short-only fact survives; the claim's headline framing and its actionable conclusion do not.

WHAT CHECKS OUT: The quote is verbatim and accurate. Table 5 panel (a) "Performance before transaction costs" shows short-only cumulative returns of -89.8, -83.5, -93.5, -90.1, -98.8, -67.2, -74.0, -72.0, -86.8, -82.6, -57.7, -45.9, -17.6, +10.0, -83.9, -77.7, -68.3, -67.4, -60.9, -60.0. Line 1765 states verbatim "most short-only portfolios are liquidated during the sample period." On the actually-shortable Binance-futures universe (Table 21) every short-only leg is negative (Cum -88% to -99%).

DEFECT 1 - WRONG COUNT: It is 19 of 20, not 20 of 21. Table 5 tests 20 pairs ({7,14,21,28} lookback x {1,3,5,7,14} holding); only (21,7) is positive. The "21 pairs" figure belongs to the *cross-sectional* section ("even though we select the best 21 pairs from the regression analysis", line 1747), a different table. The claim merged two tables.

DEFECT 2 - CONTRADICTED BY THE SAME PAPER'S LONG-SHORT TABLES: "Adding short positions only erodes the mean return" is stated *relative to long-only*, not relative to zero. Every time-series LS portfolio in Table 5 panel (a) earns a strongly positive mean (30.3% to 77.7% p.a.) with positive cumulative re
  - counterSource: Liu, Tsyvinski & Wu, "Common Risk Factors in Cryptocurrency," The Journal of Finance 77(2), 1133-1177 (2022) - peer-reviewed, top-3 finance journal - finds "Ten cryptocurrency characteristics form successful long-short strategies that generate sizable and statistically significant excess returns," with market/size/momentum as priced factors (https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.13119). Also self-contradicting within the primary source itself: Table 14 line 1773 ("After accounting for transaction costs, six long-short portfolios outperform the market in terms of the Sharpe ratio") and Table 21 line 2465 on the shortable Binance-futures universe ("Most long-short portfolios earn profits and six of them outperform the market"), plus the authors' own fragility disclaimer at line 2474. Additional context: Starkiller Capital (https://www.starkiller.capital/post/cross-sectional-momentum-in-cryptocurrency-markets) declines to build long/short not because it is unprofitable but for microstructure reasons - "we do not attempt, in this specific paper, to produce long/short market neutral portfolios" due to thin perp liquidity and volatile funding - which is an implementability objection, not an edge objection.

- refuted=True confidence=high
  - evidence: I downloaded and read the primary PDF (116pp, Han/Kang/Ryu, Sungkyunkwan Univ., SSRN 4675565, Dec 2023 working paper, NOT peer-reviewed/published). The literal quotes are real, but the claim's headline and its actionable conclusion are refuted by the SAME paper.

1) SELF-CONTRADICTION IN THE MOST RELEVANT TEST (Binance futures — the exact venue for retail shorts). Section 5.3.2 / Table 21 (Feb 2020–Aug 2023, 15bps costs): "Most long-short portfolios earn profits and six of them outperform the market. They also have smaller MDDs than the market. The (5, 21) and (7, 28) strategies perform best with Sharpe ratios of 1.32 and 1.21" vs market Sharpe 0.84. The table numbers show the short leg roughly HALVES risk: long-only Std ~86–94% / MDD ~81–90%, vs long-short Std ~37–72% / MDD ~34–79%. This directly falsifies the claim's load-bearing premise "Adding short positions only erodes the mean return without reducing the risk" for perp/futures universes.

2) THE LONG-SHORT LEGS ARE NOT VALUE-DESTROYING. Table 5 (time-series, the very table the quote describes) shows LS cumulative returns overwhelmingly POSITIVE and Sharpe often ABOVE the market's 0.85: (14,7) LS Sharpe 1.06 / cum +12,005%; (28,5) 1.15 / +19,167%; (28,7) 1.15 / +20,046%. Cross-sectional Table 14: "All the long-short portfolios except for the (3, 21) pair yield a positive mean return"; after 15bps costs "six long-short portfolios outperform the market in terms of the Sharpe ratio", (1,7) Sharpe 1.31 and (14,7) Sharpe 1.2
  - counterSource: Same primary source, Section 5.3.2 and Table 21 (Binance futures): "Most long-short portfolios earn profits and six of them outperform the market. They also have smaller MDDs than the market... Sharpe ratios of 1.32 and 1.21" (market 0.84); long-short Std ~37-72% and MDD ~34-79% vs long-only Std ~86-94% and MDD ~81-90%. Plus Table 14 cross-sectional: six long-short portfolios beat the market net of 15bps, (14,7) annual Sharpe >1.40 in every year but 2018. External higher-quality venue: Liu, Tsyvinski & Wu, "Common Risk Factors in Cryptocurrency," Journal of Finance 77(2) 2022, pp.1133-1177 (peer-reviewed, top-3 journal) — "Ten cryptocurrency characteristics form successful long-short strategies that generate sizable and statistically significant excess returns," https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.13119
