"""
Test multiple questions in one conversation with different responses
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8001"

def test_multi_questions():
    """Test multiple questions in one conversation"""
    print("=" * 70)
    print("MULTI-QUESTION CONVERSATION TEST")
    print("=" * 70)
    
    responses = []
    
    # Question 1
    print("\n📍 Question 1: 'what is love?'")
    print("-" * 70)
    r1 = requests.post(
        f"{BASE_URL}/api/chat/ask-rumi",
        json={
            "message": "what is love",
            "model": "gemma3:270m",
            "temperature": 0.8
        }
    )
    data1 = r1.json()
    resp1 = data1.get('response', '')
    conv_id = data1.get('conversation_id')
    print(f"Response: {resp1[:200]}...")
    print(f"Conversation ID: {conv_id}")
    responses.append(resp1)
    
    # Question 2 - Different topic
    print("\n📍 Question 2: 'I'm feeling lost' (different topic)")
    print("-" * 70)
    r2 = requests.post(
        f"{BASE_URL}/api/chat/ask-rumi",
        json={
            "message": "I'm feeling lost",
            "model": "gemma3:270m",
            "temperature": 0.8,
            "conversation_id": conv_id
        }
    )
    data2 = r2.json()
    resp2 = data2.get('response', '')
    print(f"Response: {resp2[:200]}...")
    responses.append(resp2)
    
    # Question 3 - Follow-up
    print("\n📍 Question 3: 'how do I find myself' (follow-up)")
    print("-" * 70)
    r3 = requests.post(
        f"{BASE_URL}/api/chat/ask-rumi",
        json={
            "message": "how do I find myself",
            "model": "gemma3:270m",
            "temperature": 0.8,
            "conversation_id": conv_id
        }
    )
    data3 = r3.json()
    resp3 = data3.get('response', '')
    print(f"Response: {resp3[:200]}...")
    responses.append(resp3)
    
    # Question 4 - Another different topic
    print("\n📍 Question 4: 'what is wisdom' (completely different)")
    print("-" * 70)
    r4 = requests.post(
        f"{BASE_URL}/api/chat/ask-rumi",
        json={
            "message": "what is wisdom",
            "model": "gemma3:270m",
            "temperature": 0.8,
            "conversation_id": conv_id
        }
    )
    data4 = r4.json()
    resp4 = data4.get('response', '')
    print(f"Response: {resp4[:200]}...")
    responses.append(resp4)
    
    # Analyze results
    print("\n" + "=" * 70)
    print("RESULT ANALYSIS")
    print("=" * 70)
    
    # Check if all responses are different
    unique_responses = len(set(responses))
    print(f"\n✅ Total responses: {len(responses)}")
    print(f"✅ Unique responses: {unique_responses}")
    
    if unique_responses == len(responses):
        print("\n🎉 SUCCESS! All responses are different!")
    else:
        print(f"\n❌ FAILURE! {len(responses) - unique_responses} duplicate responses")
        
    # Show which ones are different
    for i, resp in enumerate(responses, 1):
        is_unique = responses.count(resp) == 1
        status = "✅" if is_unique else "❌ DUPLICATE"
        print(f"\n{status} Response {i} is unique: {is_unique}")
    
    # Check conversation history
    print("\n" + "=" * 70)
    print("CONVERSATION HISTORY")
    print("=" * 70)
    
    history = requests.get(f"{BASE_URL}/api/chat/conversations/{conv_id}")
    hist_data = history.json()
    
    for i, msg in enumerate(hist_data.get('messages', []), 1):
        print(f"\nMessage {i}:")
        print(f"  Role: {msg.get('role')}")
        content = msg.get('content', '')
        print(f"  Content: {content[:150]}...")
    
    return unique_responses == len(responses)

if __name__ == "__main__":
    print("\n🧪 Starting Multi-Question Chat Test\n")
    success = test_multi_questions()
    
    if success:
        print("\n✅ TEST PASSED: System working correctly!")
    else:
        print("\n❌ TEST FAILED: Context issue detected!")
    
    print("\n" + "=" * 70)

