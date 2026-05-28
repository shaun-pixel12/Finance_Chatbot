"""
finance_agent.py - 금융 AI 에이전트 설정

LangChain의 create_agent를 사용해서
도구(tools)를 자유롭게 사용할 수 있는 AI 에이전트를 만듭니다.

이 에이전트는:
1. 사용자 질문을 이해하고
2. 필요한 도구(주가 조회, 리포트 검색 등)를 스스로 선택해서
3. 데이터를 가져와서 사용자에게 답변합니다
"""

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent

# 설정 파일에서 API 정보 가져오기
from config import OPENAI_API_KEY, OPENAI_API_BASE, MODEL_NAME

# 도구 모음 가져오기
from tools.stock_tools import (
    get_stock_price,
    get_stock_history,
    get_stock_info,
    get_analyst_recommendations,
)
from tools.market_tools import (
    get_market_indices,
    get_exchange_rates,
    get_commodities,
)
from tools.report_tools import (
    get_broker_reports,
    get_recent_reports_summary,
)


# ── AI에게 줄 역할 설명 (시스템 프롬프트) ──────────────────
SYSTEM_PROMPT = """당신은 한국과 미국 증시를 전문적으로 분석하는 금융 AI 어시스턴트입니다.

## 당신의 역할
- 사용자의 금융/투자 관련 질문에 정확하고 이해하기 쉽게 답변합니다
- 필요한 데이터는 주어진 도구(tool)를 사용해서 실시간으로 가져옵니다
- 한국어로 친절하게 답변하되, 전문 용어는 쉽게 풀어서 설명합니다

## 사용 가능한 도구
- get_stock_price: 특정 종목의 현재 주가 조회
- get_stock_history: 과거 주가 추이 조회
- get_stock_info: 기업 기본 정보 및 재무 지표 조회
- get_analyst_recommendations: 애널리스트 투자 추천 의견 조회
- get_market_indices: 주요 증시 지수 (KOSPI, NASDAQ 등) 조회
- get_exchange_rates: 환율 조회
- get_commodities: 원자재 (금, 은, 원유) 가격 조회
- get_broker_reports: 증권사 리포트 검색
- get_recent_reports_summary: 최신 리포트 전체 요약

## 한국 주식 티커 규칙
- KOSPI 종목: 종목코드 뒤에 .KS 붙이기 (예: 삼성전자 → 005930.KS)
- KOSDAQ 종목: 종목코드 뒤에 .KQ 붙이기 (예: 에코프로비엠 → 247540.KQ)

## 주요 한국 주식 티커 매핑
- 삼성전자: 005930.KS
- SK하이닉스: 000660.KS
- LG에너지솔루션: 373220.KS
- 삼성바이오로직스: 207940.KS
- 현대자동차: 005380.KS
- 기아: 000270.KS
- 셀트리온: 068270.KS
- KB금융: 105560.KS
- 신한지주: 055550.KS
- NAVER: 035420.KS
- 카카오: 035720.KS
- 포스코홀딩스: 005490.KS
- LG화학: 051910.KS
- 현대모비스: 012330.KS
- 삼성SDI: 006400.KS
- SK이노베이션: 096770.KS

## 답변 시 주의사항
1. 투자 관련 답변은 참고 정보일 뿐, 투자 권유가 아님을 명시하세요
2. 데이터 출처(Yahoo Finance, 네이버 금융)를 언급하세요
3. 숫자는 읽기 쉽게 단위(억, 조)를 표시하세요
4. 이모지를 적절히 사용해서 가독성을 높이세요
"""


def create_finance_agent():
    """
    금융 AI 에이전트를 생성하는 함수.

    Returns:
        LangChain Agent (create_agent로 생성된 에이전트)
    """
    # 1. LLM(대형 언어 모델) 설정 - OpenAI 호환 API 사용
    llm = ChatOpenAI(
        model=MODEL_NAME,
        openai_api_key=OPENAI_API_KEY,
        openai_api_base=OPENAI_API_BASE,
        temperature=0.3,  # 낮을수록 정확하고 일관된 답변 (0~1)
    )

    # 2. 에이전트가 사용할 도구 목록
    tools = [
        get_stock_price,
        get_stock_history,
        get_stock_info,
        get_analyst_recommendations,
        get_market_indices,
        get_exchange_rates,
        get_commodities,
        get_broker_reports,
        get_recent_reports_summary,
    ]

    # 3. create_agent로 에이전트 생성 (LangChain 1.x 최신 방식)
    #    - model: AI 모델
    #    - tools: AI가 사용할 수 있는 도구들
    #    - system_prompt: AI에게 주는 역할 설명
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )

    return agent
