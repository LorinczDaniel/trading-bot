# Two data-integrity findings that must shape the multi-coin panel

**Date:** 2026-07-24
**Why:** before building a cross-sectional panel, check whether the data source can
support one honestly. A cross-sectional strategy is scored by ranking coins against each
other, so any bias in *which* coins exist, or in their price continuity, is not a rounding
error — it silently manufactures the result.

Both checks below cost one API call each and were run before any panel code was written.

## Finding 1 — survivorship: Binance is usable, which was not guaranteed

The concern: if the universe is "coins listed and liquid today", every coin that died is
missing, and a long strategy is scored in a world where going to zero was impossible.
CTREND's universe spans 100 → 2,000+ coins *including* the ones that went to zero.

Measured via `ccxt.binance().load_markets()` (4,534 spot markets today) plus `fetch_ohlcv`:

| symbol | listed | active | daily history returned |
|---|---|---|---|
| UST/USDT | yes | **false** | 141 bars, 2021-12-24 → **2022-05-13** |
| FTT/USDT | yes | true | 1000 bars from 2021-06-01 |
| LUNA/USDT | yes | true | 1000 bars from 2021-06-01 |
| BTC/USDT | yes | true | 1000 bars from 2021-06-01 |

**Dead coins remain queryable.** `UST/USDT` is retained with `active=false` and its history
terminates exactly at the collapse. So a survivorship-free universe *is* constructible
from Binance — the panel simply must not filter on `active`, because that flag is
current status, not point-in-time membership.

Two rules follow for the universe builder:

1. **Do not filter by `active`.** Inactive symbols are precisely the evidence a long
   strategy needs to be scored against.
2. **Rank point-in-time.** Membership must be decided by trailing volume *as of each
   rebalance date*, never by today's volume applied backwards. Ranking today's winners
   retroactively is look-ahead of the same class as the data-snooping already rejected
   twice in this project.

## Finding 2 — ticker reuse: `LUNA/USDT` splices two different assets

This one is severe and would not have been caught by any sanity check we currently run.

Binance renamed Terra Classic to `LUNC` and reassigned the `LUNA` ticker to Terra 2.0.
The **pre-collapse history stayed attached to `LUNA/USDT`**, so the symbol's daily series
reads:

| date | close | note |
|---|---|---|
| 2022-05-05 | 82.35 | Terra Classic, pre-collapse |
| 2022-05-09 | 30.29 | |
| 2022-05-11 | 1.0769 | |
| 2022-05-12 | 0.00032 | |
| 2022-05-13 | 0.00005 | −99.9999% from the 5th |
| **2022-05-31** | **8.87** | **Terra 2.0 — same ticker** |
| 2022-06-05 | 4.8767 | |

From 0.00005 to 8.87 is a **177,400× gain in 18 days**, entirely an artifact of a rename.
`LUNC/USDT` returns *no* data for that window at all — the old chain's history was not
moved there; it only begins at LUNC's own listing in Sept 2022.

**Why this is fatal to an unguarded panel:** a cross-sectional trend or momentum ranking
scores coins by trailing return. A coin showing +17,740,000% over the prior weeks would
rank first in every indicator simultaneously, be bought at maximum weight, and dominate
the entire backtest. The strategy would look spectacular for reasons that have nothing to
do with any tradeable effect — and the equity curve would show it as the single best
decision the system ever made.

This is the same failure mode as the fabricated-winner risk in the `edge` column and the
band's knife-edge PASS: a number that looks like performance but is an artifact of how the
measurement was constructed.

### What the panel must do about it

Detect and reject redenomination discontinuities rather than trusting the series. The
signature is unambiguous and does not require a maintained denylist: a collapse to
near-zero followed by a jump of several orders of magnitude, on the same symbol, within a
short window. A simple guard — flag any single-bar return above some large multiple, and
any recovery from a >99% drawdown to a level near the pre-collapse price — catches
`LUNA/USDT` and any future rename.

A denylist alone would be fragile: it only catches the renames we already know about, and
the whole point of a universe of thousands of coins is that we do not know them all.

## Verified end-to-end on real data

The screen was built (`data/panel.py`, `find_redenominations`) and then run against a
genuine Binance backfill rather than only against fixtures:

```
LUNA/USDT: 1603 bars, 2022-02-16 -> 2026-07-24
redenominations detected: ['2022-05-31']
  2022-05-13 close=5e-05
  2022-05-31 close=8.87   <- x177,400
```

It also handled the two-week gap correctly: Binance halted LUNA trading between
2022-05-13 and 2022-05-31, so the bars are not adjacent, and the screen still fires on
the jump rather than being confused by the missing days.

Note that a 1,500-day backfill from today *starts* at 2022-06-16 — after the rename — so
the splice is invisible at that depth and only appears once the window reaches back past
May 2022. The hazard is depth-dependent, which is an argument for the screen running
always rather than being triggered by suspicion.

## A third hazard, found while fetching: the candidate list skews recent

Backfilling the top 30 symbols by current quote volume produced this coverage profile
across the assembled panel (32 symbols including two forced-in dead coins):

| date | coins with a price |
|---|---|
| 2022-07-01 | 16 / 32 |
| 2023-07-01 | 16 / 32 |
| 2024-07-01 | 19 / 32 |
| 2025-07-01 | 21 / 32 |
| 2026-07-01 | 31 / 32 |

Half the "top 30 coins" did not exist four years ago. Several have almost no history at
all — `AERO/USDT` returned 8 bars, `RE/USDT` 37, `SPCXB/USDT` 43, `ZAMA/USDT` 173.

This is the point-in-time problem made concrete: **today's highest-volume coins are
disproportionately recent listings**, so a universe defined as "top N today" is not merely
survivorship-biased, it is structurally a bet on newly-listed assets. Any backtest ranking
that set over 2022–2024 would be ranking a handful of survivors while pretending to rank
thirty coins.

Confirms the design rule already stated: `candidate_symbols` chooses what to *download*;
membership at each rebalance date must be re-derived from trailing volume in the cached
data.

## Consequences for the build

The multi-coin data layer is now three requirements, not one:

1. **Fetch** — multi-symbol backfill, reusing the existing paginated `backfill`.
2. **Universe** — point-in-time membership by trailing volume, `active` deliberately
   ignored.
3. **Panel** — align symbols on a common index *and* screen for redenomination splices
   before any ranking sees the data.

Requirement 3 was not in the plan an hour ago and would have quietly invalidated every
result built on top of it.

## Note on expected value

Worth stating plainly before building: the verification in
`2026-07-24-ctrend-claim-verified.md` found the tradeable long-only leg is β≈1.01 to the
market with alpha of 1.10%/week at t=1.94 — not significant at the 5% level — on a sample
ending May 2022. The realistic outcome of this work is another honest negative.

It is still worth building, because the panel is the instrument that can answer the
question at all, and because the same fetch produces per-coin single-asset scans for free:
we can finally ask whether `1d ma` generalizes beyond BTC, or whether that first PASS was
BTC-specific.
