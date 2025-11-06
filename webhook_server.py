from flask import Flask, request, jsonify
import psycopg2
import hmac
import hashlib
import os

app = Flask(__name__)

# PostgreSQL connection details from Railway Environment
DB_CONFIG = {
    "host": os.environ.get("gondola.proxy.rlwy.net"),
    "database": os.environ.get("railway"),
    "user": os.environ.get("postgres"),
    "password": os.environ.get("uCpvFYAOYMHldAAAxkcCtdfGeLspeuVO"),
    "port": os.environ.get("29621", 5432)
}

WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "defaultsecret")

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

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
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("UPDATE transactions SET txn_id=%s WHERE id=%s", (payment_id, receipt))
            conn.commit()
            conn.close()
            print(f"✅ Payment captured: {payment_id} for transaction {receipt}")

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
