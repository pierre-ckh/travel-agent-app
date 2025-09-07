#!/usr/bin/env python3
"""
Test script for MailJet email functionality
"""
import os
from tools.mailjet_email_tool import MailJetEmailTool
from dotenv import load_dotenv

def test_email_setup():
    """Test that email environment variables are configured"""
    load_dotenv()
    
    required_vars = [
        "MAILJET_API_KEY",
        "MAILJET_API_SECRET", 
        "SHARE_SENDER_EMAIL",
        "SHARE_SENDER_NAME"
    ]
    
    print("Checking email environment variables...")
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if var in ["MAILJET_API_KEY", "MAILJET_API_SECRET"]:
                # Hide sensitive values
                display_value = f"{value[:8]}..." if len(value) > 8 else "***"
            else:
                display_value = value
            print(f"OK {var}: {display_value}")
        else:
            print(f"MISSING {var}: Not set")
            return False
    
    return True

def test_email_tool_creation():
    """Test creating the MailJet email tool"""
    print("\nTesting MailJet tool creation...")
    try:
        email_tool = MailJetEmailTool()
        print("OK MailJet tool created successfully")
        return True, email_tool
    except Exception as e:
        print(f"ERROR Failed to create MailJet tool: {str(e)}")
        return False, None

def test_sample_recommendation():
    """Create sample recommendation data for testing"""
    return {
        "title": "🤖 AI-Powered Travel Plan for Tokyo",
        "description": "A fantastic trip to Japan's capital city with AI-curated experiences!",
        "destination": "Tokyo",
        "dates": "2024-12-15 to 2024-12-22", 
        "budget": 3500,
        "full_recommendation": """# Trip to Tokyo

## Overview
Experience the perfect blend of traditional culture and cutting-edge technology in Tokyo! This 7-day itinerary combines must-see landmarks, authentic cuisine, and unique experiences.

## Highlights
- Visit iconic temples like Senso-ji and Meiji Shrine
- Explore vibrant neighborhoods: Shibuya, Harajuku, Ginza
- Experience world-class sushi at Tsukiji Outer Market
- Take in panoramic views from Tokyo Skytree
- Day trip to nearby Mount Fuji area

## Budget Breakdown
- Flights: $1,200
- Hotels: $1,400 (7 nights)
- Food & Activities: $800
- Transportation: $100

## Travel Tips
- Get a JR Pass for unlimited train travel
- Learn basic Japanese phrases
- Try convenience store food - it's amazing!
- Book restaurant reservations in advance

This itinerary offers the perfect introduction to Japan's most dynamic city!""",
        "interests": ["culture", "food", "technology"],
        "api_sources": ["Amadeus Flight API", "Booking.com Hotel API", "Anthropic Claude AI"]
    }

def main():
    """Main test function"""
    print("Testing MailJet Email Functionality")
    print("=" * 50)
    
    # Test 1: Check environment variables
    if not test_email_setup():
        print("\nERROR Email setup test failed. Please check your .env file.")
        return
    
    # Test 2: Create email tool
    success, email_tool = test_email_tool_creation()
    if not success:
        return
    
    # Test 3: Show sample data
    print("\nSample recommendation data:")
    sample_data = test_sample_recommendation()
    print(f"Title: {sample_data['title']}")
    print(f"Destination: {sample_data['destination']}")
    print(f"Dates: {sample_data['dates']}")
    print(f"Budget: ${sample_data['budget']:,}")
    print(f"Description length: {len(sample_data['full_recommendation'])} characters")
    
    print("\nOK All tests passed! Email functionality is ready to use.")
    print("\nTo test email sending:")
    print("1. Make sure your MailJet API credentials are valid")
    print("2. Use the Share Recommendation button in the app")
    print("3. Enter a test email address")
    print("4. Click Send Email")
    
    # Optionally test actual email sending (commented out for safety)
    """
    print("\n🧪 Testing actual email sending...")
    test_email = input("Enter test email address (or press Enter to skip): ").strip()
    if test_email and '@' in test_email:
        print(f"Sending test email to {test_email}...")
        result = email_tool.send_recommendation_email(
            recipient_email=test_email,
            recommendation_data=sample_data,
            user_name="Test User"
        )
        print(f"Result: {result}")
    else:
        print("Skipping actual email test")
    """

if __name__ == "__main__":
    main()