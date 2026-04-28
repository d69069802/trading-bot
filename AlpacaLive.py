from flask import Flask, request, jsonify
import alpaca_trade_api as tradeapi
import os
import traceback
from dotenv import load_dotenv
from alpaca_trade_api.rest import APIError

load_dotenv()

app = Flask(__name__)

api = tradeapi.REST(
    os.getenv("ALPACA_KEY"),
    os.getenv("ALPACA_SECRET"),
    os.getenv("BASE_URL"),
    api_version="v2"
)

import os

MODE = os.getenv("MODE", "PAPER")
CONFIRM_LIVE = os.getenv("CONFIRM_LIVE", "NO")

confirm_live = CONFIRM_LIVE == "YES"

if MODE == "LIVE":
    print("⚠ LIVE MODE ENABLED")

if MODE == "LIVE" and CONFIRM_LIVE != "YES":
    return {"error": "Live trading disabled by environment"}

@app.route("/", methods=["GET"])
def home():
    return "Server is running", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        # 1. Capture raw data ONCE
        raw_data = request.get_data(as_text=True)
        print(f"RAW DATA RECEIVED: '{raw_data}'")

        # 2. Parse JSON ONCE
        data = request.get_json(force=True, silent=True)

        # 3. Handle non-JSON or Empty alerts
        if data is None:
            print("SKIPPING: Received plain text or invalid JSON. (e.g. crossing alert)")
            return jsonify({"error": "Invalid JSON payload"}), 400

        print("Parsed JSON:", data)

        # 4. Extract Symbol/Ticker
        raw_symbol = (data.get("ticker") or data.get("symbol") or "").strip().upper()
        if raw_symbol.endswith("USD") and "/" not in raw_symbol:
            symbol = raw_symbol[:-3] + "/USD"
        else:
            symbol = raw_symbol

        # 5. Extract Action & Qty
        action = data.get("action", "").lower()
        try:
            qty = float(data.get("qty", 1))
        except:
            qty = 1.0

        # 6. Check Position
        position_qty = 0.0

        print("symbol: ",symbol, "raw_symbol: ",raw_symbol) 

        try:
        #    position = api.get_position(symbol)
            position = api.get_position(raw_symbol)
            position_qty = float(position.qty)
            print(f"Current position for {symbol}: {position_qty}")
        except Exception:
            print(f"No existing position for {symbol}")

        # 7. Logic Guardrails
        print(f"Processing: {action} {qty} {symbol}")
        
        if action == "sell":
            if position_qty <= 0:
                print("REJECTED: No position to sell.")
                return jsonify({"status": "no position to sell"}), 200
            
            if qty > position_qty:
                print(f"Reducing sell qty from {qty} to {position_qty}")
                qty = position_qty

        # 8. Submit Order
        if action in ["buy", "sell"] and qty > 0:
            order = api.submit_order(
                symbol=symbol,
                qty=qty,
                side=action,
                type="market",
                time_in_force="gtc"
                "confirm_live": "YES"
            )
            print(f"SUCCESS: {action.upper()} order placed for {symbol}")
            return jsonify({"status": "order placed", "order_id": order.id}), 200
        
        return jsonify({"error": "Missing symbol or invalid action"}), 400

    except Exception as e:
        print("CRITICAL ERROR:")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)