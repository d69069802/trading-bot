from flask import Flask, request, jsonify
import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import APIError
import os
import traceback
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

api = tradeapi.REST(
    os.getenv("ALPACA_KEY"),
    os.getenv("ALPACA_SECRET"),
    os.getenv("BASE_URL"),
    api_version="v2"
)

@app.route("/webhook", methods=["POST"])

def webhook():
    raw_data = request.get_data(as_text=True)
    print("RAW BODY:", raw_data)

    print("HEADERS:", dict(request.headers))
    
    try:
        # ===============================
        # 1️⃣ Read & Validate JSON
        # ===============================
        data = request.get_json(force=True)

        if not data:
            return jsonify({"error": "Empty JSON"}), 400

        symbol_raw = data.get("ticker") or data.get("symbol")
        action = str(data.get("action", "")).lower()
        qty_raw = data.get("qty")

        if not symbol_raw or action not in ["buy", "sell"]:
            return jsonify({"error": "Invalid symbol or action"}), 400

        if qty_raw is None:
            return jsonify({"error": "Qty missing"}), 400

        # ===============================
        # 2️⃣ Normalize Symbol
        # ===============================
        symbol_raw = symbol_raw.strip().upper()

        #if symbol_raw.endswith("USD") and "/" not in symbol_raw:
        #    symbol = symbol_raw[:-3] + "/USD"
        #else:
        #    symbol = symbol_raw
#start
symbol = data.get("ticker", "").strip().upper()
action = data.get("action", "").lower()

if not symbol or action not in ["buy", "sell"]:
    return jsonify({"error": "invalid symbol or action"}), 400

from alpaca_trade_api.rest import APIError

# Default buy size
default_qty = 0.01  # adjust for crypto

if action == "buy":
    qty = default_qty

elif action == "sell":
    try:
        position = api.get_position(symbol)
        qty = float(position.qty)
    except APIError:
        return jsonify({"status": "no position to sell"}), 200

    if qty <= 0:
        return jsonify({"status": "no position to sell"}), 200

# Submit order
order = api.submit_order(
    symbol=symbol,
    qty=qty,
    side=action,
    type="market",
    time_in_force="gtc"
)

print(f"SUCCESS: {action.upper()} {qty} {symbol}")

#return jsonify({"status": "order placed"}), 200
return jsonify({
        "status": "order placed",
        "symbol": symbol,
        "side": action,
        "qty": qty,
        "order_id": order.id
        }), 200
#ending
    except Exception as e:
        print("CRITICAL ERROR:")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
    
if __name__ == "__main__":
    # Render uses environment variables for Port, defaulting to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)