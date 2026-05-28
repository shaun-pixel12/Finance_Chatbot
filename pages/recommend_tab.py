"""
recommend_tab.py - 추천 종목 Top5 탭

단기/중기/장기 투자 추천 종목을 AI가 분석해서 보여주는 화면입니다.
Yahoo Finance 데이터 + 네이버 금융 증권사 리포트를 기반으로 분석합니다.

앱을 열 때마다 새로 분석합니다 (항상 최신 데이터 제공).
"""

import streamlit as st
from agent.finance_agent import create_finance_agent


# ── AI에게 보낼 분석 요청 프롬프트 ──────────────────────
RECOMMEND_PROMPT_TEMPLATE = """
아래 조건에 맞는 투자 추천 종목 Top 5를 분석해주세요.

## 분석 조건
- 투자 기간: {period_label}
- 대상 시장: {market_label}
- 분석 범위: KOSPI + KOSDAQ (한국) 또는 NYSE + NASDAQ (미국)

## 분석 방법
1. 먼저 get_recent_reports_summary 도구로 최신 증권사 리포트 트렌드를 확인하세요
2. 주목받는 종목들의 주가, 재무 지표를 get_stock_info와 get_stock_price로 조회하세요
3. 애널리스트 추천 의견도 참고하세요

## 투자 기간별 분석 기준
- 단기 (1주~1개월): 최근 거래량 급증, 기술적 반등 가능성, 실적 발표 예정
- 중기 (1~6개월): 실적 개선 추세, 산업 성장성, 적정 밸류에이션
- 장기 (6개월 이상): 안정적 재무구조, 배당 매력, 산업 선도 기업

## 응답 형식
각 종목에 대해 아래 형식으로 답변해주세요:

### 🏆 {market_label} 추천 종목 Top 5 ({period_label})

| 순위 | 종목명 | 현재가 | 목표가 | 추천 이유 |
|------|--------|--------|--------|-----------|
| 1 | ... | ... | ... | 간단한 이유 |
| 2 | ... | ... | ... | ... |
| ... | ... | ... | ... | ... |

⚠️ 참고: 이 추천은 AI 분석 기반이며 투자 권유가 아닙니다.
데이터 출처: Yahoo Finance, 네이버 금융 증권사 리포트
"""


def render_recommend_tab():
    """
    추천 종목 탭을 그리는 메인 함수.
    """
    st.markdown("### 🏆 AI 추천 종목 Top 5")
    st.caption("Yahoo Finance 데이터 + 증권사 리포트를 종합하여 AI가 분석합니다")

    # ── 투자 기간 선택 ───────────────────────────────────
    period_col, market_col = st.columns(2)

    with period_col:
        period_label = st.radio(
            "📅 투자 기간",
            options=["단기 (1주~1개월)", "중기 (1~6개월)", "장기 (6개월 이상)"],
            index=0,
            horizontal=True,
        )

    with market_col:
        market_label = st.radio(
            "🌍 대상 시장",
            options=["🇰🇷 한국 증시", "🇺🇸 미국 증시"],
            index=0,
            horizontal=True,
        )

    st.markdown("---")

    # ── 분석 실행 버튼 ───────────────────────────────────
    if st.button("🔍 AI 분석 시작", type="primary", width="stretch"):
        # 에이전트 생성 (캐시 사용)
        if "recommend_agent" not in st.session_state:
            st.session_state.recommend_agent = create_finance_agent()

        # 분석 요청 프롬프트 생성
        prompt = RECOMMEND_PROMPT_TEMPLATE.format(
            period_label=period_label,
            market_label=market_label,
        )

        # AI 분석 실행
        with st.spinner(f"🤖 {market_label} {period_label} 추천 종목을 분석하고 있어요... (1~2분 소요)"):
            try:
                # create_agent 방식: messages 리스트로 전달
                response = st.session_state.recommend_agent.invoke({
                    "messages": [{"role": "user", "content": prompt}],
                })

                # 응답에서 마지막 AI 메시지 추출
                result_messages = response.get("messages", [])
                if result_messages:
                    last_msg = result_messages[-1]
                    if hasattr(last_msg, "content_blocks"):
                        result = "\n".join(
                            block.text for block in last_msg.content_blocks
                            if hasattr(block, "text")
                        )
                    elif hasattr(last_msg, "content"):
                        result = last_msg.content
                    else:
                        result = str(last_msg)
                else:
                    result = "분석 결과를 생성하지 못했습니다."

                # 결과 저장 (탭을 다시 열어도 유지)
                cache_key = f"recommend_{period_label}_{market_label}"
                st.session_state[cache_key] = result

            except Exception as e:
                st.error(f"⚠️ 분석 중 오류가 발생했습니다: {str(e)}")
                result = None

        if result:
            st.markdown(result)

    # ── 이전 분석 결과 표시 ──────────────────────────────
    else:
        cache_key = f"recommend_{period_label}_{market_label}"
        if cache_key in st.session_state:
            st.markdown(st.session_state[cache_key])
        else:
            # 아직 분석하지 않은 경우 안내 메시지
            st.info(
                "위의 **'🔍 AI 분석 시작'** 버튼을 눌러주세요.\n\n"
                "AI가 Yahoo Finance와 증권사 리포트를 분석하여\n"
                "추천 종목 Top 5를 선정합니다."
            )

    # ── 면책 조항 ────────────────────────────────────────
    st.markdown("---")
    st.warning(
        "⚠️ **투자 유의사항**\n\n"
        "이 추천은 AI가 공개 데이터를 기반으로 분석한 참고 자료이며, "
        "투자 권유가 아닙니다. 투자의 최종 결정과 책임은 투자자 본인에게 있습니다."
    )
