"""
statsmodels 도입 전 자체 구현 ADF/공적분 근사치.
utils/compare_stats.py 비교 리포트 전용 — 프로덕션 코드에서는 사용하지 않는다.
"""

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

from utils.stats import ols, add_constant


def adf_test_stat(series: np.ndarray, lags: int = 1) -> float:
    y = np.asarray(series, dtype=float)
    dy = np.diff(y)
    n = len(dy) - lags
    if n <= lags + 2:
        return np.nan

    rows = []
    for t in range(lags, len(dy)):
        row = [1.0, y[t]]
        for i in range(1, lags + 1):
            row.append(dy[t - i])
        rows.append(row)
    X = np.array(rows)
    target = dy[lags:]

    params, resid, se_params = ols(target, X)
    rho = params[1]
    se_rho = se_params[1] if se_params[1] > 0 else np.nan
    t_stat = rho / se_rho if se_rho and not np.isnan(se_rho) else np.nan
    return t_stat


_EG_CRITICAL_VALUES = {0.01: -3.90, 0.05: -3.34, 0.10: -3.04}


def eg_pvalue_approx(t_stat: float) -> float:
    if np.isnan(t_stat):
        return 1.0
    cvs = sorted(_EG_CRITICAL_VALUES.items())
    if t_stat <= cvs[0][1]:
        return 0.005
    if t_stat >= cvs[-1][1]:
        return float(min(1.0, 1 - scipy_stats.norm.cdf(-t_stat) + 0.10))
    for (p_low, cv_low), (p_high, cv_high) in zip(cvs, cvs[1:]):
        if cv_low <= t_stat <= cv_high:
            frac = (t_stat - cv_low) / (cv_high - cv_low)
            return p_low + frac * (p_high - p_low)
    return 1.0


def engle_granger_test_legacy(y: pd.Series, x: pd.Series) -> dict:
    y, x = y.align(x, join="inner")
    y = y.dropna()
    x = x.loc[y.index]

    X = add_constant(x.values)
    params, resid, _ = ols(y.values, X)
    hedge_ratio = params[1]
    spread = pd.Series(resid, index=y.index)

    t_stat = adf_test_stat(spread.values, lags=1)
    p_value = eg_pvalue_approx(t_stat)

    return {
        "hedge_ratio": hedge_ratio,
        "spread": spread,
        "adf_tstat": t_stat,
        "coint_pvalue": p_value,
        "is_cointegrated": p_value < 0.05,
    }
