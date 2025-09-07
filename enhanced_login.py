#!/usr/bin/env python3
"""
Enhanced login server with real CrewAI and API integrations
"""
from fastapi import FastAPI, Form, BackgroundTasks, HTTPException, status
from main import authenticate_user, create_access_token, create_refresh_token
from real_agents import RealTripPlannerCrew  # Updated
from datetime import datetime
import asyncio
import uuid
from typing import Optional
import json

app = FastAPI()

# In-memory storage for search results
search_results = {}

@app.post("/simple-login")
async def simple_login(username: str = Form(...), password: str = Form(...)):
    """Simple login test"""
    print(f"Simple login for: {username}")
    
    user = authenticate_user(username, password)
    if not user:
        return {"error": "Authentication failed"}
    
    access_token = create_access_token(data={"sub": user["username"]})
    return {
        "success": True,
        "access_token": access_token,
        "username": user["username"]
    }

# Background task for enhanced CrewAI processing with real APIs
async def process_trip_search_with_real_apis(search_id: str, search_params: dict):
    """Background task to process trip search with real APIs and AI"""
    try:
        print(f"Starting enhanced trip search for: {search_params['destination']}")
        
        # Update status to processing
        search_results[search_id] = {
            "status": "processing",
            "search_id": search_id,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Create enhanced CrewAI crew with real APIs
        crew = RealTripPlannerCrew(
            destination=search_params["destination"],
            origin=search_params["origin"],
            start_date=search_params["departure_date"],
            end_date=search_params["return_date"] if search_params["return_date"] else None, 
            budget=search_params.get("budget", 20000.0),  # User-specified budget from form
            interests=search_params.get("preferences", []),
            travel_style=search_params.get("trip_type", "economy").lower(),
            # Hotel parameters
            hotel_adults=search_params.get("hotel_adults", 2),
            hotel_rooms=search_params.get("hotel_rooms", 1),
            hotel_children=search_params.get("hotel_children", 0),
            hotel_currency=search_params.get("hotel_currency", "USD"),
            hotel_price_min=search_params.get("hotel_price_min", 0),
            hotel_price_max=search_params.get("hotel_price_max", 500),
            hotel_sort=search_params.get("hotel_sort", "price"),
            hotel_locale=search_params.get("hotel_locale", "en-gb"),
            flight_currency=search_params.get("flight_currency", "USD")
        )
        
        # Run enhanced CrewAI with real APIs (this may take some time)
        print("Running enhanced CrewAI crew with real APIs...")
        results = crew.kickoff()
        print("Enhanced CrewAI completed successfully")
        
        # Convert result to serializable format (already handled in RealTripPlannerCrew)
        serializable_results = results
        
        # Store results
        search_results[search_id] = {
            "status": "completed",
            "search_id": search_id,
            "results": serializable_results,
            "created_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"Enhanced CrewAI error: {str(e)}")
        # Store error
        search_results[search_id] = {
            "status": "failed", 
            "search_id": search_id,
            "error": str(e),
            "created_at": datetime.utcnow().isoformat()
        }

@app.post("/search")
async def trip_search(
    background_tasks: BackgroundTasks,
    # Flight search parameters (matching Amadeus API)
    origin: str = Form(..., description="Origin airport IATA code (3 letters, e.g., 'NYC')"),
    destination: str = Form(..., description="Destination airport IATA code (3 letters, e.g., 'LAX')"),
    departure_date: str = Form(..., description="Departure date in YYYY-MM-DD format"),
    return_date: str = Form(None, description="Return date in YYYY-MM-DD format (optional for one-way)"),
    adults: int = Form(1, ge=1, le=9, description="Number of adult passengers (1-9)"),
    children: int = Form(0, ge=0, le=9, description="Number of child passengers (0-9)"),
    infants: int = Form(0, ge=0, le=9, description="Number of infant passengers (0-9)"),
    max_stops: int = Form(None, ge=0, le=3, description="Maximum stops (0=nonstop, 1-3=with stops)"),
    trip_type: str = Form("economy", description="Trip type: economy, business, or first"),
    flight_currency: str = Form("USD", description="Currency for flight prices (USD, EUR, GBP, CAD, AUD, JPY)"),
    # Hotel search parameters (comprehensive Booking.com API support)
    hotel_nights: int = Form(0, ge=0, le=30, description="Number of hotel nights (0-30, 0 if no hotel needed)"),
    hotel_adults: int = Form(2, ge=1, le=8, description="Number of adults per hotel room (1-8)"),
    hotel_rooms: int = Form(1, ge=1, le=5, description="Number of hotel rooms needed (1-5)"),
    hotel_children: int = Form(0, ge=0, le=4, description="Number of children per room (0-4)"),
    hotel_currency: str = Form("USD", description="Currency for hotel prices (USD, EUR, GBP, CAD, AUD, JPY)"),
    hotel_price_min: int = Form(0, ge=0, le=1000, description="Minimum price per night in selected currency (0-1000)"),
    hotel_price_max: int = Form(500, ge=0, le=2000, description="Maximum price per night in selected currency (0-2000)"),
    hotel_sort: str = Form("price", description="Sort hotels by: price, popularity, distance, rating"),
    hotel_locale: str = Form("en-gb", description="Language/region: en-gb, en-us, fr-fr, de-de, es-es, it-it, pt-pt, nl-nl"),
    # Trip preferences and budget
    budget: float = Form(20000.0, ge=500.0, le=100000.0, description="Total trip budget in USD (500-100000)"),
    preferences: str = Form("", description="Additional preferences (comma-separated)"),
    notes: str = Form("", description="Special requirements or notes")
):
    """Search for trips using enhanced CrewAI with real APIs"""
    
    # Generate search ID
    search_id = str(uuid.uuid4())
    
    # Parse preferences
    preferences_list = []
    if preferences:
        preferences_list = [p.strip() for p in preferences.split(",") if p.strip()]
    
    # Prepare search parameters for Amadeus API and hotels
    search_params = {
        # Flight parameters
        "origin": origin.upper(),  # Convert to uppercase IATA code
        "destination": destination.upper(),  # Convert to uppercase IATA code
        "departure_date": departure_date,
        "return_date": return_date,
        "adults": adults,
        "children": children, 
        "infants": infants,
        "max_stops": max_stops,
        "trip_type": trip_type,
        "flight_currency": flight_currency,
        # Hotel parameters (comprehensive)
        "hotel_nights": hotel_nights,
        "hotel_adults": hotel_adults,
        "hotel_rooms": hotel_rooms,
        "hotel_children": hotel_children,
        "hotel_currency": hotel_currency,
        "hotel_price_min": hotel_price_min,
        "hotel_price_max": hotel_price_max,
        "hotel_sort": hotel_sort,
        "hotel_locale": hotel_locale,
        # Budget and additional preferences  
        "budget": budget,
        "preferences": preferences_list,
        "notes": notes
    }
    
    print(f"Received enhanced trip search request: {search_params}")
    
    # Add background task for enhanced CrewAI processing
    background_tasks.add_task(
        process_trip_search_with_real_apis,
        search_id,
        search_params
    )
    
    # Return immediately with search ID
    return {
        "search_id": search_id,
        "status": "processing", 
        "message": "Enhanced trip search with real APIs started. Check results using the search ID.",
        "created_at": datetime.utcnow().isoformat()
    }

@app.get("/search/{search_id}")
async def get_search_results(search_id: str):
    """Get search results by search ID"""
    if search_id not in search_results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search not found"
        )
    
    result = search_results[search_id]
    
    # If completed, format the results for the frontend
    if result["status"] == "completed" and "results" in result:
        enhanced_results = result["results"]
        
        # Format enhanced results into the expected frontend format
        formatted_results = {
            "status": "completed",
            "search_id": search_id,
            "results": {
                "results": format_enhanced_results(enhanced_results)
            },
            "created_at": result["created_at"]
        }
        return formatted_results
    
    return result

def format_enhanced_results(enhanced_output):
    """Format enhanced CrewAI output with real API data into expected frontend format"""
    try:
        # Enhanced results already come in a good format from RealTripPlannerCrew
        if isinstance(enhanced_output, dict):
            if enhanced_output.get("status") == "success":
                # Extract the main content
                raw_content = enhanced_output.get("raw", "")
                tasks_output = enhanced_output.get("tasks_output", [])
                
                # Combine all content for display
                full_content = raw_content
                if tasks_output:
                    full_content += "\n\n**Processing Summary:**\n" + "\n".join([f"✓ {task}" for task in tasks_output])
                
                return [
                    {
                        "type": "enhanced_recommendation",
                        "title": f"🤖 AI-Powered Travel Plan for {enhanced_output.get('destination', 'Your Destination')}",
                        "description": str(full_content)[:500] + "..." if len(str(full_content)) > 500 else str(full_content),
                        "full_recommendation": full_content,
                        "destination": enhanced_output.get("destination", ""),
                        "dates": enhanced_output.get("dates", ""),
                        "budget": enhanced_output.get("budget", 0),
                        "interests": enhanced_output.get("interests", []),
                        "raw_output": raw_content,
                        "tasks": tasks_output,
                        "api_sources": ["Amadeus Flight API", "Booking.com Hotel API", "Anthropic Claude AI"]
                    }
                ]
            else:
                return [
                    {
                        "type": "error",
                        "title": "Enhanced Search Error",
                        "description": enhanced_output.get("error", "Unknown error occurred in enhanced search"),
                        "error": True
                    }
                ]
        else:
            # Fallback for other formats
            content = str(enhanced_output)
            return [
                {
                    "type": "enhanced_recommendation", 
                    "title": "🤖 AI-Powered Travel Plan",
                    "description": content[:500] + "..." if len(content) > 500 else content,
                    "full_recommendation": content
                }
            ]
    except Exception as e:
        return [
            {
                "type": "error",
                "title": "Result Formatting Error", 
                "description": f"Error formatting enhanced results: {str(e)}",
                "error": True
            }
        ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)