from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from groq import Groq
import os, random, requests

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "bht-hard-security-key-999")
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

otp_store = {}

def send_otp(phone, otp):
    api_key = os.environ.get("FAST2SMS_KEY")
    url = "https://www.fast2sms.com/dev/bulkV2"
    querystring = {"variables_values": str(otp), "route": "otp", "numbers": str(phone)}
    headers = {"authorization": api_key, "cache-control": "no-cache"}
    try:
        # GET request Fast2SMS ke liye 100% chalti hai
        r = requests.get(url, headers=headers, params=querystring, timeout=10)
        return r.json()
    except:
        return {"return": False}

@app.route("/")
def index():
    if session.get("verified"): return redirect(url_for("chat_page"))
    return render_template("index.html")

@app.route("/send-otp", methods=["POST"])
def send_otp_route():
    data = request.get_json()
    phone = data.get("phone", "").strip()
    if len(phone) != 10: return jsonify({"success": False, "message": "10 digit dalo!"})
    otp = random.randint(111111, 999999)
    otp_store[phone] = otp
    result = send_otp(phone, otp)
    if result.get("return"): return jsonify({"success": True})
    return jsonify({"success": False, "message": "SMS Fail!"})

@app.route("/verify-otp", methods=["POST"])
def verify_otp_route():
    data = request.get_json()
    phone, otp = data.get("phone", "").strip(), data.get("otp", "").strip()
    if phone in otp_store and str(otp_store[phone]) == str(otp):
        session.clear()
        session["verified"], session["user_id"], session["msg_count"] = True, phone, 0
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Wrong OTP!"})

@app.route("/chat-page")
def chat_page():
    if not session.get("verified"): return redirect(url_for("index"))
    return render_template("index.html", verified=True)

@app.route("/chat", methods=["POST"])
def chat_route():
    if not session.get("verified"): return jsonify({"error": "No Login"}), 403
    if session.get("msg_count", 0) >= 5: return jsonify({"reply": "Limit Over (5/5)!"})
    
    user_msg = request.json.get("message")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": user_msg}]
    )
    session["msg_count"] = session.get("msg_count", 0) + 1
    return jsonify({"reply": response.choices[0].message.content})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
