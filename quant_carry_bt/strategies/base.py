"""
전략 공통 인터페이스.

모든 전략(베이시스 평균회귀, 페어 트레이딩, 추후 추가될 전략)은
이 BaseStrategy 를 상속하여 동일한 방식으로 백테스트 엔진 및
실행 러너와 연결된다. 새 전략을 추가해도 엔진/러너 코드는
전혀 수정할 필요가 없다 (Open-Closed Principle).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import pandas as pd


class Signal(Enum):
    LONG = 1
    SHORT = -1
    FLAT = 0
    CLOSE = 2  # 포지션 청산 (방향 무관)


@dataclass
class StrategyOutput:
    """매 시점 전략이 반환하는 표준 출력 포맷"""
    timestamp: pd.Timestamp
    signal: Signal
    target_weight: float          # -1.0 (풀숏) ~ +1.0 (풀롱), 자금 배분 비중
    meta: dict                    # z-score, 반감기 등 디버깅/로깅용 부가정보


class BaseStrategy(ABC):
    """모든 전략의 추상 베이스 클래스"""

    name: str = "base"

    def __init__(self, config):
        self.config = config
        self._state = {}  # 전략별 내부 상태 (포지션 여부, 마지막 진입 z-score 등)
        self._initial_state = {}  # reset() 시 복원할 기본 상태 (서브클래스에서 설정)

    @abstractmethod
    def required_symbols(self) -> list:
        """이 전략이 필요로 하는 심볼 목록 반환 (데이터 로더가 참조)"""
        raise NotImplementedError

    @abstractmethod
    def warmup_period(self) -> int:
        """전략 계산에 필요한 최소 워밍업 바 수"""
        raise NotImplementedError

    @abstractmethod
    def generate_signal(self, market_data: dict) -> StrategyOutput:
        """
        market_data: {symbol: pd.DataFrame(OHLCV + 부가데이터)} 형태.
        가장 최근 시점까지의 데이터를 받아 단일 시점의 시그널을 생성한다.
        """
        raise NotImplementedError

    def reset(self):
        """백테스트 재실행 등을 위한 내부 상태 초기화 (서브클래스가 설정한 초기값으로 복원)"""
        self._state = dict(self._initial_state)

    def describe(self) -> str:
        return f"<Strategy name={self.name}>"
