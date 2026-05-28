"""
report_tools.py - 네이버 금융 증권사 리포트 크롤링 도구

네이버 금융의 증권사 리포트 게시판에서 최신 리포트 목록을 가져옵니다.
제목, 증권사명, 목표가, 투자의견 등의 정보를 수집합니다.

⚠️ 주의사항:
- 이 크롤링은 개인 학습 용도로만 사용해야 합니다.
- 네이버 서버에 부담을 주지 않도록 요청 간격을 둡니다.
- 네이버가 페이지 구조를 변경하면 코드 수정이 필요할 수 있습니다.
"""

import time
import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool


# 네이버 금융에 접속할 때 사용하는 헤더 (웹 브라우저처럼 보이게 설정)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def _fetch_naver_reports(page: int = 1) -> list:
    """
    네이버 금융 투자정보 > 종목분석 리포트 목록을 가져오는 내부 함수.

    Args:
        page: 페이지 번호 (1부터 시작)

    Returns:
        리포트 정보 리스트 [{"title": ..., "broker": ..., ...}, ...]
    """
    # 네이버 금융 종목분석 리포트 URL
    url = f"https://finance.naver.com/research/company_list.naver?&page={page}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.encoding = "euc-kr"  # 네이버 금융은 euc-kr 인코딩 사용

        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        # 리포트 테이블에서 각 행(row) 추출
        table = soup.find("table", class_="type_1")
        if not table:
            return []

        rows = table.find_all("tr")
        reports = []

        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 5:
                continue

            try:
                # 각 열에서 데이터 추출
                stock_name = cols[0].get_text(strip=True)   # 종목명
                title = cols[1].get_text(strip=True)         # 리포트 제목
                broker = cols[2].get_text(strip=True)        # 증권사
                opinion = cols[3].get_text(strip=True)       # 투자의견 (매수, 중립 등)
                target_price = cols[4].get_text(strip=True)  # 목표가
                date = cols[5].get_text(strip=True) if len(cols) > 5 else ""  # 날짜

                # 빈 행은 건너뛰기
                if not stock_name or stock_name == "종목명":
                    continue

                reports.append({
                    "stock_name": stock_name,
                    "title": title,
                    "broker": broker,
                    "opinion": opinion,
                    "target_price": target_price,
                    "date": date,
                })
            except (IndexError, AttributeError):
                continue

        return reports

    except Exception as e:
        return [{"error": str(e)}]


@tool
def get_broker_reports(stock_name: str = "") -> str:
    """
    네이버 금융에서 최신 증권사 리포트 목록을 가져옵니다.
    특정 종목명을 입력하면 해당 종목의 리포트만 필터링합니다.

    Args:
        stock_name: 검색할 종목명 (예: "삼성전자", "SK하이닉스")
                    빈 문자열이면 전체 최신 리포트를 보여줍니다.

    Returns:
        증권사 리포트 목록을 텍스트로 반환
    """
    # 서버 부담을 줄이기 위해 최대 2페이지만 조회
    all_reports = []
    for page in range(1, 3):
        reports = _fetch_naver_reports(page)
        all_reports.extend(reports)
        time.sleep(0.5)  # 0.5초 간격으로 요청 (네이버 서버 보호)

    # 에러 체크
    if not all_reports:
        return "❌ 증권사 리포트를 가져오는데 실패했습니다."

    if all_reports and "error" in all_reports[0]:
        return f"❌ 크롤링 오류: {all_reports[0]['error']}"

    # 특정 종목으로 필터링
    if stock_name:
        filtered = [r for r in all_reports if stock_name in r.get("stock_name", "")]
        if not filtered:
            return f"'{stock_name}'에 대한 최근 증권사 리포트가 없습니다."
        reports_to_show = filtered
    else:
        reports_to_show = all_reports[:15]  # 전체 조회 시 최대 15개

    # 결과 포맷팅
    result = f"📋 증권사 리포트 {'(' + stock_name + ')' if stock_name else '(최신)'}\n"
    result += "━" * 60 + "\n"

    for r in reports_to_show:
        opinion_emoji = "🟢" if "매수" in r.get("opinion", "") else "🟡" if "중립" in r.get("opinion", "") else "🔴" if "매도" in r.get("opinion", "") else "⚪"
        result += f"{opinion_emoji} [{r['stock_name']}] {r['title']}\n"
        result += f"   📌 {r['broker']} | 의견: {r['opinion']} | 목표가: {r['target_price']} | {r['date']}\n"
        result += "\n"

    return result


@tool
def get_recent_reports_summary() -> str:
    """
    최신 증권사 리포트 전체를 요약합니다.
    어떤 종목들이 주목받고 있는지, 증권사들의 의견 트렌드를 파악할 때 유용합니다.

    Returns:
        최근 리포트 요약 정보를 텍스트로 반환
    """
    all_reports = []
    for page in range(1, 3):
        reports = _fetch_naver_reports(page)
        all_reports.extend(reports)
        time.sleep(0.5)

    if not all_reports or "error" in all_reports[0]:
        return "❌ 리포트 요약을 생성할 수 없습니다."

    # 투자의견 통계
    buy_count = sum(1 for r in all_reports if "매수" in r.get("opinion", ""))
    neutral_count = sum(1 for r in all_reports if "중립" in r.get("opinion", ""))
    sell_count = sum(1 for r in all_reports if "매도" in r.get("opinion", ""))

    # 가장 많이 언급된 종목
    stock_mentions = {}
    for r in all_reports:
        name = r.get("stock_name", "")
        if name:
            stock_mentions[name] = stock_mentions.get(name, 0) + 1

    # 상위 5개 종목
    top_stocks = sorted(stock_mentions.items(), key=lambda x: x[1], reverse=True)[:5]

    result = "📊 최신 증권사 리포트 요약\n"
    result += "━" * 45 + "\n\n"
    result += f"📈 투자의견 분포 (총 {len(all_reports)}건)\n"
    result += f"  🟢 매수: {buy_count}건\n"
    result += f"  🟡 중립: {neutral_count}건\n"
    result += f"  🔴 매도: {sell_count}건\n\n"
    result += "🔥 가장 많이 분석된 종목 Top5\n"

    for rank, (name, count) in enumerate(top_stocks, 1):
        result += f"  {rank}. {name} ({count}건)\n"

    return result
