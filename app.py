from flask import Flask, render_template, request, jsonify, session
from groq import Groq
import os

app = Flask(__name__)
app.secret_key = "secret-key"

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat_route():
    user_msg = request.json.get("message")

    if "chat_history" not in session:
        session["chat_history"] = []

    history = session["chat_history"]

    history.append({
        "role": "user",
        "content": user_msg
    })

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=history
    )

    ai_reply = response.choices[0].message.content

    history.append({
        "role": "assistant",
        "content": ai_reply
    })

    session["chat_history"] = history

    return jsonify({"reply": ai_reply})


if __name__ == "__main__":
    app.run(debug=True)
