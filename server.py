"""
server.py - 금융 AI 챗봇 백엔드 웹 서버 🚀

이 파일은 프로젝트의 새로운 시작점입니다.
실행 명령어: python server.py

역할:
1. 웹 브라우저가 화면 파일(HTML, CSS, JS)을 요청하면 전송해줍니다.
2. 화면에서 온 API 요청(챗봇 질문, 종목 추천, 차트 데이터 등)을 처리하여 결과를 반환합니다.
"""

import os
import sys
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict

# 환경 변수 로드 (.env 파일 읽기)
from dotenv import load_dotenv
load_dotenv()

# 핵심 금융 AI 에이전트 생성 함수 가져오기
from agent.finance_agent import create_finance_agent

# 시장 데이터 도구 및 리스트 가져오기
from tools.market_tools import (
    INDEX_TICKERS,
    EXCHANGE_TICKERS,
    COMMODITY_TICKERS,
    fetch_current_data,
    fetch_history_data,
)

# ── 1. FastAPI 웹 서버 초기화 ─────────────────────────────────────
# FastAPI는 현대적이고 초고속인 파이썬 웹 프레임워크입니다.
app = FastAPI(
    title="금융 AI 어시스턴트 API",
    description="금융 챗봇, AI 종목 추천, 실시간 시장 데이터 제공용 API",
    version="1.0.0"
)

# ── 2. AI 에이전트 인스턴스 미리 생성 ──────────────────────────────
# 에이전트는 불러오는 데 시간이 걸리므로, 서버 실행 시 한 번만 생성하여 계속 재사용합니다.
try:
    print("[INFO] 금융 AI 에이전트를 준비하는 중입니다. 잠시만 기다려주세요...")
    finance_agent = create_finance_agent()
    print("[OK] 금융 AI 에이전트 준비 완료!")
except Exception as e:
    print(f"[ERROR] AI 에이전트 생성 중 오류 발생: {e}")
    sys.exit(1)

# ── 3. 요청 데이터 형식 정의 (Pydantic 모델) ──────────────────────
# 화면(프론트엔드)에서 서버로 데이터를 보낼 때 어떤 모양으로 보낼지 정하는 규칙입니다.

class ChatMessage(BaseModel):
    role: str      # 'user' (사용자) 또는 'assistant' (AI)
    content: str   # 대화 내용

class ChatRequest(BaseModel):
    messages: List[ChatMessage]  # 대화 기록 전체 목록

class RecommendRequest(BaseModel):
    period_label: str  # 투자 기간 (예: "단기 (1주~1개월)", "중기 (1~6개월)", "장기 (6개월 이상)")
    market_label: str  # 대상 시장 (예: "🇰🇷 한국 증시", "🇺🇸 미국 증시")


# ── 4. AI 에이전트 응답 파싱 유틸리티 함수 ────────────────────────
def extract_ai_answer(response: dict) -> str:
    """
    AI 에이전트가 돌려준 원본 응답 딕셔너리에서
    최종적으로 사용자에게 보여줄 'AI의 답변 텍스트'만 쏙 뽑아내는 함수입니다.
    """
    result_messages = response.get("messages", [])
    answer = "죄송합니다, 답변을 생성하지 못했습니다."
    
    # 메시지 목록을 뒤에서부터 읽으면서 AI가 한 말을 찾습니다.
    for msg in reversed(result_messages):
        # AI 메시지 클래스이면서 내용이 채워져 있는 경우
        if msg.__class__.__name__ == "AIMessage" and getattr(msg, "content", ""):
            content = msg.content
            # 가끔 응답이 텍스트 리스트 형태로 오는 경우 처리
            if isinstance(content, list):
                text_parts = []
                for block in content:
                    if isinstance(block, dict) and "text" in block:
                        text_parts.append(block["text"])
                    elif hasattr(block, "text"):
                        text_parts.append(block.text)
                answer = "\n".join(text_parts) if text_parts else str(content)
            else:
                answer = str(content)
            break
        # 일반 텍스트가 들어 있는 다른 종류의 메시지인 경우의 보완(폴백) 처리
        elif getattr(msg, "content", "") and not getattr(msg, "tool_calls", []):
            answer = str(msg.content)
            break
            
    return answer


# ── 5. API 엔드포인트(기능) 개발 ──────────────────────────────────

# [A] AI 챗봇 질문 답변 API
@app.post("/api/chat")
async def chat_with_agent(chat_req: ChatRequest):
    """
    화면에서 여태까지 나눈 대화 기록 전체를 받아,
    AI 에이전트가 그 대화 흐름을 이해한 후 적절한 답변을 생성해 돌려줍니다.
    """
    try:
        # Pydantic 모델 리스트를 딕셔너리 리스트로 변환
        formatted_messages = []
        for msg in chat_req.messages:
            formatted_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # AI 에이전트 호출
        response = finance_agent.invoke({
            "messages": formatted_messages,
        })
        
        # 최종 답변 추출
        answer = extract_ai_answer(response)
        return {"answer": answer}
        
    except Exception as e:
        print(f"❌ 챗봇 API 처리 오류: {e}")
        raise HTTPException(status_code=500, detail=f"AI 답변 생성 중 오류가 발생했습니다: {str(e)}")


# [B] AI 종목 추천 보고서 생성 API
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

@app.post("/api/recommend")
async def recommend_stocks(req: RecommendRequest):
    """
    선택된 투자 기간과 시장을 기반으로
    AI가 종목을 분석한 뒤 마크다운 표 형식의 추천 결과 보고서를 반환합니다.
    """
    try:
        # 프롬프트 생성
        prompt = RECOMMEND_PROMPT_TEMPLATE.format(
            period_label=req.period_label,
            market_label=req.market_label,
        )
        
        # 에이전트 호출 (첫 질문과 동일하게 1턴 대화로 호출)
        response = finance_agent.invoke({
            "messages": [{"role": "user", "content": prompt}],
        })
        
        # 최종 답변 추출
        result = extract_ai_answer(response)
        return {"result": result}
        
    except Exception as e:
        print(f"❌ 종목 추천 API 처리 오류: {e}")
        raise HTTPException(status_code=500, detail=f"종목 분석 중 오류가 발생했습니다: {str(e)}")


# [C] 실시간 시장 지표 데이터 가져오기 API
@app.get("/api/market/current")
async def get_current_market():
    """
    주요 지수(코스피, 코스닥, S&P500 등), 환율(달러, 유로, 엔화), 원자재(금, 은, 유가)의
    현재 가격 및 등락률 데이터를 긁어와 화면에 넘겨줍니다.
    """
    try:
        indices = fetch_current_data(INDEX_TICKERS)
        exchange_rates = fetch_current_data(EXCHANGE_TICKERS)
        commodities = fetch_current_data(COMMODITY_TICKERS)
        
        return {
            "indices": indices,
            "exchange_rates": exchange_rates,
            "commodities": commodities
        }
    except Exception as e:
        print(f"❌ 실시간 지표 API 처리 오류: {e}")
        raise HTTPException(status_code=500, detail=f"시장 데이터 조회 중 오류가 발생했습니다: {str(e)}")


# [D] 차트용 주가/지수 히스토리 데이터 가져오기 API
@app.get("/api/market/history")
async def get_market_history(ticker: str, period: str = "1mo"):
    """
    특정 티커 코드의 일자별 종가 데이터를 받아
    프론트엔드 차트 라이브러리(Chart.js)가 이해할 수 있는 날짜 리스트와 가격 리스트로 변환해 줍니다.
    """
    try:
        data = fetch_history_data(ticker, period)
        if data.empty:
            return {"dates": [], "prices": []}
        
        # 날짜 포맷 변환 (YYYY-MM-DD)
        dates = [d.strftime("%Y-%m-%d") for d in data.index]
        
        # 종가(Close) 리스트 추출 (numpy float를 파이썬 순수 float로 안전 변환)
        prices = []
        for x in data["Close"].values:
            try:
                # numpy.nan 또는 빈 값 등 예외 처리
                import math
                val = float(x)
                if math.isnan(val):
                    # NaN 값인 경우 직전 가격으로 채우거나 0 처리
                    val = prices[-1] if prices else 0.0
                prices.append(val)
            except Exception:
                prices.append(0.0)
                
        return {
            "dates": dates,
            "prices": prices
        }
    except Exception as e:
        print(f"❌ 히스토리 차트 API 처리 오류: {e}")
        raise HTTPException(status_code=500, detail=f"차트 데이터 조회 중 오류가 발생했습니다: {str(e)}")


# ── 6. 정적 화면 파일(HTML, CSS, JS) 서비스 마운트 ──────────────────
# static 디렉터리를 만들고, 그 안의 정적 파일들을 서비스합니다.
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# static/css 및 static/js 폴더도 구조화하여 미리 생성
os.makedirs(os.path.join(static_dir, "css"), exist_ok=True)
os.makedirs(os.path.join(static_dir, "js"), exist_ok=True)

# /static 경로로 정적 파일 폴더 마운트
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 브라우저에서 'http://localhost:8000/' 으로 접속하면 static/index.html 파일을 기본 화면으로 전달
@app.get("/")
async def read_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "message": "서버가 정상 구동 중입니다. static/index.html 파일이 준비되면 웹 화면이 이곳에 표시됩니다!"
    }


# ── 7. 서버 직접 실행 시 메인 로직 ─────────────────────────────────
if __name__ == "__main__":
    # 포트 8000번으로 웹서버를 작동시킵니다.
    print("\n" + "=" * 60)
    print("[INFO] 금융 AI 챗봇 웹 서버가 곧 실행됩니다.")
    print("[LINK] 브라우저를 열고 http://localhost:8000 에 접속해 주세요!")
    print("=" * 60 + "\n")
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
