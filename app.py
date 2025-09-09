# app.py
import streamlit as st
import requests
from datetime import datetime, date, timedelta
import jwt
from typing import Optional
import json
import os
from tools.mailjet_email_tool import MailJetEmailTool

# Configuration
# Get API URL from environment variable, fallback to localhost for development
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8002")
JWT_SECRET = "your-secret-key-change-this-in-production"  # Should match backend secret
JWT_ALGORITHM = "HS256"

# Page config
st.set_page_config(
    page_title="Travel Trip Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        padding: 0.5rem;
    }
    .stButton > button:hover {
        background-color: #45a049;
    }
    .trip-card {
        padding: 1rem;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'token' not in st.session_state:
        st.session_state.token = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'search_results' not in st.session_state:
        st.session_state.search_results = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'login'

init_session_state()

# Helper functions
def make_api_request(endpoint: str, method: str = "GET", data: dict = None, headers: dict = None, form_data: bool = False):
    """Make API request to FastAPI backend"""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, params=data, headers=headers)
        elif method == "POST":
            if form_data:
                response = requests.post(url, data=data, headers=headers)
            else:
                response = requests.post(url, json=data, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        return response
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to the backend server. Please ensure the FastAPI server is running.")
        return None
    except Exception as e:
        st.error(f"❌ Error making request: {str(e)}")
        return None

def get_auth_headers():
    """Get authorization headers with JWT token"""
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}

def decode_token(token: str) -> Optional[dict]:
    """Decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        st.error("Session expired. Please login again.")
        logout()
        return None
    except jwt.InvalidTokenError:
        return None

def logout():
    """Logout user"""
    st.session_state.authenticated = False
    st.session_state.token = None
    st.session_state.username = None
    st.session_state.search_results = None
    st.session_state.current_page = 'login'

# Pages
def login_page():
    """Login page"""
    st.title("🔐 Login")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            st.subheader("Welcome Back!")
            
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                login_button = st.form_submit_button("🔓 Login", use_container_width=True)
            
            with col_btn2:
                register_button = st.form_submit_button("📝 Register", use_container_width=True)
            
            if login_button:
                if username and password:
                    try:
                        # Make API call to login endpoint  
                        response = make_api_request(
                            "/login",
                            method="POST",
                            data={"username": username, "password": password},
                            form_data=True
                        )
                        
                        if response and response.status_code == 200:
                            data = response.json()
                            
                            if data.get("access_token"):
                                st.session_state.authenticated = True
                                st.session_state.token = data.get("access_token")
                                st.session_state.username = username
                                st.session_state.current_page = 'search'
                                
                                st.success("✅ Login successful! Redirecting...")
                                st.rerun()
                            else:
                                st.error("❌ Login response missing required data")
                                st.error(f"Debug: Response data: {data}")
                        elif response and response.status_code == 401:
                            st.error("❌ Invalid username or password")
                        elif response and response.status_code == 503:
                            st.error("❌ Database not available. Please try again later.")
                        else:
                            st.error(f"❌ Login failed. Status code: {response.status_code if response else 'No response'}")
                            if response:
                                try:
                                    error_data = response.json()
                                    st.error(f"Debug: Error details: {error_data}")
                                except:
                                    st.error(f"Debug: Raw response: {response.text}")
                    except Exception as e:
                        st.error(f"❌ Login error: {str(e)}")
                else:
                    st.warning("Please fill in all fields")
            
            if register_button:
                st.session_state.current_page = 'register'
                st.rerun()

def register_page():
    """Registration page"""
    st.title("📝 Register")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("register_form"):
            st.subheader("Create Your Account")
            
            username = st.text_input("Username", placeholder="Choose a username")
            email = st.text_input("Email", placeholder="Enter your email")
            password = st.text_input("Password", type="password", placeholder="Create a password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                register_button = st.form_submit_button("✅ Register", use_container_width=True)
            
            with col_btn2:
                back_button = st.form_submit_button("🔙 Back to Login", use_container_width=True)
            
            if register_button:
                if username and email and password and confirm_password:
                    if password != confirm_password:
                        st.error("❌ Passwords do not match")
                    elif len(password) < 6:
                        st.error("❌ Password must be at least 6 characters long")
                    else:
                        # Make API call to register endpoint
                        response = make_api_request(
                            "/register",
                            method="POST",
                            data={"username": username, "email": email, "password": password}
                        )
                        
                        if response and response.status_code == 201:
                            st.success("✅ Registration successful! Please login.")
                            st.session_state.current_page = 'login'
                            st.rerun()
                        elif response and response.status_code == 400:
                            st.error("❌ Username already exists")
                        elif response and response.status_code == 503:
                            st.error("❌ Database not available. Please try again later.")
                        else:
                            st.error(f"❌ Registration failed. Status code: {response.status_code if response else 'No response'}")
                            if response:
                                try:
                                    error_data = response.json()
                                    st.error(f"Debug: Error details: {error_data}")
                                except:
                                    st.error(f"Debug: Raw response: {response.text}")
                else:
                    st.warning("Please fill in all fields")
            
            if back_button:
                st.session_state.current_page = 'login'
                st.rerun()

def search_page():
    """Trip search form page"""
    st.title("✈️ Plan Your Trip with Real APIs")
    
    # Show what APIs are being used
    st.info("🔥 **Real-time data powered by**: Amadeus Flight API • Booking.com Hotels • Anthropic Claude AI")
    
    # User info in sidebar
    with st.sidebar:
        st.write(f"👤 Logged in as: **{st.session_state.username}**")
        if st.button("🚪 Logout", use_container_width=True):
            logout()
            st.rerun()
        
        st.markdown("---")
        st.subheader("📋 Popular Airport Codes")
        st.markdown("""
        **🇺🇸 USA:**
        - NYC (New York)
        - LAX (Los Angeles) 
        - CHI (Chicago)
        - MIA (Miami)
        - LAS (Las Vegas)
        
        **🌍 International:**
        - LHR (London)
        - CDG (Paris)
        - NRT (Tokyo)
        - DXB (Dubai)
        - SYD (Sydney)
        """)
        
        st.markdown("---")
        st.markdown("💡 **Tips:**")
        st.markdown("- Use 3-letter IATA codes")
        st.markdown("- Search may take 30-60s for real data")
        st.markdown("- Try different dates for better prices")
    
    # Trip type selection (outside form for reactivity)
    st.subheader("✈️ Flight Search")
    st.info("💡 **Airport codes**: Use 3-letter IATA codes (e.g., NYC for New York, LAX for Los Angeles, LHR for London)")
    
    trip_type_radio = st.radio(
        "✈️ Trip Type",
        options=["One-way", "Round-trip"],
        horizontal=True,
        help="Choose between one-way or round-trip flight"
    )
    
    # Trip search form with Amadeus API parameters
    with st.form("trip_search_form"):
        # Row 1: Origin and Destination (horizontal)
        col1, col2 = st.columns(2)
        with col1:
            origin = st.text_input(
                "🛫 Origin Airport",
                placeholder="e.g., NYC, JFK, LAX",
                help="Enter 3-letter IATA airport code for departure city. Examples: NYC (New York), LAX (Los Angeles), CHI (Chicago)",
                max_chars=3
            )
        with col2:
            destination = st.text_input(
                "🛬 Destination Airport",
                placeholder="e.g., LAX, LHR, CDG",
                help="Enter 3-letter IATA airport code for destination city. Examples: LAX (Los Angeles), LHR (London), CDG (Paris)",
                max_chars=3
            )
        
        # Row 2: Dates (horizontal)
        col3, col4 = st.columns(2)
        with col3:
            departure_date = st.date_input(
                "📅 Departure Date",
                min_value=date.today(),
                value=date.today(),
                help="Select your departure date (YYYY-MM-DD format)"
            )
        with col4:
            if trip_type_radio == "Round-trip":
                return_date = st.date_input(
                    "📅 Return Date",
                    min_value=departure_date,
                    key="return_date_input",
                    help="Select your return date for round-trip flight"
                )
            else:
                return_date = None
                st.info("🎯 One-way flight selected - no return date needed")
        
        # Row 3: Passengers (horizontal)
        col5, col6, col7 = st.columns(3)
        with col5:
            adults = st.number_input(
                "👤 Adults (18+ years)",
                min_value=1,
                max_value=9,
                value=1,
                help="Number of adult passengers (1-9)"
            )
        with col6:
            children = st.number_input(
                "👶 Children (2-11 yrs)",
                min_value=0,
                max_value=9,
                value=0,
                help="Number of child passengers (0-9)"
            )
        with col7:
            infants = st.number_input(
                "🍼 Infants (under 2)",
                min_value=0,
                max_value=9,
                value=0,
                help="Number of infant passengers (0-9)"
            )
        
        # Row 4: Travel Options (horizontal)
        col8, col9, col10 = st.columns(3)
        with col8:
            trip_type = st.selectbox(
                "💺 Travel Class",
                options=["economy", "business", "first"],
                format_func=lambda x: x.title() + " Class",
                help="Select your preferred travel class"
            )
        with col9:
            max_stops = st.selectbox(
                "🔄 Maximum Stops",
                options=[None, 0, 1, 2, 3],
                format_func=lambda x: "Any number of stops" if x is None else ("Non-stop only" if x == 0 else f"Up to {x} stop(s)"),
                help="Filter by maximum number of stops you're willing to make"
            )
        with col10:
            flight_currency = st.selectbox(
                "💱 Flight Currency",
                options=["USD", "EUR", "GBP", "CAD", "AUD", "JPY"],
                index=0,
                help="Currency for flight prices (USD, EUR, GBP, CAD, AUD, JPY)"
            )
        
        st.subheader("🏨 Hotel Accommodation")
        st.info("💡 **Hotel Search**: Uses Booking.com API via RapidAPI for real-time availability and pricing")
        
        # Hotel basic parameters
        col_h1, col_h2 = st.columns(2)
        with col_h1:
            hotel_nights = st.number_input(
                "🌙 Hotel Nights",
                min_value=0,
                max_value=30,
                value=0,
                help="Number of nights you need hotel accommodation (0 if no hotel needed). Max: 30 nights"
            )
        with col_h2:
            hotel_adults = st.number_input(
                "👥 Adults in Hotel Room",
                min_value=1,
                max_value=8,
                value=2,
                help="Number of adults per hotel room (1-8). Default: 2"
            )
        
        # Advanced hotel parameters (only show if hotel nights > 0)
        if hotel_nights > 0:
            st.markdown("**🔧 Advanced Hotel Options**")
            
            col_h3, col_h4, col_h5 = st.columns(3)
            with col_h3:
                hotel_rooms = st.number_input(
                    "🏠 Number of Rooms",
                    min_value=1,
                    max_value=5,
                    value=1,
                    help="Number of hotel rooms needed (1-5). Default: 1"
                )
            with col_h4:
                hotel_children = st.number_input(
                    "👶 Children in Room",
                    min_value=0,
                    max_value=4,
                    value=0,
                    help="Number of children per room (0-4). Optional"
                )
            with col_h5:
                hotel_currency = st.selectbox(
                    "💱 Currency",
                    options=["USD", "EUR", "GBP", "CAD", "AUD", "JPY"],
                    index=0,
                    help="Preferred currency for hotel prices. Default: USD"
                )
            
            col_h6, col_h7 = st.columns(2)
            with col_h6:
                hotel_price_min = st.number_input(
                    "💰 Min Price/Night",
                    min_value=0,
                    max_value=1000,
                    value=0,
                    help="Minimum price per night in selected currency. Optional filter"
                )
            with col_h7:
                hotel_price_max = st.number_input(
                    "💰 Max Price/Night",
                    min_value=0,
                    max_value=2000,
                    value=500,
                    help="Maximum price per night in selected currency. Default: 500"
                )
            
            col_h8, col_h9 = st.columns(2)
            with col_h8:
                hotel_sort = st.selectbox(
                    "📊 Sort Hotels By",
                    options=["price", "popularity", "distance", "rating"],
                    index=0,
                    help="How to sort hotel results. Default: price (lowest first)"
                )
            with col_h9:
                hotel_locale = st.selectbox(
                    "🌍 Language/Region",
                    options=["en-gb", "en-us", "fr-fr", "de-de", "es-es", "it-it", "pt-pt", "nl-nl"],
                    index=0,
                    help="Language and region for hotel descriptions. Default: English (UK)"
                )
        else:
            # Set default values when no hotel is needed
            hotel_adults = 2
            hotel_rooms = 1
            hotel_children = 0
            hotel_currency = "USD"
            hotel_price_min = 0
            hotel_price_max = 500
            hotel_sort = "price"
            hotel_locale = "en-gb"
        
        # Budget
        st.subheader("💰 Budget")
        budget = st.number_input(
            "💵 Total Trip Budget (USD)",
            min_value=500,
            max_value=100000,
            value=20000,
            step=500,
            help="Set your total budget for flights, hotels, and activities (in USD)"
        )
        
        # Additional preferences
        st.subheader("🎨 Additional Preferences")
        
        preferences = st.multiselect(
            "✈️ Flight Preferences",
            options=[
                "Window Seat",
                "Extra Legroom", 
                "Meal Included",
                "WiFi Available",
                "Priority Boarding",
                "Flexible Dates",
                "Same Airline",
                "Direct Flights Preferred"
            ],
            help="Select any special preferences for your flight"
        )
        
        notes = st.text_area(
            "📝 Special Requirements or Notes",
            placeholder="Any dietary restrictions, mobility assistance, or other special requirements?",
            height=80,
            help="Optional: Add any special requirements or preferences for your trip"
        )
        
        search_button = st.form_submit_button("🔍 Search Trips", use_container_width=True)
        
        if search_button:
            # Validate required fields
            errors = []
            if not origin:
                errors.append("❌ Origin airport code is required")
            elif len(origin) != 3 or not origin.isalpha():
                errors.append("❌ Origin must be a valid 3-letter airport code (e.g., NYC, LAX)")
                
            if not destination:
                errors.append("❌ Destination airport code is required")
            elif len(destination) != 3 or not destination.isalpha():
                errors.append("❌ Destination must be a valid 3-letter airport code (e.g., NYC, LAX)")
                
            if return_date and return_date < departure_date:
                errors.append("❌ Return date cannot be before departure date")
                
            if adults + children + infants > 9:
                errors.append("❌ Total passengers cannot exceed 9")
                
            if errors:
                for error in errors:
                    st.error(error)
            else:
                # Prepare search data for enhanced backend with real APIs
                search_data = {
                    # Flight parameters
                    "origin": origin.upper(),
                    "destination": destination.upper(), 
                    "departure_date": departure_date.isoformat(),
                    "return_date": return_date.isoformat() if return_date else None,
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
                    # Budget and preferences
                    "budget": budget,
                    "preferences": ",".join(preferences) if preferences else "",
                    "notes": notes
                }
                
                with st.spinner("🔄 Searching for trips with real APIs..."):
                    # Make API call to search endpoint using form data
                    response = make_api_request(
                        "/search",
                        method="POST",
                        data=search_data,
                        headers=get_auth_headers(),
                        form_data=True
                    )
                    
                    if response and response.status_code == 200:
                        search_response = response.json()
                        
                        # Enhanced backend returns search_id and processes asynchronously
                        if 'search_id' in search_response:
                            search_id = search_response['search_id']
                            
                            # Poll for results with progress indicator
                            import time
                            max_attempts = 30  # 30 attempts = 60 seconds max
                            attempt = 0
                            
                            while attempt < max_attempts:
                                # Get results using search_id
                                results_response = make_api_request(
                                    f"/search/{search_id}",
                                    method="GET",
                                    headers=get_auth_headers()
                                )
                                
                                if results_response and results_response.status_code == 200:
                                    results_data = results_response.json()
                                    
                                    if results_data.get('status') == 'completed':
                                        # Success! Store results and navigate
                                        st.session_state.search_results = results_data
                                        st.session_state.current_page = 'results'
                                        st.rerun()
                                        break
                                    elif results_data.get('status') == 'failed':
                                        st.error(f"❌ Search failed: {results_data.get('error', 'Unknown error')}")
                                        break
                                    else:
                                        # Still processing, wait and try again
                                        time.sleep(2)
                                        attempt += 1
                                        # Update progress
                                        progress_text = f"Processing... ({attempt}/{max_attempts})"
                                        st.text(progress_text)
                                else:
                                    st.error("❌ Failed to retrieve search results.")
                                    break
                            
                            if attempt >= max_attempts:
                                st.error("❌ Search timed out. Please try again with simpler criteria.")
                        else:
                            # Direct results (fallback for other backends)
                            st.session_state.search_results = search_response
                            st.session_state.current_page = 'results'
                            st.rerun()
                            
                    elif response and response.status_code == 401:
                        st.error("❌ Session expired. Please login again.")
                        logout()
                        st.rerun()
                    else:
                        st.error("❌ Search failed. Please try again.")

def handle_email_sharing_modals():
    """Handle email sharing modals for all recommendations"""
    # Check if there are any search results
    if not st.session_state.search_results or 'results' not in st.session_state.search_results:
        return
    
    results = st.session_state.search_results['results']
    
    # Check each recommendation for active share modals
    for i, trip in enumerate(results.get('results', []), 1):
        modal_key = f"show_share_modal_{i}"
        recommendation_key = f"share_recommendation_{i}"
        
        # If modal should be shown for this recommendation
        if st.session_state.get(modal_key, False):
            # Create modal container
            with st.container():
                st.markdown("---")
                st.subheader(f"📧 Share Recommendation {i}")
                
                with st.form(key=f"email_form_{i}"):
                    st.markdown("**Send this travel recommendation via email:**")
                    
                    # Email input field
                    recipient_email = st.text_input(
                        "📨 Recipient Email Address",
                        placeholder="Enter recipient's email address",
                        key=f"email_input_{i}",
                        help="Enter the email address where you want to send this recommendation"
                    )
                    
                    # Display preview of what will be sent
                    recommendation_data = st.session_state.get(recommendation_key, trip)
                    st.markdown("**Preview:**")
                    with st.expander("Email Content Preview", expanded=False):
                        st.markdown(f"**Subject:** 🌍 Travel Recommendation from {st.session_state.username}")
                        st.markdown(f"**Destination:** {recommendation_data.get('destination', 'N/A')}")
                        st.markdown(f"**Dates:** {recommendation_data.get('dates', 'N/A')}")
                        st.markdown(f"**Budget:** ${recommendation_data.get('budget', 0):,.0f}")
                        
                        # Show truncated recommendation text
                        description = recommendation_data.get('description', 'No description available')
                        if len(description) > 200:
                            st.markdown(f"**Description:** {description[:200]}...")
                        else:
                            st.markdown(f"**Description:** {description}")
                    
                    # Form buttons
                    col1, col2, col3 = st.columns([1, 1, 1])
                    with col1:
                        send_button = st.form_submit_button("📧 Send Email", use_container_width=True)
                    with col2:
                        cancel_button = st.form_submit_button("❌ Cancel", use_container_width=True)
                    
                    # Handle form submission
                    if send_button:
                        if recipient_email:
                            if '@' in recipient_email and '.' in recipient_email:  # Basic email validation
                                # Send email using MailJet
                                result = send_recommendation_email(
                                    recipient_email=recipient_email,
                                    recommendation_data=recommendation_data,
                                    sender_name=st.session_state.username
                                )
                                
                                if result['status'] == 'success':
                                    st.success(f"✅ Email sent successfully to {recipient_email}!")
                                    # Clear modal state
                                    st.session_state[modal_key] = False
                                    if recommendation_key in st.session_state:
                                        del st.session_state[recommendation_key]
                                    st.rerun()
                                else:
                                    st.error(f"❌ Failed to send email: {result['message']}")
                            else:
                                st.error("❌ Please enter a valid email address")
                        else:
                            st.error("❌ Please enter an email address")
                    
                    if cancel_button:
                        # Clear modal state
                        st.session_state[modal_key] = False
                        if recommendation_key in st.session_state:
                            del st.session_state[recommendation_key]
                        st.rerun()

def send_recommendation_email(recipient_email: str, recommendation_data: dict, sender_name: str) -> dict:
    """Send recommendation email using MailJet"""
    try:
        email_tool = MailJetEmailTool()
        return email_tool.send_recommendation_email(
            recipient_email=recipient_email,
            recommendation_data=recommendation_data,
            user_name=sender_name
        )
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error initializing email service: {str(e)}'
        }

def results_page():
    """Display search results"""
    st.title("🎯 Search Results")
    
    # User info in sidebar
    with st.sidebar:
        st.write(f"👤 Logged in as: **{st.session_state.username}**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 New Search", use_container_width=True):
                st.session_state.current_page = 'search'
                st.rerun()
        with col2:
            if st.button("🚪 Logout", use_container_width=True):
                logout()
                st.rerun()
    
    if st.session_state.search_results:
        results = st.session_state.search_results
        
        # Check if results is a list or dict with results key
        if isinstance(results, dict) and 'results' in results:
            inner_results = results['results']
            # Handle nested results structure from enhanced backend
            if isinstance(inner_results, dict) and 'results' in inner_results:
                trips = inner_results['results']  # Enhanced backend format
            else:
                trips = inner_results  # Direct array format
        elif isinstance(results, list):
            trips = results
        else:
            trips = []
        
        if trips:
            st.subheader(f"🎯 AI-Powered Trip Recommendations")
            
            # Display each recommendation
            for i, trip in enumerate(trips, 1):
                # Check if this is an enhanced recommendation
                if trip.get('type') == 'enhanced_recommendation':
                    # Display enhanced AI recommendation
                    st.markdown(f"### {trip.get('title', f'Trip Recommendation {i}')}")
                    
                    # Show quick overview
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.info(f"🎯 **Destination:** {trip.get('destination', 'N/A')}")
                    with col2:
                        st.info(f"📅 **Dates:** {trip.get('dates', 'N/A')}")
                    with col3:
                        st.info(f"💰 **Budget:** ${trip.get('budget', 0):,.0f}")
                    
                    # Show AI sources
                    if trip.get('api_sources'):
                        st.success(f"🔥 **Powered by:** {' • '.join(trip['api_sources'])}")
                    
                    # Show the full AI recommendation
                    with st.expander("📖 View Full AI-Powered Trip Plan", expanded=True):
                        st.markdown(trip.get('full_recommendation', trip.get('description', 'No details available')))
                    
                    # Show processing summary
                    if trip.get('tasks'):
                        with st.expander("⚙️ Processing Summary"):
                            for task in trip['tasks']:
                                st.success(f"✅ {task}")
                    
                    # Action buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"🔖 Save Recommendation {i}", key=f"save_{i}"):
                            st.success(f"Recommendation {i} saved!")
                    with col2:
                        if st.button(f"📧 Share Recommendation {i}", key=f"share_{i}"):
                            st.session_state[f"show_share_modal_{i}"] = True
                            st.session_state[f"share_recommendation_{i}"] = trip
                    
                else:
                    # Display traditional flight format (fallback)
                    with st.container():
                        st.markdown(f"""
                        <div class="trip-card">
                            <h4>Trip {i}: {trip.get('airline', 'Unknown')} - {trip.get('flight_number', 'N/A')}</h4>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Price", f"${trip.get('price', 0):,.0f}")
                        
                        with col2:
                            st.metric("Duration", f"{trip.get('duration', 0)} hrs")
                        
                        with col3:
                            st.metric("Stops", trip.get('stops', 0))
                        
                        with col4:
                            if st.button(f"Book Trip {i}", key=f"book_{i}"):
                                st.success(f"Booking initiated for Trip {i}!")
                        
                        # Additional trip details
                        if trip.get('departure_time'):
                            st.write(f"🛫 Departure: {trip.get('departure_time')}")
                        if trip.get('arrival_time'):
                            st.write(f"🛬 Arrival: {trip.get('arrival_time')}")
                        if trip.get('aircraft_type'):
                            st.write(f"✈️ Aircraft: {trip.get('aircraft_type')}")
                
                st.divider()
        else:
            st.info("🔍 No trips found matching your criteria. Try adjusting your search parameters.")
    else:
        st.error("No search results available. Please go back and search for trips.")
    
    # Email sharing modal
    handle_email_sharing_modals()

# Main app routing
def main():
    """Main application function"""
    # Check authentication
    if st.session_state.authenticated and st.session_state.token:
        # Verify token is still valid
        token_data = decode_token(st.session_state.token)
        if not token_data:
            logout()
            st.rerun()
    
    # Route to appropriate page
    if not st.session_state.authenticated:
        if st.session_state.current_page == 'register':
            register_page()
        else:
            login_page()
    else:
        if st.session_state.current_page == 'results':
            results_page()
        else:
            search_page()

# Run the app
if __name__ == "__main__":
    main()