import json
from flask import Flask, Response, render_template, request, jsonify
from llm.main_llm import generate_llm_response

app = Flask(__name__)

# In-memory storage for messages (replace with a database in a real app)
messages = []


@app.route('/')
def index():
    return render_template('planner.html')


@app.route('/plan_trip', methods=['POST'])
def plan_trip():
    """Generate a streamed day-by-day travel plan from the submitted form data."""
    data = request.json or {}

    # Build a rich prompt from the form fields
    prompt_lines = [
        "Generate an engaging, detailed day-by-day travel itinerary in markdown format using the following trip information:",
        f"- Trip name: {data.get('trip_name','My Trip')}",
        f"- Origin city: {data.get('origin','')}",
        f"- Destination city: {data.get('destination','')}",
        f"- Start date: {data.get('start_date','')}",
        f"- Trip length (days): {data.get('length_days','')}",
        f"- Travelers: {data.get('travelers','')}",
        f"- Budget: {data.get('budget','')}",
        f"- Interests: {data.get('interests','')}",
        f"- Accessibility considerations: {data.get('accessibility','None')}\n",
        "Please include daily schedules with morning/afternoon/evening suggestions, local dining recommendations, and travel tips."
    ]
    prompt = "\n".join(prompt_lines)

    # Create minimal message history expected by LLM helper
    message_history = [{"sender": "user", "text": prompt}]

    def stream_llm():
        for chunk in generate_llm_response(message_history):
            yield f'data: {json.dumps({"token": chunk})}\n\n'

    return Response(stream_llm(), mimetype='text/event-stream')


@app.route('/send_message', methods=['POST'])
def send_message():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"status": "error", "message": "No message provided"}), 400

    messages.append({"sender": "user", "text": user_message})

    def stream_llm_response():
        full_response_text = ""
        # The `generate_llm_response` function is now a generator that takes the whole history
        for chunk in generate_llm_response(messages):
            full_response_text += chunk
            # Yield each chunk in the SSE format
            yield f'data: {json.dumps({"token": chunk})}\n\n'
        
        # After the stream is complete, save the full message
        messages.append({"sender": "bot", "text": full_response_text})

    return Response(stream_llm_response(), mimetype='text/event-stream')


@app.route('/get_messages', methods=['GET'])
def get_messages():
    # Return messages in a format expected by the frontend
    return jsonify({"messages": messages})


if __name__ == '__main__':
    app.run(debug=True)
