import os
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Configure Google Generative AI (Gemini). Expect the GOOGLE_API_KEY in environment or .env.
#api_key = os.getenv("GOOGLE_API_KEY")
#if not api_key:
    #raise RuntimeError("Please set GOOGLE_API_KEY in environment variables or in a .env file.")

#genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash")

app = Flask(__name__)

@app.route("/")
def index():
    """Serve the chat UI."""
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    """Receive user message and return model response as JSON. test"""
    user_msg = request.json.get("message", "")
    if not user_msg:
        return jsonify({"error": "Empty message"}), 400
    try:
        response = model.generate_content(user_msg)
        text = response.text if hasattr(response, "text") else str(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"response": text})

if __name__ == "__main__":
    app.run(debug=True)
