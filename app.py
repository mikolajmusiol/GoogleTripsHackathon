from flask import Flask, render_template, request, jsonify
from llm.main_llm import generate_llm_response  # Assuming this function exists and works as described

app = Flask(__name__)

# In-memory storage for messages (replace with a database in a real app)
messages = []


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/send_message', methods=['POST'])
def send_message():
    user_message = request.json.get('message')
    if user_message:
        messages.append({"sender": "user", "text": user_message})  # Append user message first

        llm_response = generate_llm_response(user_message)  # Call the LLM function
        print(llm_response)
        messages.append({"sender": "bot", "text": llm_response})  # Append LLM response
        print(messages)
        return jsonify({"status": "success", "message": "Message received", "messages": messages})
    return jsonify({"status": "error", "message": "No message provided"}), 400


@app.route('/get_messages', methods=['GET'])
def get_messages():
    return jsonify(messages)


if __name__ == '__main__':
    app.run(debug=True)
