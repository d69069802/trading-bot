from dotenv import load_dotenv
import os

load_dotenv()

print("ALPACA_KEY:", os.getenv("ALPACA_KEY"))
print("ALPACA_SECRET:", os.getenv("ALPACA_SECRET"))
print("BASE_URL:", os.getenv("BASE_URL"))
print("SECRET_KEY:", os.getenv("SECRET_KEY"))