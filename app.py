import json
from flask import Flask, Response, render_template, request, jsonify
from llm.main_llm import generate_llm_response, model

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
        "The output MUST be GitHub-flavored markdown and follow this exact structure:\n\n# <center>Trip Name (replace)</center>\n\n**Dates:** YYYY-MM-DD to YYYY-MM-DD (**Length:** X days)  \\n**Approx. Budget:** Provide a realistic overall budget in the local destination currency and USD.  \\n**Travelers:** <number>  \\n**Interests:** comma list  \\n\n---\n\n## Day 1 – <Short catchy day title>\n- Morning: ...\n- Afternoon: ...\n- Evening: ...\n- Dining Highlight: ...\n\n> Insider Tip: ...\n\n---\n\n(Repeat for each day)\n\nEnd the plan with a short inspirational quote.\n\nEnsure headings, bold text, and bullet formatting render beautifully."
    ]
    prompt = "\n".join(prompt_lines)

    # Create minimal message history expected by LLM helper
    message_history = [{"sender": "user", "text": prompt}]

    from google.generativeai import types as genai_types

    search_tool = None
    try:
        search_tool = genai_types.Tool(google_search=genai_types.GoogleSearch())
    except AttributeError:
        # Older library version without GoogleSearch; proceed without grounding
        pass

    def stream_llm():
        # Use Gemini with Google Search grounding enabled
        if search_tool:
            stream_iter = model.generate_content(prompt, tools=[search_tool], stream=True)
        else:
            stream_iter = model.generate_content(prompt, stream=True)
        for chunk in stream_iter:
            yield f'data: {json.dumps({"token": chunk.text})}\n\n'

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



@app.route('/calendar_ics', methods=['POST'])
def calendar_ics():
    """Create a simple iCalendar file from the generated plan."""
    data = request.json or {}
    plan_text = data.get('plan', '')
    trip_name = data.get('trip_name', 'Trip')
    start_date = data.get('start_date')  # YYYY-MM-DD

    # naive parse days
    lines = plan_text.splitlines()
    day_titles = [ln for ln in lines if ln.startswith('## Day')]
    from datetime import datetime, timedelta
    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    except Exception:
        return jsonify({'error': 'invalid date'}), 400

    events = []
    for idx, title in enumerate(day_titles):
        day_dt = start_dt + timedelta(days=idx)
        dt_str = day_dt.strftime('%Y%m%d')
        events.append(f"BEGIN:VEVENT\nUID:{idx}@googletrips\nDTSTAMP:{dt_str}T090000Z\nDTSTART;VALUE=DATE:{dt_str}\nSUMMARY:{title[3:]}\nEND:VEVENT")

    ics = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Google Trips Planner//EN\n" + "\n".join(events) + "\nEND:VCALENDAR"
    from io import BytesIO
    buffer = BytesIO(ics.encode('utf-8'))
    buffer.seek(0)
    return Response(buffer, mimetype='text/calendar', headers={
        'Content-Disposition': f'attachment; filename="{trip_name}.ics"'
    })


if __name__ == '__main__':
    app.run(debug=True)
