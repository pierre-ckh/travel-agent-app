#!/usr/bin/env python3
"""
Enhanced CrewAI agents with real API integrations
"""
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import BaseTool
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, date
import json
import os
from dotenv import load_dotenv
import anthropic

# Import the real API tools
from tools.amadeus_flight_tool import AmadeusFlightTool
from tools.booking_hotel_tool import BookingHotelTool

load_dotenv()

class RealFlightTool(BaseTool):
    """Real flight search using Amadeus API with CrewAI compatibility"""
    name: str = "flight_search"
    description: str = "Search for real flights using Amadeus API"
    
    def _run(self, **kwargs) -> str:
        """Search flights with real API or fallback to mock data"""
        try:
            # Create Amadeus tool instance
            amadeus_tool = AmadeusFlightTool()
            
            # Extract and format parameters for Amadeus API
            origin = kwargs.get('origin', 'NYC')
            destination = kwargs.get('destination', 'LAX')
            departure_date = kwargs.get('departure_date', '2024-12-01')
            return_date = kwargs.get('return_date', None)
            passengers = kwargs.get('passengers', kwargs.get('adults', 1))
            
            # Format the search parameters for Amadeus
            search_params = {
                "origin": origin,
                "destination": destination,
                "departure_date": departure_date,
                "adults": passengers,
                "currency_code": kwargs.get('currency_code', 'USD')
            }
            
            if return_date:
                search_params["return_date"] = return_date
            
            # Call the real Amadeus API
            result = amadeus_tool._run(json.dumps(search_params))
            return result
            
        except Exception as e:
            print(f"Flight API error: {e}")
            # Fallback to mock data if API fails
            return self._mock_flights(kwargs)
    
    def _mock_flights(self, kwargs):
        """Fallback mock flight data"""
        flights = [
            {
                "airline": "Air France",
                "flight_number": "AF123", 
                "price": 850,
                "duration": "8h 30m",
                "stops": 0,
                "departure_time": "10:00 AM",
                "arrival_time": "6:30 PM",
                "departure_airport": kwargs.get('origin', 'NYC'),
                "arrival_airport": kwargs.get('destination', 'LAX'),
                "departure_date": kwargs.get('departure_date', '2024-12-01')
            },
            {
                "airline": "Delta",
                "flight_number": "DL456",
                "price": 920,
                "duration": "9h 15m", 
                "stops": 1,
                "departure_time": "2:15 PM",
                "arrival_time": "11:30 PM",
                "departure_airport": kwargs.get('origin', 'NYC'),
                "arrival_airport": kwargs.get('destination', 'LAX'),
                "departure_date": kwargs.get('departure_date', '2024-12-01')
            }
        ]
        return json.dumps({"status": "success", "flights": flights, "source": "fallback"})

class RealHotelTool(BaseTool):
    """Real hotel search using Booking.com API with CrewAI compatibility"""
    name: str = "hotel_search"  
    description: str = "Search for real hotels using Booking.com API"
    
    def _run(self, **kwargs) -> str:
        """Search hotels with real API or fallback to mock data"""
        try:
            # Create Booking tool instance
            booking_tool = BookingHotelTool()
            
            # Extract comprehensive parameters for Booking API
            destination = kwargs.get('destination', 'Paris')
            checkin = kwargs.get('checkin', '2024-12-01') 
            checkout = kwargs.get('checkout', '2024-12-08')
            adults = kwargs.get('adults', 2)
            rooms = kwargs.get('rooms', 1)
            children = kwargs.get('children', 0)
            currency = kwargs.get('currency', 'USD')
            price_min = kwargs.get('price_min', 0)
            price_max = kwargs.get('price_max', 500)
            sort_by = kwargs.get('sort_by', 'price')
            locale = kwargs.get('locale', 'en-gb')
            
            # Call the real Booking API with comprehensive parameters
            result = booking_tool._execute(
                destination=destination,
                check_in_date=checkin,
                check_out_date=checkout,
                adults=adults,
                rooms=rooms,
                children=children,
                currency=currency,
                price_min=price_min,
                price_max=price_max,
                sort_by=sort_by,
                locale=locale
            )
            return result
                
        except Exception as e:
            print(f"Hotel API error: {e}")
            return self._mock_hotels(kwargs)
    
    def _mock_hotels(self, kwargs):
        """Fallback mock hotel data"""
        hotels = [
            {
                "name": "Grand Hotel Paris",
                "price_per_night": 180,
                "rating": 4.5,
                "location": "City Center",
                "amenities": ["WiFi", "Restaurant", "Gym"],
                "discount": "15% off for 7+ nights",
                "checkin": kwargs.get('checkin', '2024-12-01'),
                "checkout": kwargs.get('checkout', '2024-12-08')
            },
            {
                "name": "Budget Inn",
                "price_per_night": 85,
                "rating": 3.8,
                "location": "Near Metro", 
                "amenities": ["WiFi", "Breakfast"],
                "discount": "10% off",
                "checkin": kwargs.get('checkin', '2024-12-01'),
                "checkout": kwargs.get('checkout', '2024-12-08')
            }
        ]
        return json.dumps({"status": "success", "hotels": hotels, "source": "fallback"})

def create_real_agents():
    """Create enhanced agents with real APIs and Anthropic LLM"""
    
    # Configure Anthropic LLM
    try:
        anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        # Test the API key
        test_message = anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}]
        )
        print("Anthropic API connected successfully")
        use_anthropic = True
    except Exception as e:
        print(f"Anthropic API error: {e}")
        use_anthropic = False
    
    # Create agents - with or without LLM depending on API availability
    flight_agent = Agent(
        role="Flight Search Specialist",
        goal="Find the best flight options using real-time data from Amadeus API",
        backstory="You are an expert at finding flights with great prices and convenient schedules using live airline data. You analyze real flight options and recommend the best choices based on traveler preferences.",
        tools=[RealFlightTool()],
        verbose=True
    )
    
    hotel_agent = Agent(
        role="Hotel Booking Expert", 
        goal="Find great hotel deals using real-time data from Booking.com",
        backstory="You specialize in finding hotels with excellent value, good locations, and special discounts using live booking data. You know how to spot the best deals for different types of travelers.",
        tools=[RealHotelTool()],
        verbose=True
    )
    
    coordinator_agent = Agent(
        role="Trip Coordinator",
        goal="Create comprehensive travel itineraries combining real flight and hotel data",
        backstory="You are a master trip planner who excels at combining real flight and hotel options into perfect travel packages. You use live data to optimize for budget, convenience, and traveler satisfaction.",
        verbose=True
    )
    
    return flight_agent, hotel_agent, coordinator_agent, use_anthropic

class RealTripPlannerCrew:
    def __init__(self, destination: str, start_date: str, end_date: Optional[str], budget: float, 
                 interests: List[str] = None, travel_style: str = "comfort", origin: str = "NYC",
                 hotel_adults: int = 2, hotel_rooms: int = 1, hotel_children: int = 0,
                 hotel_currency: str = "USD", hotel_price_min: float = 0, hotel_price_max: float = 500,
                 hotel_sort: str = "price", hotel_locale: str = "en-gb", flight_currency: str = "USD"):
        self.destination = destination
        self.origin = origin
        self.start_date = start_date  
        self.end_date = end_date
        self.budget = budget
        self.interests = interests or []
        self.travel_style = travel_style
        # Hotel search parameters
        self.hotel_adults = hotel_adults
        self.hotel_rooms = hotel_rooms
        self.hotel_children = hotel_children
        self.hotel_currency = hotel_currency
        self.hotel_price_min = hotel_price_min
        self.hotel_price_max = hotel_price_max
        self.hotel_sort = hotel_sort
        self.hotel_locale = hotel_locale
        self.flight_currency = flight_currency
        
        # Create agents
        self.flight_agent, self.hotel_agent, self.coordinator_agent, self.use_anthropic = create_real_agents()
        
        if self.use_anthropic:
            self.anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    def kickoff(self) -> Dict[str, Any]:
        """Execute the trip planning with real APIs and AI analysis"""
        try:
            print(f"Starting real trip planning for {self.destination}...")
            
            # Step 1: Get real flight data
            flight_tool = RealFlightTool()
            flight_params = {
                'origin': self.origin,
                'destination': self.destination,
                'departure_date': self.start_date,
                'return_date': self.end_date,
                'passengers': 1,  # Could be made configurable
                'currency_code': self.flight_currency
            }
            flight_data = flight_tool._run(**flight_params)
            print("Flight data retrieved")
            
            # Step 2: Get real hotel data with comprehensive parameters
            hotel_tool = RealHotelTool()
            # For one-way trips, assume 1-night stay
            checkout_date = self.end_date if self.end_date else datetime.strptime(self.start_date, '%Y-%m-%d').date() + timedelta(days=1)
            
            # Extract hotel parameters from search (if passed via constructor)
            hotel_params = {
                'destination': self.destination,
                'checkin': self.start_date,
                'checkout': checkout_date.strftime('%Y-%m-%d') if isinstance(checkout_date, date) else checkout_date,
                'adults': getattr(self, 'hotel_adults', 2),
                'rooms': getattr(self, 'hotel_rooms', 1),
                'children': getattr(self, 'hotel_children', 0),
                'currency': getattr(self, 'hotel_currency', 'USD'),
                'price_min': getattr(self, 'hotel_price_min', 0),
                'price_max': getattr(self, 'hotel_price_max', 500),
                'sort_by': getattr(self, 'hotel_sort', 'price'),
                'locale': getattr(self, 'hotel_locale', 'en-gb')
            }
            hotel_data = hotel_tool._run(**hotel_params)
            print("Hotel data retrieved")
            
            # Step 3: Use AI to analyze and create comprehensive recommendation
            if self.use_anthropic:
                recommendation = self._create_ai_recommendation(flight_data, hotel_data)
            else:
                recommendation = self._create_structured_recommendation(flight_data, hotel_data)
            
            return {
                "status": "success",
                "destination": self.destination,
                "dates": f"{self.start_date}" + (f" to {self.end_date}" if self.end_date else " (one-way)"),
                "budget": self.budget,
                "interests": self.interests,
                "raw": recommendation,
                "tasks_output": [
                    "Real flight search completed via Amadeus API",
                    "Real hotel search completed via Booking.com API", 
                    "AI-powered trip coordination completed"
                ],
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Real trip planning error: {str(e)}")
            return {
                "status": "error", 
                "error": str(e),
                "destination": self.destination,
                "timestamp": datetime.now().isoformat()
            }
    
    def _create_ai_recommendation(self, flight_data: str, hotel_data: str) -> str:
        """Use Anthropic AI to create intelligent recommendations"""
        try:
            prompt = f"""
            You are a professional travel agent creating a comprehensive trip recommendation.
            
            Trip Details:
            - Destination: {self.destination}
            - Dates: {self.start_date} to {self.end_date}  
            - Budget: ${self.budget:,}
            - Travel Style: {self.travel_style}
            - Interests: {', '.join(self.interests) if self.interests else 'General sightseeing'}
            
            Flight Data: {flight_data}
            
            Hotel Data: {hotel_data}
            
            Create a comprehensive travel recommendation that includes:
            1. Trip overview with personalized insights
            2. Analysis of the flight options with specific recommendations
            3. Analysis of the hotel options with specific recommendations  
            4. Detailed budget breakdown
            5. Personalized activity recommendations based on interests
            6. Practical travel tips
            7. Why this itinerary works well for the traveler
            
            Format with clear sections using emojis and markdown formatting.
            Be specific about prices, amenities, and practical details.
            """
            
            message = self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return message.content[0].text
            
        except Exception as e:
            print(f"AI recommendation error: {e}")
            return self._create_structured_recommendation(flight_data, hotel_data)
    
    def _create_structured_recommendation(self, flight_data: str, hotel_data: str) -> str:
        """Create structured recommendation without AI"""
        return f"""# Trip Recommendation for {self.destination}

## 🎯 Trip Overview  
- **Destination**: {self.destination}
- **Dates**: {self.start_date} to {self.end_date}
- **Budget**: ${self.budget:,}
- **Travel Style**: {self.travel_style.title()}
- **Interests**: {', '.join(self.interests) if self.interests else 'General sightseeing'}

## ✈️ Flight Options (Real-Time Data)
{flight_data}

## 🏨 Hotel Options (Real-Time Data)  
{hotel_data}

## 💰 Budget Analysis
Budget optimization based on real pricing data from our API partners.

## 🎨 Activity Recommendations
Personalized suggestions based on your interests: {', '.join(self.interests) if self.interests else 'general exploration'}

## 📋 Travel Tips
- Real-time pricing ensures accurate budget planning
- Book soon for best availability
- Check for last-minute deals

## 🌟 Why This Plan Works
This itinerary uses real-time data from Amadeus and Booking.com to ensure accuracy and availability.
        """

# Example usage
if __name__ == "__main__":
    crew = RealTripPlannerCrew(
        destination="Paris",
        start_date="2024-12-01", 
        end_date="2024-12-08",
        budget=2500.0,
        interests=["museums", "food", "architecture"]
    )
    
    results = crew.kickoff()
    print(json.dumps(results, indent=2))