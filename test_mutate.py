import os
import sys
from dotenv import load_dotenv
load_dotenv()
from agent.finance_agent import create_finance_agent

agent = create_finance_agent()

chat_messages = [{"role": "user", "content": "삼성전자 주가 알려줘"}]
print("Before:", len(chat_messages))
response = agent.invoke({"messages": chat_messages})
print("After invoke:", len(chat_messages))
print("chat_messages:", chat_messages)
