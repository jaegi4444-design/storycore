"""
전략 B: 코인 페어 트레이딩 (Statistical Arbitrage / Cointegration Pairs)

아이디어:
  BTC와 공적분 관계에 있는 알트코인을 찾아 헤지비율(hedge ratio)로
  스프레드를 구성한다. 스프레드의 z-score가 임계값을 벗어나면
  스프레드 축소(회귀)에 베팅하여 한쪽은 롱, 다른 쪽은 숏 포지션을 취한다.

  스프레드 = BTC - hedge_ratio * ALT
  z-score >> 0  -> BTC 고평가/ALT 저평가 -> BTC 숏 + ALT 롱
  z-score << 0  -> BTC 저평가/ALT 고평가 -> BTC 롱 + ALT 숏
"""

import pandas as pd
import numpy as np

from strategies.base import BaseStrategy, StrategyOutput, Signal
from utils.stats import rolling_zscore, engle_granger_test


class PairTradingStrategy(BaseStrategy):

    name = "pair_trading"

    def __init__(self, config, base_symbol: str = "BTC/USDT", quote_symbol: str = "ETH/USDT"):
        super().__init__(config)
        self.base_symbol = base_symbol
        self.quote_symbol = quote_symbol
        self._initial_state = {
            "in_position": False,
            "direction": 0,
            "hedge_ratio": None,
            "bars_since_check": 0,
        }
        self._state = dict(self._initial_state)

    def required_symbols(self) -> list:
        return [self.base_symbol, self.quote_symbol]

    def warmup_period(self) -> int:
        return self.config.pair.lookback_period + 10

    def generate_signal(self, market_data: dict) -> StrategyOutput:
        # 룩어헤드 없음: market_data 는 엔진이 iloc[:i+1] 로 잘라 전달 (미래 바 미포함)
        cfg = self.config.pair
        base_df = market_data[self.base_symbol]
        quote_df = market_data[self.quote_symbol]

        base_close = base_df["close"].tail(cfg.lookback_period)
        quote_close = quote_df["close"].tail(cfg.lookback_period)
        current_ts = base_df.index[-1]

        need_recheck = (
            self._state["hedge_ratio"] is None
            or self._state["bars_since_check"] >= cfg.recheck_coint_every
        )

        if need_recheck:
            # 공적분 검정: lookback_period 윈도우만 사용 (미래 데이터 미참조)
            result = engle_granger_test(
                np.log(base_close), np.log(quote_close),
                pvalue_threshold=cfg.coint_pvalue_threshold,
            )
            self._state["hedge_ratio"] = result["hedge_ratio"]
            self._state["is_cointegrated"] = result["is_cointegrated"]
            self._state["bars_since_check"] = 0
        else:
            self._state["bars_since_check"] += 1

        hedge_ratio = self._state["hedge_ratio"]
        is_cointegrated = self._state.get("is_cointegrated", False)

        spread = np.log(base_close) - hedge_ratio * np.log(quote_close)
        z = rolling_zscore(spread, min(cfg.lookback_period, len(spread)))  # rolling: 룩어헤드 없음
        current_z = z.iloc[-1] if len(z) else np.nan
        spread_std = float(spread.std()) if len(spread) > 1 else 0.01

        meta = {
            "hedge_ratio": float(hedge_ratio) if hedge_ratio is not None else None,
            "zscore": float(current_z) if pd.notna(current_z) else None,
            "is_cointegrated": bool(is_cointegrated),
            "pair": f"{self.base_symbol}/{self.quote_symbol}",
            "spread_std": spread_std,
            "stop_zscore": cfg.stop_zscore,
        }

        if pd.isna(current_z) or not is_cointegrated:
            return StrategyOutput(current_ts, Signal.FLAT, 0.0, meta)

        in_position = self._state.get("in_position", False)
        direction = self._state.get("direction", 0)

        if in_position:
            if abs(current_z) <= cfg.exit_zscore:
                self._state.update({"in_position": False, "direction": 0})
                return StrategyOutput(current_ts, Signal.CLOSE, 0.0, meta)
            if abs(current_z) >= cfg.stop_zscore or not is_cointegrated:
                self._state.update({"in_position": False, "direction": 0})
                meta["stopped_out"] = True
                return StrategyOutput(current_ts, Signal.CLOSE, 0.0, meta)
            return StrategyOutput(
                current_ts,
                Signal.LONG if direction > 0 else Signal.SHORT,
                float(direction),
                meta,
            )

        if current_z >= cfg.entry_zscore:
            self._state.update({"in_position": True, "direction": -1})
            meta["entry_zscore"] = float(current_z)
            return StrategyOutput(current_ts, Signal.SHORT, -1.0, meta)

        if current_z <= -cfg.entry_zscore:
            self._state.update({"in_position": True, "direction": 1})
            meta["entry_zscore"] = float(current_z)
            return StrategyOutput(current_ts, Signal.LONG, 1.0, meta)

        return StrategyOutput(current_ts, Signal.FLAT, 0.0, meta)
