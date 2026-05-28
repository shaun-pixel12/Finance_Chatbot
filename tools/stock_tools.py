"""
stock_tools.py - 주식 데이터 조회 도구

Yahoo Finance(yfinance)를 사용해서 개별 종목의 주가, 기업 정보,
애널리스트 추천 등을 가져오는 도구 모음입니다.

LangChain의 @tool 데코레이터를 사용하면,
AI가 사용자 질문에 따라 이 함수들을 자동으로 호출합니다.
"""

import yfinance as yf
from langchain_core.tools import tool


@tool
def get_stock_price(ticker: str) -> str:
    """
    특정 종목의 현재 주가를 조회합니다.

    Args:
        ticker: 종목 코드 (예: "005930.KS"는 삼성전자, "AAPL"은 애플)

    Returns:
        현재가, 전일 대비 변동, 거래량 등의 정보를 텍스트로 반환
    """
    try:
        # yfinance로 종목 정보 가져오기
        stock = yf.Ticker(ticker)
        info = stock.info

        # 주요 정보 추출 (없으면 "정보 없음" 표시)
        name = info.get("shortName", info.get("longName", ticker))
        current_price = info.get("currentPrice", info.get("regularMarketPrice", "정보 없음"))
        previous_close = info.get("previousClose", "정보 없음")
        day_high = info.get("dayHigh", "정보 없음")
        day_low = info.get("dayLow", "정보 없음")
        volume = info.get("volume", "정보 없음")
        market_cap = info.get("marketCap", "정보 없음")

        # 변동률 계산
        change_text = ""
        if isinstance(current_price, (int, float)) and isinstance(previous_close, (int, float)):
            change = current_price - previous_close
            change_pct = (change / previous_close) * 100
            direction = "▲" if change > 0 else "▼" if change < 0 else "─"
            change_text = f"전일 대비: {direction} {abs(change):,.0f} ({change_pct:+.2f}%)"

        # 시가총액을 읽기 쉬운 단위로 변환
        if isinstance(market_cap, (int, float)):
            if market_cap >= 1_000_000_000_000:  # 1조 이상
                market_cap_text = f"{market_cap / 1_000_000_000_000:.1f}조"
            elif market_cap >= 100_000_000:  # 1억 이상
                market_cap_text = f"{market_cap / 100_000_000:.0f}억"
            else:
                market_cap_text = f"{market_cap:,.0f}"
        else:
            market_cap_text = "정보 없음"

        result = f"""📈 {name} ({ticker})
현재가: {current_price:,.0f} 원
{change_text}
최고가: {day_high:,} / 최저가: {day_low:,}
거래량: {volume:,}
시가총액: {market_cap_text}"""

        return result

    except Exception as e:
        return f"❌ '{ticker}' 종목 정보를 가져오는데 실패했습니다: {str(e)}"


@tool
def get_stock_history(ticker: str, period: str = "1mo") -> str:
    """
    특정 종목의 과거 주가 히스토리를 조회합니다.

    Args:
        ticker: 종목 코드 (예: "005930.KS", "AAPL")
        period: 조회 기간 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max)

    Returns:
        최근 주가 데이터를 텍스트로 반환
    """
    try:
        stock = yf.Ticker(ticker)
        # 주가 히스토리 다운로드
        hist = stock.history(period=period)

        if hist.empty:
            return f"❌ '{ticker}'의 주가 데이터가 없습니다."

        # 최근 10일치만 보여주기 (너무 많으면 AI가 처리하기 어려움)
        recent = hist.tail(10)

        result = f"📊 {ticker} 최근 주가 추이 ({period} 기준)\n"
        result += "─" * 50 + "\n"
        result += f"{'날짜':<12} {'종가':>10} {'거래량':>12}\n"
        result += "─" * 50 + "\n"

        for date, row in recent.iterrows():
            date_str = date.strftime("%Y-%m-%d")
            result += f"{date_str:<12} {row['Close']:>10,.0f} {row['Volume']:>12,.0f}\n"

        # 기간 내 통계
        result += "─" * 50 + "\n"
        result += f"기간 최고가: {hist['High'].max():,.0f}\n"
        result += f"기간 최저가: {hist['Low'].min():,.0f}\n"
        result += f"기간 평균 거래량: {hist['Volume'].mean():,.0f}\n"

        return result

    except Exception as e:
        return f"❌ '{ticker}' 히스토리를 가져오는데 실패했습니다: {str(e)}"


@tool
def get_stock_info(ticker: str) -> str:
    """
    특정 종목의 기업 기본 정보를 조회합니다.
    PER, PBR, 배당수익률 등 투자 판단에 필요한 재무 지표를 보여줍니다.

    Args:
        ticker: 종목 코드 (예: "005930.KS", "AAPL")

    Returns:
        기업 기본 정보와 재무 지표를 텍스트로 반환
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        name = info.get("shortName", info.get("longName", ticker))
        sector = info.get("sector", "정보 없음")
        industry = info.get("industry", "정보 없음")

        # 주요 재무 지표
        per = info.get("trailingPE", info.get("forwardPE", "정보 없음"))
        pbr = info.get("priceToBook", "정보 없음")
        eps = info.get("trailingEps", "정보 없음")
        dividend_yield = info.get("dividendYield", None)
        target_price = info.get("targetMeanPrice", "정보 없음")
        recommendation = info.get("recommendationKey", "정보 없음")

        # 배당수익률을 퍼센트로 변환
        if dividend_yield and isinstance(dividend_yield, (int, float)):
            dividend_text = f"{dividend_yield * 100:.2f}%"
        else:
            dividend_text = "없음"

        # PER, PBR 포맷팅
        per_text = f"{per:.2f}" if isinstance(per, (int, float)) else per
        pbr_text = f"{pbr:.2f}" if isinstance(pbr, (int, float)) else pbr

        result = f"""🏢 {name} ({ticker}) 기업 정보
━━━━━━━━━━━━━━━━━━━━━━━━━━
섹터: {sector}
산업: {industry}
━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 재무 지표
PER (주가수익비율): {per_text}
PBR (주가순자산비율): {pbr_text}
EPS (주당순이익): {eps}
배당수익률: {dividend_text}
━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 애널리스트 의견
목표 주가: {target_price}
추천 등급: {recommendation}"""

        return result

    except Exception as e:
        return f"❌ '{ticker}' 기업 정보를 가져오는데 실패했습니다: {str(e)}"


@tool
def get_analyst_recommendations(ticker: str) -> str:
    """
    특정 종목에 대한 애널리스트(전문가)들의 투자 추천 의견을 조회합니다.

    Args:
        ticker: 종목 코드 (예: "005930.KS", "AAPL")

    Returns:
        최근 애널리스트 추천 의견을 텍스트로 반환
    """
    try:
        stock = yf.Ticker(ticker)
        rec = stock.recommendations

        if rec is None or rec.empty:
            return f"'{ticker}'에 대한 애널리스트 추천 의견이 없습니다."

        # 최근 10개만 표시
        recent_rec = rec.tail(10)

        result = f"🎯 {ticker} 애널리스트 추천 의견\n"
        result += "─" * 60 + "\n"

        for idx, row in recent_rec.iterrows():
            date_str = idx.strftime("%Y-%m-%d") if hasattr(idx, 'strftime') else str(idx)
            firm = row.get("Firm", "")
            grade = row.get("To Grade", row.get("toGrade", ""))
            action = row.get("Action", row.get("action", ""))
            result += f"{date_str} | {firm} | {action} → {grade}\n"

        return result

    except Exception as e:
        return f"❌ '{ticker}' 애널리스트 의견을 가져오는데 실패했습니다: {str(e)}"
