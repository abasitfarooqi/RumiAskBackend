"""
Test the Rumi conversational system
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.query_analyzer import get_query_analyzer
from services.quote_retriever import get_quote_retriever
from services.rumi_responder import get_rumi_responder

def test_query_analysis():
    """Test query analysis"""
    print("=" * 60)
    print("TEST 1: Query Analysis")
    print("=" * 60)
    
    analyzer = get_query_analyzer()
    
    test_queries = [
        "I'm afraid to love deeply, should I take risks?",
        "How do I find my purpose in life?",
        "Why do I feel so lost and empty?",
        "How do I become wiser?",
        "I'm seeking guidance on love"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        intent = analyzer.analyze(query)
        print(f"  Intent: {intent.intent_type}")
        print(f"  Emotions: {intent.emotions}")
        print(f"  Themes: {intent.themes}")
        print(f"  Keywords: {intent.keywords[:5]}")
    
    print("\n" + "=" * 60)
    print("✅ Query Analysis Test Complete")
    print("=" * 60)

def test_quote_retrieval():
    """Test quote retrieval"""
    print("\n" + "=" * 60)
    print("TEST 2: Quote Retrieval")
    print("=" * 60)
    
    analyzer = get_query_analyzer()
    retriever = get_quote_retriever()
    
    test_query = "I'm afraid to love, what should I do?"
    
    print(f"\nQuery: {test_query}")
    intent = analyzer.analyze(test_query)
    print(f"\nDetected:")
    print(f"  Intent: {intent.intent_type}")
    print(f"  Emotions: {intent.emotions}")
    print(f"  Themes: {intent.themes}")
    
    quotes = retriever.retrieve(intent, max_quotes=3)
    
    print(f"\nRetrieved {len(quotes)} quotes:")
    for i, quote in enumerate(quotes, 1):
        print(f"\n{i}. {quote['quote'][:80]}...")
        print(f"   Theme: {quote.get('primary_theme', 'N/A')}")
        print(f"   Tags: {', '.join(quote.get('micro_tags', [])[:3])}")
    
    print("\n" + "=" * 60)
    print("✅ Quote Retrieval Test Complete")
    print("=" * 60)

def test_response_generation():
    """Test response generation"""
    print("\n" + "=" * 60)
    print("TEST 3: Response Generation")
    print("=" * 60)
    
    analyzer = get_query_analyzer()
    retriever = get_quote_retriever()
    responder = get_rumi_responder()
    
    query = "I'm afraid to love deeply"
    
    print(f"\nQuery: {query}")
    
    intent = analyzer.analyze(query)
    quotes = retriever.retrieve(intent, max_quotes=3)
    
    prompt = responder.generate_prompt(query, quotes, intent)
    
    print(f"\nGenerated Prompt (preview):")
    print("─" * 60)
    print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
    print("─" * 60)
    
    print("\n" + "=" * 60)
    print("✅ Response Generation Test Complete")
    print("=" * 60)

def test_complete_flow():
    """Test complete flow"""
    print("\n" + "=" * 60)
    print("TEST 4: Complete Flow")
    print("=" * 60)
    
    analyzer = get_query_analyzer()
    retriever = get_quote_retriever()
    responder = get_rumi_responder()
    
    queries = [
        "What is the meaning of life?",
        "I'm afraid to take risks in love",
        "How do I find myself?",
        "Why do I feel empty inside?"
    ]
    
    for query in queries:
        print(f"\n{'─' * 60}")
        print(f"Query: {query}")
        print("─" * 60)
        
        # Analyze
        intent = analyzer.analyze(query)
        print(f"Intent: {intent.intent_type} | Emotions: {intent.emotions} | Themes: {intent.themes}")
        
        # Retrieve
        quotes = retriever.retrieve(intent, max_quotes=2)
        print(f"Retrieved: {len(quotes)} quotes")
        
        if quotes:
            print(f"\nTop quote:")
            print(f'  "{quotes[0]["quote"][:100]}..."')
    
    print("\n" + "=" * 60)
    print("✅ Complete Flow Test Complete")
    print("=" * 60)

def main():
    """Run all tests"""
    print("\n🧪 Testing Rumi Conversational System")
    print("=" * 60)
    
    try:
        # Run tests
        test_query_analysis()
        test_quote_retrieval()
        test_response_generation()
        test_complete_flow()
        
        print("\n" + "=" * 60)
        print("🎉 All Tests Passed!")
        print("=" * 60)
        print("\n✅ System is ready to use!")
        print("\nTo test via API:")
        print("  python main.py  # or uvicorn main:app")
        print("  curl -X POST http://localhost:8000/api/chat/ask-rumi \\")
        print('       -H "Content-Type: application/json" \\')
        print('       -d \'{"message": "What is love?"}\'')
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

