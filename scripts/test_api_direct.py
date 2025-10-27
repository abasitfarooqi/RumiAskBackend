"""
Test the API directly to debug issues
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8001"

def test_basic_query():
    """Test a basic query without conversation"""
    print("=" * 60)
    print("TEST 1: Basic Query")
    print("=" * 60)
    
    response = requests.post(
        f"{BASE_URL}/api/chat/ask-rumi",
        json={
            "message": "what is love",
            "model": "gemma3:270m",
            "temperature": 0.8
        }
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {data.get('response', 'EMPTY')[:150]}")
    conv_id = data.get('conversation_id')
    print(f"Conv ID: {conv_id}")
    return conv_id

def test_followup(conv_id):
    """Test followup with conversation context"""
    print("\n" + "=" * 60)
    print("TEST 2: Followup Query (with context)")
    print("=" * 60)
    
    response = requests.post(
        f"{BASE_URL}/api/chat/ask-rumi",
        json={
            "message": "I'm afraid to love",
            "model": "gemma3:270m",
            "temperature": 0.8,
            "conversation_id": conv_id
        }
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    response_text = data.get('response', 'EMPTY')
    print(f"Response: {response_text[:200]}")
    
    if len(response_text) == 0:
        print("\n❌ ERROR: Empty response!")
    
    return response_text != data.get('response', '')  # Check if different from first

def check_conversation(conv_id):
    """Check conversation history"""
    print("\n" + "=" * 60)
    print("TEST 3: Check Conversation History")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/api/chat/conversations/{conv_id}")
    data = response.json()
    
    print(f"Total messages: {len(data.get('messages', []))}")
    for i, msg in enumerate(data.get('messages', []), 1):
        print(f"\nMessage {i}:")
        print(f"  Role: {msg.get('role')}")
        print(f"  Content: {msg.get('content')[:100]}...")

if __name__ == "__main__":
    try:
        conv_id = test_basic_query()
        test_followup(conv_id)
        check_conversation(conv_id)
        print("\n✅ All tests complete")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

