from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from groq import Groq
import os, random, requests

app = Flask(__name__)

# Railway Variables se keys lega
app.secret_key = os.environ.get("SECRET_KEY", "anime-secret-key-2024")
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# OTP Store (Memory mein rahega)
otp_store = {}

def send_otp(phone, otp):
    api_key = os.environ.get("FAST2SMS_KEY")
    url = "https://www.fast2sms.com/dev/bulkV2"
    payload = {
        "variables_values": str(otp),
        "route": "otp",
        "numbers": phone,
    }
    headers = {"authorization": api_key}
    try:
        r = requests.post(url, json=payload, headers=headers)
        return r.json()
    except:
        return {"return": False}

@app.route("/")
def index():
    if session.get("verified"):
        return redirect(url_for("welcome"))
    return render_template("index.html")

@app.route("/send-otp", methods=["POST"])
def send_otp_route():
    data = request.get_json()
    phone = data.get("phone", "").strip()
    if len(phone) != 10 or not phone.isdigit():
        return jsonify({"success": False, "message": "Invalid number!"})
    
    otp = random.randint(100000, 999999)
    otp_store[phone] = otp
    result = send_otp(phone, otp)
    
    if result.get("return"):
        return jsonify({"success": True, "message": "OTP sent!"})
    return jsonify({"success": False, "message": "SMS failed. API Key check karein."})

@app.route("/verify-otp", methods=["POST"])
def verify_otp_route():
    data = request.get_json()
    phone = data.get("phone", "").strip()
    otp = data.get("otp", "").strip()
    
    if phone in otp_store and str(otp_store[phone]) == str(otp):
        session["verified"] = True
        session["phone"] = phone
        del otp_store[phone]
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Wrong OTP!"})

@app.route("/welcome")
def welcome():
    if not session.get("verified"):
        return redirect(url_for("index"))
    # Agar aapne chat.html banaya hai toh wahan bhej sakte hain
    return render_template("chat.html", phone=session.get("phone"))

@app.route("/chat", methods=["POST"])
def chat_route():
    if not session.get("verified"):
        return jsonify({"error": "Unauthorized"}), 401
    
    user_msg = request.json.get("message")
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": user_msg}]
        )
        return jsonify({"reply": response.choices[0].message.content})
    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"})

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    # Railway ke liye ye line sabse zaroori hai
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
