import json
from langchain_core.tools import tool


@tool
def search_flights(origin: str, destination: str, date: str, return_date: str = None) -> str:
    """
    Searches for flight information.
    Takes origin, destination, and date (YYYY-MM-DD) as required.
    Optional: return_date (YYYY-MM-DD) for round trips.
    Returns a JSON string of flight details or an error message.
    """
    print(f"Searching flights from {origin} to {destination} on {date}")
    if return_date:
        print(f"Returning on {return_date}")

    # In a real application, you would integrate with a flight API here
    # For demonstration, we'll return mock data.
    mock_flights = {
        "London_Paris_2025-07-15": {
            "flights": [
                {"airline": "Air France", "flight_number": "AF123", "departure_time": "09:00", "arrival_time": "10:15", "price": "€85"},
                {"airline": "British Airways", "flight_number": "BA456", "departure_time": "11:00", "arrival_time": "12:15", "price": "€95"},
            ]
        },
        "NewYork_Tokyo_2025-08-01": {
            "flights": [
                {"airline": "Japan Airlines", "flight_number": "JL006", "departure_time": "14:00", "arrival_time": "17:00 next day", "price": "$1200"},
            ]
        },
    }
    key = f"{origin}_{destination}_{date}"
    if return_date:
        key += f"_{return_date}"

    data = mock_flights.get(key.replace('-', '_')) # Adjust key for mock data lookup
    if data:
        return json.dumps(data)
    else:
        return json.dumps({"error": "No flights found for the given criteria. Please try another date or destination."})

@tool
def get_hotels(location: str, check_in_date: str, check_out_date: str, num_guests: int = 1) -> str:
    """
    Searches for hotel information.
    Takes location, check_in_date (YYYY-MM-DD), and check_out_date (YYYY-MM-DD) as required.
    Optional: num_guests.
    Returns a JSON string of hotel details or an error message.
    """
    print(f"Searching hotels in {location} from {check_in_date} to {check_out_date} for {num_guests} guests")

    # In a real application, you would integrate with a hotel API here
    mock_hotels = {
        "Paris_2025-07-15_2025-07-18": {
            "hotels": [
                {"name": "Hotel Louvre", "stars": 4, "price_per_night": "€200", "availability": "yes"},
                {"name": "Eiffel Tower Inn", "stars": 3, "price_per_night": "€150", "availability": "limited"},
            ]
        },
        "Tokyo_2025-08-01_2025-08-07": {
            "hotels": [
                {"name": "Shinjuku Grand", "stars": 5, "price_per_night": "$350", "availability": "yes"},
            ]
        },
    }
    key = f"{location}_{check_in_date}_{check_out_date}"
    data = mock_hotels.get(key.replace('-', '_')) # Adjust key for mock data lookup
    if data:
        return json.dumps(data)
    else:
        return json.dumps({"error": "No hotels found for the given criteria."})

@tool
def get_local_attractions(location: str, category: str = None) -> str:
    """
    Gets information about local attractions in a given location.
    Optional: category (e.g., "museums", "parks", "restaurants").
    Returns a JSON string of attractions or an error message.
    """
    print(f"Getting local attractions in {location}, category: {category if category else 'all'}")

    # In a real application, you would integrate with a local attractions API
    mock_attractions = {
        "Paris": {
            "museums": ["Louvre Museum", "Musée d'Orsay"],
            "parks": ["Luxembourg Gardens", "Tuileries Garden"],
            "restaurants": ["Le Jules Verne (Eiffel Tower)", "Septime"],
            "all": ["Louvre Museum", "Eiffel Tower", "Notre Dame Cathedral", "Arc de Triomphe", "Sacre-Cœur Basilica"]
        },
        "Tokyo": {
            "museums": ["Tokyo National Museum", "Ghibli Museum"],
            "parks": ["Shinjuku Gyoen National Garden", "Ueno Park"],
            "restaurants": ["Sukiyabashi Jiro", "Ichiran Ramen"],
            "all": ["Tokyo Skytree", "Senso-ji Temple", "Shibuya Crossing", "Imperial Palace", "Meiji Jingu Shrine"]
        }
    }
    attractions = mock_attractions.get(location)
    if attractions:
        if category and category in attractions:
            return json.dumps({"attractions": attractions[category]})
        elif category:
            return json.dumps({"error": f"No attractions found for category '{category}' in {location}."})
        else:
            return json.dumps({"attractions": attractions["all"]})
    else:
        return json.dumps({"error": f"No attraction data available for {location}."})