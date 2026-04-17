from flask import Flask, request, jsonify
import alpaca_trade_api as tradeapi
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

api = tradeapi.REST(
    os.getenv("ALPACA_KEY"),
    os.getenv("ALPACA_SECRET"),
    os.getenv("BASE_URL"),
    api_version="v2"
)

@app.route("/", methods=["GET"])
def home():
    return "Server is running"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)

    print("Incoming data:", data)

    symbol = data.get("symbol")
    action = data.get("action", "").lower()
    qty = int(data.get("qty", 1))

    if not symbol or not action:
        return jsonify({"error": "missing data"}), 400

    try:
        if action == "buy":
            api.submit_order(
                symbol=symbol,
                qty=qty,
                side="buy",
                type="market",
                time_in_force="gtc"
            )

        elif action == "sell":
            api.submit_order(
                symbol=symbol,
                qty=qty,
                side="sell",
                type="market",
                time_in_force="gtc"
            )

        else:
            return jsonify({"error": "invalid action"}), 400

        return jsonify({"status": "order placed"}), 200

    except Exception as e:
        print("ALPACA ERROR:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("Starting Flask server...")
    app.run(host="0.0.0.0", port=5000)



