import os
import sys

# Load env vars
from dotenv import load_dotenv
load_dotenv()

from agent.finance_agent import create_finance_agent

agent = create_finance_agent()

print("Agent created. Invoking...")
try:
    response = agent.invoke({
        "messages": [{"role": "user", "content": "삼성전자 주가 알려줘"}]
    })
    print("Response received:")
    # sys.stdout에 utf-8로 강제 인코딩해서 출력
    sys.stdout.buffer.write(str(response).encode("utf-8"))
except Exception as e:
    print("Error:", str(e).encode("utf-8"))
