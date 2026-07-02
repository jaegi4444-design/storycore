"""
데이터 로더.

두 가지 모드를 지원한다:
1. LiveDataLoader   : ccxt 로 실제 거래소에서 OHLCV/펀딩비 수집 (네트워크 필요)
2. SyntheticDataLoader : 네트워크 없이 전략/백테스트 엔진을 검증하기 위한
                          합성 데이터 생성기 (개발/CI/오프라인 테스트용)
"""

from abc import ABC, abstractmethod
import numpy as np
import pandas as pd


class BaseDataLoader(ABC):
    @abstractmethod
    def get_ohlcv(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        ...

    @abstractmethod
    def get_spot_future_pair(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        """basis 전략용: spot_close, future_close, funding_rate 컬럼을 가진 DataFrame"""
        ...


def _to_spot_symbol(symbol: str) -> str:
    """BTC/USDT:USDT -> BTC/USDT 등 선물 표기를 현물 표기로 정규화"""
    return symbol.split(":")[0]


def _to_future_symbol(symbol: str) -> str:
    """BTC/USDT -> BTC/USDT:USDT (Binance perpetual)"""
    if ":" in symbol:
        return symbol
    return f"{symbol}:USDT"


class LiveDataLoader(BaseDataLoader):
    """ccxt 기반 실거래소 데이터 로더 (Binance Futures + Spot 분리)"""

    def __init__(self, exchange_config):
        import ccxt

        self.cfg = exchange_config
        exchange_class = getattr(ccxt, exchange_config.exchange_id)

        self.future_exchange = exchange_class({
            "enableRateLimit": True,
            "options": {"defaultType": exchange_config.market_type},
        })
        self.spot_exchange = exchange_class({
            "enableRateLimit": True,
            "options": {"defaultType": "spot"},
        })

        if exchange_config.testnet and hasattr(self.future_exchange, "set_sandbox_mode"):
            self.future_exchange.set_sandbox_mode(True)
            if hasattr(self.spot_exchange, "set_sandbox_mode"):
                self.spot_exchange.set_sandbox_mode(True)

    def _fetch_ohlcv_paginated(self, exchange, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        """Binance 1회 1000건 제한을 우회하기 위한 페이지네이션"""
        batch = min(limit, 1000)
        ms_per_bar = exchange.parse_timeframe(timeframe) * 1000
        since = exchange.milliseconds() - (limit * ms_per_bar)
        all_rows = []

        while len(all_rows) < limit:
            chunk = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=batch)
            if not chunk:
                break
            all_rows.extend(chunk)
            since = chunk[-1][0] + 1
            if len(chunk) < batch:
                break

        all_rows = all_rows[-limit:]
        df = pd.DataFrame(all_rows, columns=["ts", "open", "high", "low", "close", "volume"])
        df["ts"] = pd.to_datetime(df["ts"], unit="ms")
        return df.drop_duplicates("ts").set_index("ts")

    def get_ohlcv(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        future_symbol = _to_future_symbol(symbol)
        return self._fetch_ohlcv_paginated(self.future_exchange, future_symbol, timeframe, limit)

    def get_spot_ohlcv(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        spot_symbol = _to_spot_symbol(symbol)
        return self._fetch_ohlcv_paginated(self.spot_exchange, spot_symbol, timeframe, limit)

    def get_funding_rate_history(self, symbol: str, limit: int) -> pd.Series:
        future_symbol = _to_future_symbol(symbol)
        batch = 1000
        ms_per_funding = 8 * 3600 * 1000
        since = self.future_exchange.milliseconds() - (limit * ms_per_funding)
        all_rows = []

        while len(all_rows) < limit:
            chunk = self.future_exchange.fetch_funding_rate_history(
                future_symbol, since=since, limit=min(batch, limit - len(all_rows)),
            )
            if not chunk:
                break
            all_rows.extend(chunk)
            since = chunk[-1]["timestamp"] + 1
            if len(chunk) < batch:
                break

        all_rows = all_rows[-limit:]
        s = pd.Series(
            {pd.to_datetime(r["timestamp"], unit="ms"): r["fundingRate"] for r in all_rows}
        )
        return s.sort_index()

    def get_spot_future_pair(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        future_df = self.get_ohlcv(symbol, timeframe, limit)
        spot_df = self.get_spot_ohlcv(symbol, timeframe, limit)
        funding = self.get_funding_rate_history(symbol, limit)

        out = pd.DataFrame(index=future_df.index)
        out["spot_close"] = spot_df["close"].reindex(out.index, method="ffill")
        out["future_close"] = future_df["close"]
        out["funding_rate"] = funding.reindex(out.index, method="ffill")
        return out.dropna(subset=["spot_close", "future_close"])


class SyntheticDataLoader(BaseDataLoader):
    """
    오프라인 검증용 합성 데이터 생성기.
    - 기초자산: GBM(기하 브라운 운동) 기반 랜덤워크
    - 베이시스/스프레드: OU(Ornstein-Uhlenbeck) 프로세스로 평균회귀 성질을 주입
    """

    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)

    def _gbm(self, n: int, s0: float, mu: float, sigma: float) -> np.ndarray:
        dt = 1 / (365 * 6)
        shocks = self.rng.normal((mu - 0.5 * sigma**2) * dt, sigma * np.sqrt(dt), n)
        return s0 * np.exp(np.cumsum(shocks))

    def _ou_process(self, n: int, mu: float, theta: float, sigma: float, x0: float = 0.0) -> np.ndarray:
        x = np.zeros(n)
        x[0] = x0
        dt = 1.0
        for t in range(1, n):
            x[t] = x[t - 1] + theta * (mu - x[t - 1]) * dt + sigma * self.rng.normal()
        return x

    def get_ohlcv(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        idx = pd.date_range(end=pd.Timestamp.utcnow(), periods=limit, freq="4h")
        base_price = 60000 if "BTC" in symbol else 3000
        close = self._gbm(limit, base_price, mu=0.05, sigma=0.6)
        high = close * (1 + np.abs(self.rng.normal(0, 0.003, limit)))
        low = close * (1 - np.abs(self.rng.normal(0, 0.003, limit)))
        open_ = np.roll(close, 1)
        open_[0] = close[0]
        volume = self.rng.uniform(500, 5000, limit)
        return pd.DataFrame(
            {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
            index=idx,
        )

    def get_spot_future_pair(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        spot = self.get_ohlcv(symbol, timeframe, limit)
        basis_pct = self._ou_process(limit, mu=0.0005, theta=0.08, sigma=0.004)
        future_close = spot["close"] * (1 + basis_pct)
        funding_rate = basis_pct * 0.1 + self.rng.normal(0, 0.00005, limit)

        return pd.DataFrame({
            "spot_close": spot["close"].values,
            "future_close": future_close.values,
            "funding_rate": funding_rate,
        }, index=spot.index)

    def get_correlated_pair(self, timeframe: str, limit: int) -> dict:
        btc = self.get_ohlcv("BTC/USDT", timeframe, limit)
        k = 0.045
        residual = self._ou_process(limit, mu=0.0, theta=0.1, sigma=50)
        alt_close = k * btc["close"].values + 200 + residual
        alt = btc.copy()
        alt_open = np.roll(alt_close, 1)
        alt_open[0] = alt_close[0]
        alt["close"] = alt_close
        alt["open"] = alt_open
        alt["high"] = alt_close * 1.003
        alt["low"] = alt_close * 0.997
        return {"BTC/USDT": btc, "ETH/USDT": alt}

    def get_btc_price_series(self, timeframe: str, limit: int) -> pd.Series:
        return self.get_ohlcv("BTC/USDT", timeframe, limit)["close"]
