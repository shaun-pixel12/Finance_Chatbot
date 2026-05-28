import os
import sys
from dotenv import load_dotenv
load_dotenv()

from tools.market_tools import INDEX_TICKERS, fetch_current_data

print("Fetching index data...")
try:
    data = fetch_current_data(INDEX_TICKERS)
    print("Index data:", data)
except Exception as e:
    print("Error:", e)
