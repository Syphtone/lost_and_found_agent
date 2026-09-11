import requests
import json

# Test the backend /chat endpoint
url = "http://localhost:8000/chat"

# Test 1: Initial message
print("=== Test 1: Initial lost report ===")
payload = {
    "message": "I lost my wallet near the library",
    "conversation_id": "test123"
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    # Test 2: Verification answer
    print("\n=== Test 2: Verification answer ===")
    payload2 = {
        "message": "red sticker inside",
        "conversation_id": "test123"
    }
    
    response2 = requests.post(url, json=payload2)
    print(f"Status Code: {response2.status_code}")
    result2 = response2.json()
    print(f"Response: {json.dumps(result2, indent=2)}")
    
except Exception as e:
    print(f"Error: {e}")
