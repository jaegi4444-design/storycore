"""
전략 C: 펀딩비 캐리 트레이드 (델타 뉴트럴)

아이디어:
  현물 롱 + 무기한선물 숏 (펀딩비 양(+)일 때)으로 델타를 0에 가깝게 유지하고
  8시간마다 지급되는 펀딩비를 수취한다.
  펀딩비가 역전되거나 임계값 이하로 떨어지면 청산한다.

실패 조건 (docs/FAILURE_SCENARIOS.md 참조):
  - 펀딩비가 장기간 마이너스인 약세/백워데이션 국면 → 구조적 손실
  - 급등 시 숏 레그 청산(liquidation) 위험
  - 거래비용(수수료·슬리피지)이 낮은 펀딩 수익을 상쇄
"""

import numpy as np
import pandas as pd

from strategies.base import BaseStrategy, StrategyOutput, Signal


def annualize_funding(rate_per_8h: float) -> float:
    """8시간 펀딩비율 → 연환산 (3회/일 × 365일)"""
    return rate_per_8h * 3 * 365


class FundingCarryStrategy(BaseStrategy):

    name = "funding_carry"

    def __init__(self, config, symbol: str = "BTC/USDT"):
        super().__init__(config)
        self.symbol = symbol
        self._initial_state = {
            "in_position": False,
            "direction": 0,
            "entry_future_price": None,
        }
        self._state = dict(self._initial_state)

    def required_symbols(self) -> list:
        return [self.symbol]

    def warmup_period(self) -> int:
        return self.config.funding.funding_lookback + 5

    def _current_funding(self, df: pd.DataFrame) -> tuple[float, float]:
        """룩어헤드 없음: 마지막 바의 펀딩비만 사용."""
        rate = float(df["funding_rate"].iloc[-1]) if "funding_rate" in df.columns else 0.0
        return rate, annualize_funding(rate)

    def _liquidation_triggered(
        self,
        entry_price: float,
        current_price: float,
        direction: int,
    ) -> bool:
        """
        숏 레그 청산 위험 시뮬레이션 (엔진/리스크매니저 수정 없이 전략 내부 처리).
        레버리지 상한 이하에서 유지마진 돌파 시 강제 청산 시그널.
        """
        cfg = self.config.funding
        if entry_price <= 0 or direction == 0:
            return False

        leverage = cfg.max_leverage
        max_adverse = (1.0 / leverage) - cfg.maintenance_margin_rate
        if max_adverse <= 0:
            return False

        if direction < 0:
            adverse = (current_price - entry_price) / entry_price
        else:
            adverse = (entry_price - current_price) / entry_price

        return adverse >= max_adverse

    def generate_signal(self, market_data: dict) -> StrategyOutput:
        # 룩어헤드 없음: market_data 는 엔진이 iloc[:i+1] 로 잘라 전달 (미래 바 미포함)
        df = market_data[self.symbol]
        cfg = self.config.funding
        current_ts = df.index[-1]
        future_price = float(df["future_close"].iloc[-1])

        rate, ann_rate = self._current_funding(df)
        lookback = df["funding_rate"].tail(cfg.funding_lookback) if "funding_rate" in df.columns else pd.Series([0.0])
        funding_std = float(lookback.std()) if len(lookback) > 1 else 0.0001

        meta = {
            "funding_rate_8h": rate,
            "funding_annualized_pct": round(ann_rate * 100, 4),
            "spread_std": max(funding_std, cfg.min_stop_pct),
            "stop_zscore": cfg.stop_zscore,
            "hedge_ratio": 1.0,
        }

        in_position = self._state.get("in_position", False)
        direction = self._state.get("direction", 0)
        entry_price = self._state.get("entry_future_price")

        if in_position and entry_price is not None:
            if self._liquidation_triggered(entry_price, future_price, direction):
                self._state.update({"in_position": False, "direction": 0, "entry_future_price": None})
                meta["liquidation"] = True
                return StrategyOutput(current_ts, Signal.CLOSE, 0.0, meta)

            exit_due_funding = False
            if direction < 0:
                exit_due_funding = ann_rate < cfg.exit_annualized_pct or rate <= 0
            else:
                exit_due_funding = ann_rate > -cfg.exit_annualized_pct or rate >= 0

            if exit_due_funding:
                self._state.update({"in_position": False, "direction": 0, "entry_future_price": None})
                meta["exit_reason"] = "funding_threshold"
                return StrategyOutput(current_ts, Signal.CLOSE, 0.0, meta)

            return StrategyOutput(
                current_ts,
                Signal.LONG if direction > 0 else Signal.SHORT,
                float(direction),
                meta,
            )

        if ann_rate >= cfg.entry_annualized_pct:
            self._state.update({
                "in_position": True,
                "direction": -1,
                "entry_future_price": future_price,
            })
            meta["entry_zscore"] = 1.5
            meta["entry_reason"] = "positive_funding_carry"
            return StrategyOutput(current_ts, Signal.SHORT, -1.0, meta)

        if cfg.allow_reverse_carry and ann_rate <= -cfg.entry_annualized_pct:
            self._state.update({
                "in_position": True,
                "direction": 1,
                "entry_future_price": future_price,
            })
            meta["entry_zscore"] = 1.5
            meta["entry_reason"] = "negative_funding_carry"
            return StrategyOutput(current_ts, Signal.LONG, 1.0, meta)

        return StrategyOutput(current_ts, Signal.FLAT, 0.0, meta)
