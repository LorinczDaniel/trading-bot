import pandas as pd

from backtest.engine import run_backtest
from backtest.metrics import total_return


def walk_forward(
    df: pd.DataFrame,
    make_strategy,
    param_grid: list,
    n_splits: int = 4,
    initial_cash: float = 10_000.0,
    fee: float = 0.001,
    warmup: int = 50,
) -> list:
    """Walk-forward validation.

    Split the data into n_splits+1 contiguous folds. For each fold k, optimize
    the strategy parameters on fold k (in-sample) by picking the grid entry with
    the best in-sample return, then measure that choice on fold k+1 (out-of-sample).

    The gap between average in-sample and average out-of-sample return is the
    overfitting signal: a strategy that only looks good in-sample is curve-fit.

    `make_strategy(params)` must build a Strategy from one grid entry.
    Returns a list of dicts: fold, best_params, in_sample_return, oos_return.
    """
    n = len(df)
    fold = n // (n_splits + 1)
    if fold == 0:
        raise ValueError("not enough data for the requested number of splits")

    results = []
    for k in range(n_splits):
        is_slice = df.iloc[k * fold : (k + 1) * fold]
        oos_end = n if k == n_splits - 1 else (k + 2) * fold
        oos_slice = df.iloc[(k + 1) * fold : oos_end]

        best_params, best_is = param_grid[0], float("-inf")
        for params in param_grid:
            r = run_backtest(is_slice, make_strategy(params), initial_cash, fee, warmup)
            ret = total_return(r.equity)
            if ret > best_is:
                best_is, best_params = ret, params

        oos = run_backtest(oos_slice, make_strategy(best_params), initial_cash, fee, warmup)
        results.append(
            {
                "fold": k,
                "best_params": best_params,
                "in_sample_return": best_is,
                "oos_return": total_return(oos.equity),
            }
        )
    return results
