"""
market_tools.py - 시장 전반 데이터 조회 도구

증시 지수(KOSPI, NASDAQ 등), 환율(USD/KRW 등),
원자재(금, 은, 원유) 데이터를 Yahoo Finance에서 가져옵니다.

이 도구들은 '시장 현황 대시보드' 탭과 AI 챗봇에서 모두 사용됩니다.
"""

import yfinance as yf
import pandas as pd
from langchain_core.tools import tool


# ── Yahoo Finance에서 사용하는 티커(코드) 모음 ──────────────

# 증시 지수 티커
INDEX_TICKERS = {
    "KOSPI": "^KS11",        # 한국 코스피
    "KOSDAQ": "^KQ11",       # 한국 코스닥
    "S&P 500": "^GSPC",      # 미국 S&P 500
    "NASDAQ": "^IXIC",       # 미국 나스닥
    "다우존스": "^DJI",       # 미국 다우존스
}

# 환율 티커
EXCHANGE_TICKERS = {
    "USD/KRW (달러)": "USDKRW=X",   # 미국 달러 → 한국 원
    "EUR/KRW (유로)": "EURKRW=X",   # 유로 → 한국 원
    "JPY/KRW (엔화)": "JPYKRW=X",   # 일본 엔 → 한국 원
}

# 원자재 티커
COMMODITY_TICKERS = {
    "금 (Gold)": "GC=F",      # 금 선물
    "은 (Silver)": "SI=F",    # 은 선물
    "WTI 원유": "CL=F",       # WTI 원유 선물
}


def fetch_current_data(tickers_dict: dict) -> dict:
    """
    여러 티커의 현재 가격을 한번에 가져오는 내부 함수.
    (AI가 직접 호출하는 것이 아닌, 다른 함수들이 사용하는 도우미 함수)

    Args:
        tickers_dict: {"이름": "티커코드"} 형태의 딕셔너리

    Returns:
        {"이름": {"price": 현재가, "change": 변동률, ...}} 딕셔너리
    """
    results = {}
    for name, ticker in tickers_dict.items():
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            current = info.get("regularMarketPrice",
                              info.get("currentPrice", None))
            previous = info.get("previousClose", None)

            # 변동률 계산
            change = None
            change_pct = None
            if current and previous:
                change = current - previous
                change_pct = (change / previous) * 100

            results[name] = {
                "price": current,
                "previous_close": previous,
                "change": change,
                "change_pct": change_pct,
                "ticker": ticker,
            }
        except Exception as e:
            results[name] = {
                "price": None,
                "error": str(e),
                "ticker": ticker,
            }

    return results


def fetch_history_data(ticker: str, period: str = "1mo") -> pd.DataFrame:
    """
    특정 티커의 과거 가격 데이터를 가져오는 내부 함수.
    차트를 그릴 때 사용합니다.

    Args:
        ticker: Yahoo Finance 티커 코드
        period: 조회 기간 (1d, 5d, 1mo, 3mo, 6mo, 1y)

    Returns:
        날짜별 시가/고가/저가/종가 데이터 (pandas DataFrame)
    """
    try:
        data = yf.download(ticker, period=period, progress=False)
        return data
    except Exception:
        return pd.DataFrame()


@tool
def get_market_indices() -> str:
    """
    한국과 미국의 주요 증시 지수를 조회합니다.
    KOSPI, KOSDAQ, S&P 500, NASDAQ, 다우존스 지수를 한눈에 보여줍니다.

    Returns:
        각 지수의 현재값과 등락률을 텍스트로 반환
    """
    data = fetch_current_data(INDEX_TICKERS)

    result = "📊 주요 증시 지수 현황\n"
    result += "━" * 45 + "\n"

    for name, info in data.items():
        if info.get("price"):
            price = info["price"]
            change_pct = info.get("change_pct", 0)
            direction = "🔴" if change_pct and change_pct < 0 else "🟢" if change_pct and change_pct > 0 else "⚪"
            pct_text = f"({change_pct:+.2f}%)" if change_pct else ""
            result += f"{direction} {name}: {price:,.2f} {pct_text}\n"
        else:
            result += f"⚠️ {name}: 데이터 조회 실패\n"

    return result


@tool
def get_exchange_rates() -> str:
    """
    주요 환율 정보를 조회합니다.
    달러, 유로, 엔화의 원화 환율을 보여줍니다.

    Returns:
        각 환율의 현재값과 등락을 텍스트로 반환
    """
    data = fetch_current_data(EXCHANGE_TICKERS)

    result = "💱 주요 환율 현황\n"
    result += "━" * 45 + "\n"

    for name, info in data.items():
        if info.get("price"):
            price = info["price"]
            change = info.get("change", 0)
            change_pct = info.get("change_pct", 0)
            direction = "▲" if change and change > 0 else "▼" if change and change < 0 else "─"
            pct_text = f"{direction} {abs(change_pct):.2f}%" if change_pct else ""
            result += f"{name}: {price:,.2f}원 {pct_text}\n"
        else:
            result += f"⚠️ {name}: 데이터 조회 실패\n"

    return result


@tool
def get_commodities() -> str:
    """
    주요 원자재(금, 은, 원유) 가격을 조회합니다.

    Returns:
        각 원자재의 현재 가격과 등락을 텍스트로 반환
    """
    data = fetch_current_data(COMMODITY_TICKERS)

    result = "🪙 원자재 가격 현황\n"
    result += "━" * 45 + "\n"

    for name, info in data.items():
        if info.get("price"):
            price = info["price"]
            change_pct = info.get("change_pct", 0)
            direction = "🔴" if change_pct and change_pct < 0 else "🟢" if change_pct and change_pct > 0 else "⚪"
            pct_text = f"({change_pct:+.2f}%)" if change_pct else ""
            result += f"{direction} {name}: ${price:,.2f} {pct_text}\n"
        else:
            result += f"⚠️ {name}: 데이터 조회 실패\n"

    return result
