from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from groq import Groq
import os, random, requests

app = Flask(__name__)

# Railway Variables: SECRET_KEY session security ke liye zaroori hai
app.secret_key = os.environ.get("SECRET_KEY", "bht-hard-security-key-999")
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# OTP store
otp_store = {}

# --- Security Functions ---
def send_otp(phone, otp):
    api_key = os.environ.get("FAST2SMS_KEY")
    url = "https://www.fast2sms.com/dev/bulkV2"
    querystring = {
        "variables_values": str(otp),
        "route": "otp",
        "numbers": str(phone)
    }
    headers = {
        "authorization": api_key,
        "cache-control": "no-cache"
    }
    try:
        r = requests.get(url, headers=headers, params=querystring, timeout=10)
        return r.json()
    except:
        return {"return": False}

# --- Routes ---
@app.route("/")
def index():
    if session.get("verified") and session.get("user_id"):
        return redirect(url_for("chat_page"))
    return render_template("index.html")

@app.route("/send-otp", methods=["POST"])
def send_otp_route():
    data = request.get_json()
    phone = data.get("phone", "").strip()
    if len(phone) != 10 or not phone.isdigit():
        return jsonify({"success": False, "message": "Sahi 10-digit number dalo!"})
    
    otp = random.randint(111111, 999999)
    otp_store[phone] = {"otp": otp}
    
    result = send_otp(phone, otp)
    if result.get("return"):
        return jsonify({"success": True, "message": "OTP bhej diya!"})
    return jsonify({"success": False, "message": "SMS gateway error!"})

@app.route("/verify-otp", methods=["POST"])
def verify_otp_route():
    data = request.get_json()
    phone = data.get("phone", "").strip()
    otp = data.get("otp", "").strip()
    
    if phone in otp_store and str(otp_store[phone]["otp"]) == str(otp):
        session.clear()
        session["verified"] = True
        session["user_id"] = phone
        session["msg_count"] = 0
        del otp_store[phone]
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Galat OTP! Entry Denied."})

@app.route("/chat-page")
def chat_page():
    if not session.get("verified"):
        return redirect(url_for("index"))
    return render_template("index.html", verified=True)

@app.route("/chat", methods=["POST"])
def chat_route():
    if not session.get("verified") or not session.get("user_id"):
        return jsonify({"error": "Unauthorized Access!"}), 403
    
    count = session.get("msg_count", 0)
    if count >= 5:
        return jsonify({"reply": "⚠️ Limit reached! Aapne 5 free messages use kar liye hain."})
    
    user_msg = request.json.get("message")
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": user_msg}]
        )
        session["msg_count"] = count + 1
        return jsonify({"reply": response.choices[0].message.content})
    except Exception as e:
        return jsonify({"reply": "AI Busy hai, baad mein try karein."})

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
