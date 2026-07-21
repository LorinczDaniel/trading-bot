# Crypto Trading Bot — Build-Ready Blueprint

**Scope:** A fully-functioning, automated **crypto** swing/position trading bot in **Python**.
**Style:** Holding periods from hours to weeks (not high-frequency).
**Design goal:** Broker-abstracted so adding stocks (Alpaca/IBKR) later is a module swap, not a rewrite.

> ⚠️ **This is not financial advice.** A trading bot is a tool for *executing* a strategy automatically. It does not create edge. Most retail trading bots lose money. Read §1 before you get excited.

---

## 1. Reality check — how hard is this, honestly?

Building the *software* is the easy part. Making it *profitable* and *safe to run* is the hard part. Split it like this:

| Part | Difficulty | Time to "good enough" |
|---|---|---|
| A bot that pulls data and places orders on a schedule | 🟢 Easy | A weekend |
| A bot with backtesting, risk limits, monitoring, and restart-safety | 🟡 Moderate | 2–6 weeks |
| A *strategy that actually makes money after fees* | 🔴 Very hard | Months–years, may never happen |
| Operating it for months without a bug losing you money | 🔴 Underrated-hard | Ongoing |

**The 20/80 rule of trading bots:** the code is ~20% of the work. The other 80% is finding a real edge, not fooling yourself in backtests, managing risk, and running it reliably with real money on the line.

### Where people fail
- **Overfitting the backtest.** Tuning parameters until the historical curve looks amazing → it fails live. This is the #1 killer.
- **Ignoring costs.** Fees, slippage, spread, and funding quietly turn a "profitable" strategy into a losing one.
- **No risk management.** One un-stopped trade or a bug in a loop can wipe an account.
- **Operational bugs.** Bot crashes mid-order, restarts, and double-buys. Or loses track of a position.
- **Emotional interference.** Manually overriding the bot, moving stops, "just this once."
- **Security.** Leaked API keys with withdrawal permissions = funds gone.

If you internalize this section, you're already ahead of most people who build one of these.

---

## 2. System architecture

Think of the bot as a pipeline of small, independently testable components. Data flows left to right; the store and risk manager guard the whole thing.

```
                         ┌──────────────────────────────┐
                         │        Config + Secrets       │
                         │  (.env, API keys, params)     │
                         └──────────────┬───────────────┘
                                        │
  ┌────────────┐   candles/ticks   ┌────▼─────┐   signals   ┌──────────────┐
  │ Market     ├──────────────────►│ Strategy ├────────────►│ Risk /       │
  │ Data       │                   │ Engine   │             │ Portfolio    │
  │ Provider   │◄──── history ─────┤          │             │ Manager      │
  └────────────┘                   └──────────┘             └──────┬───────┘
        ▲                                                          │ sized orders
        │ REST / WebSocket                                         ▼
  ┌─────┴──────┐                                          ┌────────────────┐
  │  Exchange  │◄─────────── orders / fills ──────────────┤ Execution /    │
  │  (ccxt)    │─────────── order updates ───────────────►│ Order Manager  │
  └────────────┘                                          └──────┬─────────┘
                                                                 │
       ┌───────────────────────┬─────────────────────────┬──────▼────────┐
       │  State Store (DB)      │  Monitoring / Alerts     │  Scheduler    │
       │  positions, orders,    │  logs, metrics, Telegram │  (the clock   │
       │  trades, PnL           │  dashboard, heartbeat    │  that ticks)  │
       └───────────────────────┴─────────────────────────┴───────────────┘
```

### The components (each = one module with one job)

| Component | Responsibility | Depends on |
|---|---|---|
| **Config/Secrets** | Load API keys, strategy params, risk limits | env, files |
| **Market Data Provider** | Fetch live + historical OHLCV, current prices | Exchange API |
| **Strategy Engine** | Turn data → signals (`BUY` / `SELL` / `HOLD`) | Data, indicators |
| **Risk / Portfolio Manager** | Position sizing, stop levels, exposure & drawdown limits, kill-switch | Store, config |
| **Execution / Order Manager** | Place/cancel/track orders, handle fills, reconcile | Exchange (broker abstraction) |
| **State Store** | Source-of-truth-of-record for orders, positions, trades, PnL | SQLite/Postgres |
| **Scheduler** | The heartbeat: run the cycle every N minutes / on candle close | APScheduler |
| **Monitoring/Alerts** | Logs, metrics, notifications, dashboard, dead-man's switch | Telegram/Discord |

### The key boundary: broker abstraction
Define one interface and hide the exchange behind it. `ccxt` already normalizes ~100 exchanges, but wrap it anyway so your strategy/risk code never imports `ccxt` directly:

```python
# broker/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class Order:
    symbol: str
    side: str            # "buy" | "sell"
    qty: float
    type: str            # "market" | "limit"
    price: float | None = None
    client_id: str | None = None   # for idempotency

class Broker(ABC):
    @abstractmethod
    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int): ...
    @abstractmethod
    def fetch_balance(self) -> dict: ...
    @abstractmethod
    def place_order(self, order: Order) -> dict: ...
    @abstractmethod
    def cancel_order(self, order_id: str, symbol: str) -> dict: ...
    @abstractmethod
    def fetch_open_orders(self, symbol: str | None = None) -> list: ...
    @abstractmethod
    def fetch_positions(self) -> list: ...
```

Then `CcxtBroker(Broker)` for crypto today, and `AlpacaBroker(Broker)` later for stocks. The rest of the bot doesn't change.

---

## 3. APIs & services you need

### 3.1 Exchange / execution API (required)
This is the one that places real orders. Pick one to start.

| Exchange | Python access | Testnet? | Notes |
|---|---|---|---|
| **Binance** | `ccxt` | ✅ Yes | Deepest liquidity, most pairs. (Check availability in your country.) |
| **Coinbase Advanced Trade** | `ccxt` | ⚠️ Sandbox | Reputable, good for EU/US, higher fees. |
| **Kraken** | `ccxt` | ⚠️ Limited | Solid EU-friendly option, good compliance reputation. |
| **Bybit** | `ccxt` | ✅ Yes | Great testnet, derivatives-friendly. |

**Recommendation:** Prototype against a **testnet** (Binance or Bybit) so you can place fake orders with live-like data. Use `ccxt` so switching exchanges is a config change.

### 3.2 Market-data API (often the same exchange, sometimes separate)
- **Live prices & candles:** the exchange itself, via REST (polling) or **WebSocket** (push). For swing trading, REST polling every candle close is plenty.
- **Historical candles (OHLCV):** exchanges give you thousands of bars via `fetch_ohlcv`. For deep history or cross-exchange data consider **CryptoCompare**, **Kaiko** (paid), or **CoinGecko** (free, coarse).

### 3.3 Supporting services
| Need | Free option | Paid/robust option |
|---|---|---|
| Notifications | **Telegram Bot** (free, trivial API), Discord webhook | PagerDuty, Twilio SMS |
| Hosting | Your own PC (fine to start) | VPS: Hetzner / DigitalOcean / AWS Lightsail (~€5/mo) |
| Secrets | `.env` file (gitignored) | Doppler, AWS Secrets Manager, 1Password CLI |
| Dashboard | Streamlit (local) | Grafana + Prometheus |
| Error tracking | logs | Sentry |

**You do NOT need paid data or fancy infra to start.** A free exchange API key + a Telegram bot + your laptop is enough for phases 1–2.

### 3.4 API keys — set them up safely (do this right the first time)
- Create keys with **trade permission only**. **Disable withdrawals.** Always.
- **IP-allowlist** the key to your VPS's IP.
- Store in `.env`, never commit. Add `.env` to `.gitignore` on line one.
- Use **separate keys** for testnet and live.

---

## 4. Data layer

### 4.1 What data you need
- **OHLCV candles** (Open/High/Low/Close/Volume) at your timeframe (e.g. `1h`, `4h`, `1d` for swing).
- **Current price / order book** at execution time (to price limit orders and estimate slippage).
- **Account state**: balances, open orders, positions (fetched from the exchange, not remembered blindly).

### 4.2 Live vs historical
- **Historical** (for backtesting and indicator warm-up): pull once, cache to disk. `ccxt.fetch_ohlcv()` in a pagination loop.
- **Live** (for trading decisions): on each cycle, fetch the latest N candles so indicators are current.

```python
import ccxt, pandas as pd

ex = ccxt.binance()
raw = ex.fetch_ohlcv("BTC/USDT", timeframe="1h", limit=500)
df = pd.DataFrame(raw, columns=["ts","open","high","low","close","volume"])
df["ts"] = pd.to_datetime(df["ts"], unit="ms")
df.set_index("ts", inplace=True)
```

### 4.3 Storage
For a swing bot you don't need much:
- **SQLite** (single file) for trades, orders, positions, PnL journal — zero-config, perfect to start.
- **Parquet / CSV** for cached historical candles.
- Upgrade to **Postgres/TimescaleDB** only if you run many strategies/symbols or want a shared DB for a dashboard.

**Rule:** the *exchange* is the source of truth for balances/positions; your DB is the source of truth for *your intent and history* (why you placed each order, your PnL journal). On restart, reconcile the two (§8.4).

---

## 5. Strategy engine

### 5.1 How a strategy is expressed
A strategy is a pure-ish function: **market data in → a signal out.** Keep it free of order-placement code so you can backtest and live-trade the *same* function.

```python
# strategies/base.py
from dataclasses import dataclass
import pandas as pd

@dataclass
class Signal:
    action: str          # "BUY" | "SELL" | "HOLD"
    strength: float = 1.0
    reason: str = ""

class Strategy:
    def generate(self, df: pd.DataFrame) -> Signal:
        raise NotImplementedError
```

### 5.2 Indicators
Use a library so you don't reimplement (and mis-implement) TA math:
- **`pandas-ta`** — pure Python, `pip install` and go (easiest).
- **`TA-Lib`** — C library, faster, but the install is fiddly (needs a system dependency).

### 5.3 Two concrete starter strategies

**A. Moving-average crossover (trend following)** — buy when fast MA crosses above slow MA.

```python
import pandas_ta as ta
from strategies.base import Strategy, Signal

class MACrossover(Strategy):
    def __init__(self, fast=20, slow=50):
        self.fast, self.slow = fast, slow

    def generate(self, df):
        df = df.copy()
        df["fast"] = ta.sma(df["close"], self.fast)
        df["slow"] = ta.sma(df["close"], self.slow)
        prev, curr = df.iloc[-2], df.iloc[-1]
        crossed_up   = prev.fast <= prev.slow and curr.fast > curr.slow
        crossed_down = prev.fast >= prev.slow and curr.fast < curr.slow
        if crossed_up:   return Signal("BUY",  reason="fast crossed above slow")
        if crossed_down: return Signal("SELL", reason="fast crossed below slow")
        return Signal("HOLD")
```

**B. RSI mean-reversion (counter-trend)** — buy oversold, sell overbought.

```python
class RSIReversion(Strategy):
    def __init__(self, period=14, low=30, high=70):
        self.period, self.low, self.high = period, low, high

    def generate(self, df):
        rsi = ta.rsi(df["close"], self.period).iloc[-1]
        if rsi < self.low:  return Signal("BUY",  reason=f"RSI {rsi:.0f} oversold")
        if rsi > self.high: return Signal("SELL", reason=f"RSI {rsi:.0f} overbought")
        return Signal("HOLD")
```

> ⚠️ These are **teaching examples, not money-printers.** Naked MA-cross and RSI strategies are widely known and rarely profitable alone after fees. Real edge usually comes from combining signals, regime filters, good risk management, and testing many ideas honestly.

### 5.4 Signal → decision
The strategy only says BUY/SELL/HOLD. It does **not** decide *how much* or *whether risk allows it* — that's the risk manager's job (§7). This separation is what keeps the system sane.

---

## 6. Backtesting

Backtesting = replaying a strategy over historical data to estimate how it would have done. **It is where you'll fool yourself the most, so treat it with suspicion.**

### 6.1 Two engine styles
| Style | What it does | Libraries | Use when |
|---|---|---|---|
| **Vectorized** | Computes signals over the whole series at once (fast) | `vectorbt`, `pandas` | Fast idea screening, parameter sweeps |
| **Event-driven** | Simulates bar-by-bar with an order book, fees, partial fills | `backtesting.py`, `backtrader`, `nautilus_trader` | Realistic pre-live validation |

**Recommendation:** screen ideas with `vectorbt` (fast), then validate the finalist with an **event-driven** engine that models fees and slippage, because those are what kill you live.

### 6.2 The pitfalls that produce fake profits
- **Look-ahead bias** — using data you wouldn't have had yet (e.g. deciding on a candle using its own close before it closed). Only act on *closed* candles.
- **Overfitting / curve-fitting** — tuning params to the past. Guard with out-of-sample and walk-forward testing.
- **Ignoring costs** — always subtract taker/maker fees, spread, and slippage. Model funding for perps.
- **Survivorship / selection bias** — only testing coins that survived. Less severe for BTC/ETH majors.
- **Unrealistic fills** — assuming you got the exact close price with infinite liquidity.

### 6.3 Doing it honestly
1. **Split data:** in-sample (optimize) vs out-of-sample (never touched during tuning).
2. **Walk-forward:** optimize on window 1, test on window 2, roll forward. Simulates real re-tuning.
3. **Parameter sensitivity:** if profits vanish when you nudge a parameter by 10%, it's overfit.
4. **Include costs:** set fees + a conservative slippage estimate. If it only works at zero cost, it doesn't work.
5. **Benchmark:** compare to just buying and holding BTC. Many strategies lose to HODL.

### 6.4 Metrics that matter
CAGR, **max drawdown** (how much peak-to-trough pain), **Sharpe / Sortino** (return per unit risk), win rate, profit factor, average win/loss, and **exposure** (time in market). A high return with a 70% drawdown is unrunnable in real life.

---

## 7. Risk management — the part that keeps you solvent

If you only do one thing well, do this. Good risk management can survive a mediocre strategy; a great strategy with no risk control still blows up.

### 7.1 Position sizing
- **Fixed fractional (recommended to start):** risk a fixed % of equity per trade, e.g. **0.5–1%**. Size the position so that *if the stop is hit, you lose only that %*.
- **Volatility targeting:** size inversely to recent volatility (ATR) so each trade risks similar dollars.
- **Kelly criterion:** mathematically optimal growth, but full-Kelly is brutally volatile — use *fractional* Kelly (¼) if at all.

```python
def position_size(equity, risk_pct, entry, stop, price):
    risk_amount = equity * risk_pct           # e.g. 1000 * 0.01 = $10 at risk
    per_unit_risk = abs(entry - stop)         # $ lost per coin if stopped
    if per_unit_risk == 0:
        return 0.0
    qty = risk_amount / per_unit_risk
    return round(qty, 6)
```

### 7.2 Stops and exits
- **Stop-loss** on every position — ATR-based (e.g. entry − 2×ATR) or fixed %. Non-negotiable.
- **Take-profit** and/or **trailing stop** to lock gains.
- **Time stop** — exit if a swing trade hasn't worked within N days.

### 7.3 Portfolio-level guardrails (the kill-switches)
Enforce these *before* any order is sent:
- **Max risk per trade** (e.g. 1%).
- **Max total exposure** (e.g. no more than 3 open positions / 30% of equity deployed).
- **Max daily loss** → stop trading for the day if breached.
- **Max drawdown kill-switch** → halt the whole bot and alert you if equity drops X% from peak.
- **Per-asset cap** and **correlation awareness** (BTC and ETH move together — that's not diversification).
- **Leverage:** if trading perps, cap it hard. Leverage is the fastest way to zero.

```python
class RiskManager:
    def __init__(self, cfg, store):
        self.cfg, self.store = cfg, store

    def approve(self, proposed_order, equity) -> tuple[bool, str]:
        if self.store.drawdown_from_peak() >= self.cfg.max_drawdown:
            return False, "KILL-SWITCH: max drawdown hit"
        if self.store.realized_pnl_today() <= -self.cfg.max_daily_loss:
            return False, "Daily loss limit reached"
        if self.store.open_position_count() >= self.cfg.max_positions:
            return False, "Max concurrent positions reached"
        return True, "ok"
```

**The kill-switch is the single most important line of code in the whole bot.** Build it early.

---

## 8. Execution & order management

This is where "it worked in backtest" meets reality: fees, slippage, partial fills, rate limits, and crashes.

### 8.1 Order types
| Type | Use |
|---|---|
| **Market** | Guaranteed fill, unknown price (pays spread + slippage) |
| **Limit** | Your price or better, may not fill |
| **Stop / stop-limit** | Trigger an order when price crosses a level (for stops) |
| **Post-only** | Ensures you're a maker (lower fees), rejects if it would take |
| **Reduce-only** | Can only shrink a position (safety on derivatives) |

For swing trading, **limit orders** near the price keep costs down; use **market** only when you must get filled.

### 8.2 Costs to model and respect
- **Maker/taker fees** (e.g. 0.02–0.1% each side). They compound with turnover.
- **Slippage** — the gap between expected and filled price; worse in thin books and fast moves.
- **Spread** — you cross it on market orders.
- **Funding** (perps only) — periodic payments that can dominate PnL.

### 8.3 Order lifecycle & partial fills
An order isn't done when you send it. Track state: `submitted → open → partially_filled → filled | cancelled | rejected`. Poll (or subscribe to) order updates and update your store. Don't assume a fill.

### 8.4 Restart-safety, idempotency & reconciliation (the ops stuff that saves you)
- **Idempotency:** attach a **`clientOrderId`** to every order so a retry after a network blip doesn't create a duplicate.
- **Reconciliation on startup:** on boot, fetch open orders + positions + balances from the exchange and rebuild your view. **The exchange is the truth.** Never resume from stale memory.
- **Crash between "decide" and "confirm":** persist intent *before* sending, then reconcile against the exchange to see if it actually landed.
- **Rate limits:** respect them (`ccxt` has `enableRateLimit=True`). Back off on `429`s.
- **Clock sync:** signed requests need accurate time — run **NTP** on your VPS or you'll get signature errors.

```python
import uuid
def submit(broker, store, order):
    order.client_id = f"bot-{uuid.uuid4().hex[:16]}"
    store.record_intent(order)                 # persist BEFORE sending
    resp = broker.place_order(order)           # ccxt passes clientOrderId
    store.record_ack(order.client_id, resp)
    return resp
```

---

## 9. Monitoring & operations

A bot you can't see is a bot you can't trust. You need to know *at a glance* that it's alive and behaving.

### 9.1 Logging & the trade journal
- **Structured logs** (`loguru` or stdlib `logging` + JSON). Log every decision *and its reason*, every order, every fill, every risk rejection.
- **Trade journal** in the DB: entry/exit, size, PnL, strategy, and *why*. This is how you learn and debug.

### 9.2 Alerts (push, don't pull)
Wire a **Telegram bot** (or Discord webhook) to ping you on:
- New position opened/closed, stop hit, take-profit hit.
- Any error/exception.
- **Kill-switch fired.**
- **Heartbeat / dead-man's switch:** the bot sends "I'm alive" every cycle; a separate check alerts you if it goes silent (a *crashed* bot can't alert you itself).

### 9.3 Dashboard (optional but nice)
- **Streamlit** — a few lines gives you a local equity curve, open positions, and recent trades.
- **Grafana + Prometheus** — if you want proper time-series metrics.

### 9.4 Deployment
- **Where:** a small **VPS** (Hetzner/DigitalOcean/Lightsail, ~€5/mo) so it runs 24/7 without your laptop. Pick a region near the exchange for lower latency (not critical for swing).
- **How:** **Docker** container + `restart: unless-stopped`, or a **systemd** service with auto-restart. Either way it must come back after a crash/reboot and reconcile (§8.4).
- **Config:** environment variables / mounted `.env`. Separate `testnet` and `live` profiles.
- **Backups:** back up the SQLite/Postgres DB (your journal).
- **Updates:** deploy from git; don't SSH-edit code on the live box.

---

## 10. The build roadmap (do it in this order)

Resist the urge to go live fast. Each phase de-risks the next. **Real money is the last step, not the first.**

**Phase 0 — Foundations (1–2 days)**
Repo, `.env` + secrets, `ccxt` connection to a testnet, pull and cache historical candles, plot them. Goal: you can get data.

**Phase 1 — Strategy + backtest offline (3–7 days)**
Implement 1 strategy + the backtester. Add fees/slippage. Do out-of-sample + walk-forward. Goal: an *honest* backtest you don't trust yet.

**Phase 2 — Paper trade on testnet (1–2 weeks, then let it run)**
Wire strategy → risk manager → execution against the **exchange testnet** with live data. Add logging, alerts, restart-safety, kill-switch. Goal: it runs unattended for days without breaking, and paper results roughly match backtest.

**Phase 3 — Tiny real capital (weeks)**
Go live with **money you can fully afford to lose** (think €50–200). This surfaces real fees, slippage, and partial fills that testnet hides. Goal: real behavior matches expectations; ops are boring.

**Phase 4 — Iterate & scale (ongoing)**
Only after phase 3 is *boring and stable*: add strategies, more symbols, refine risk, improve the dashboard. Scale capital slowly. Consider the **Alpaca/stocks** broker module here if you want equities.

> If you get to phase 3 and it's not profitable, that's the *normal* outcome — it means the strategy needs work, not that the bot is broken. The bot succeeded by *safely* proving the strategy doesn't have edge yet, at tiny cost.

---

## 11. Recommended tech stack (Python)

| Concern | Pick | Why |
|---|---|---|
| Exchange/broker API | **`ccxt`** (+ `ccxt.pro` for WebSockets) | One API for ~100 exchanges; the broker-abstraction win |
| Data wrangling | **`pandas`**, **`numpy`** | Standard |
| Indicators | **`pandas-ta`** (or `TA-Lib` for speed) | Batteries-included TA |
| Fast backtest / screening | **`vectorbt`** | Vectorized, quick parameter sweeps |
| Realistic backtest | **`backtesting.py`** or `backtrader` | Event-driven with fees/slippage |
| Config & validation | **`pydantic`** + `.env` | Typed config, fewer footguns |
| Scheduling | **`APScheduler`** | Run on candle close / interval |
| Storage | **SQLite** (start) → **Postgres/Timescale** | Journal + state |
| Logging | **`loguru`** | Simple structured logs |
| Alerts | **`python-telegram-bot`** / Discord webhook | Free push notifications |
| Dashboard | **Streamlit** | Fast local UI |
| Testing | **`pytest`** | Test strategies & risk with fixed data |
| Packaging/deploy | **Docker**, `uv`/`poetry` | Reproducible runs on the VPS |

### Suggested repo layout
```
trading_bot/
├─ config/            # yaml/env, strategy & risk params
├─ broker/            # base.py (interface) + ccxt_broker.py  ← abstraction
├─ data/              # market data provider + candle cache
├─ strategies/        # base.py + ma_crossover.py, rsi_reversion.py
├─ risk/              # position sizing + RiskManager (kill-switch)
├─ execution/         # order manager, reconciliation, idempotency
├─ store/             # DB models: orders, positions, trades, pnl
├─ monitoring/        # logging, telegram alerts, heartbeat, dashboard
├─ backtest/          # engines + metrics + walk-forward
├─ engine.py          # the main loop wiring it all together
├─ tests/
├─ .env               # gitignored!  API keys
└─ docs/
```

### The main loop, conceptually
```python
def run_cycle(broker, data, strategy, risk, execution, store):
    df = data.latest_candles(symbol, timeframe, limit=200)   # closed candles only
    signal = strategy.generate(df)
    if signal.action == "HOLD":
        return
    equity = broker.fetch_balance()["total"]["USDT"]
    order  = execution.build_order(signal, df, equity)       # sizing + stop
    ok, why = risk.approve(order, equity)
    if not ok:
        log.warning(f"blocked: {why}"); alert(why); return
    execution.submit(broker, store, order)                   # idempotent
# scheduled by APScheduler to run at each candle close
```

---

## 12. Risk, security, legal & tax (read before going live)

### 12.1 Security (protect the keys and the funds)
- **API keys: trade-only, withdrawals disabled, IP-allowlisted.** Non-negotiable.
- Never commit secrets. `.env` in `.gitignore`; consider a secrets manager on the VPS.
- Keep only *working capital* on the exchange. Exchanges fail (see FTX 2022) — **not your keys, not your coins**. Move the rest to self-custody.
- Lock down the VPS: SSH keys only, firewall, auto-updates, no exposed dashboard without auth.

### 12.2 Financial risk
- You can lose 100% of deposited funds; with leverage, more (liquidation). Start with money you can lose.
- Bugs cost real money. A bad loop with no rate limiting or no kill-switch can act fast. This is why phases 2–3 exist.
- Crypto runs 24/7 — the bot must handle nights/weekends and exchange outages gracefully.

### 12.3 Legal / regulatory (jurisdiction-dependent)
- Rules vary by country. In the **EU**, **MiCA** governs crypto-asset services; using a regulated exchange within the EU is generally the simplest path. Some countries/exchanges restrict algorithmic or leveraged trading for retail.
- If you ever trade *other people's* money, that's a whole different regulated activity — don't.
- **This document is not legal advice.** Check your local rules and the exchange's Terms of Service (some restrict bot/API trading tiers).

### 12.4 Tax
- In most jurisdictions, **each trade is a taxable event** (crypto-to-crypto too). A bot can generate thousands of them.
- **Log every trade** with timestamp, price, fees, and PnL from day one — your DB journal doubles as tax records. Tools like Koinly/CoinTracking can import from exchange APIs.
- **Not tax advice** — consult a local professional; crypto tax treatment differs a lot by country.

### 12.5 Behavioral
- Once live, **let the bot run its rules.** The most common way people break a working bot is manual intervention driven by fear/greed.
- Decide your rules (and kill-switch thresholds) *before* real money is on the line.

---

## 13. TL;DR

- **Feasible?** Yes — a working automated crypto swing bot in Python is a realistic personal project over a few weeks.
- **Hard part?** Not the code — it's (1) finding real edge without fooling yourself in backtests, (2) risk management, and (3) running it safely with real money.
- **Minimum to start:** free exchange **testnet** API key + `ccxt` + `pandas`/`pandas-ta` + a backtester + a Telegram bot for alerts. No paid services needed.
- **Golden rules:** withdrawals-disabled API keys · a real kill-switch · costs modeled in every backtest · testnet before real, tiny real before scaling.
- **Next step:** Phase 0 — scaffold the repo, connect `ccxt` to a testnet, and pull your first candles.

---

*Want me to turn this into an actual project scaffold (the repo layout above with working stubs for each module, a testnet connection, and one backtestable strategy)? That's Phase 0 — say the word and I'll write the implementation plan.*
