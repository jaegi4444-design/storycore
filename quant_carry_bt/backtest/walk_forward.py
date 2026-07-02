"""
워크포워드(rolling window) 검증 루프.

in-sample 구간에서 Sharpe/Calmar 기준 그리드서치 → 바로 다음 OOS 구간 검증.
IS-OOS 괴리가 크면 과최적화 경고를 남긴다.
"""

import copy
import logging
from dataclasses import dataclass, field
from itertools import product

import numpy as np
import pandas as pd

from backtest.engine import BacktestEngine, objective_score
from config.settings import AppConfig

logger = logging.getLogger(__name__)

BARS_90D = 90 * 6  # 4h 봉 기준 90일 = 540바


@dataclass
class WalkForwardFold:
    fold_id: int
    is_start: pd.Timestamp
    is_end: pd.Timestamp
    oos_start: pd.Timestamp
    oos_end: pd.Timestamp
    best_params: dict
    is_metrics: dict
    oos_metrics: dict
    overfit_warning: bool = False
    overfit_reason: str = ""


@dataclass
class WalkForwardResult:
    strategy: str
    folds: list = field(default_factory=list)
    regime: str = "all"
    summary: dict = field(default_factory=dict)


PARAM_GRIDS = {
    "basis": {
        "lookback_period": [60, 100, 150],
        "entry_zscore": [1.5, 2.0, 2.5],
        "exit_zscore": [0.2, 0.3, 0.5],
    },
    "pair": {
        "lookback_period": [60, 90, 120],
        "entry_zscore": [1.5, 2.0, 2.5],
        "exit_zscore": [0.3, 0.5, 0.7],
    },
    "funding": {
        "entry_annualized_pct": [0.08, 0.10, 0.15],
        "exit_annualized_pct": [0.02, 0.03, 0.05],
    },
    "momentum": {
        # fold별 재최적화가 IS-OOS 괴리를 오히려 키우는 것으로 확인됨
        # (grid gap=4.49 vs 고정값 gap=1.9). 고정 파라미터로 단일 정책만 검증한다.
        "fast_period": [20],
        "slow_period": [60],
        "entry_strength": [1.0],
    },
}

# 빠른 확인: 파라미터 2개씩 → 조합 8회 (기본 27회 대비)
FAST_PARAM_GRIDS = {
    "basis": {
        "lookback_period": [60, 100],
        "entry_zscore": [1.5, 2.0],
        "exit_zscore": [0.3, 0.5],
    },
    "pair": {
        "lookback_period": [60, 90],
        "entry_zscore": [1.5, 2.0],
        "exit_zscore": [0.3, 0.5],
    },
    "funding": {
        "entry_annualized_pct": [0.08, 0.12],
        "exit_annualized_pct": [0.02, 0.04],
    },
    "momentum": {
        "fast_period": [20],
        "slow_period": [60],
        "entry_strength": [1.0],
    },
}


def get_param_grid(strategy_key: str, fast: bool = False) -> dict:
    return FAST_PARAM_GRIDS[strategy_key] if fast else PARAM_GRIDS[strategy_key]


def _slice_market_data(market_data: dict, start: pd.Timestamp, end: pd.Timestamp) -> dict:
    return {
        sym: df.loc[start:end].copy()
        for sym, df in market_data.items()
        if not df.loc[start:end].empty
    }


def _apply_params(config: AppConfig, strategy_key: str, params: dict) -> AppConfig:
    cfg = copy.deepcopy(config)
    if strategy_key == "basis":
        target = cfg.basis
    elif strategy_key == "pair":
        target = cfg.pair
    elif strategy_key == "momentum":
        target = cfg.momentum
    else:
        target = cfg.funding
    for k, v in params.items():
        setattr(target, k, v)
    return cfg


def _grid_search(
    strategy_key: str,
    market_data: dict,
    config: AppConfig,
    spec: dict,
    fast: bool = False,
) -> tuple[dict, dict]:
    grid = get_param_grid(strategy_key, fast=fast)
    keys = list(grid.keys())
    best_score = -np.inf
    best_params = {k: grid[k][0] for k in keys}
    best_metrics = {}

    for combo in product(*(grid[k] for k in keys)):
        params = dict(zip(keys, combo))
        cfg = _apply_params(config, strategy_key, params)
        strategy = spec["class"](cfg)
        engine = BacktestEngine(
            strategy=strategy,
            backtest_config=cfg.backtest,
            risk_config=cfg.risk,
            price_symbol=spec["price_symbol"],
            price_field=spec["price_field"],
            hedge_symbol=spec.get("hedge_symbol"),
            hedge_field=spec.get("hedge_field") or "close",
        )
        result = engine.run(market_data)
        score = objective_score(result.metrics, config.walkforward.objective)
        if score > best_score:
            best_score = score
            best_params = params
            best_metrics = result.metrics

    return best_params, best_metrics


def run_walkforward(
    strategy_key: str,
    market_data: dict,
    config: AppConfig,
    spec: dict,
    regime: str = "all",
    adaptive_window: bool = False,
    fast: bool = False,
) -> WalkForwardResult:
    wf = config.walkforward
    any_df = next(iter(market_data.values()))
    n = len(any_df)
    is_bars = wf.in_sample_bars
    oos_bars = wf.out_sample_bars
    step_bars = wf.step_bars

    if adaptive_window and n < is_bars + oos_bars + 100:
        is_bars = max(int(n * 0.55), 180)
        oos_bars = max(int(n * 0.25), 60)
        step_bars = max(oos_bars, 60)

    window = is_bars + oos_bars
    folds = []

    fold_id = 0
    start_idx = 0
    while start_idx + window <= n:
        is_slice = any_df.index[start_idx: start_idx + is_bars]
        oos_slice = any_df.index[
            start_idx + is_bars: start_idx + is_bars + oos_bars
        ]
        if len(is_slice) < is_bars or len(oos_slice) < oos_bars:
            break

        is_data = _slice_market_data(market_data, is_slice[0], is_slice[-1])
        oos_data = _slice_market_data(market_data, oos_slice[0], oos_slice[-1])

        best_params, is_metrics = _grid_search(strategy_key, is_data, config, spec, fast=fast)

        cfg = _apply_params(config, strategy_key, best_params)
        strategy = spec["class"](cfg)
        engine = BacktestEngine(
            strategy=strategy,
            backtest_config=cfg.backtest,
            risk_config=cfg.risk,
            price_symbol=spec["price_symbol"],
            price_field=spec["price_field"],
            hedge_symbol=spec.get("hedge_symbol"),
            hedge_field=spec.get("hedge_field") or "close",
        )
        oos_result = engine.run(oos_data)
        oos_metrics = oos_result.metrics

        overfit = False
        reason = ""
        obj = wf.objective
        is_val = objective_score(is_metrics, obj)
        oos_val = objective_score(oos_metrics, obj)
        gap = is_val - oos_val if np.isfinite(is_val) and np.isfinite(oos_val) else np.nan

        threshold = wf.overfit_sharpe_gap if obj == "sharpe" else wf.overfit_calmar_gap
        if np.isfinite(gap) and gap > threshold:
            overfit = True
            reason = f"IS-OOS {obj} gap={gap:.2f} > {threshold} (IS={is_val:.2f}, OOS={oos_val:.2f})"
            logger.warning("[%s fold %d] 과최적화 의심: %s", strategy_key, fold_id, reason)

        folds.append(WalkForwardFold(
            fold_id=fold_id,
            is_start=is_slice[0], is_end=is_slice[-1],
            oos_start=oos_slice[0], oos_end=oos_slice[-1],
            best_params=best_params,
            is_metrics=is_metrics,
            oos_metrics=oos_metrics,
            overfit_warning=overfit,
            overfit_reason=reason,
        ))
        fold_id += 1
        start_idx += step_bars

    summary = _aggregate_folds(folds, config.walkforward.objective)
    return WalkForwardResult(strategy=strategy_key, folds=folds, regime=regime, summary=summary)


def _aggregate_folds(folds: list, objective: str) -> dict:
    if not folds:
        return {}

    def _avg(key, metrics_list, min_trades: int = 0):
        vals = [
            m.get(key) for m in metrics_list
            if m.get(key) is not None and m.get("num_trades", 0) >= min_trades
        ]
        return round(float(np.mean(vals)), 2) if vals else None

    is_list = [f.is_metrics for f in folds]
    oos_list = [f.oos_metrics for f in folds]

    is_obj = [objective_score(m, objective) for m in is_list]
    oos_obj = [objective_score(m, objective) for m in oos_list]
    valid_pairs = [
        (a, b) for a, b in zip(is_obj, oos_obj)
        if np.isfinite(a) and np.isfinite(b)
    ]

    traded_oos = [m for m in oos_list if m.get("num_trades", 0) > 0]

    return {
        "num_folds": len(folds),
        "overfit_warnings": sum(1 for f in folds if f.overfit_warning),
        f"avg_is_{objective}": round(float(np.mean([p[0] for p in valid_pairs])), 2) if valid_pairs else None,
        f"avg_oos_{objective}": round(float(np.mean([p[1] for p in valid_pairs])), 2) if valid_pairs else None,
        f"avg_is_oos_gap_{objective}": (
            round(float(np.mean([p[0] - p[1] for p in valid_pairs])), 2) if valid_pairs else None
        ),
        "avg_oos_sharpe": _avg("sharpe_ratio", traded_oos if traded_oos else oos_list),
        "avg_oos_calmar": _avg("calmar_ratio", traded_oos if traded_oos else oos_list),
        "avg_oos_mdd_pct": _avg("max_drawdown_pct", oos_list),
        "avg_oos_trades": _avg("num_trades", oos_list),
        "discard_candidate": (
            len(valid_pairs) > 0
            and float(np.mean([p[1] for p in valid_pairs])) < 0
        ),
    }


def _longest_labeled_segments(regimes: pd.Series, min_bars: int = 200) -> dict:
    result = {}
    for name in ("bull", "bear", "sideways"):
        mask = regimes == name
        if not mask.any():
            continue
        groups = (mask != mask.shift()).cumsum()
        best_len = 0
        best_bounds = None
        for gid, grp in mask.groupby(groups):
            if not grp.iloc[0]:
                continue
            seg_len = int(grp.sum())
            if seg_len > best_len:
                best_len = seg_len
                idx = grp[grp].index
                best_bounds = (idx[0], idx[-1])
        if best_bounds and best_len >= min_bars:
            result[name] = best_bounds
    return result


def _tertile_fallback(btc_close: pd.Series, ret_90d: pd.Series, min_bars: int = 200) -> dict:
    """
    롤링 수익률 임계값으로 200바 이상 연속 구간을 찾지 못한 국면에 대한 폴백.
    전체 기간을 3등분한 뒤, 각 구간의 평균 90일 수익률이 가장 높은 구간=bull,
    가장 낮은 구간=bear, 중간=sideways 로 라벨한다.
    """
    n = len(btc_close)
    chunk = max(n // 3, min_bars)
    chunks = [
        (btc_close.index[0], btc_close.index[chunk - 1]),
        (btc_close.index[chunk], btc_close.index[2 * chunk - 1]),
        (btc_close.index[2 * chunk], btc_close.index[-1]),
    ]
    scores = []
    for start, end in chunks:
        scores.append(float(ret_90d.loc[start:end].mean()))
    order = np.argsort(scores)
    labels = ["bear", "sideways", "bull"]
    return {labels[rank]: chunks[win_idx] for rank, win_idx in enumerate(order)}


def classify_market_regimes(btc_close: pd.Series) -> dict:
    """
    BTC 현물 종가를 3개 시장 국면으로 분할.

    1차 기준 (4h 봉, 90일=540바 롤링 수익률):
      - bull  : ret_90d > +15%  (강한 상승 추세)
      - bear  : ret_90d < -15%  (강한 하락 추세)
      - sideways: 그 외           (방향성 약한 박스권)

    각 라벨별 **가장 긴 연속 구간**(>=200바)을 선택.
    2차 폴백: 1차에서 누락된 국면은 기간 3등분 + 평균 ret_90d 순위로 할당.
    """
    ret_90d = btc_close.pct_change(BARS_90D)
    regimes = pd.Series("sideways", index=btc_close.index)
    regimes[ret_90d > 0.15] = "bull"
    regimes[ret_90d < -0.15] = "bear"

    result = _longest_labeled_segments(regimes, min_bars=200)
    missing = [r for r in ("bull", "bear", "sideways") if r not in result]
    if missing:
        fallback = _tertile_fallback(btc_close, ret_90d)
        for name in missing:
            result[name] = fallback[name]
    return result
