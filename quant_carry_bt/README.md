# quant_carry_bt — 리스크 조정 수익 중심 퀀트 백테스트

Sharpe / Calmar 기준으로 전략을 검증하는 **독립 신규 프로젝트**입니다.  
`quant_bot/` 은 참고만 하며 **수정하지 않습니다.**

## 전략

| CLI 이름 | 설명 |
|---|---|
| `basis` | 스팟-선물 베이시스 평균회귀 |
| `pair` | BTC-ETH 페어 트레이딩 |
| `funding` | 펀딩비 캐리 (델타 뉴트럴) |

## 실행

```bash
cd quant_carry_bt
py -3 -m pip install -r requirements.txt

py -3 main.py --strategy basis --mode synthetic

# 빠른 확인 (90일, 그리드 축소, WF 1 fold, ~1분)
py -3 main.py --strategy basis --mode synthetic --walkforward --fast

# 전략 1개 빠른 리포트
py -3 scripts/generate_report.py --mode synthetic --fast --strategy basis

# 전체 리포트 (느림 — 국면별 포함)
py -3 scripts/generate_report.py --mode cached
```

## 0단계 감사 (quant_bot 대비)

| 항목 | 본 프로젝트 |
|---|---|
| ADF/공적분 | statsmodels `coint`, `adfuller` |
| 현물 데이터 | ccxt spot + futures 분리 fetch |
| 슬리피지/펀딩 | engine 반영 (4h 봉 비례 펀딩 누적) |
| 워크포워드 | `backtest/walk_forward.py` (Sharpe/Calmar 목적함수) |

자세한 백테스트 결과: `BACKTEST_RESULTS.md`
