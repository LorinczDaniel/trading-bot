import pandas as pd

from backtest.simulate import simulate, scan_risk_config
from backtest.metrics import total_return


def walk_forward(
    df: pd.DataFrame,
    make_strategy,
    param_grid: list,
    n_splits: int = 4,
    initial_cash: float = 10_000.0,
    fee: float = 0.001,
    warmup: int = 50,
    risk_config=None,
    min_trades_fold: int = 5,
) -> list:
    """Walk-forward validation.

    Split the data into n_splits+1 contiguous folds. For each fold k, optimize
    the strategy parameters on fold k (in-sample) by picking the grid entry with
    the best in-sample return, then measure that choice on fold k+1 (out-of-sample).

    The gap between average in-sample and average out-of-sample return is the
    overfitting signal: a strategy that only looks good in-sample is curve-fit.

    Grid entries making fewer than `min_trades_fold` in-sample trades are
    rejected before "best" is chosen. Without that, risk sizing makes it possible
    for a near-inactive parameter set to win the fold on a single lucky trade —
    curve-fitting by inactivity, entering through the optimizer where the final
    ranking would never see it.

    `make_strategy(params)` must build a Strategy from one grid entry.
    """
    config = risk_config if risk_config is not None else scan_risk_config()
    n = len(df)
    fold = n // (n_splits + 1)
    if fold == 0:
        raise ValueError("not enough data for the requested number of splits")

    results = []
    for k in range(n_splits):
        is_slice = df.iloc[k * fold : (k + 1) * fold]
        oos_end = n if k == n_splits - 1 else (k + 2) * fold
        oos_slice = df.iloc[(k + 1) * fold : oos_end]

        best_params, best_is, best_is_trades = None, float("-inf"), 0
        for params in param_grid:
            r = simulate(is_slice, make_strategy(params), config,
                         initial_cash, fee, warmup)
            if len(r.trades) < min_trades_fold:
                continue                      # too inactive to be evidence
            ret = total_return(r.equity)
            if ret > best_is:
                best_is, best_params, best_is_trades = ret, params, len(r.trades)

        if best_params is None:
            results.append({
                "fold": k, "valid": False, "best_params": None,
                "in_sample_return": 0.0, "in_sample_trades": 0,
                "oos_return": 0.0, "oos_trades": 0,
            })
            continue

        oos = simulate(oos_slice, make_strategy(best_params), config,
                       initial_cash, fee, warmup)
        results.append({
            "fold": k,
            "valid": True,
            "best_params": best_params,
            "in_sample_return": best_is,
            "in_sample_trades": best_is_trades,
            "oos_return": total_return(oos.equity),
            "oos_trades": len(oos.trades),
        })
    return results
