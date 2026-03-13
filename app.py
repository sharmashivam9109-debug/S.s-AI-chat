from flask import Flask, render_template, request, jsonify
from google import genai
import os

app = Flask(__name__)

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat_route():
    user_msg = request.json.get("message")
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=user_msg
    )
    return jsonify({"reply": response.text})

if __name__ == "__main__":
    app.run(debug=True)
