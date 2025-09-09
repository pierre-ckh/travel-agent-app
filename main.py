# main.py
from fastapi import FastAPI, HTTPException, Depends, status, Form, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from jose import JWTError, jwt
from passlib.context import CryptContext
import uvicorn
import os
from dotenv import load_dotenv
import json
import uuid
import asyncio
from typing import Set

# Import your custom modules
try:
    from database import Database
    database_available = True
except ImportError as e:
    print(f"Database module not available: {e}")
    Database = None
    database_available = False
    
# from agents import TripPlannerCrew  # Comment out for now if causing issues


# Load environment variables
load_dotenv()

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Initialize FastAPI app
app = FastAPI(
    title="Trip Planner API",
    description="API for trip planning with CrewAI integration",
    version="1.0.0"
)

# CORS configuration for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# In-memory storage for tokens (replace Redis for now)
blacklisted_tokens: Set[str] = set()
search_cache = {}
refresh_tokens = {}

# Get database URL from environment or use SQLite as fallback
database_url = os.getenv("DATABASE_URL")
if not database_url or "[YOUR-PROJECT-ID]" in database_url:
    database_url = "sqlite:///travel_app.db"  # Fallback to SQLite
    print(f"Using SQLite database: {database_url}")
else:
    print(f"Using database URL: {database_url[:50]}...")  # Print first 50 chars for security
    
# Try to connect to database with fallback to SQLite
if database_available and Database:
    try:
        db = Database(database_url)
        print("Database connection successful!")
    except Exception as e:
        print(f"Database connection failed: {e}")
        print("Falling back to SQLite...")
        try:
            db = Database("sqlite:///travel_app.db")
        except Exception as e2:
            print(f"SQLite fallback also failed: {e2}")
            db = None
else:
    print("Database module not available - running without database")
    db = None

# Helper function to check database availability
def require_database():
    if not db:
        raise HTTPException(
            status_code=503, 
            detail="Database not available. Please try again later."
        )

# Pydantic models
class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None
    
    @validator('username')
    def username_alphanumeric(cls, v):
        assert v.replace('_', '').isalnum(), 'Username must be alphanumeric (underscores allowed)'
        return v

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    created_at: datetime
    is_active: bool

class TripSearchRequest(BaseModel):
    destination: str = Field(..., min_length=1, max_length=100)
    start_date: str = Field(..., description="Format: YYYY-MM-DD")
    end_date: str = Field(..., description="Format: YYYY-MM-DD")
    budget: float = Field(..., gt=0, le=1000000)
    interests: List[str] = Field(default_factory=list, max_items=10)
    travel_style: Optional[str] = Field(None, pattern="^(budget|comfort|luxury)$")
    
    @validator('start_date', 'end_date')
    def validate_dates(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')
        return v
    
    @validator('end_date')
    def end_after_start(cls, v, values):
        if 'start_date' in values:
            if v <= values['start_date']:
                raise ValueError('End date must be after start date')
        return v

class TripSearchResponse(BaseModel):
    search_id: str
    status: str
    results: Optional[Dict[str, Any]] = None
    created_at: datetime

# Utility functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Check if token is blacklisted
        if token in blacklisted_tokens:
            raise credentials_exception
            
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if username is None or token_type != "access":
            raise credentials_exception
            
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    require_database()
    user = db.get_user_by_auth(username=token_data.username)
    if user is None:
        raise credentials_exception
    
    if not user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user

def authenticate_user(username: str, password: str):
    """Authenticate a user"""
    user = db.get_user_by_auth(username=username)
    if not user:
        return False
    if not verify_password(password, user["password_hash"]):
        return False
    return user

# Background task for trip processing (simplified without CrewAI for now)
async def process_trip_search(search_id: str, user_id: int, search_params: dict):
    """Background task to process trip search"""
    try:
        # Update status in memory
        search_cache[f"search:{search_id}"] = {
            "status": "processing", 
            "user_id": user_id
        }
        
        # Simulate processing delay
        await asyncio.sleep(2)
        
        # Generate mock results for now
        mock_results = {
            "results": [
                {
                    "airline": "Delta Airlines",
                    "flight_number": "DL123",
                    "price": 850,
                    "duration": 6.5,
                    "stops": 1,
                    "departure_time": "08:00 AM",
                    "arrival_time": "02:30 PM",
                    "aircraft_type": "Boeing 737"
                },
                {
                    "airline": "American Airlines", 
                    "flight_number": "AA456",
                    "price": 920,
                    "duration": 7.2,
                    "stops": 2,
                    "departure_time": "10:15 AM",
                    "arrival_time": "05:18 PM",
                    "aircraft_type": "Airbus A320"
                }
            ]
        }
        
        # Store results
        search_result = {
            "status": "completed",
            "user_id": user_id,
            "results": mock_results,
            "completed_at": datetime.utcnow().isoformat()
        }
        
        # Update memory cache
        search_cache[f"search:{search_id}"] = search_result
        
        # Store in database
        # db.save_search_result(user_id, search_id, search_params, mock_results)
        
    except Exception as e:
        # Update status to failed
        error_result = {
            "status": "failed",
            "user_id": user_id,
            "error": str(e),
            "failed_at": datetime.utcnow().isoformat()
        }
        search_cache[f"search:{search_id}"] = error_result

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Trip Planner API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.post("/test-login")
async def test_login():
    """Simple test endpoint"""
    try:
        print("Test login endpoint hit!")
        return {"message": "Test login works"}
    except Exception as e:
        print(f"Test login error: {e}")
        return {"error": str(e)}

@app.post("/create-test-user")
async def create_test_user():
    """Create a test user for debugging"""
    try:
        if not db:
            return {"error": "Database not available", "status": 503}
        
        # Try to create a simple test user
        test_user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password_hash": pwd_context.hash("testpass123"),
            "is_active": True
        }
        
        user = db.create_user(test_user_data)
        return {"message": "Test user created successfully", "user_id": user.get("id") if user else None}
    except Exception as e:
        return {"error": str(e), "status": 500}

@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserRegister):
    """Register a new user"""
    # Check if user exists
    existing_user = db.get_user_by_auth(username=user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    existing_email = db.get_user_by_auth(email=user.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    hashed_password = get_password_hash(user.password)
    user_data = {
        "username": user.username,
        "email": user.email,
        "password_hash": hashed_password,
        "full_name": user.full_name,
        "created_at": datetime.utcnow(),
        "is_active": True
    }
    
    new_user = db.create_user(user_data)
    
    return UserResponse(
        id=new_user["id"],
        username=new_user["username"],
        email=new_user["email"],
        full_name=new_user.get("full_name"),
        created_at=new_user["created_at"],
        is_active=new_user["is_active"]
    )

@app.post("/login", response_model=Token)
async def login(username: str = Form(...), password: str = Form(...)):
    """Login and receive JWT tokens"""
    print(f"Login attempt for username: {username}")
    
    user = authenticate_user(username, password)
    print(f"Authentication result: {user is not False}")
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    print("Creating tokens...")
    # Create tokens
    access_token = create_access_token(data={"sub": user["username"]})
    refresh_token = create_refresh_token(data={"sub": user["username"]})
    
    print("Storing refresh token...")
    # Store refresh token in memory (optional, for token management)
    refresh_tokens[f"refresh:{user['username']}:{refresh_token[:10]}"] = refresh_token
    
    print("Updating last login...")
    # Update last login
    try:
        db.update_last_login(user["id"])
    except Exception as e:
        print(f"Warning: Could not update last login: {e}")
    
    print("Login successful!")
    return Token(
        access_token=access_token,
        refresh_token=refresh_token
    )

@app.post("/logout", status_code=status.HTTP_200_OK)
async def logout(token: str = Depends(oauth2_scheme), current_user: dict = Depends(get_current_user)):
    """Logout and blacklist the token"""
    try:
        # Decode token to get expiration
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = payload.get("exp")
        
        # Calculate TTL for blacklist
        ttl = exp - datetime.utcnow().timestamp() if exp else 3600
        
        # Add token to blacklist
        blacklisted_tokens.add(token)
        
        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )

@app.delete("/user", status_code=status.HTTP_200_OK)
async def unregister(
    current_user: dict = Depends(get_current_user),
    token: str = Depends(oauth2_scheme)
):
    """Delete user account"""
    try:
        # Blacklist current token
        blacklisted_tokens.add(token)
        
        # Delete user from database
        db.delete_user(current_user["id"])
        
        # Clean up user's refresh tokens
        keys_to_remove = [key for key in refresh_tokens.keys() if current_user['username'] in key]
        for key in keys_to_remove:
            del refresh_tokens[key]
        
        return {"message": "User account successfully deleted"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}"
        )

@app.post("/search", response_model=TripSearchResponse, status_code=status.HTTP_202_ACCEPTED)
async def trip_search(
    background_tasks: BackgroundTasks,
    destination: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    budget: float = Form(...),
    interests: Optional[str] = Form(None),
    travel_style: Optional[str] = Form("comfort"),
    current_user: dict = Depends(get_current_user)
):
    """
    Search for trip recommendations using CrewAI
    Returns immediately with search_id, processing happens in background
    """
    # Parse interests
    interests_list = []
    if interests:
        interests_list = [i.strip() for i in interests.split(",") if i.strip()]
    
    # Validate request
    search_request = TripSearchRequest(
        destination=destination,
        start_date=start_date,
        end_date=end_date,
        budget=budget,
        interests=interests_list,
        travel_style=travel_style
    )
    
    # Generate search ID
    search_id = str(uuid.uuid4())
    
    # Prepare search parameters
    search_params = {
        "destination": search_request.destination,
        "start_date": search_request.start_date,
        "end_date": search_request.end_date,
        "budget": search_request.budget,
        "interests": search_request.interests,
        "travel_style": search_request.travel_style
    }
    
    # Add background task
    background_tasks.add_task(
        process_trip_search,
        search_id,
        current_user["id"],
        search_params
    )
    
    return TripSearchResponse(
        search_id=search_id,
        status="processing",
        created_at=datetime.utcnow()
    )

@app.get("/search/{search_id}", response_model=TripSearchResponse)
async def get_search_results(
    search_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get search results by search ID"""
    # Get from memory cache first (faster lookup)
    cache_key = f"search:{search_id}"
    search_result = search_cache.get(cache_key)
    
    if search_result:
        
        # Check if the search belongs to current user
        if search_result.get("user_id") != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return TripSearchResponse(
            search_id=search_id,
            status=search_result["status"],
            results=search_result.get("results"),
            created_at=datetime.fromisoformat(search_result.get("created_at", datetime.utcnow().isoformat()))
        )
    
    # Fallback to database
    search_result = db.get_search_result(search_id, current_user["id"])
    if not search_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search not found"
        )
    
    return TripSearchResponse(
        search_id=search_id,
        status=search_result["status"],
        results=search_result.get("results"),
        created_at=search_result["created_at"]
    )

@app.get("/user/searches")
async def get_user_searches(
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 20
):
    """Get all searches for current user"""
    searches = db.get_user_searches(current_user["id"], skip=skip, limit=limit)
    return {"searches": searches}

@app.get("/user/profile", response_model=UserResponse)
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    return UserResponse(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user["email"],
        full_name=current_user.get("full_name"),
        created_at=current_user["created_at"],
        is_active=current_user["is_active"]
    )

@app.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str = Form(...)):
    """Refresh access token using refresh token"""
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if username is None or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Check if user exists and is active
        user = db.get_user_by_auth(username=username)
        if not user or not user.get("is_active"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new tokens
        new_access_token = create_access_token(data={"sub": username})
        new_refresh_token = create_refresh_token(data={"sub": username})
        
        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token
        )
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)