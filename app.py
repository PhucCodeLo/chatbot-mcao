from flask import Flask, render_template, request, jsonify, session
from pinecone_chatbot import chat_with_bot
from flask_cors import CORS
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

@app.route("/")
def index():
    return render_template("chat.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "")
    history = session.get("history", None)
    bot_response, new_history = chat_with_bot(user_input, history)
    # Chỉ lưu 5 lượt chat gần nhất vào session để tránh cookie quá lớn
    session["history"] = new_history[-5:]
    return jsonify({"bot": bot_response})

if __name__ == "__main__":
    app.run(debug=True)
