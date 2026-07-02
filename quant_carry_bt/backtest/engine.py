"""
백테스트 엔진.

BaseStrategy 인터페이스만 지키면 어떤 전략이든 그대로 꽂아서 실행할 수 있다.
슬리피지·펀딩비·z-score 기반 손절을 손익 계산에 반영한다.
"""

import logging
import numpy as np
import pandas as pd
from dataclasses import dataclass, field

from strategies.base import Signal
from risk.risk_manager import RiskManager, AccountState
from utils.stats import calmar_ratio

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp = None
    direction: int = 0
    entry_price: float = 0.0
    exit_price: float = None
    qty: float = 0.0
    pnl: float = 0.0
    fees: float = 0.0
    slippage: float = 0.0
    funding_pnl: float = 0.0
    hedge_entry_price: float = None
    hedge_exit_price: float = None
    hedge_qty: float = 0.0
    hedge_pnl: float = 0.0


@dataclass
class BacktestResult:
    equity_curve: pd.Series
    trades: list
    metrics: dict = field(default_factory=dict)


class BacktestEngine:

    def __init__(self, strategy, backtest_config, risk_config, price_symbol: str,
                 price_field: str = "future_close", hedge_symbol: str = None,
                 hedge_field: str = "close"):
        self.strategy = strategy
        self.cfg = backtest_config
        self.risk_manager = RiskManager(risk_config)
        self.price_symbol = price_symbol
        self.price_field = price_field
        self.hedge_symbol = hedge_symbol
        self.hedge_field = hedge_field
        self._slippage_frac = self.cfg.slippage_bps / 10_000.0

    def _apply_slippage(self, price: float, direction: int, is_entry: bool) -> float:
        """불리한 방향으로 슬리피지 적용 (진입/청산 모두)"""
        slip = self._slippage_frac
        if is_entry:
            return price * (1 + slip * direction)
        return price * (1 - slip * direction)

    def _get_funding_rate(self, window: dict, ts: pd.Timestamp) -> float:
        df = window.get(self.price_symbol)
        if df is None or "funding_rate" not in df.columns:
            return 0.0
        rate = df["funding_rate"].iloc[-1]
        return float(rate) if pd.notna(rate) else 0.0

    def _should_settle_funding(self, prev_ts: pd.Timestamp, curr_ts: pd.Timestamp) -> bool:
        hours = (curr_ts - prev_ts).total_seconds() / 3600.0
        return hours >= self.cfg.funding_interval_hours

    def _funding_accrual(
        self,
        prev_ts: pd.Timestamp,
        curr_ts: pd.Timestamp,
        rate: float,
        notional: float,
        direction: int,
    ) -> float:
        """8h 펀딩 주기에 비례하여 바 간격만큼 펀딩 손익을 누적한다."""
        hours = (curr_ts - prev_ts).total_seconds() / 3600.0
        if hours <= 0:
            return 0.0
        fraction = hours / self.cfg.funding_interval_hours
        return -direction * notional * rate * fraction

    def run(self, market_data: dict) -> BacktestResult:
        self.strategy.reset()
        self.risk_manager.reset_daily()

        any_symbol = next(iter(market_data))
        timestamps = market_data[any_symbol].index
        warmup = self.strategy.warmup_period()

        equity = self.cfg.initial_capital
        equity_curve = []
        trades = []
        open_trade = None
        account = AccountState(equity=equity)
        prev_ts = None

        for i in range(warmup, len(timestamps)):
            window = {sym: df.iloc[: i + 1] for sym, df in market_data.items()}
            ts = timestamps[i]
            price = window[self.price_symbol][self.price_field].iloc[-1]

            account = self.risk_manager.roll_daily(account, ts.date())

            output = self.strategy.generate_signal(window)

            hedge_price = None
            if self.hedge_symbol is not None:
                hedge_price = window[self.hedge_symbol][self.hedge_field].iloc[-1]

            # --- 펀딩비 정산 (보유 중, 8h 주기에 비례 누적) ---
            if open_trade is not None and prev_ts is not None:
                rate = self._get_funding_rate(window, ts)
                notional = open_trade.entry_price * open_trade.qty
                funding = self._funding_accrual(prev_ts, ts, rate, notional, open_trade.direction)
                if funding != 0.0:
                    open_trade.funding_pnl += funding
                    equity += funding
                    account.daily_pnl += funding

            # --- 청산 처리 ---
            if output.signal == Signal.CLOSE and open_trade is not None:
                exit_price = self._apply_slippage(price, open_trade.direction, is_entry=False)
                gross = (exit_price - open_trade.entry_price) * open_trade.direction * open_trade.qty
                fee = exit_price * open_trade.qty * self.cfg.fee_rate
                slip_cost = abs(exit_price - price) * open_trade.qty
                open_trade.exit_time = ts
                open_trade.exit_price = exit_price
                open_trade.fees += fee
                open_trade.slippage += slip_cost

                hedge_pnl = 0.0
                if open_trade.hedge_entry_price is not None and hedge_price is not None:
                    hedge_exit = self._apply_slippage(hedge_price, -open_trade.direction, is_entry=False)
                    hedge_dir = -open_trade.direction
                    hedge_gross = (hedge_exit - open_trade.hedge_entry_price) * hedge_dir * open_trade.hedge_qty
                    hedge_fee = hedge_exit * open_trade.hedge_qty * self.cfg.fee_rate
                    open_trade.hedge_exit_price = hedge_exit
                    open_trade.hedge_pnl = hedge_gross - hedge_fee
                    open_trade.fees += hedge_fee
                    open_trade.slippage += abs(hedge_exit - hedge_price) * open_trade.hedge_qty
                    hedge_pnl = open_trade.hedge_pnl

                open_trade.pnl = gross - fee + hedge_pnl + open_trade.funding_pnl
                trades.append(open_trade)

                equity += gross - fee + hedge_pnl
                account.daily_pnl += gross - fee + hedge_pnl
                account.open_positions = max(0, account.open_positions - 1)
                open_trade = None

            # --- 신규 진입 처리 ---
            elif output.signal in (Signal.LONG, Signal.SHORT) and open_trade is None:
                if self.risk_manager.can_open_new_position(account):
                    direction = 1 if output.signal == Signal.LONG else -1
                    entry_z = output.meta.get("entry_zscore") or abs(output.meta.get("zscore", 2.0))
                    spread_std = output.meta.get("spread_std") or 0.01
                    stop_z = output.meta.get("stop_zscore", self.risk_manager.cfg.stop_loss_zscore)

                    stop_price = self.risk_manager.compute_stop_price(
                        price, direction, entry_z, stop_z, spread_std,
                    )
                    qty = self.risk_manager.position_size(account, price, stop_price)
                    if qty <= 0:
                        continue

                    entry_price = self._apply_slippage(price, direction, is_entry=True)
                    entry_fee = entry_price * qty * self.cfg.fee_rate
                    slip_cost = abs(entry_price - price) * qty

                    open_trade = Trade(
                        entry_time=ts, direction=direction,
                        entry_price=entry_price, qty=qty, fees=entry_fee, slippage=slip_cost,
                    )

                    if self.hedge_symbol is not None and hedge_price is not None:
                        hedge_ratio = output.meta.get("hedge_ratio") or 1.0
                        hedge_qty = qty * abs(hedge_ratio) * (entry_price / hedge_price)
                        hedge_entry = self._apply_slippage(hedge_price, -direction, is_entry=True)
                        hedge_fee = hedge_entry * hedge_qty * self.cfg.fee_rate
                        open_trade.hedge_entry_price = hedge_entry
                        open_trade.hedge_qty = hedge_qty
                        open_trade.fees += hedge_fee
                        open_trade.slippage += abs(hedge_entry - hedge_price) * hedge_qty
                        equity -= hedge_fee

                    equity -= entry_fee
                    account.open_positions += 1

            # --- 보유중 미실현 손익 반영 ---
            unrealized = 0.0
            if open_trade is not None:
                unrealized = (price - open_trade.entry_price) * open_trade.direction * open_trade.qty
                if open_trade.hedge_entry_price is not None and hedge_price is not None:
                    hedge_dir = -open_trade.direction
                    unrealized += (hedge_price - open_trade.hedge_entry_price) * hedge_dir * open_trade.hedge_qty

            equity_curve.append((ts, equity + unrealized))
            prev_ts = ts

        if open_trade is not None:
            last_price = market_data[self.price_symbol][self.price_field].iloc[-1]
            exit_price = self._apply_slippage(last_price, open_trade.direction, is_entry=False)
            gross = (exit_price - open_trade.entry_price) * open_trade.direction * open_trade.qty
            open_trade.exit_time = timestamps[-1]
            open_trade.exit_price = exit_price
            hedge_pnl = 0.0
            if open_trade.hedge_entry_price is not None and self.hedge_symbol is not None:
                last_hedge_price = market_data[self.hedge_symbol][self.hedge_field].iloc[-1]
                hedge_exit = self._apply_slippage(last_hedge_price, -open_trade.direction, is_entry=False)
                hedge_dir = -open_trade.direction
                hedge_pnl = (hedge_exit - open_trade.hedge_entry_price) * hedge_dir * open_trade.hedge_qty
                open_trade.hedge_exit_price = hedge_exit
                open_trade.hedge_pnl = hedge_pnl
            open_trade.pnl = gross - open_trade.fees + hedge_pnl + open_trade.funding_pnl
            trades.append(open_trade)

        curve = pd.Series(dict(equity_curve))
        result = BacktestResult(equity_curve=curve, trades=trades)
        result.metrics = compute_metrics(curve, trades, self.cfg.initial_capital)
        return result


def compute_metrics(equity_curve: pd.Series, trades: list, initial_capital: float) -> dict:
    if len(equity_curve) < 2:
        return {}

    returns = equity_curve.pct_change().dropna()
    total_return = equity_curve.iloc[-1] / initial_capital - 1

    periods_per_year = 6 * 365
    ann_return = (1 + total_return) ** (periods_per_year / len(equity_curve)) - 1 if len(equity_curve) > 0 else 0
    ann_vol = returns.std() * np.sqrt(periods_per_year) if returns.std() > 0 else np.nan
    sharpe = ann_return / ann_vol if ann_vol and ann_vol > 0 else np.nan
    if len(trades) < 2 or (returns.std() is not np.nan and returns.std() < 1e-8):
        sharpe = np.nan

    running_max = equity_curve.cummax()
    drawdown = equity_curve / running_max - 1
    max_dd = drawdown.min()
    calmar = calmar_ratio(ann_return, max_dd)

    wins = [t for t in trades if t.pnl > 0]
    losses = [t for t in trades if t.pnl <= 0]
    win_rate = len(wins) / len(trades) if trades else np.nan
    avg_win = np.mean([t.pnl for t in wins]) if wins else 0
    avg_loss = np.mean([t.pnl for t in losses]) if losses else 0
    profit_factor = (
        sum(t.pnl for t in wins) / abs(sum(t.pnl for t in losses))
        if losses and sum(t.pnl for t in losses) != 0 else np.nan
    )

    total_funding = sum(getattr(t, "funding_pnl", 0) for t in trades)
    total_slippage = sum(getattr(t, "slippage", 0) for t in trades)
    total_fees = sum(getattr(t, "fees", 0) for t in trades)

    return {
        "total_return_pct": round(total_return * 100, 2),
        "annualized_return_pct": round(ann_return * 100, 2),
        "annualized_vol_pct": round(ann_vol * 100, 2) if pd.notna(ann_vol) else None,
        "sharpe_ratio": round(sharpe, 2) if pd.notna(sharpe) else None,
        "calmar_ratio": round(calmar, 2) if pd.notna(calmar) else None,
        "max_drawdown_pct": round(max_dd * 100, 2),
        "num_trades": len(trades),
        "win_rate_pct": round(win_rate * 100, 2) if pd.notna(win_rate) else None,
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "profit_factor": round(profit_factor, 2) if pd.notna(profit_factor) else None,
        "total_funding_pnl": round(total_funding, 2),
        "total_slippage_cost": round(total_slippage, 2),
        "total_fees": round(total_fees, 2),
    }


def objective_score(metrics: dict, objective: str = "sharpe") -> float:
    """파라미터 최적화 목적함수. total_return 은 사용하지 않는다."""
    if objective == "calmar":
        val = metrics.get("calmar_ratio")
    else:
        val = metrics.get("sharpe_ratio")
    return float(val) if val is not None and not np.isnan(val) else -np.inf
