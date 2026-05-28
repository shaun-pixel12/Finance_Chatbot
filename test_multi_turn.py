import os
import sys

from dotenv import load_dotenv
load_dotenv()

from agent.finance_agent import create_finance_agent

agent = create_finance_agent()

chat_messages = []
question1 = "삼성전자 주가 알려줘"
chat_messages.append({"role": "user", "content": question1})

print("Turn 1 invoking...")
try:
    response1 = agent.invoke({"messages": chat_messages})
    answer1 = response1["messages"][-1].content
    print("Answer 1:", answer1.encode("utf-8"))
    
    # Simulate chatbot_tab logic
    chat_messages.append({"role": "assistant", "content": answer1})
    
    question2 = "애플 주가도 알려줘"
    chat_messages.append({"role": "user", "content": question2})
    
    print("Turn 2 invoking...")
    response2 = agent.invoke({"messages": chat_messages})
    answer2 = response2["messages"][-1].content
    print("Answer 2:", answer2.encode("utf-8"))
except Exception as e:
    print("Error:", str(e).encode("utf-8"))
