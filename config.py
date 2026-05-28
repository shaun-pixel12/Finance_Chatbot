"""
config.py - 설정 관리 파일

.env 파일에 저장된 API 키와 모델 정보를 안전하게 불러옵니다.
코드에 API 키를 직접 적지 않고, 이 파일을 통해 가져옵니다.
"""

import os
from dotenv import load_dotenv

# .env 파일의 내용을 읽어서 환경 변수로 등록합니다
load_dotenv()

# ── API 설정 ──────────────────────────────────────────
# OPENAI_API_KEY: AI 모델에 접속하기 위한 인증 키
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OPENAI_API_BASE: AI 모델 서버의 주소 (URL)
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")

# MODEL_NAME: 사용할 AI 모델의 이름
MODEL_NAME = os.getenv("MODEL_NAME", "openai/gpt-4o-mini")
