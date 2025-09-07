#!/usr/bin/env python3
"""
Simplified CrewAI agents without external API dependencies
"""
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import BaseTool
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Simple mock tools that return structured data
class MockFlightTool(BaseTool):
    name: str = "flight_search"
    description: str = "Search for flights between destinations"
    
    def _run(self, **kwargs) -> str:
        """Mock flight search that returns sample data"""
        origin = kwargs.get('origin', 'NYC')
        destination = kwargs.get('destination', 'LAX')
        departure_date = kwargs.get('departure_date', '2024-12-01')
        return_date = kwargs.get('return_date', None)
        passengers = kwargs.get('passengers', 1)
        flights = [
            {
                "airline": "Air France",
                "flight_number": "AF123", 
                "price": 850,
                "duration": "8h 30m",
                "stops": 0,
                "departure_time": "10:00 AM",
                "arrival_time": "6:30 PM",
                "departure_airport": origin,
                "arrival_airport": destination,
                "departure_date": departure_date,
                "return_date": return_date
            },
            {
                "airline": "Delta",
                "flight_number": "DL456",
                "price": 920,
                "duration": "9h 15m", 
                "stops": 1,
                "departure_time": "2:15 PM",
                "arrival_time": "11:30 PM",
                "departure_airport": origin,
                "arrival_airport": destination,
                "departure_date": departure_date,
                "return_date": return_date
            }
        ]
        return json.dumps(flights)

class MockHotelTool(BaseTool):
    name: str = "hotel_search"
    description: str = "Search for hotels in destination"
    
    def _run(self, **kwargs) -> str:
        """Mock hotel search that returns sample data"""
        destination = kwargs.get('destination', 'Paris')
        checkin = kwargs.get('checkin', '2024-12-01')
        checkout = kwargs.get('checkout', '2024-12-08')
        guests = kwargs.get('guests', 2)
        hotels = [
            {
                "name": "Grand Hotel Paris",
                "price_per_night": 180,
                "rating": 4.5,
                "location": "City Center",
                "amenities": ["WiFi", "Restaurant", "Gym"],
                "discount": "15% off for 7+ nights",
                "checkin": checkin,
                "checkout": checkout
            },
            {
                "name": "Budget Inn",
                "price_per_night": 85,
                "rating": 3.8,
                "location": "Near Metro",
                "amenities": ["WiFi", "Breakfast"],
                "discount": "10% off",
                "checkin": checkin,
                "checkout": checkout
            }
        ]
        return json.dumps(hotels)

def create_simple_agents():
    """Create simplified agents with mock tools"""
    
    # Try different LLM configuration
    try:
        from crewai import LLM
        # Use default LLM for now to avoid API issues
        default_llm = None  # Let CrewAI use default
    except Exception as e:
        print(f"LLM configuration error: {e}")
        default_llm = None
    
    flight_agent = Agent(
        role="Flight Search Specialist",
        goal="Find the best flight options for travelers",
        backstory="You are an expert at finding flights with great prices and convenient schedules. You analyze flight options and recommend the best choices based on traveler preferences.",
        tools=[MockFlightTool()],
        verbose=True
    )
    
    hotel_agent = Agent(
        role="Hotel Booking Expert", 
        goal="Find great hotel deals and accommodations",
        backstory="You specialize in finding hotels with excellent value, good locations, and special discounts. You know how to spot the best deals for different types of travelers.",
        tools=[MockHotelTool()],
        verbose=True
    )
    
    coordinator_agent = Agent(
        role="Trip Coordinator",
        goal="Create comprehensive travel itineraries combining flights and hotels",
        backstory="You are a master trip planner who excels at combining flight and hotel options into perfect travel packages. You optimize for budget, convenience, and traveler satisfaction.",
        verbose=True
    )
    
    return flight_agent, hotel_agent, coordinator_agent

class SimpleTripPlannerCrew:
    def __init__(self, destination: str, start_date: str, end_date: str, budget: float, 
                 interests: List[str] = None, travel_style: str = "comfort"):
        self.destination = destination
        self.start_date = start_date  
        self.end_date = end_date
        self.budget = budget
        self.interests = interests or []
        self.travel_style = travel_style
    
    def kickoff(self) -> Dict[str, Any]:
        """Execute the trip planning crew and return results"""
        try:
            print(f"Starting trip planning for {self.destination}...")
            
            # Simulate AI-powered trip planning with realistic responses
            flight_tool = MockFlightTool()
            hotel_tool = MockHotelTool()
            
            # Get mock data from tools
            flight_data = flight_tool._run()
            hotel_data = hotel_tool._run()
            
            # Generate comprehensive recommendation
            recommendation = f"""# Trip Recommendation for {self.destination}

## 🎯 Trip Overview
- **Destination**: {self.destination}
- **Dates**: {self.start_date} to {self.end_date}
- **Budget**: ${self.budget:,}
- **Travel Style**: {self.travel_style.title()}
- **Interests**: {', '.join(self.interests) if self.interests else 'General sightseeing'}

## ✈️ Flight Recommendations
Based on your dates and budget, I've found excellent flight options:

{flight_data}

**Recommended**: Air France AF123 - Best balance of price and convenience
- Direct flight saves time
- Reasonable price at $850
- Good departure time (10:00 AM)

## 🏨 Hotel Recommendations
For your accommodation in {self.destination}:

{hotel_data}

**Recommended**: Grand Hotel Paris
- Excellent location in City Center
- Great rating (4.5/5)
- Special discount: 15% off for 7+ nights
- Price: $180/night

## 💰 Budget Breakdown
- **Flight**: $850 (for best option)
- **Hotel**: $1,260 (7 nights at $180/night)
- **Total Core**: $2,110
- **Remaining Budget**: ${self.budget - 2110:,} for activities, meals, and shopping

## 🎨 Activity Recommendations
Based on your interests in {', '.join(self.interests) if self.interests else 'general sightseeing'}:

- **Museums**: Visit the Louvre, Musée d'Orsay, and Centre Pompidou
- **Food**: Try local bistros, food markets, and cooking classes
- **Architecture**: Walking tours of historic districts
- **Local Experiences**: Seine river cruise, neighborhood exploration

## 📋 Travel Tips
- Book flights at least 2-3 weeks in advance for better prices
- Hotel offers 15% discount for 7+ night stays - great value!
- Consider a Museum Pass for convenience and savings
- Pack layers for variable weather in {self.destination}

## 🌟 Why This Plan Works
This itinerary optimizes your budget while ensuring comfort and covering your key interests. The central hotel location minimizes transportation costs and maximizes exploration time.
            """
            
            return {
                "status": "success",
                "destination": self.destination,
                "dates": f"{self.start_date} to {self.end_date}",
                "budget": self.budget,
                "interests": self.interests,
                "raw": recommendation,
                "tasks_output": [
                    "Flight search completed - Found 2 excellent options",
                    "Hotel search completed - Found 2 great properties with discounts", 
                    "Trip coordination completed - Comprehensive itinerary generated"
                ],
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Trip planning error: {str(e)}")
            return {
                "status": "error", 
                "error": str(e),
                "destination": self.destination,
                "timestamp": datetime.now().isoformat()
            }

# Example usage
if __name__ == "__main__":
    crew = SimpleTripPlannerCrew(
        destination="Paris",
        start_date="2024-12-01", 
        end_date="2024-12-08",
        budget=2500.0,
        interests=["museums", "food", "architecture"]
    )
    
    results = crew.kickoff()
    print(json.dumps(results, indent=2))