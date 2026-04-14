import os
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi

load_dotenv()

api = tradeapi.REST(
    os.getenv("ALPACA_KEY"),
    os.getenv("ALPACA_SECRET"),
    os.getenv("BASE_URL"),
    api_version="v2"
)

account = api.get_account()

print("Account status:", account.status)
print("Buying power:", account.buying_power)