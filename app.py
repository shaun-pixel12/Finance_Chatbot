"""
app.py - 금융 AI 챗봇 메인 앱 🚀

이 파일이 앱의 시작점입니다.
실행 명령어: streamlit run app.py

3개의 탭으로 구성:
1. 💬 AI 챗봇: 자유 질문 → AI 답변
2. 🏆 추천 종목: 단기/중기/장기 투자 추천 Top5
3. 📊 시장 현황: 환율, 지수, 원자재 차트
"""

import streamlit as st

# ── 페이지 기본 설정 ─────────────────────────────────────
st.set_page_config(
    page_title="💹 금융 AI 챗봇",
    page_icon="💹",
    layout="wide",              # 넓은 레이아웃
    initial_sidebar_state="expanded",  # 사이드바 펼쳐서 시작
)

# ── 사이드바 ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("# 💹 금융 AI 챗봇")
    st.markdown("---")
    st.markdown(
        """
        **Yahoo Finance** 데이터와 **증권사 리포트**를
        AI가 실시간으로 분석해드립니다.

        📊 한국 & 미국 증시
        💱 환율 & 원자재
        🏆 AI 추천 종목

        ---
        ⚠️ 투자의 최종 결정과 책임은
        투자자 본인에게 있습니다.
        """
    )
    st.markdown("---")
    st.caption("데이터 출처: Yahoo Finance, 네이버 금융")
    st.caption("Powered by LangChain + GPT-4o-mini")

# ── 메인 영역: 탭 구성 ──────────────────────────────────
tab_chatbot, tab_recommend, tab_dashboard = st.tabs([
    "💬 AI 챗봇",
    "🏆 추천 종목",
    "📊 시장 현황",
])

# ── 각 탭 렌더링 ─────────────────────────────────────────
with tab_chatbot:
    from pages.chatbot_tab import render_chatbot_tab
    render_chatbot_tab()

with tab_recommend:
    from pages.recommend_tab import render_recommend_tab
    render_recommend_tab()

with tab_dashboard:
    from pages.dashboard_tab import render_dashboard_tab
    render_dashboard_tab()
