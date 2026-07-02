"""
전략 전반에서 재사용되는 통계 함수 모음.
- z-score, OLS, 반감기: numpy/scipy 기반 (외부 의존 최소화)
- 공적분/ADF 검정: statsmodels.tsa.stattools (정확한 MacKinnon p-value)

statsmodels 미설치 환경에서는 engle_granger_test 가 ImportError 를 발생시킨다.
비교 리포트용 레거시 근사 구현은 stats_legacy.py 참조.
"""

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

try:
    from statsmodels.tsa.stattools import adfuller, coint
    _HAS_STATSMODELS = True
except ImportError:
    _HAS_STATSMODELS = False


def rolling_zscore(series: pd.Series, window: int) -> pd.Series:
    """롤링 평균/표준편차 기반 z-score (현재 바 포함, 미래 바 미참조 — 룩어헤드 없음)"""
    roll_mean = series.rolling(window).mean()
    roll_std = series.rolling(window).std()
    return (series - roll_mean) / roll_std.replace(0, np.nan)


def ols(y: np.ndarray, X: np.ndarray):
    """
    단순 OLS 회귀 (numpy.linalg.lstsq 기반).
    반환: params(ndarray), residuals(ndarray), se_params(ndarray)
    """
    n, k = X.shape
    params, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    fitted = X @ params
    resid = y - fitted

    dof = max(n - k, 1)
    sigma2 = (resid @ resid) / dof
    XtX_inv = np.linalg.pinv(X.T @ X)
    se_params = np.sqrt(np.diag(sigma2 * XtX_inv))

    return params, resid, se_params


def add_constant(x: np.ndarray) -> np.ndarray:
    return np.column_stack([np.ones(len(x)), x])


def half_life(spread: pd.Series) -> float:
    """
    Ornstein-Uhlenbeck 프로세스 가정 하 반감기 추정.
    spread(t) - spread(t-1) = theta * spread(t-1) + noise
    """
    spread = spread.dropna()
    if len(spread) < 20:
        return np.inf

    lag = spread.shift(1).dropna()
    delta = (spread - spread.shift(1)).dropna()
    lag = lag.loc[delta.index]

    X = add_constant(lag.values)
    params, _, _ = ols(delta.values, X)
    theta = params[1]

    if theta >= 0:
        return np.inf
    return -np.log(2) / theta


def adf_test(series: np.ndarray, lags: int = 1) -> dict:
    """statsmodels ADF 검정. 반환: t_stat, p_value, is_stationary(5% 기준)"""
    if not _HAS_STATSMODELS:
        raise ImportError("statsmodels 가 필요합니다: pip install statsmodels")
    result = adfuller(series, maxlag=lags, autolag=None, regression="c")
    t_stat, p_value = result[0], result[1]
    return {
        "adf_tstat": t_stat,
        "adf_pvalue": p_value,
        "is_stationary": p_value < 0.05,
        "critical_values": result[4],
    }


def engle_granger_test(
    y: pd.Series,
    x: pd.Series,
    pvalue_threshold: float = 0.05,
) -> dict:
    """
    Engle-Granger 공적분 검정 (statsmodels.tsa.stattools.coint).
    1) y = alpha + beta*x + resid  (OLS)
    2) coint(y, x) 로 정확한 t-stat / p-value 산출
    """
    if not _HAS_STATSMODELS:
        raise ImportError("statsmodels 가 필요합니다: pip install statsmodels")

    y, x = y.align(x, join="inner")
    y = y.dropna()
    x = x.loc[y.index]

    if len(y) < 30:
        return {
            "hedge_ratio": np.nan,
            "spread": pd.Series(dtype=float),
            "adf_tstat": np.nan,
            "coint_pvalue": 1.0,
            "is_cointegrated": False,
        }

    X = add_constant(x.values)
    params, resid, _ = ols(y.values, X)
    hedge_ratio = params[1]
    spread = pd.Series(resid, index=y.index)

    coint_t, p_value, crit_values = coint(y.values, x.values, trend="c", autolag="AIC")

    return {
        "hedge_ratio": hedge_ratio,
        "spread": spread,
        "adf_tstat": coint_t,
        "coint_pvalue": p_value,
        "critical_values": crit_values,
        "is_cointegrated": p_value < pvalue_threshold,
    }


def average_true_range(df: pd.DataFrame, period: int) -> pd.Series:
    """True Range 롤링평균(ATR). df는 high/low/close 컬럼 필요. 룩어헤드 없음(현재 바 포함)."""
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def calmar_ratio(annualized_return: float, max_drawdown: float) -> float:
    """Calmar = 연환산 수익률 / |최대낙폭| (MDD 는 음수)"""
    if max_drawdown is None or max_drawdown >= 0 or np.isnan(max_drawdown):
        return np.nan
    return annualized_return / abs(max_drawdown)
