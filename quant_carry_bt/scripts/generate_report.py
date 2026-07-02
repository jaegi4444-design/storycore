"""
BACKTEST_RESULTS.md 생성 스크립트.

3전략 × 3시장국면 워크포워드 백테스트를 실행하고 결과를 마크다운으로 저장한다.
"""

from __future__ import annotations

import json
import logging
import sys
from copy import deepcopy
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DEFAULT_CONFIG, DEFAULT_DATA_BARS, apply_fast_mode
from backtest.walk_forward import run_walkforward, classify_market_regimes
from main import STRATEGY_REGISTRY, build_market_data, _walkforward_config_for, WALKFORWARD_INCOMPATIBLE

import numpy as np

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def _risk_config_for(strategy_key: str, config):
    spec = STRATEGY_REGISTRY[strategy_key]
    risk = deepcopy(config.risk)
    override = spec.get("risk_override") or {}
    for k, v in override.items():
        setattr(risk, k, v)
    return risk


def _run_single_wf(
    strategy_key: str, data: dict, config, regime: str = "all",
    adaptive: bool = False, fast: bool = False,
):
    spec = STRATEGY_REGISTRY[strategy_key]
    cfg = deepcopy(config)
    cfg.risk = _risk_config_for(strategy_key, config)
    cfg.walkforward = _walkforward_config_for(strategy_key, config)
    return run_walkforward(
        strategy_key, data, cfg, spec, regime=regime,
        adaptive_window=adaptive, fast=fast,
    )


def _cost_breakdown(trades_metrics: dict, initial_capital: float) -> dict:
    """거래비용 비중 추정 (메트릭 기반)."""
    total_return = trades_metrics.get("total_return_pct", 0) or 0
    gross_pnl = initial_capital * total_return / 100
    funding = trades_metrics.get("total_funding_pnl", 0) or 0
    slippage = trades_metrics.get("total_slippage_cost", 0) or 0
    return {
        "gross_pnl_est": round(gross_pnl, 2),
        "funding_pnl": funding,
        "slippage_cost": slippage,
    }


def _aggregate_oos_metrics(wf_result) -> dict:
    if not wf_result.folds:
        return {}
    keys = [
        "sharpe_ratio", "calmar_ratio", "total_return_pct", "max_drawdown_pct",
        "num_trades", "win_rate_pct", "profit_factor", "total_fees",
        "total_slippage_cost", "total_funding_pnl",
    ]
    out = {}
    traded = [f for f in wf_result.folds if f.oos_metrics.get("num_trades", 0) > 0]
    pool = traded if traded else wf_result.folds
    for k in keys:
        vals = [f.oos_metrics.get(k) for f in pool if f.oos_metrics.get(k) is not None]
        out[k] = round(float(np.mean(vals)), 2) if vals else None
    return out


def load_data(mode: str, limit: int) -> tuple[dict, dict, dict, object, int]:
    config = deepcopy(DEFAULT_CONFIG)
    if mode == "cached":
        from data.cache import load_market_bundle
        bundle = load_market_bundle(limit=limit)
        basis_data = bundle["basis"]
        funding_data = bundle["funding"]
        pair_data = bundle["pair"]
        btc_close = bundle["btc_close"]
        total_bars = len(btc_close)
    else:
        basis_data = build_market_data(mode, "basis", config, limit)
        funding_data = build_market_data(mode, "funding", config, limit)
        pair_data = build_market_data(mode, "pair", config, limit)
        btc_close = basis_data["BTC/USDT"]["spot_close"]
        total_bars = len(btc_close)

    return basis_data, funding_data, pair_data, btc_close, total_bars


def run_full_matrix(
    mode: str = "cached",
    limit: int = DEFAULT_DATA_BARS,
    fast: bool = False,
    strategies: list | None = None,
) -> dict:
    config = deepcopy(DEFAULT_CONFIG)
    if fast:
        config = apply_fast_mode(config)

    basis_data, funding_data, pair_data, btc_close, total_bars = load_data(mode, limit)
    momentum_data = build_market_data(mode, "momentum", config, limit)

    all_data = {
        "basis": basis_data,
        "pair": pair_data,
        "funding": funding_data,
        "momentum": momentum_data,
    }
    keys = strategies or list(all_data.keys())
    data_map = {k: all_data[k] for k in keys if k in all_data}

    regimes = {} if fast else classify_market_regimes(btc_close)

    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "mode": mode,
        "fast": fast,
        "data_period": [str(btc_close.index[0]), str(btc_close.index[-1])],
        "total_bars": total_bars,
        "strategies": list(data_map.keys()),
        "regime_criteria": (
            "1차: 90d rolling return bull>+15%, bear<-15%, else sideways (longest >=200 bars); "
            "2차 폴백: calendar tertile by mean 90d return"
        ),
        "regime_boundaries": {
            k: [str(v[0]), str(v[1])] for k, v in regimes.items()
        },
        "regimes": {},
        "full_period": {},
        "initial_capital": config.backtest.initial_capital,
    }

    for strategy_key, data in data_map.items():
        wf = _run_single_wf(strategy_key, data, config, fast=fast)
        report["full_period"][strategy_key] = {
            "summary": wf.summary,
            "oos_avg": _aggregate_oos_metrics(wf),
            "folds": [
                {
                    "is_sharpe": f.is_metrics.get("sharpe_ratio"),
                    "oos_sharpe": f.oos_metrics.get("sharpe_ratio"),
                    "is_calmar": f.is_metrics.get("calmar_ratio"),
                    "oos_calmar": f.oos_metrics.get("calmar_ratio"),
                    "overfit_warning": f.overfit_warning,
                    "overfit_reason": f.overfit_reason,
                }
                for f in wf.folds
            ],
        }

    if not fast:
        for regime_name, (start, end) in regimes.items():
            report["regimes"][regime_name] = {
                "period": [str(start), str(end)],
                "strategies": {},
            }
            for strategy_key, data in data_map.items():
                sliced = {sym: df.loc[start:end].copy() for sym, df in data.items()}
                if any(len(df) < 240 for df in sliced.values()):
                    report["regimes"][regime_name]["strategies"][strategy_key] = {"skipped": True}
                    continue
                wf = _run_single_wf(
                    strategy_key, sliced, config, regime=regime_name, adaptive=True,
                )
                report["regimes"][regime_name]["strategies"][strategy_key] = {
                    "summary": wf.summary,
                    "oos_avg": _aggregate_oos_metrics(wf),
                }

    return report


def _report_strategies(report: dict) -> list:
    return report.get("strategies") or list(report.get("full_period", {}).keys())


def _worst_regime(report: dict, strategy: str) -> tuple[str, dict]:
    best_worst = None
    worst_name = None
    for regime, info in report["regimes"].items():
        strat = info["strategies"].get(strategy, {})
        if strat.get("skipped"):
            continue
        sharpe = strat.get("oos_avg", {}).get("sharpe_ratio")
        if sharpe is None:
            continue
        if best_worst is None or sharpe < best_worst:
            best_worst = sharpe
            worst_name = regime
    return worst_name, report["regimes"].get(worst_name, {})


def render_markdown(report: dict) -> str:
    lines = [
        "# 백테스트 결과 요약 (BACKTEST_RESULTS)",
        "",
        f"생성 시각 (UTC): {report['generated_at']}",
        "",
        "## 1. 데이터 개요",
        "",
        f"- **기간**: {report['data_period'][0]} ~ {report['data_period'][1]}",
        f"- **총 bar 수**: {report['total_bars']} (4h 봉)",
        f"- **국면 구분 기준**: {report['regime_criteria']}",
        f"- **국면 경계**: {report.get('regime_boundaries', {})}",
        f"- **데이터 소스**: `{report['mode']}`" + (" (fast)" if report.get("fast") else ""),
        f"- **초기 자본**: ${report['initial_capital']:,.0f}",
        "",
        "## 2. 전략 × 국면별 성과 (OOS 평균)",
        "",
        "| 전략 | 국면 | Sharpe | Calmar | 총수익률(%) | MDD(%) | 거래횟수 | 승률(%) | Profit Factor |",
        "|------|------|--------|--------|-------------|--------|---------|---------|---------------|",
    ]

    regime_labels = {"bull": "상승장", "bear": "하락장", "sideways": "횡보장", "all": "전체"}
    for regime_key in ["bull", "bear", "sideways"]:
        if regime_key not in report["regimes"]:
            continue
        info = report["regimes"][regime_key]
        for strat in _report_strategies(report):
            s = info["strategies"].get(strat, {})
            if s.get("skipped"):
                lines.append(f"| {strat} | {regime_labels[regime_key]} | — | — | — | — | — | — | — |")
                continue
            m = s.get("oos_avg", {})
            lines.append(
                f"| {strat} | {regime_labels[regime_key]} | {m.get('sharpe_ratio', '—')} | "
                f"{m.get('calmar_ratio', '—')} | {m.get('total_return_pct', '—')} | "
                f"{m.get('max_drawdown_pct', '—')} | {m.get('num_trades', '—')} | "
                f"{m.get('win_rate_pct', '—')} | {m.get('profit_factor', '—')} |"
            )

    lines.extend([
        "",
        "### 전체 기간 (워크포워드 OOS 평균)",
        "",
        "| 전략 | Sharpe | Calmar | 총수익률(%) | MDD(%) | 거래횟수 | 승률(%) | Profit Factor |",
        "|------|--------|--------|-------------|--------|---------|---------|---------------|",
    ])
    for strat in _report_strategies(report):
        m = report["full_period"][strat].get("oos_avg", {})
        lines.append(
            f"| {strat} | {m.get('sharpe_ratio', '—')} | {m.get('calmar_ratio', '—')} | "
            f"{m.get('total_return_pct', '—')} | {m.get('max_drawdown_pct', '—')} | "
            f"{m.get('num_trades', '—')} | {m.get('win_rate_pct', '—')} | "
            f"{m.get('profit_factor', '—')} |"
        )

    lines.extend(["", "## 3. In-Sample vs Out-of-Sample 괴리 (과최적화 판단)", ""])
    for strat in _report_strategies(report):
        summ = report["full_period"][strat]["summary"]
        obj = DEFAULT_CONFIG.walkforward.objective
        lines.append(f"### {strat}")
        lines.append(
            f"- 평균 IS {obj}: {summ.get(f'avg_is_{obj}', '—')} | "
            f"평균 OOS {obj}: {summ.get(f'avg_oos_{obj}', '—')} | "
            f"괴리: {summ.get(f'avg_is_oos_gap_{obj}', '—')}"
        )
        warnings = sum(1 for f in report["full_period"][strat]["folds"] if f.get("overfit_warning"))
        lines.append(f"- 과최적화 경고 fold 수: {warnings} / {summ.get('num_folds', 0)}")
        lines.append(f"- discard_candidate: {summ.get('discard_candidate', False)}")
        if strat in WALKFORWARD_INCOMPATIBLE:
            lines.append(
                "- ⚠️ 이 전략은 전체 구간 거래 횟수가 극히 적어(개별 백테스트 기준 2건 내외) "
                "폴드 단위 워크포워드로는 통계적 유의성을 확보할 수 없다. 위 수치는 참고용."
            )
        lines.append("")

    lines.extend(["", "## 4. 최악 성과 국면 및 추정 원인", ""])
    reasons = {
        "basis": "장기 콘탱고/백워데이션에서 베이시스가 평균회귀하지 않고 발산",
        "pair": "공적분 붕괴 또는 단방향 추세로 스프레드 미회귀",
        "funding": "펀딩비 역전·마이너스 지속 또는 급등 시 숏 레그 청산 위험",
        "momentum": "횡보·전환 구간에서 진입/청산 반복(휩쏘)으로 손실 누적",
    }
    for strat in _report_strategies(report):
        worst_name, info = _worst_regime(report, strat)
        sharpe = None
        if worst_name and info:
            sharpe = info["strategies"].get(strat, {}).get("oos_avg", {}).get("sharpe_ratio")
        lines.append(
            f"- **{strat}**: 최악 국면 = {worst_name or 'N/A'} "
            f"(OOS Sharpe {sharpe}) — {reasons[strat]}"
        )

    lines.extend([
        "",
        "## 5. 전략별 명시적 실패 조건",
        "",
        "자세한 내용은 `docs/FAILURE_SCENARIOS.md` 참조.",
        "",
        "- **basis**: 장기 콘탱고/백워데이션, 반감기 붕괴, 펀딩비 역방향 누적",
        "- **pair**: 공적분 붕괴, 단방향 추세, 유동성 비대칭",
        "- **funding**: 펀딩비 장기 마이너스(약세·백워데이션), 거래비용 > 펀딩 수익, 급등 청산",
        "- **momentum**: 횡보장 휩쏘, 추세 반전 시 손절 지연, 저변동성 구간 다이렉션리스",
        "",
        "## 6. 거래비용 비중",
        "",
        "수수료는 엔진 fee_rate(0.04%)로 반영. 아래는 OOS 메트릭 기반 펀딩·슬리피지 합계.",
        "",
    ])
    for strat in _report_strategies(report):
        m = report["full_period"][strat].get("oos_avg", {})
        ret = m.get("total_return_pct") or 0
        fees = m.get("total_fees") or 0
        slip = m.get("total_slippage_cost") or 0
        fund = m.get("total_funding_pnl") or 0
        cost_sum = abs(fees) + abs(slip) - fund if fund < 0 else abs(fees) + abs(slip)
        lines.append(
            f"- **{strat}**: 순수익률 {ret}% | 수수료(평균) ${fees} | 슬리피지 ${slip} | "
            f"펀딩 PnL ${fund} | 비용합계 추정 ${round(cost_sum, 2)}"
        )

    lines.extend([
        "",
        "## 7. 실거래 투입 가능성 (솔직한 결론)",
        "",
    ])

    deployable = []
    for strat in _report_strategies(report):
        summ = report["full_period"][strat]["summary"]
        oos_sharpe = summ.get("avg_oos_sharpe")
        gap = summ.get("avg_is_oos_gap_sharpe")
        trades = summ.get("avg_oos_trades") or 0
        if (
            oos_sharpe is not None
            and oos_sharpe > 0.3
            and trades >= 1
            and not summ.get("discard_candidate")
            and (gap is None or abs(gap) < 1.0)
        ):
            deployable.append(strat)

    if deployable:
        lines.append(
            f"조건부 고려 가능: **{', '.join(deployable)}** — "
            "단, OOS Sharpe > 0 및 IS-OOS 괴리 < 1.0 조건만 충족. "
            "페이퍼 트레이딩·실행 인프라 검증 전 실거래 비권장."
        )
    else:
        lines.append(
            "**현재 백테스트 기준으로 실거래 투입을 권장하지 않는다.** "
            "OOS Sharpe가 0 이하이거나 IS-OOS 괴리가 크거나, 국면별 성과가 불안정하다."
        )

    lines.extend([
        "",
        "## 8. 개선 우선순위 3가지",
        "",
        "1. **실데이터 캐시 확장**: 펀딩비 히스토리 전구간 정합성, 다중 거래소 크로스체크",
        "2. **거래비용 모델 고도화**: 변동성 연동 슬리피지, 테이커/메이커 분리",
        "3. **레짐 필터**: 국면별 전략 on/off 또는 포지션 스케일링으로 최악 국면 노출 축소",
        "",
    ])
    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["synthetic", "cached", "live"], default="synthetic")
    parser.add_argument("--limit", type=int, default=DEFAULT_DATA_BARS)
    parser.add_argument("--strategy", choices=list(STRATEGY_REGISTRY.keys()))
    parser.add_argument(
        "--fast", action="store_true",
        help="빠른 확인: 작은 그리드, WF 1 fold, 국면별 생략",
    )
    parser.add_argument("--output", type=str, default=str(ROOT / "BACKTEST_RESULTS.md"))
    args = parser.parse_args()

    strategies = [args.strategy] if args.strategy else None
    report = run_full_matrix(
        mode=args.mode, limit=args.limit, fast=args.fast, strategies=strategies,
    )
    md = render_markdown(report)
    out = Path(args.output)
    if args.fast:
        out = out.with_name("BACKTEST_RESULTS_FAST.md")
    out.write_text(md, encoding="utf-8")

    json_out = ROOT / "reports" / f"backtest_matrix_{args.mode}{'_fast' if args.fast else ''}.json"
    json_out.parent.mkdir(exist_ok=True)
    json_out.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"저장: {out}")
    print(f"JSON: {json_out}")


if __name__ == "__main__":
    main()
