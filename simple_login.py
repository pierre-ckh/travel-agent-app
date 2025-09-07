#!/usr/bin/env python3
"""
Simplified login server with CrewAI integration
"""
from fastapi import FastAPI, Form, BackgroundTasks, HTTPException, status
from main import authenticate_user, create_access_token, create_refresh_token
from simple_agents import SimpleTripPlannerCrew
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

# Background task for CrewAI processing
async def process_trip_search_with_crewai(search_id: str, search_params: dict):
    """Background task to process trip search with CrewAI"""
    try:
        print(f"Starting CrewAI trip search for: {search_params['destination']}")
        
        # Update status to processing
        search_results[search_id] = {
            "status": "processing",
            "search_id": search_id,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Create CrewAI crew
        crew = SimpleTripPlannerCrew(
            destination=search_params["destination"],
            start_date=search_params["departure_date"],
            end_date=search_params["return_date"], 
            budget=float(search_params["price_max"]),
            interests=search_params.get("preferences", []),
            travel_style=search_params.get("trip_type", "comfort").lower()
        )
        
        # Run CrewAI (this may take some time)
        print("Running CrewAI crew...")
        results = crew.kickoff()
        print("CrewAI completed successfully")
        
        # Convert CrewAI result to serializable format
        try:
            if hasattr(results, 'raw'):
                # Handle CrewOutput object
                serializable_results = {
                    "status": "success",
                    "raw": str(results.raw),
                    "tasks_output": [str(task) for task in getattr(results, 'tasks_output', [])]
                }
            else:
                # Handle other result types
                serializable_results = results
        except Exception as e:
            print(f"Error serializing results: {e}")
            serializable_results = {
                "status": "success", 
                "raw": str(results),
                "note": f"Serialization handled as string due to: {str(e)}"
            }
        
        # Store results
        search_results[search_id] = {
            "status": "completed",
            "search_id": search_id,
            "results": serializable_results,
            "created_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"CrewAI error: {str(e)}")
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
    destination: str = Form(...),
    origin: str = Form(...),
    departure_date: str = Form(...),
    return_date: str = Form(...),
    passengers: int = Form(1),
    stops: int = Form(0),
    hotel_nights: int = Form(0),
    price_min: float = Form(0),
    price_max: float = Form(2000),
    trip_type: str = Form("comfort"),
    preferences: str = Form(""),
    notes: str = Form("")
):
    """Search for trips using CrewAI"""
    
    # Generate search ID
    search_id = str(uuid.uuid4())
    
    # Parse preferences
    preferences_list = []
    if preferences:
        preferences_list = [p.strip() for p in preferences.split(",") if p.strip()]
    
    # Prepare search parameters
    search_params = {
        "destination": destination,
        "origin": origin,
        "departure_date": departure_date,
        "return_date": return_date,
        "passengers": passengers,
        "price_min": price_min,
        "price_max": price_max,
        "trip_type": trip_type,
        "preferences": preferences_list,
        "notes": notes
    }
    
    print(f"Received trip search request: {search_params}")
    
    # Add background task for CrewAI processing
    background_tasks.add_task(
        process_trip_search_with_crewai,
        search_id,
        search_params
    )
    
    # Return immediately with search ID
    return {
        "search_id": search_id,
        "status": "processing", 
        "message": "Trip search started. Check results using the search ID.",
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
        crewai_results = result["results"]
        
        # Format CrewAI results into the expected frontend format
        formatted_results = {
            "status": "completed",
            "search_id": search_id,
            "results": {
                "results": format_crewai_results(crewai_results)
            },
            "created_at": result["created_at"]
        }
        return formatted_results
    
    return result

def format_crewai_results(crewai_output):
    """Format CrewAI output into expected frontend format"""
    try:
        # Handle the new serializable format
        if isinstance(crewai_output, dict):
            if crewai_output.get("status") == "success":
                # Extract the main content
                raw_content = crewai_output.get("raw", "")
                tasks_output = crewai_output.get("tasks_output", [])
                
                # Combine all content for display
                full_content = raw_content
                if tasks_output:
                    full_content += "\n\nTask Details:\n" + "\n".join(tasks_output)
                
                return [
                    {
                        "type": "crewai_recommendation",
                        "title": "AI Travel Recommendation",
                        "description": str(full_content)[:500] + "..." if len(str(full_content)) > 500 else str(full_content),
                        "full_recommendation": full_content,
                        "raw_output": raw_content,
                        "tasks": tasks_output
                    }
                ]
            else:
                return [
                    {
                        "type": "error",
                        "title": "Search Error",
                        "description": crewai_output.get("error", "Unknown error occurred"),
                        "error": True
                    }
                ]
        else:
            # Fallback for other formats
            content = str(crewai_output)
            return [
                {
                    "type": "crewai_recommendation", 
                    "title": "AI Travel Recommendation",
                    "description": content[:500] + "..." if len(content) > 500 else content,
                    "full_recommendation": content
                }
            ]
    except Exception as e:
        return [
            {
                "type": "error",
                "title": "Result Formatting Error", 
                "description": f"Error formatting results: {str(e)}",
                "error": True
            }
        ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)