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

        if symbol_raw.endswith("USD") and "/" not in symbol_raw:
            symbol = symbol_raw[:-3] + "/USD"
        else:
            symbol = symbol_raw

        # ===============================
        # 3️⃣ Safe Quantity Conversion
        # ===============================
        try:
            qty = float(qty_raw)
            if qty <= 0:
                return jsonify({"error": "Qty must be positive"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid qty format"}), 400

        # ===============================
        # 4️⃣ Position Check
        # ===============================
        try:
            position = api.get_position(symbol)
            position_qty = float(position.qty)
        except APIError as e:
            if "position does not exist" in str(e):
                position_qty = 0
            else:
                raise

        # Prevent overselling
        if action == "sell":
            if position_qty <= 0:
                return jsonify({"status": "No position to sell"}), 200
            qty = min(qty, position_qty)

        # ===============================
        # 5️⃣ Submit Order
        # ===============================
        order = api.submit_order(
            symbol=symbol,
            qty=qty,
            side=action,
            type="market",
            time_in_force="gtc"
        )

        return jsonify({
            "status": "order placed",
            "symbol": symbol,
            "side": action,
            "qty": qty,
            "order_id": order.id
        }), 200

    except Exception as e:
        print("CRITICAL ERROR:")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
    
if __name__ == "__main__":
    # Render uses environment variables for Port, defaulting to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)