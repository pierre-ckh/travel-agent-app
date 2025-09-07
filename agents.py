# agents.py
from crewai import Agent, Task, Crew, Process
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

# Import the tools
from tools.amadeus_flight_tool import AmadeusFlightTool  
from tools.booking_hotel_tool import BookingHotelTool

load_dotenv()

class Config:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/travel_db")
    
    # API Keys
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    AMADEUS_API_KEY = os.getenv("AMADEUS_API_KEY")
    AMADEUS_API_SECRET = os.getenv("AMADEUS_API_SECRET")
    BOOKING_API_KEY = os.getenv("RAPIDAPI_KEY")
    
    # Amadeus API
    AMADEUS_BASE_URL = os.getenv("AMADEUS_BASE_URL", "https://api.amadeus.com/v2")
    
    # Booking API  
    BOOKING_BASE_URL = os.getenv("BOOKING_BASE_URL", "https://api.booking.com/v1")
def create_agents():
    """Create and return the agents with their tools"""
    flight_search_agent = Agent(
        role="Flight Search Agent",
        goal="Find flights matching user criteria with best prices and schedules",
        backstory="You are an expert travel agent specializing in flight bookings with extensive knowledge of airline routes, pricing patterns, and optimal booking strategies.",
        tools=[AmadeusFlightTool()],
        verbose=True
    )

    hotel_search_agent = Agent(
        role="Hotel Search Agent", 
        goal="Find hotels with discounts or long-stay deals matching user preferences",
        backstory="You are a specialist in hotel accommodations with expertise in finding the best deals, promotions, and long-stay packages for travelers.",
        tools=[BookingHotelTool()],
        verbose=True
    )

    trip_coordination_agent = Agent(
        role="Trip Coordination Agent",
        goal="Coordinate and optimize complete trip itinerary based on flight and hotel options", 
        backstory="You are an experienced trip coordinator who excels at creating seamless travel experiences by optimizing timing, locations, and budget across all trip components.",
        verbose=True
    )
    
    return flight_search_agent, hotel_search_agent, trip_coordination_agent

# Define Tasks
def create_flight_search_task(destination: str, start_date: str, end_date: str, budget: float, passengers: int = 1) -> Task:
    return Task(
        description=f"""
        Search for flights to {destination} from major airports for {passengers} passenger(s).
        Departure date: {start_date}
        Return date: {end_date}
        Budget consideration: ${budget} total trip budget
        
        Find the best flight options considering:
        1. Price within reasonable portion of total budget
        2. Convenient departure/arrival times
        3. Minimal layovers when possible
        4. Reputable airlines
        
        Return structured flight information including prices, times, airlines, and any special deals.
        """,
        agent=flight_search_agent,
        expected_output="JSON formatted list of flight options with detailed pricing, timing, and airline information"
    )

def create_hotel_search_task(destination: str, start_date: str, end_date: str, budget: float) -> Task:
    return Task(
        description=f"""
        Search for hotels in {destination} with focus on discounts and long-stay deals.
        Check-in: {start_date}  
        Check-out: {end_date}
        Budget consideration: ${budget} total trip budget
        
        Priority search criteria:
        1. Hotels with active discounts (>10% off)
        2. Long-stay deals for extended visits
        3. Good value for money within budget
        4. Well-located properties
        5. Good ratings and amenities
        
        Return structured hotel information with pricing, discounts, and amenities.
        """, 
        agent=hotel_search_agent,
        expected_output="JSON formatted list of hotel options with discount information, pricing, and amenity details"
    )

def create_trip_coordination_task(destination: str, start_date: str, end_date: str, budget: float, interests: List[str]) -> Task:
    return Task(
        description=f"""
        Create a coordinated trip plan for {destination} from {start_date} to {end_date} with ${budget} budget.
        
        User interests: {', '.join(interests) if interests else 'General sightseeing'}
        
        Using the flight and hotel search results, create an optimized trip plan that:
        1. Combines the best flight and hotel options within budget
        2. Ensures timing compatibility between flights and hotel bookings
        3. Maximizes value by highlighting deals and savings
        4. Provides a cohesive itinerary recommendation
        5. Includes budget breakdown and total estimated costs
        6. Suggests activities based on user interests and location
        
        Present the final recommendation as a complete trip package.
        """,
        agent=trip_coordination_agent,
        expected_output="Complete trip itinerary with selected flights, hotels, activities, detailed budget breakdown, and booking recommendations"
    )

# Trip Planner Crew Class
class TripPlannerCrew:
    def __init__(self, destination: str, start_date: str, end_date: str, budget: float, 
                 interests: List[str] = None, travel_style: str = "comfort"):
        self.destination = destination
        self.start_date = start_date  
        self.end_date = end_date
        self.budget = budget
        self.interests = interests or []
        self.travel_style = travel_style
        
        # Create agents
        flight_agent, hotel_agent, coordination_agent = create_agents()
        
        # Create tasks  
        self.flight_task = create_flight_search_task(
            destination, start_date, end_date, budget
        )
        self.hotel_task = create_hotel_search_task(
            destination, start_date, end_date, budget
        )
        self.coordination_task = create_trip_coordination_task(
            destination, start_date, end_date, budget, self.interests
        )
        
        # Update task agents
        self.flight_task.agent = flight_agent
        self.hotel_task.agent = hotel_agent
        self.coordination_task.agent = coordination_agent
        
        # Create crew
        self.crew = Crew(
            agents=[flight_agent, hotel_agent, coordination_agent],
            tasks=[self.flight_task, self.hotel_task, self.coordination_task],
            process=Process.sequential,
            verbose=True
        )
    
    def kickoff(self) -> Dict[str, Any]:
        """Execute the trip planning crew and return results"""
        try:
            result = self.crew.kickoff()
            return {
                "status": "success",
                "destination": self.destination,
                "dates": f"{self.start_date} to {self.end_date}",
                "budget": self.budget,
                "interests": self.interests,
                "recommendations": result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "error", 
                "error": str(e),
                "destination": self.destination,
                "timestamp": datetime.now().isoformat()
            }

# Example usage
if __name__ == "__main__":
    # Example trip planning
    crew = TripPlannerCrew(
        destination="Paris",
        start_date="2024-06-15", 
        end_date="2024-06-22",
        budget=2500.0,
        interests=["museums", "food", "architecture"],
        travel_style="comfort"
    )
    
    results = crew.kickoff()
    print(f"Trip planning results: {results}")