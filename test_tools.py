import json
from tools.amadeus_flight_tool import AmadeusFlightTool
from tools.booking_hotel_tool import BookingHotelTool

flight_tool = AmadeusFlightTool()
flight_params = {
    "origin": "JFK", 
    "destination": "LAX", 
    "departure_date": "2025-10-01",
    "adults": 2, 
    "max_stops": 1, 
    "avoid_stops": ["ORD"]
}
print(flight_tool._run(json.dumps(flight_params)))

hotel_tool = BookingHotelTool()
hotel_params = {
    "destination": "Los Angeles", 
    "check_in_date": "2025-10-01",
    "check_out_date": "2025-10-05", 
    "price_min": 50, 
    "price_max": 200, 
    "num_days": 4
}
print(hotel_tool._execute(**hotel_params))
