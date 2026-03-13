from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from groq import Groq
import os, random, requests

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ss-ai-secret-key")
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

otp_store = {}

def send_otp(phone, otp):
    api_key = os.environ.get("FAST2SMS_KEY")
    url = "https://www.fast2sms.com/dev/bulkV2"
    
    # Fast2SMS OTP route ke liye exact ye format chahiye
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
        # GET request zyada reliably kaam karta hai Fast2SMS OTP ke liye
        r = requests.get(url, headers=headers, params=querystring, timeout=10)
        print(f"Fast2SMS Response: {r.text}") # Ye logs mein dikhega agar error aaye
        return r.json()
    except Exception as e:
        print(f"SMS Error: {e}")
        return {"return": False}

@app.route("/")
def index():
    if session.get("verified"):
        return redirect(url_for("chat_page"))
    return render_template("index.html")

@app.route("/send-otp", methods=["POST"])
def send_otp_route():
    data = request.get_json()
    phone = data.get("phone", "").strip()
    
    if len(phone) != 10:
        return jsonify({"success": False, "message": "10-digit number dalo!"})
    
    otp = random.randint(100000, 999999)
    otp_store[phone] = otp
    
    result = send_otp(phone, otp)
    if result.get("return") == True:
        return jsonify({"success": True, "message": "OTP bhej diya gaya!"})
    
    # Agar fail hua toh Fast2SMS ka error message dikhayega
    error_msg = result.get("message", "SMS fail ho gaya")
    return jsonify({"success": False, "message": f"Error: {error_msg}"})

@app.route("/verify-otp", methods=["POST"])
def verify_otp_route():
    data = request.get_json()
    phone = data.get("phone", "").strip()
    otp = data.get("otp", "").strip()
    
    if phone in otp_store and str(otp_store[phone]) == str(otp):
        session["verified"] = True
        session["phone"] = phone
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Galat OTP!"})

@app.route("/chat-page")
def chat_page():
    if not session.get("verified"):
        return redirect(url_for("index"))
    return render_template("index.html", verified=True)

@app.route("/chat", methods=["POST"])
def chat_route():
    if not session.get("verified"):
        return jsonify({"error": "Unauthorized"}), 401
    user_msg = request.json.get("message")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": user_msg}]
    )
    return jsonify({"reply": response.choices[0].message.content})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
