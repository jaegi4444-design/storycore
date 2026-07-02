"""
전략 A: 스팟-선물 베이시스 평균회귀 (Basis Mean Reversion)

아이디어:
  무기한 선물가 - 현물가 (+ 펀딩비 가중) = 베이시스
  베이시스가 롤링 평균 대비 과도하게 벌어지면(z-score 초과)
  차익거래자들의 유입으로 평균에 회귀할 것이라는 가정 하에
  반대 방향 포지션을 취한다.

  베이시스 >> 0 (선물이 현물보다 비쌈, 콘탱고 과열) -> 선물 숏
  베이시스 << 0 (선물이 현물보다 쌈, 백워데이션 과열)  -> 선물 롱
"""

import pandas as pd
import numpy as np

from strategies.base import BaseStrategy, StrategyOutput, Signal
from utils.stats import rolling_zscore, half_life


class BasisMeanReversionStrategy(BaseStrategy):

    name = "basis_mean_reversion"

    def __init__(self, config, symbol: str = "BTC/USDT"):
        super().__init__(config)
        self.symbol = symbol
        self._initial_state = {"in_position": False, "direction": 0}
        self._state = dict(self._initial_state)

    def required_symbols(self) -> list:
        # 선물 심볼과 현물 심볼 둘 다 필요
        return [self.symbol]

    def warmup_period(self) -> int:
        return self.config.basis.lookback_period + 10

    def _compute_basis(self, df: pd.DataFrame) -> pd.Series:
        """
        df 는 다음 컬럼을 포함해야 한다:
        'spot_close', 'future_close', 'funding_rate'
        룩어헤드 없음: 현재 바까지의 종가/펀딩비만 사용.
        """
        raw_basis = (df["future_close"] - df["spot_close"]) / df["spot_close"]
        funding_component = df["funding_rate"].fillna(0.0)
        w = self.config.basis.funding_weight
        return raw_basis + w * funding_component

    def generate_signal(self, market_data: dict) -> StrategyOutput:
        # 룩어헤드 없음: market_data 는 엔진이 iloc[:i+1] 로 잘라 전달 (미래 바 미포함)
        df = market_data[self.symbol]
        cfg = self.config.basis

        basis = self._compute_basis(df)
        z = rolling_zscore(basis, cfg.lookback_period)  # rolling: 현재 바 포함, 미래 미포함
        current_z = z.iloc[-1]
        current_ts = df.index[-1]
        basis_std = float(basis.tail(cfg.lookback_period).std()) if len(basis) >= cfg.lookback_period else 0.01

        hl = half_life(basis.tail(cfg.lookback_period))
        tradable = cfg.min_half_life <= hl <= cfg.max_half_life

        meta = {
            "basis": float(basis.iloc[-1]),
            "zscore": float(current_z) if pd.notna(current_z) else None,
            "half_life": float(hl) if np.isfinite(hl) else None,
            "tradable_regime": bool(tradable),
            "spread_std": basis_std,
            "stop_zscore": cfg.stop_zscore,
        }

        if pd.isna(current_z) or not tradable:
            return StrategyOutput(current_ts, Signal.FLAT, 0.0, meta)

        in_position = self._state.get("in_position", False)
        direction = self._state.get("direction", 0)

        # --- 청산 조건 우선 체크 ---
        if in_position:
            if abs(current_z) <= cfg.exit_zscore:
                self._state.update({"in_position": False, "direction": 0})
                return StrategyOutput(current_ts, Signal.CLOSE, 0.0, meta)
            if abs(current_z) >= cfg.stop_zscore:
                self._state.update({"in_position": False, "direction": 0})
                meta["stopped_out"] = True
                return StrategyOutput(current_ts, Signal.CLOSE, 0.0, meta)
            # 포지션 유지
            return StrategyOutput(
                current_ts,
                Signal.LONG if direction > 0 else Signal.SHORT,
                float(direction),
                meta,
            )

        # --- 신규 진입 조건 ---
        if current_z >= cfg.entry_zscore:
            self._state.update({"in_position": True, "direction": -1})
            meta["entry_zscore"] = float(current_z)
            return StrategyOutput(current_ts, Signal.SHORT, -1.0, meta)

        if current_z <= -cfg.entry_zscore:
            self._state.update({"in_position": True, "direction": 1})
            meta["entry_zscore"] = float(current_z)
            return StrategyOutput(current_ts, Signal.LONG, 1.0, meta)

        return StrategyOutput(current_ts, Signal.FLAT, 0.0, meta)
