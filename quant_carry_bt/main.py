"""
실행 진입점.

사용 예:
    python main.py --strategy basis --mode synthetic
    python main.py --strategy pair  --mode synthetic
    python main.py --strategy funding --mode synthetic
    python main.py --strategy basis --mode live
    python main.py --walkforward --mode synthetic
    python main.py --walkforward --mode cached
    python scripts/generate_report.py --mode cached
"""

import argparse
import json
import logging
import sys
from copy import deepcopy
from pathlib import Path

from config.settings import DEFAULT_CONFIG, DEFAULT_DATA_BARS, apply_fast_mode
from data.loader import SyntheticDataLoader, LiveDataLoader
from strategies.basis_mean_reversion import BasisMeanReversionStrategy
from strategies.pair_trading import PairTradingStrategy
from strategies.funding_carry import FundingCarryStrategy
from strategies.momentum_trend import MomentumTrendStrategy
from backtest.engine import BacktestEngine
from backtest.walk_forward import run_walkforward, classify_market_regimes

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

STRATEGY_REGISTRY = {
    "basis": {
        "class": BasisMeanReversionStrategy,
        "price_symbol": "BTC/USDT",
        "price_field": "future_close",
        "hedge_symbol": None,
        "hedge_field": None,
    },
    "pair": {
        "class": PairTradingStrategy,
        "price_symbol": "BTC/USDT",
        "price_field": "close",
        "hedge_symbol": "ETH/USDT",
        "hedge_field": "close",
    },
    "funding": {
        "class": FundingCarryStrategy,
        "price_symbol": "BTC/USDT",
        "price_field": "future_close",
        "hedge_symbol": "BTC/USDT",
        "hedge_field": "spot_close",
        "risk_override": {"max_leverage": 2.0},
    },
    "momentum": {
        "class": MomentumTrendStrategy,
        "price_symbol": "BTC/USDT",
        "price_field": "close",
        "hedge_symbol": None,
        "hedge_field": None,
        # 중앙값 보유기간 ~45봉(7.5일)이 기본 OOS 90봉(15일)에 겨우 1~2 사이클만 들어가
        # fold별 Sharpe가 대부분 None이 되는 문제 확인 -> OOS/IS 확대
        "walkforward_override": {"in_sample_bars": 810, "out_sample_bars": 270, "step_bars": 270},
    },
}

# basis: 2년 데이터에 평균 2건만 거래(중앙값 보유 322일) — 어떤 폴드 크기를 잡아도
# 워크포워드로 통계적 유의성을 얻을 수 없는 구조. 폴드 기반 검증 대상에서 제외하고
# 별도로 단일 구간 백테스트로만 참고한다.
WALKFORWARD_INCOMPATIBLE = {"basis"}


def _risk_config_for(strategy_key: str, config):
    risk = deepcopy(config.risk)
    override = STRATEGY_REGISTRY[strategy_key].get("risk_override") or {}
    for k, v in override.items():
        setattr(risk, k, v)
    return risk


def _walkforward_config_for(strategy_key: str, config):
    wf = deepcopy(config.walkforward)
    override = STRATEGY_REGISTRY[strategy_key].get("walkforward_override") or {}
    for k, v in override.items():
        setattr(wf, k, v)
    return wf


def build_market_data(mode: str, strategy_key: str, config, limit: int = DEFAULT_DATA_BARS):
    if mode == "cached":
        from data.cache import load_market_bundle
        bundle = load_market_bundle(limit=limit)
        if strategy_key == "basis":
            return bundle["basis"]
        if strategy_key == "funding":
            return bundle["funding"]
        if strategy_key == "pair":
            return bundle["pair"]
        if strategy_key == "momentum":
            return bundle["momentum"]
        raise ValueError(f"unknown strategy: {strategy_key}")

    if mode == "synthetic":
        loader = SyntheticDataLoader(seed=42)
    elif mode == "live":
        config.exchange.testnet = False
        loader = LiveDataLoader(config.exchange)
    else:
        raise ValueError(f"unknown mode: {mode}")

    if strategy_key == "basis":
        df = loader.get_spot_future_pair("BTC/USDT", config.backtest.timeframe, limit)
        return {"BTC/USDT": df}

    if strategy_key == "funding":
        df = loader.get_spot_future_pair("BTC/USDT", config.backtest.timeframe, limit)
        return {"BTC/USDT": df}

    if strategy_key == "pair":
        if mode == "synthetic":
            return loader.get_correlated_pair(config.backtest.timeframe, limit)
        btc = loader.get_ohlcv("BTC/USDT", config.backtest.timeframe, limit)
        eth = loader.get_ohlcv("ETH/USDT", config.backtest.timeframe, limit)
        return {"BTC/USDT": btc, "ETH/USDT": eth}

    if strategy_key == "momentum":
        df = loader.get_ohlcv("BTC/USDT", config.backtest.timeframe, limit)
        return {"BTC/USDT": df}

    raise ValueError(f"unknown strategy: {strategy_key}")


def build_full_market_data(mode: str, config, limit: int):
    """워크포워드/국면분석용: 세 전략 데이터를 한번에 로드"""
    basis = build_market_data(mode, "basis", config, limit)
    funding = build_market_data(mode, "funding", config, limit)
    pair = build_market_data(mode, "pair", config, limit)
    merged = deepcopy(basis)
    merged.update(pair)
    return merged, basis, funding, pair


def run(strategy_key: str, mode: str, config=DEFAULT_CONFIG, limit: int = DEFAULT_DATA_BARS):
    spec = STRATEGY_REGISTRY[strategy_key]
    strategy = spec["class"](config)
    market_data = build_market_data(mode, strategy_key, config, limit)
    cfg = deepcopy(config)
    cfg.risk = _risk_config_for(strategy_key, config)

    engine = BacktestEngine(
        strategy=strategy,
        backtest_config=cfg.backtest,
        risk_config=cfg.risk,
        price_symbol=spec["price_symbol"],
        price_field=spec["price_field"],
        hedge_symbol=spec.get("hedge_symbol"),
        hedge_field=spec.get("hedge_field") or "close",
    )
    return engine.run(market_data)


def run_walkforward_all(
    mode: str,
    config,
    limit: int,
    fast: bool = False,
    strategies: list | None = None,
) -> dict:
    if fast:
        config = apply_fast_mode(config)

    merged, basis_data, funding_data, pair_data = build_full_market_data(mode, config, limit)
    momentum_data = build_market_data(mode, "momentum", config, limit)

    if mode == "synthetic":
        btc_close = SyntheticDataLoader(seed=42).get_btc_price_series(
            config.backtest.timeframe, limit,
        )
    elif mode == "cached":
        btc_close = basis_data["BTC/USDT"]["spot_close"]
    else:
        col = "close" if "close" in merged["BTC/USDT"].columns else "spot_close"
        btc_close = merged["BTC/USDT"][col]

    all_data = {
        "basis": basis_data,
        "pair": pair_data,
        "funding": funding_data,
        "momentum": momentum_data,
    }
    keys = strategies or list(all_data.keys())
    data_map = {k: all_data[k] for k in keys if k in all_data}

    report = {
        "mode": mode,
        "limit": limit,
        "fast": fast,
        "strategies": list(data_map.keys()),
        "regimes": {},
        "full_period": {},
    }

    for strategy_key, data in data_map.items():
        cfg = deepcopy(config)
        cfg.risk = _risk_config_for(strategy_key, config)
        cfg.walkforward = _walkforward_config_for(strategy_key, config)
        wf = run_walkforward(
            strategy_key, data, cfg, STRATEGY_REGISTRY[strategy_key], fast=fast,
        )
        report["full_period"][strategy_key] = {
            "summary": wf.summary,
            "folds": [
                {
                    "fold": f.fold_id,
                    "is_sharpe": f.is_metrics.get("sharpe_ratio"),
                    "oos_sharpe": f.oos_metrics.get("sharpe_ratio"),
                    "is_calmar": f.is_metrics.get("calmar_ratio"),
                    "oos_calmar": f.oos_metrics.get("calmar_ratio"),
                    "oos_mdd": f.oos_metrics.get("max_drawdown_pct"),
                    "oos_trades": f.oos_metrics.get("num_trades"),
                    "overfit_warning": f.overfit_warning,
                    "best_params": f.best_params,
                }
                for f in wf.folds
            ],
        }

    if fast:
        return report

    regimes = classify_market_regimes(btc_close)
    for regime_name, (start, end) in regimes.items():
        report["regimes"][regime_name] = {"period": [str(start), str(end)], "strategies": {}}
        for strategy_key, data in data_map.items():
            sliced = {sym: df.loc[start:end].copy() for sym, df in data.items()}
            if any(len(df) < 240 for df in sliced.values()):
                continue
            cfg = deepcopy(config)
            cfg.risk = _risk_config_for(strategy_key, config)
            cfg.walkforward = _walkforward_config_for(strategy_key, config)
            wf = run_walkforward(
                strategy_key, sliced, cfg, STRATEGY_REGISTRY[strategy_key],
                regime=regime_name, adaptive_window=True,
            )
            report["regimes"][regime_name]["strategies"][strategy_key] = wf.summary

    return report


def main():
    parser = argparse.ArgumentParser(description="BTC 선물 퀀트 전략 러너")
    parser.add_argument("--strategy", choices=list(STRATEGY_REGISTRY.keys()))
    parser.add_argument("--mode", choices=["synthetic", "live", "cached"], default="synthetic")
    parser.add_argument(
        "--limit", type=int, default=DEFAULT_DATA_BARS,
        help=f"가져올 바(bar) 개수 (기본 {DEFAULT_DATA_BARS}=90일, 4h봉)",
    )
    parser.add_argument("--walkforward", action="store_true", help="워크포워드 검증 실행")
    parser.add_argument(
        "--fast", action="store_true",
        help="빠른 확인: 작은 그리드, WF 1 fold, 국면별 생략",
    )
    parser.add_argument("--objective", choices=["sharpe", "calmar"], default="sharpe")
    args = parser.parse_args()

    config = deepcopy(DEFAULT_CONFIG)
    config.walkforward.objective = args.objective

    if args.walkforward:
        limit = max(args.limit, DEFAULT_DATA_BARS)
        strategies = [args.strategy] if args.strategy else None
        report = run_walkforward_all(
            args.mode, config, limit, fast=args.fast, strategies=strategies,
        )
        tag = f"walkforward_{args.mode}{'_fast' if args.fast else ''}"
        out = Path(__file__).parent / "reports" / f"{tag}.json"
        out.parent.mkdir(exist_ok=True)
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
        print(f"\n저장: {out}")
        return

    if not args.strategy:
        parser.error("--strategy 는 --walkforward 없이 필수입니다.")

    result = run(args.strategy, args.mode, config, limit=args.limit)
    print(f"\n=== 전략: {args.strategy} | 모드: {args.mode} ===")
    print(json.dumps(result.metrics, indent=2, ensure_ascii=False))
    print(f"\n총 트레이드 수: {len(result.trades)}")
    if result.trades:
        print("최근 5개 트레이드:")
        for t in result.trades[-5:]:
            print(f"  {t.entry_time} -> {t.exit_time} | dir={t.direction} | pnl={t.pnl:.2f}")


if __name__ == "__main__":
    main()
