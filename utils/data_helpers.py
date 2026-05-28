"""
data_helpers.py - 데이터 가공 도우미 함수

여러 곳에서 반복적으로 사용하는 데이터 변환/포맷팅 함수 모음입니다.
"""


def format_number_korean(number) -> str:
    """
    숫자를 한국식 단위(억, 조)로 변환합니다.

    예시:
        1234567890000 → "1.2조"
        12345678900 → "123억"
        12345678 → "1,235만"

    Args:
        number: 변환할 숫자

    Returns:
        한국식 단위가 붙은 문자열
    """
    if not isinstance(number, (int, float)):
        return str(number)

    abs_num = abs(number)
    sign = "-" if number < 0 else ""

    if abs_num >= 1_000_000_000_000:  # 1조 이상
        return f"{sign}{abs_num / 1_000_000_000_000:.1f}조"
    elif abs_num >= 100_000_000:  # 1억 이상
        return f"{sign}{abs_num / 100_000_000:.0f}억"
    elif abs_num >= 10_000:  # 1만 이상
        return f"{sign}{abs_num / 10_000:.0f}만"
    else:
        return f"{sign}{abs_num:,.0f}"


def format_change_pct(change_pct) -> str:
    """
    변동률을 이모지와 함께 포맷팅합니다.

    예시:
        2.5 → "🟢 +2.50%"
        -1.3 → "🔴 -1.30%"
        0 → "⚪ 0.00%"

    Args:
        change_pct: 변동률 (%)

    Returns:
        이모지 + 퍼센트 문자열
    """
    if change_pct is None:
        return "⚪ N/A"

    if change_pct > 0:
        return f"🟢 +{change_pct:.2f}%"
    elif change_pct < 0:
        return f"🔴 {change_pct:.2f}%"
    else:
        return f"⚪ {change_pct:.2f}%"


def ticker_to_name(ticker: str) -> str:
    """
    자주 사용하는 티커를 한국어 이름으로 변환합니다.

    Args:
        ticker: Yahoo Finance 티커 코드

    Returns:
        한국어 이름 (없으면 티커 그대로 반환)
    """
    TICKER_NAMES = {
        # 한국 주식
        "005930.KS": "삼성전자",
        "000660.KS": "SK하이닉스",
        "373220.KS": "LG에너지솔루션",
        "207940.KS": "삼성바이오로직스",
        "005380.KS": "현대자동차",
        "000270.KS": "기아",
        "068270.KS": "셀트리온",
        "035420.KS": "NAVER",
        "035720.KS": "카카오",
        "005490.KS": "포스코홀딩스",
        # 미국 주식
        "AAPL": "애플",
        "MSFT": "마이크로소프트",
        "GOOGL": "구글",
        "AMZN": "아마존",
        "NVDA": "엔비디아",
        "TSLA": "테슬라",
        "META": "메타",
        # 지수
        "^KS11": "KOSPI",
        "^KQ11": "KOSDAQ",
        "^GSPC": "S&P 500",
        "^IXIC": "NASDAQ",
        "^DJI": "다우존스",
    }

    return TICKER_NAMES.get(ticker, ticker)
