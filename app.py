import json
import datetime
from flask import Flask, Response, render_template, request, jsonify
from llm.main_llm import generate_llm_response, model

app = Flask(__name__)

# In-memory storage for messages (replace with a database in a real app)
messages = []

# ---------- Multi-agent helper functions ----------
import google.generativeai as genai

def _gemini_json(prompt: str):
    """Call Gemini and return parsed JSON or None."""
    resp = model.generate_content(prompt)
    try:
        return json.loads(resp.text)
    except json.JSONDecodeError:
        return None

def get_weather_forecast(destination: str, start_date: str, num_days: int):
    dates = []
    try:
        start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        dates = [(start_dt + datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(num_days)]
    except Exception:
        return []
    schema = {"type":"array","items":{"type":"object","properties":{
        "date":{"type":"string"},"summary":{"type":"string"},"high_c":{"type":"number"},"low_c":{"type":"number"}},
        "required":["date","summary","high_c","low_c"],"propertyOrdering":["date","summary","high_c","low_c"]}}
    prompt = (
        f"Provide 1-sentence weather summary and high/low in Celsius for each date in {destination}. "
        f"Return ONLY JSON matching this schema: {json.dumps(schema)}. Dates: {dates}.")
    return _gemini_json(prompt) or []

def get_flight_options(origin: str, destination: str, start_date: str):
    schema = {"type":"array","items":{"type":"object","properties":{
        "airline":{"type":"string"},"flight_no":{"type":"string"},"depart_time":{"type":"string"},"arrive_time":{"type":"string"},
        "price_usd":{"type":"number"},"link":{"type":"string"}},
        "required":["airline","flight_no","depart_time","arrive_time","price_usd","link"],"propertyOrdering":["airline","flight_no","depart_time","arrive_time","price_usd","link"]}}
    prompt = (
        f"Find up to 3 economy flights from {origin} to {destination} near {start_date}. Prices USD. "
        f"Return ONLY JSON per schema: {json.dumps(schema)}.")
    return _gemini_json(prompt) or []

def get_hotel_options(destination: str, start_date: str, num_days: int):
    end_date = ""
    try:
        end_date = (datetime.datetime.strptime(start_date, "%Y-%m-%d") + datetime.timedelta(days=num_days)).strftime("%Y-%m-%d")
    except Exception:
        pass
    schema = {"type":"array","items":{"type":"object","properties":{
        "name":{"type":"string"},"location":{"type":"string"},"price_per_night_usd":{"type":"number"},
        "total_price_usd":{"type":"number"},"rating":{"type":"number"},"link":{"type":"string"}},
        "required":["name","location","price_per_night_usd","total_price_usd","rating","link"],
        "propertyOrdering":["name","location","price_per_night_usd","total_price_usd","rating","link"]}}
    prompt = (
        f"List 3 highly rated hotels in {destination} between {start_date} and {end_date}. Prices USD. "
        f"Return ONLY JSON per schema: {json.dumps(schema)}.")
    return _gemini_json(prompt) or []


@app.route('/')
def index():
    return render_template('planner.html')


@app.route('/plan_trip', methods=['POST'])
def plan_trip():
    """Generate a streamed day-by-day travel plan from the submitted form data."""
    data = request.json or {}

    # gather agent data
    length_days = int(data.get('length_days', 1) or 1)
    weather = get_weather_forecast(data.get('destination',''), data.get('start_date',''), length_days)
    flights = get_flight_options(data.get('origin',''), data.get('destination',''), data.get('start_date',''))
    hotels = get_hotel_options(data.get('destination',''), data.get('start_date',''), length_days)

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
        "Day-by-day plan including a weather box for each day and a top section with flight options (use links) and recommended hotels. Use the provided JSON context strictly.",
        "\nJSON_CONTEXT::\n" + json.dumps({"weather": weather, "flights": flights, "hotels": hotels})]
    prompt = "\n".join(prompt_lines)

    # Create minimal message history expected by LLM helper
    message_history = [{"sender": "user", "text": prompt}]

    from data_sources.web_search import create_search_web_tool

    # GoogleSearch removed; Tavily search tool can be utilized elsewhere if needed
# tavily_search_tool = create_search_web_tool()

    def stream_llm():
        # Use Gemini with Google Search grounding enabled
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



from flask import send_from_directory

@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('images', filename)


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
