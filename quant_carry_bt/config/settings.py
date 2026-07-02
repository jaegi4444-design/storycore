"""
전역 설정 모듈.
전략/리스크/데이터 관련 파라미터를 한 곳에서 관리한다.
실계좌 연결 시에는 API 키를 환경변수로 관리하고 여기서는 이름만 참조한다.
"""

from dataclasses import dataclass, field
from typing import Optional

# 4h 봉 기준 기본 데이터 기간
BARS_PER_DAY_4H = 6
DEFAULT_DATA_DAYS = 90
DEFAULT_DATA_BARS = DEFAULT_DATA_DAYS * BARS_PER_DAY_4H  # 540 bars ≈ 90일


@dataclass
class ExchangeConfig:
    exchange_id: str = "binance"          # ccxt exchange id (binance, bybit, okx ...)
    market_type: str = "future"           # 'future' = 무기한 선물
    api_key_env: str = "EXCHANGE_API_KEY"       # 환경변수 이름 (실제 키는 코드에 넣지 않음)
    api_secret_env: str = "EXCHANGE_API_SECRET"
    testnet: bool = True                  # 반드시 테스트넷/페이퍼 모드로 시작할 것


@dataclass
class RiskConfig:
    max_risk_per_trade_pct: float = 0.01      # 트레이드당 최대 손실 (계좌 대비 %)
    max_leverage: float = 3.0                 # 최대 레버리지
    max_concurrent_positions: int = 1         # 동시 보유 포지션 수 제한 (단일 전략 기준)
    max_daily_loss_pct: float = 0.03          # 일일 최대 손실 한도 (도달 시 신규 진입 중단)
    min_stop_pct: float = 0.005               # z-score 손절 환산 시 최소 가격 손절폭 (0.5%)
    stop_loss_zscore: float = 3.5             # z-score 기준 구조적 손절선 (평균회귀 계열)
    take_profit_zscore: float = 0.2           # 목표 z-score (평균회귀 근접 시 청산)


@dataclass
class BasisMeanReversionConfig:
    """스팟-선물 베이시스 평균회귀 전략 파라미터"""
    lookback_period: int = 100            # 베이시스 z-score 계산용 롤링 윈도우 (바 수)
    entry_zscore: float = 2.0             # 진입 임계 z-score
    exit_zscore: float = 0.3              # 청산 임계 z-score
    stop_zscore: float = 3.5              # 손절 임계 z-score
    min_half_life: int = 5                # 최소 반감기 (바 수) - 너무 느리면 제외
    max_half_life: int = 200              # 최대 반감기 - 너무 느리면 제외
    funding_weight: float = 0.3           # 베이시스 계산 시 펀딩비 반영 가중치


@dataclass
class PairTradingConfig:
    """코인 페어 트레이딩 전략 파라미터"""
    lookback_period: int = 90             # 스프레드 z-score 롤링 윈도우
    coint_pvalue_threshold: float = 0.05  # 공적분 검정 유의수준
    entry_zscore: float = 2.0
    exit_zscore: float = 0.5
    stop_zscore: float = 4.0
    recheck_coint_every: int = 30         # 공적분 관계 재검증 주기 (바 수)
    candidate_symbols: list = field(default_factory=lambda: [
        "ETH/USDT", "SOL/USDT", "BNB/USDT", "AVAX/USDT"
    ])


@dataclass
class FundingCarryConfig:
    """펀딩비 캐리 (델타 뉴트럴) 전략 파라미터"""
    funding_lookback: int = 30              # 펀딩비 변동성 추정용 롤링 윈도우
    entry_annualized_pct: float = 0.10      # 진입: 연환산 펀딩비 >= 10%
    exit_annualized_pct: float = 0.03       # 청산: 연환산 펀딩비 < 3%
    allow_reverse_carry: bool = False       # 음(-) 펀딩 역캐리 허용 여부
    max_leverage: float = 2.0               # 숏 레그 최대 레버리지 (청산 시뮬용)
    maintenance_margin_rate: float = 0.005  # 유지마진률 (0.5%)
    min_stop_pct: float = 0.005
    stop_zscore: float = 3.5


@dataclass
class MomentumTrendConfig:
    """이동평균 크로스오버 기반 모멘텀/추세추종 전략 파라미터"""
    fast_period: int = 20                 # 단기 EMA 기간 (바 수)
    slow_period: int = 60                 # 장기 EMA 기간 (바 수)
    atr_period: int = 14                  # ATR 계산 롤링 윈도우
    entry_strength: float = 1.0           # 진입 임계 추세강도 ((fast_ema-slow_ema)/ATR)
    exit_strength: float = 0.2            # 청산 임계 추세강도 (추세 약화 시)
    stop_strength_floor: float = 0.0      # 포지션 사이징용 기준 추세강도 (risk_manager 연동)
    atr_stop_mult: float = 3.0            # ATR 배수 기반 하드 손절
    min_atr_pct: float = 0.001            # 저변동성 구간 필터 (ATR/가격 최소치, 미만이면 미진입)
    cooldown_bars: int = 8                # 청산 후 재진입 금지 기간 (바 수) - 휩쏘 방지


@dataclass
class WalkForwardConfig:
    in_sample_bars: int = 360             # IS 구간 (~60일, 4h 봉)
    out_sample_bars: int = 90             # OOS 구간 (~15일)
    step_bars: int = 90                   # 롤링 스텝 (~15일)
    objective: str = "sharpe"             # 'sharpe' | 'calmar' (total_return 사용 금지)
    overfit_sharpe_gap: float = 1.0       # IS-OOS Sharpe 차이 경고 임계값
    overfit_calmar_gap: float = 0.5       # IS-OOS Calmar 차이 경고 임계값


@dataclass
class BacktestConfig:
    initial_capital: float = 10_000.0
    fee_rate: float = 0.0004              # 테이커 수수료 (0.04%, 거래소별 상이)
    slippage_bps: float = 2.0             # 슬리피지 (bps)
    funding_interval_hours: int = 8       # 무기한선물 펀딩 주기
    timeframe: str = "4h"                 # 스윙(1~수일) 전략에 적합한 봉 주기


@dataclass
class AppConfig:
    exchange: ExchangeConfig = field(default_factory=ExchangeConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    basis: BasisMeanReversionConfig = field(default_factory=BasisMeanReversionConfig)
    pair: PairTradingConfig = field(default_factory=PairTradingConfig)
    funding: FundingCarryConfig = field(default_factory=FundingCarryConfig)
    momentum: MomentumTrendConfig = field(default_factory=MomentumTrendConfig)
    backtest: BacktestConfig = field(default_factory=BacktestConfig)
    walkforward: WalkForwardConfig = field(default_factory=WalkForwardConfig)


DEFAULT_CONFIG = AppConfig()


def apply_fast_mode(config: AppConfig) -> AppConfig:
    """
    빠른 확인 모드: 작은 그리드 + 워크포워드 1 fold (90일 데이터 기준).
    - IS 45일 / OOS 15일 / step=전체 윈도우 → fold 1개
    - 국면별 백테스트 생략 (호출측에서 처리)
    """
    from copy import deepcopy
    cfg = deepcopy(config)
    cfg.walkforward.in_sample_bars = 270   # ~45일
    cfg.walkforward.out_sample_bars = 90     # ~15일
    cfg.walkforward.step_bars = 360          # fold 1개만 (270+90)
    return cfg
