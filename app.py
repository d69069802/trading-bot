from flask import Flask, request, jsonify
import alpaca_trade_api as tradeapi
import os
import traceback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize Alpaca API
api = tradeapi.REST(
    os.getenv("ALPACA_KEY"),
    os.getenv("ALPACA_SECRET"),
    os.getenv("BASE_URL"),
    api_version="v2"
)

@app.route("/", methods=["GET"])
def home():
    return "Server is running", 200

@app.route("/webhook", methods=["POST"])
@app.route("/webhook", methods=["POST"])
def webhook():
    # ADD THESE TWO LINES FOR DEBUGGING:
    raw_data = request.get_data(as_text=True)
    print(f"RAW DATA RECEIVED: '{raw_data}'")

    data = request.get_json(force=True, silent=True)
    # ... rest of your code

    try:
        # 1. Use force=True to ignore Content-Type
        # 2. Use silent=True to prevent a 400 error if JSON is malformed
        data = request.get_json(force=True, silent=True)

        if data is None:
            print("ERROR: Received empty or invalid JSON")
            return jsonify({"error": "Invalid JSON payload"}), 400

        print("Incoming data:", data)

        # FIX: Check for 'symbol' OR 'ticker' to avoid validation failure
        symbol = data.get("symbol") or data.get("ticker")
        action = data.get("action", "").lower()
        
        # following 2 lines suggested by ChatGpt
        #symbol = data["ticker"].replace("USD", "/USD")  # XRPUSD → XRP/USD
        #symbol = data["ticker"].strip().upper().replace("USD", "/USD")

        print("RAW DATA:", data)
        raw_symbol = data.get("ticker", "").strip()

        if raw_symbol.endswith("USD") and "/" not in raw_symbol:
            symbol = raw_symbol[:-3] + "/USD"
        else:
            symbol = raw_symbol

        print("Converted symbol:", symbol)
        
        side = data["action"]

        try:
            position = api.get_position(symbol)
            position_qty = int(float(position.qty))
        except:
            position_qty = 0

        if action == "sell" and position_qty == 0:
            return jsonify({"status": "no position to sell"}), 200
    
        qty = min(qty, position_qty)
        
        # FIX: Ensure qty is handled safely (converting string to float then int)
        #try:
        #    qty_raw = data.get("qty", 1)
        #    qty = int(float(qty_raw))
        #except (ValueError, TypeError):
        #    qty = 1

        qty = float(data.get("qty", 1))

        # Validation Check
        if not symbol or not action:
            print(f"VALIDATION FAILED: symbol={symbol}, action={action}")
            return jsonify({"error": "missing symbol or action in JSON"}), 400

        # Execute Trade
        if action in ["buy", "sell"]:
            order = api.submit_order(
                symbol=symbol,
                qty=qty,
                side=action,
                type="market",
                time_in_force="gtc"
            )
            print(f"SUCCESS: {action.upper()} order placed for {symbol}")
            return jsonify({"status": "order placed", "order_id": order.id}), 200
        
        else:
            print(f"ERROR: Invalid action received: {action}")
            return jsonify({"error": "invalid action"}), 400

    except Exception as e:
        # This provides the full error log in Render so you can see exactly what failed
        print("CRITICAL ERROR:")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Render uses environment variables for Port, defaulting to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)