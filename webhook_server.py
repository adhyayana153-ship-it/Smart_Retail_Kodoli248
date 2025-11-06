from flask import Flask, request, jsonify
import sqlite3
import hmac
import hashlib
import os

app = Flask(__name__)

# Use environment variable for security
DB_PATH = "kirana_store.db"
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "defaultsecret")

@app.route("/razorpay-webhook", methods=["POST"])
def razorpay_webhook():
    payload = request.data
    signature = request.headers.get("X-Razorpay-Signature")

    expected_signature = hmac.new(WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_signature, signature):
        return "Invalid signature", 400

    data = request.json
    event = data.get("event")
    if event == "payment.captured":
        payment = data["payload"]["payment"]["entity"]
        payment_id = payment["id"]
        receipt = payment.get("notes", {}).get("receipt", "")

        if receipt:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("UPDATE transactions SET txn_id=? WHERE id=?", (payment_id, receipt))
            conn.commit()
            conn.close()
            print(f"✅ Payment captured: {payment_id} for transaction {receipt}")

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
