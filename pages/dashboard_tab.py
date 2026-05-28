"""
dashboard_tab.py - 시장 현황 대시보드 탭

환율, 증시 지수, 원자재(금/은/원유) 데이터를 차트로 보여주는 화면입니다.
Plotly 차트를 사용해서 인터랙티브하게 데이터를 시각화합니다.
"""

import streamlit as st
import plotly.graph_objects as go
from tools.market_tools import (
    INDEX_TICKERS,
    EXCHANGE_TICKERS,
    COMMODITY_TICKERS,
    fetch_current_data,
    fetch_history_data,
)


def _create_line_chart(ticker: str, name: str, period: str, color: str) -> go.Figure:
    """
    특정 티커의 가격 추이를 선 그래프로 그리는 함수.

    Args:
        ticker: Yahoo Finance 티커 코드
        name: 표시할 이름
        period: 조회 기간
        color: 선 색상

    Returns:
        Plotly Figure 객체
    """
    data = fetch_history_data(ticker, period)

    if data.empty:
        # 데이터가 없으면 빈 차트 반환
        fig = go.Figure()
        fig.add_annotation(text="데이터를 불러올 수 없습니다", showarrow=False)
        return fig

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data["Close"],
        mode="lines",
        name=name,
        line=dict(color=color, width=2),
        fill="tozeroy",           # 아래 영역을 색으로 채우기
        fillcolor=f"rgba{tuple(list(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + [0.1])}",
    ))

    fig.update_layout(
        title=f"{name} 추이",
        xaxis_title="날짜",
        yaxis_title="가격",
        template="plotly_dark",    # 다크 테마
        height=350,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False,
    )

    return fig


def render_dashboard_tab():
    """
    시장 현황 대시보드 탭을 그리는 메인 함수.
    """
    st.markdown("### 📊 실시간 시장 현황")
    st.caption("데이터 출처: Yahoo Finance (15분 지연)")

    # ── 기간 선택 버튼 ──────────────────────────────────
    period_options = {"1주": "5d", "1개월": "1mo", "3개월": "3mo", "1년": "1y"}
    selected_label = st.radio(
        "📅 조회 기간",
        options=list(period_options.keys()),
        index=1,  # 기본값: 1개월
        horizontal=True,
    )
    period = period_options[selected_label]

    # ── 섹션 1: 증시 지수 ────────────────────────────────
    st.markdown("---")
    st.markdown("#### 📈 증시 지수")

    # 현재 지수값을 카드 형태로 표시
    index_data = fetch_current_data(INDEX_TICKERS)
    cols = st.columns(len(INDEX_TICKERS))

    for i, (name, info) in enumerate(index_data.items()):
        with cols[i]:
            price = info.get("price")
            change_pct = info.get("change_pct")

            if price:
                delta_text = f"{change_pct:+.2f}%" if change_pct else None
                st.metric(label=name, value=f"{price:,.2f}", delta=delta_text)
            else:
                st.metric(label=name, value="N/A")

    # 지수 차트 (2열로 배치)
    chart_colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7"]
    idx_items = list(INDEX_TICKERS.items())

    for row_start in range(0, len(idx_items), 2):
        chart_cols = st.columns(2)
        for col_idx in range(2):
            item_idx = row_start + col_idx
            if item_idx < len(idx_items):
                name, ticker = idx_items[item_idx]
                with chart_cols[col_idx]:
                    fig = _create_line_chart(
                        ticker, name, period,
                        chart_colors[item_idx % len(chart_colors)]
                    )
                    st.plotly_chart(fig, use_container_width=True)

    # ── 섹션 2: 환율 ────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 💱 환율")

    exchange_data = fetch_current_data(EXCHANGE_TICKERS)
    cols = st.columns(len(EXCHANGE_TICKERS))

    for i, (name, info) in enumerate(exchange_data.items()):
        with cols[i]:
            price = info.get("price")
            change_pct = info.get("change_pct")

            if price:
                delta_text = f"{change_pct:+.2f}%" if change_pct else None
                st.metric(
                    label=name,
                    value=f"{price:,.2f}원",
                    delta=delta_text,
                    delta_color="inverse",  # 환율은 올라가면 나쁜 것이므로 색 반전
                )
            else:
                st.metric(label=name, value="N/A")

    # 환율 차트
    exchange_colors = ["#E74C3C", "#3498DB", "#2ECC71"]
    ex_items = list(EXCHANGE_TICKERS.items())
    chart_cols = st.columns(len(ex_items))

    for i, (name, ticker) in enumerate(ex_items):
        with chart_cols[i]:
            fig = _create_line_chart(ticker, name, period, exchange_colors[i])
            st.plotly_chart(fig, use_container_width=True)

    # ── 섹션 3: 원자재 ──────────────────────────────────
    st.markdown("---")
    st.markdown("#### 🪙 원자재")

    commodity_data = fetch_current_data(COMMODITY_TICKERS)
    cols = st.columns(len(COMMODITY_TICKERS))

    for i, (name, info) in enumerate(commodity_data.items()):
        with cols[i]:
            price = info.get("price")
            change_pct = info.get("change_pct")

            if price:
                delta_text = f"{change_pct:+.2f}%" if change_pct else None
                st.metric(label=name, value=f"${price:,.2f}", delta=delta_text)
            else:
                st.metric(label=name, value="N/A")

    # 원자재 차트
    commodity_colors = ["#F39C12", "#BDC3C7", "#1ABC9C"]
    cm_items = list(COMMODITY_TICKERS.items())
    chart_cols = st.columns(len(cm_items))

    for i, (name, ticker) in enumerate(cm_items):
        with chart_cols[i]:
            fig = _create_line_chart(ticker, name, period, commodity_colors[i])
            st.plotly_chart(fig, use_container_width=True)
