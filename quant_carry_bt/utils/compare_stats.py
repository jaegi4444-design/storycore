"""
자체구현 vs statsmodels 공적분/ADF 결과 비교 리포트 생성기.

실행:
    py utils/compare_stats.py
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from data.loader import SyntheticDataLoader
from utils.stats import engle_granger_test, adf_test
from utils.stats_legacy import engle_granger_test_legacy, adf_test_stat, eg_pvalue_approx


def run_comparison(n_samples: int = 500) -> dict:
    loader = SyntheticDataLoader(seed=42)
    pair = loader.get_correlated_pair("4h", n_samples)
    btc = np.log(pair["BTC/USDT"]["close"])
    eth = np.log(pair["ETH/USDT"]["close"])

    legacy = engle_granger_test_legacy(btc, eth)
    modern = engle_granger_test(btc, eth)

    legacy_adf_t = adf_test_stat(legacy["spread"].values)
    legacy_adf_p = eg_pvalue_approx(legacy_adf_t)
    modern_adf = adf_test(legacy["spread"].values)

    report = {
        "n_samples": n_samples,
        "engle_granger": {
            "legacy": {
                "hedge_ratio": round(legacy["hedge_ratio"], 6),
                "adf_tstat": round(float(legacy["adf_tstat"]), 4),
                "coint_pvalue": round(float(legacy["coint_pvalue"]), 6),
                "is_cointegrated": bool(legacy["is_cointegrated"]),
            },
            "statsmodels": {
                "hedge_ratio": round(modern["hedge_ratio"], 6),
                "adf_tstat": round(float(modern["adf_tstat"]), 4),
                "coint_pvalue": round(float(modern["coint_pvalue"]), 6),
                "is_cointegrated": bool(modern["is_cointegrated"]),
            },
            "delta": {
                "hedge_ratio": round(modern["hedge_ratio"] - legacy["hedge_ratio"], 6),
                "adf_tstat": round(float(modern["adf_tstat"]) - float(legacy["adf_tstat"]), 4),
                "coint_pvalue": round(float(modern["coint_pvalue"]) - float(legacy["coint_pvalue"]), 6),
                "cointegration_decision_changed": bool(legacy["is_cointegrated"] != modern["is_cointegrated"]),
            },
        },
        "adf_on_spread": {
            "legacy_tstat": round(float(legacy_adf_t), 4),
            "legacy_pvalue_approx": round(float(legacy_adf_p), 6),
            "statsmodels_tstat": round(float(modern_adf["adf_tstat"]), 4),
            "statsmodels_pvalue": round(float(modern_adf["adf_pvalue"]), 6),
            "pvalue_delta": round(float(modern_adf["adf_pvalue"]) - float(legacy_adf_p), 6),
        },
        "notes": [
            "레거시 p-value 는 MacKinnon 근사 임계값 보간으로 부정확할 수 있다.",
            "statsmodels coint 는 Engle-Granger 전용 임계값을 사용한다.",
            "공적분 판정(is_cointegrated)이 달라지면 페어 트레이딩 진입 빈도가 변한다.",
        ],
    }
    return report


if __name__ == "__main__":
    report = run_comparison()
    out_path = ROOT / "reports" / "stats_comparison.json"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\n저장: {out_path}")
