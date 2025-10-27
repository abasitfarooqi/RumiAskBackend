"""
Test name context and conversational memory
"""

import requests

BASE_URL = "http://127.0.0.1:8001"

def test():
    print("Testing name context and conversation memory...\n")
    
    # Message 1: Name introduction
    print("1. User: 'my name is clara'")
    r1 = requests.post(
        f"{BASE_URL}/api/chat/ask-rumi",
        json={"message": "my name is clara", "model": "gemma3:270m"}
    )
    resp1 = r1.json()
    conv_id = resp1['conversation_id']
    print(f"   Response: {resp1['response'][:100]}...")
    print(f"   Conv ID: {conv_id}\n")
    
    # Message 2: Follow-up question
    print("2. User: 'what is love'")
    r2 = requests.post(
        f"{BASE_URL}/api/chat/ask-rumi",
        json={"message": "what is love", "model": "gemma3:270m", "conversation_id": conv_id}
    )
    resp2 = r2.json()
    print(f"   Response: {resp2['response'][:300]}...")
    print(f"   Contains 'Clara' or name reference: {'Clara' in resp2['response'] or 'clara' in resp2['response']}\n")
    
    # Check conversation
    print("3. Checking conversation history...")
    history = requests.get(f"{BASE_URL}/api/chat/conversations/{conv_id}").json()
    print(f"   Total messages: {len(history['messages'])}")
    for i, msg in enumerate(history['messages'], 1):
        print(f"   {i}. {msg['role']}: {msg['content'][:80]}...")

if __name__ == "__main__":
    test()

