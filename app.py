from flask import Flask, render_template, request, jsonify, session
from groq import Groq
import os
import random
import requests

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ss-ai-2026")

# Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# OTP storage
otp_store = {}


# ---------------- HOME ----------------
@app.route("/")
def index():
    return render_template("index.html")


# ---------------- SEND OTP ----------------
@app.route("/send_otp", methods=["POST"])
def send_otp():

    phone = request.json.get("phone")

    otp = str(random.randint(100000, 999999))
    otp_store[phone] = otp

    # Example SMS API (replace with your service)
    url = "https://www.fast2sms.com/dev/bulkV2"

    payload = {
        "authorization": os.environ.get("FAST2SMS_API_KEY"),
        "route": "otp",
        "variables_values": otp,
        "numbers": phone
    }

    try:
        requests.post(url, data=payload)
    except:
        print("SMS sending failed")

    return jsonify({"status": "OTP sent"})


# ---------------- VERIFY OTP ----------------
@app.route("/verify_otp", methods=["POST"])
def verify_otp():

    phone = request.json.get("phone")
    otp = request.json.get("otp")

    if otp_store.get(phone) == otp:

        session["user"] = phone
        session["history"] = []

        return jsonify({"status": "verified"})

    else:
        return jsonify({"status": "invalid"})


# ---------------- AI CHAT ----------------
@app.route("/chat", methods=["POST"])
def chat():

    if "user" not in session:
        return jsonify({"reply": "Please login first."})

    user_msg = request.json.get("message")

    history = session.get("history", [])

    history.append({
        "role": "user",
        "content": user_msg
    })

    try:

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=history
        )

        ai_reply = response.choices[0].message.content

    except Exception as e:

        ai_reply = "AI error: " + str(e)

    history.append({
        "role": "assistant",
        "content": ai_reply
    })

    session["history"] = history

    return jsonify({"reply": ai_reply})


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():

    session.clear()

    return jsonify({"status": "logged_out"})


# ---------------- RUN SERVER ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
