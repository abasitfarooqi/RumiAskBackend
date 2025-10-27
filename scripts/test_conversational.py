"""
Test conversational, longer responses with variety
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8001"

def test_conversational_flow():
    """Test that responses are longer, more conversational, and varied"""
    print("=" * 80)
    print("CONVERSATIONAL RESPONSE TEST")
    print("=" * 80)
    
    responses = []
    
    # Question 1
    print("\n📍 Question 1: 'Hello, I'm feeling confused about life'")
    print("-" * 80)
    r1 = requests.post(
        f"{BASE_URL}/api/chat/ask-rumi",
        json={
            "message": "Hello, I'm feeling confused about life",
            "model": "gemma3:270m",
            "temperature": 0.85
        }
    )
    data1 = r1.json()
    resp1 = data1.get('response', '')
    conv_id = data1.get('conversation_id')
    print(f"Response:\n{resp1}")
    print(f"\nLength: {len(resp1.split())} words")
    print(f"Starts with: '{resp1[:50]}'")
    responses.append(resp1)
    
    # Question 2
    print("\n" + "-" * 80)
    print("📍 Question 2: 'I don't know my purpose'")
    print("-" * 80)
    r2 = requests.post(
        f"{BASE_URL}/api/chat/ask-rumi",
        json={
            "message": "I don't know my purpose",
            "model": "gemma3:270m",
            "temperature": 0.85,
            "conversation_id": conv_id
        }
    )
    data2 = r2.json()
    resp2 = data2.get('response', '')
    print(f"Response:\n{resp2}")
    print(f"\nLength: {len(resp2.split())} words")
    print(f"Starts with: '{resp2[:50]}'")
    responses.append(resp2)
    
    # Question 3
    print("\n" + "-" * 80)
    print("📍 Question 3: 'How should I live?'")
    print("-" * 80)
    r3 = requests.post(
        f"{BASE_URL}/api/chat/ask-rumi",
        json={
            "message": "How should I live?",
            "model": "gemma3:270m",
            "temperature": 0.85,
            "conversation_id": conv_id
        }
    )
    data3 = r3.json()
    resp3 = data3.get('response', '')
    print(f"Response:\n{resp3}")
    print(f"\nLength: {len(resp3.split())} words")
    print(f"Starts with: '{resp3[:50]}'")
    responses.append(resp3)
    
    # Analysis
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    
    # Check variety of openings
    openings = [r[:30].strip() for r in responses]
    unique_openings = len(set(openings))
    
    # Check lengths
    avg_length = sum(len(r.split()) for r in responses) / len(responses)
    min_length = min(len(r.split()) for r in responses)
    max_length = max(len(r.split()) for r in responses)
    
    print(f"\n✅ Average response length: {avg_length:.1f} words")
    print(f"✅ Min: {min_length} words, Max: {max_length} words")
    print(f"✅ Unique opening phrases: {unique_openings}/{len(responses)}")
    
    if avg_length >= 80:
        print("✅ Responses are sufficiently long (conversational)")
    else:
        print("⚠️  Responses too short (needs improvement)")
    
    if unique_openings == len(responses):
        print("✅ All openings are unique (good variety)")
    else:
        print(f"⚠️  Some repetitive openings ({unique_openings}/{len(responses)} unique)")
    
    # Show variety
    print("\nOpening variety:")
    for i, opening in enumerate(openings, 1):
        print(f"  {i}. '{opening}...'")
    
    print("\n" + "=" * 80)
    if avg_length >= 80 and unique_openings >= 2:
        print("✅ TEST PASSED: Conversational quality is good!")
    else:
        print("⚠️  TEST NEEDS IMPROVEMENT")

if __name__ == "__main__":
    test_conversational_flow()

