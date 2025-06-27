import json
import datetime
from flask import Flask, Response, render_template, request, jsonify
from llm.main_llm import generate_llm_response, model
from google.generativeai import types as genai_types
from flask import send_from_directory

app = Flask(__name__)

# In-memory storage for messages (replace with a database in a real app)
messages = []

# ---------- Multi-agent helper functions ----------

from data_sources.web_search import create_search_web_tool

# ----- Web search helper -----
_tavily_tool = create_search_web_tool()

def _web_search(query: str, max_results: int = 5):
    """Return Tavily web search results list (max `max_results` items)."""
    try:
        results = _tavily_tool.invoke(query)
        # ensure list-like response
        if isinstance(results, list):
            trimmed = results[:max_results]
        else:
            trimmed = list(results)[:max_results]
        print('[DEBUG] Tavily query:', query, 'results:', len(trimmed))
        return trimmed
    except Exception as e:
        print('[DEBUG] Tavily search error', e)
        return []

def get_weather_forecast(destination: str, start_date: str, num_days: int):
    """Return weather-related snippets via Tavily search."""
    query = f"{destination} weather forecast next {num_days} days"
    return _web_search(query)

def get_flight_options(origin: str, destination: str, start_date: str):
    """Return flight option snippets via Tavily search."""
    query = f"flights {origin} to {destination} {start_date} economy"
    return _web_search(query)

def get_hotel_options(destination: str, start_date: str, num_days: int):
    """Return hotel recommendation snippets via Tavily search."""
    query = f"best hotels in {destination} near {start_date}"
    return _web_search(query)

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
    print('[DEBUG] Weather len', len(weather))
    flights = get_flight_options(data.get('origin',''), data.get('destination',''), data.get('start_date',''))
    print('[DEBUG] Flights len', len(flights))
    hotels = get_hotel_options(data.get('destination',''), data.get('start_date',''), length_days)
    print('[DEBUG] Hotels len', len(hotels))

    # Fetch additional broader web context using Tavily
    local_search_tool = create_search_web_tool()
    search_query = f"{data.get('destination','')} travel guide top attractions"
    try:
        web_results = local_search_tool.invoke(search_query)
    except Exception as e:
        print('[DEBUG] Tavily search error', e)
        web_results = []
    print('[DEBUG] Tavily results len', len(web_results))

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
        "\nJSON_CONTEXT::\n" + json.dumps({"weather": weather, "flights": flights, "hotels": hotels, "web": web_results})]
    prompt = "\n".join(prompt_lines)

    # Create minimal message history expected by LLM helper
    message_history = [{"sender": "user", "text": prompt}]

    return Response(generate_llm_response(message_history), mimetype='text/event-stream')




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
