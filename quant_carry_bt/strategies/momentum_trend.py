"""
전략 D: 이동평균 크로스오버 기반 모멘텀/추세추종 (Momentum Trend Following)

아이디어 (회귀/공적분 미사용 — 순수 가격 추세):
  단기 EMA - 장기 EMA 를 ATR 로 정규화한 값을 "추세강도"로 정의한다.
  추세강도가 임계치를 넘으면 그 방향으로 순추세 베팅(outright)을 하고,
  추세가 약화되거나 ATR 배수 손절선에 닿으면 청산한다.

  추세강도 >> 0 (단기가 장기 위로 강하게 이탈) -> 롱
  추세강도 << 0 (단기가 장기 아래로 강하게 이탈) -> 숏
"""

import pandas as pd

from strategies.base import BaseStrategy, StrategyOutput, Signal
from utils.stats import average_true_range


class MomentumTrendStrategy(BaseStrategy):

    name = "momentum_trend"

    def __init__(self, config, symbol: str = "BTC/USDT"):
        super().__init__(config)
        self.symbol = symbol
        self._initial_state = {
            "in_position": False, "direction": 0,
            "entry_price": None, "entry_atr": None, "cooldown_remaining": 0,
        }
        self._state = dict(self._initial_state)

    def required_symbols(self) -> list:
        return [self.symbol]

    def warmup_period(self) -> int:
        cfg = self.config.momentum
        return max(cfg.slow_period, cfg.atr_period) + 10

    def generate_signal(self, market_data: dict) -> StrategyOutput:
        # 룩어헤드 없음: market_data 는 엔진이 iloc[:i+1] 로 잘라 전달 (미래 바 미포함)
        df = market_data[self.symbol]
        cfg = self.config.momentum
        current_ts = df.index[-1]

        fast_ema = df["close"].ewm(span=cfg.fast_period, adjust=False).mean()
        slow_ema = df["close"].ewm(span=cfg.slow_period, adjust=False).mean()
        atr = average_true_range(df, cfg.atr_period)

        price = float(df["close"].iloc[-1])
        current_atr = atr.iloc[-1]
        if pd.isna(current_atr) or current_atr <= 0:
            return StrategyOutput(current_ts, Signal.FLAT, 0.0, {"reason": "atr_unavailable"})
        current_atr = float(current_atr)
        atr_pct = current_atr / price
        trend_strength = float((fast_ema.iloc[-1] - slow_ema.iloc[-1]) / current_atr)

        meta = {
            "fast_ema": float(fast_ema.iloc[-1]),
            "slow_ema": float(slow_ema.iloc[-1]),
            "atr": current_atr,
            "atr_pct": atr_pct,
            "trend_strength": trend_strength,
            "stop_zscore": cfg.stop_strength_floor,
            "spread_std": atr_pct,
        }

        low_vol = atr_pct < cfg.min_atr_pct
        meta["low_vol_filtered"] = low_vol

        in_position = self._state.get("in_position", False)
        direction = self._state.get("direction", 0)

        # --- 청산 조건 우선 체크 ---
        if in_position:
            entry_price = self._state["entry_price"]
            entry_atr = self._state["entry_atr"]
            stop_price = (
                entry_price - cfg.atr_stop_mult * entry_atr if direction > 0
                else entry_price + cfg.atr_stop_mult * entry_atr
            )
            stopped = (direction > 0 and price <= stop_price) or (direction < 0 and price >= stop_price)
            if stopped:
                self._state.update(dict(self._initial_state))
                self._state["cooldown_remaining"] = cfg.cooldown_bars
                meta["stopped_out"] = True
                return StrategyOutput(current_ts, Signal.CLOSE, 0.0, meta)

            trend_faded = (
                (direction > 0 and trend_strength <= cfg.exit_strength)
                or (direction < 0 and trend_strength >= -cfg.exit_strength)
            )
            if trend_faded:
                self._state.update(dict(self._initial_state))
                self._state["cooldown_remaining"] = cfg.cooldown_bars
                return StrategyOutput(current_ts, Signal.CLOSE, 0.0, meta)

            # 포지션 유지
            return StrategyOutput(
                current_ts,
                Signal.LONG if direction > 0 else Signal.SHORT,
                float(direction),
                meta,
            )

        # --- 신규 진입 조건 ---
        cooldown_remaining = self._state.get("cooldown_remaining", 0)
        if cooldown_remaining > 0:
            self._state["cooldown_remaining"] = cooldown_remaining - 1
            meta["cooldown_remaining"] = cooldown_remaining
            return StrategyOutput(current_ts, Signal.FLAT, 0.0, meta)

        if low_vol:
            return StrategyOutput(current_ts, Signal.FLAT, 0.0, meta)

        if trend_strength >= cfg.entry_strength:
            self._state.update({
                "in_position": True, "direction": 1,
                "entry_price": price, "entry_atr": current_atr,
            })
            meta["entry_zscore"] = trend_strength
            return StrategyOutput(current_ts, Signal.LONG, 1.0, meta)

        if trend_strength <= -cfg.entry_strength:
            self._state.update({
                "in_position": True, "direction": -1,
                "entry_price": price, "entry_atr": current_atr,
            })
            meta["entry_zscore"] = trend_strength
            return StrategyOutput(current_ts, Signal.SHORT, -1.0, meta)

        return StrategyOutput(current_ts, Signal.FLAT, 0.0, meta)
