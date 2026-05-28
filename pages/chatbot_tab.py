"""
chatbot_tab.py - AI 챗봇 탭

사용자와 AI가 대화하는 화면입니다.
사용자가 금융 관련 질문을 하면, AI가 도구를 활용해서 답변합니다.

Streamlit의 st.chat_message를 사용해서 카카오톡처럼 대화 형태로 보여줍니다.
"""

import streamlit as st
from agent.finance_agent import create_finance_agent


def render_chatbot_tab():
    """
    AI 챗봇 탭을 그리는 메인 함수.
    """
    st.markdown("### 💬 AI 금융 어시스턴트")
    st.caption("주식, 환율, 원자재 등 금융 관련 질문을 자유롭게 해보세요!")

    # ── 예시 질문 버튼 ──────────────────────────────────
    st.markdown("**💡 이런 질문을 해보세요:**")
    example_cols = st.columns(3)

    example_questions = [
        "삼성전자 현재 주가 알려줘",
        "오늘 환율 어때?",
        "최근 증권사 리포트 요약해줘",
    ]

    for i, question in enumerate(example_questions):
        with example_cols[i]:
            if st.button(question, key=f"example_{i}", width="stretch"):
                # 예시 질문 버튼을 누르면 해당 질문을 채팅에 입력
                st.session_state.pending_question = question

    st.markdown("---")

    # ── 대화 기록 초기화 ─────────────────────────────────
    # session_state는 페이지를 새로고침해도 데이터가 유지되는 저장소
    if "chat_messages" not in st.session_state:
        # 화면에 보여줄 메시지 + AI 내부 메시지 통합 관리
        st.session_state.chat_messages = []

    if "display_messages" not in st.session_state:
        # 화면 표시용 메시지 목록
        st.session_state.display_messages = [
            {
                "role": "assistant",
                "content": (
                    "안녕하세요! 🙋‍♂️ 저는 금융 AI 어시스턴트입니다.\n\n"
                    "한국·미국 주식, 환율, 원자재 등에 대해 물어보세요.\n"
                    "Yahoo Finance와 네이버 금융 데이터를 실시간으로 분석해드립니다!"
                ),
            }
        ]

    if "agent" not in st.session_state:
        # AI 에이전트를 한 번만 생성하고 재사용 (매번 만들면 느림)
        with st.spinner("🤖 AI 에이전트를 준비하는 중..."):
            st.session_state.agent = create_finance_agent()

    # ── 이전 대화 표시 ───────────────────────────────────
    for message in st.session_state.display_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # ── 예시 질문 버튼으로 입력된 질문 처리 ──────────────
    pending = st.session_state.pop("pending_question", None)

    # ── 사용자 입력 받기 ─────────────────────────────────
    user_input = st.chat_input("궁금한 것을 물어보세요...")

    # 예시 질문이 있으면 우선 처리
    question = pending or user_input

    if question:
        # 사용자 메시지를 화면에 표시
        st.session_state.display_messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        # AI 내부 메시지 기록에 사용자 메시지 추가
        st.session_state.chat_messages.append({"role": "user", "content": question})

        # AI 응답 생성
        with st.chat_message("assistant"):
            with st.spinner("🔍 데이터를 분석하고 있어요..."):
                try:
                    # create_agent 방식: messages 리스트로 전달
                    response = st.session_state.agent.invoke({
                        "messages": st.session_state.chat_messages,
                    })

                    # 응답에서 마지막 AI 메시지 추출
                    result_messages = response.get("messages", [])
                    if result_messages:
                        last_msg = result_messages[-1]
                        # content_blocks가 있으면 텍스트 추출
                        if hasattr(last_msg, "content_blocks"):
                            answer = "\n".join(
                                block.text for block in last_msg.content_blocks
                                if hasattr(block, "text")
                            )
                        elif hasattr(last_msg, "content"):
                            answer = last_msg.content
                        else:
                            answer = str(last_msg)
                    else:
                        answer = "죄송합니다, 답변을 생성하지 못했습니다."

                except Exception as e:
                    answer = f"⚠️ 오류가 발생했습니다: {str(e)}\n\n다시 질문해주세요."

                st.markdown(answer)

        # 대화 기록 저장
        st.session_state.display_messages.append({"role": "assistant", "content": answer})
        st.session_state.chat_messages.append({"role": "assistant", "content": answer})

    # ── 대화 초기화 버튼 ─────────────────────────────────
    if st.sidebar.button("🗑️ 대화 초기화", width="stretch"):
        st.session_state.display_messages = [
            {
                "role": "assistant",
                "content": "대화가 초기화되었습니다. 새로운 질문을 해주세요! 🙋‍♂️",
            }
        ]
        st.session_state.chat_messages = []
        st.rerun()
