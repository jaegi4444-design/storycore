"""
리스크 관리 모듈.
전략에서 나온 시그널을 실제 주문 사이즈로 변환하고,
계좌 단위의 손실 한도/레버리지/동시 포지션 수를 강제한다.
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AccountState:
    equity: float
    daily_pnl: float = 0.0
    open_positions: int = 0
    current_date: object = None


class RiskManager:

    def __init__(self, risk_config):
        self.cfg = risk_config
        self._trading_halted = False
        self._halt_reason: str | None = None

    def daily_loss_breach(self, account: AccountState) -> bool:
        loss_pct = -account.daily_pnl / account.equity if account.equity > 0 else 0
        return loss_pct >= self.cfg.max_daily_loss_pct

    def can_open_new_position(self, account: AccountState) -> bool:
        if self._trading_halted:
            logger.warning("신규 진입 차단: %s", self._halt_reason or "trading_halted")
            return False
        if self.daily_loss_breach(account):
            self._trading_halted = True
            self._halt_reason = (
                f"daily_loss_limit ({self.cfg.max_daily_loss_pct:.1%}) breached"
            )
            logger.warning("일일 손실 한도 도달 — 신규 진입 중단: daily_pnl=%.2f", account.daily_pnl)
            return False
        if account.open_positions >= self.cfg.max_concurrent_positions:
            logger.info(
                "동시 포지션 한도 도달: %d/%d",
                account.open_positions,
                self.cfg.max_concurrent_positions,
            )
            return False
        return True

    def compute_stop_price(
        self,
        entry_price: float,
        direction: int,
        entry_zscore: float,
        stop_zscore: float,
        spread_std: float,
    ) -> float:
        """
        z-score 기반 구조적 손절가 (단일 정책).
        진입 z-score 에서 stop_zscore 까지의 z 거리를 스프레드 표준편차로 환산해
        가격 손절폭으로 변환한다. 최소 손절폭(min_stop_pct) 보장.
        """
        z_distance = max(abs(stop_zscore) - abs(entry_zscore), 0.5)
        pct_move = max(z_distance * spread_std, self.cfg.min_stop_pct)
        if direction > 0:
            return entry_price * (1 - pct_move)
        return entry_price * (1 + pct_move)

    def position_size(self, account: AccountState, entry_price: float, stop_price: float) -> float:
        risk_amount = account.equity * self.cfg.max_risk_per_trade_pct
        price_distance = abs(entry_price - stop_price)
        if price_distance <= 0:
            return 0.0

        raw_qty = risk_amount / price_distance
        max_notional = account.equity * self.cfg.max_leverage
        max_qty_by_leverage = max_notional / entry_price
        return min(raw_qty, max_qty_by_leverage)

    def reset_daily(self):
        self._trading_halted = False
        self._halt_reason = None

    def roll_daily(self, account: AccountState, new_date) -> AccountState:
        """일자 변경 시 daily_pnl 리셋 (워크포워드/백테스트 공통)"""
        if account.current_date is not None and new_date != account.current_date:
            if self._trading_halted:
                logger.info("새 거래일 시작 — 일일 손실 한도 리셋 (이전: %s)", self._halt_reason)
            account.daily_pnl = 0.0
            self.reset_daily()
        account.current_date = new_date
        return account
