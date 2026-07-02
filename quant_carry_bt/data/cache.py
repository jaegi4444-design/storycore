"""
ccxt 데이터를 parquet/csv 로 캐싱하여 반복 API 호출을 방지한다.

캐시 경로: data/cache/
  - btc_spot_future_4h.parquet  (spot_close, future_close, funding_rate)
  - btc_perp_4h.parquet
  - eth_perp_4h.parquet
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from config.settings import DEFAULT_CONFIG, DEFAULT_DATA_BARS
from data.loader import LiveDataLoader

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent / "cache"


def _cache_path(name: str, fmt: str = "parquet") -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{name}.{fmt}"


def load_cached(name: str) -> pd.DataFrame | None:
    parquet = _cache_path(name, "parquet")
    csv = _cache_path(name, "csv")
    if parquet.exists():
        return pd.read_parquet(parquet)
    if csv.exists():
        return pd.read_csv(csv, index_col=0, parse_dates=True)
    return None


def save_cached(df: pd.DataFrame, name: str) -> Path:
    path = _cache_path(name, "parquet")
    df.to_parquet(path)
    logger.info("캐시 저장: %s (%d bars)", path, len(df))
    return path


def fetch_and_cache_btc_spot_future(
    limit: int = DEFAULT_DATA_BARS,
    timeframe: str = "4h",
    force_refresh: bool = False,
) -> pd.DataFrame:
    """BTC/USDT 현물+무기한선물 4h 페어 데이터를 캐싱한다."""
    cache_name = "btc_spot_future_4h"
    if not force_refresh:
        cached = load_cached(cache_name)
        if cached is not None and len(cached) >= min(limit, 500):
            logger.info("캐시 로드: %s (%d bars)", cache_name, len(cached))
            return cached.tail(limit)

    cfg = DEFAULT_CONFIG
    cfg.exchange.testnet = False
    loader = LiveDataLoader(cfg.exchange)
    df = loader.get_spot_future_pair("BTC/USDT", timeframe, limit)
    save_cached(df, cache_name)
    return df


def fetch_and_cache_ohlcv(
    symbol: str,
    limit: int = DEFAULT_DATA_BARS,
    timeframe: str = "4h",
    force_refresh: bool = False,
) -> pd.DataFrame:
    """단일 심볼 OHLCV 캐싱 (페어 트레이딩용)."""
    safe = symbol.replace("/", "_").replace(":", "_")
    cache_name = f"{safe}_{timeframe}"
    if not force_refresh:
        cached = load_cached(cache_name)
        if cached is not None and len(cached) >= min(limit, 500):
            return cached.tail(limit)

    cfg = DEFAULT_CONFIG
    cfg.exchange.testnet = False
    loader = LiveDataLoader(cfg.exchange)
    df = loader.get_ohlcv(symbol, timeframe, limit)
    save_cached(df, cache_name)
    return df


def load_market_bundle(limit: int = DEFAULT_DATA_BARS, force_refresh: bool = False) -> dict:
    """백테스트/워크포워드용 통합 데이터 번들."""
    btc_pair = fetch_and_cache_btc_spot_future(limit, force_refresh=force_refresh)
    btc_ohlcv = fetch_and_cache_ohlcv("BTC/USDT", limit, force_refresh=force_refresh)
    eth_ohlcv = fetch_and_cache_ohlcv("ETH/USDT", limit, force_refresh=force_refresh)
    return {
        "basis": {"BTC/USDT": btc_pair},
        "funding": {"BTC/USDT": btc_pair},
        "pair": {"BTC/USDT": btc_ohlcv, "ETH/USDT": eth_ohlcv},
        "momentum": {"BTC/USDT": btc_ohlcv},
        "btc_close": btc_pair["spot_close"],
    }
