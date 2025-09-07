#!/usr/bin/env python3
"""
Simple test script to debug login issues
"""
import requests
import json

def test_login():
    """Test the login endpoint"""
    url = "http://localhost:8000/login"
    
    # Test with form data (OAuth2PasswordRequestForm expects this)
    data = {
        "username": "testuser",
        "password": "testpass123"
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    print("Testing login endpoint...")
    print(f"URL: {url}")
    print(f"Data: {data}")
    print(f"Headers: {headers}")
    
    try:
        response = requests.post(url, data=data, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("SUCCESS: Login successful!")
            print(f"Response: {response.json()}")
        else:
            print("FAILED: Login failed!")
            print(f"Response text: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to server. Is it running?")
    except Exception as e:
        print(f"ERROR: {e}")

def test_registration():
    """Test the registration endpoint"""
    url = "http://localhost:8000/register"
    
    data = {
        "username": "testuser2", 
        "email": "test2@example.com",
        "password": "testpass123"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("\nTesting registration endpoint...")
    print(f"URL: {url}")
    print(f"Data: {data}")
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 201:
            print("SUCCESS: Registration successful!")
            print(f"Response: {response.json()}")
        else:
            print("FAILED: Registration failed!")
            print(f"Response text: {response.text}")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_registration()
    test_login()