"""
Retrieve relevant quotes based on query intent
"""

from typing import List, Dict, Any, Tuple
from services.knowledge_loader import get_knowledge_base
from services.query_analyzer import QueryIntent

class QuoteRetriever:
    """Retrieve relevant quotes from knowledge base"""
    
    def __init__(self):
        self.kb = get_knowledge_base()
    
    def retrieve(self, intent: QueryIntent, max_quotes: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve quotes based on query intent
        
        Args:
            intent: QueryIntent object with analyzed user query
            max_quotes: Maximum number of quotes to return
            
        Returns:
            List of quotes with scores
        """
        scored_quotes = []
        
        for quote in self.kb.get_all_quotes():
            score = self._calculate_score(quote, intent)
            scored_quotes.append((score, quote))
        
        # Sort by score descending and return top quotes
        scored_quotes.sort(key=lambda x: x[0], reverse=True)
        
        # Get top quotes (those with score > 0)
        top_quotes = [
            quote for score, quote in scored_quotes[:max_quotes * 3] 
            if score > 0
        ]
        
        return top_quotes[:max_quotes]
    
    def _calculate_score(self, quote: Dict[str, Any], intent: QueryIntent) -> float:
        """Calculate relevance score for a quote"""
        score = 0.0
        
        # 1. Theme matching (highest weight)
        quote_theme = quote.get('primary_theme', '').lower()
        for theme in intent.themes:
            if theme in quote_theme:
                score += 5.0
                break
        
        # 2. Emotion matching
        quote_emotions = [e.lower() for e in quote.get('emotion_tags', [])]
        intent_emotions = [e.lower() for e in intent.emotions]
        
        for emotion in intent_emotions:
            if emotion in ' '.join(quote_emotions):
                score += 4.0
        
        # 3. Tag matching
        quote_tags = [t.lower() for t in quote.get('micro_tags', [])]
        for keyword in intent.keywords:
            # Check if keyword appears in tags
            for tag in quote_tags:
                if keyword in tag or tag in keyword:
                    score += 2.0
                    break
        
        # 4. Query intent in user_questions or query_intent
        quote_intents = quote.get('query_intent', []) + quote.get('user_questions', [])
        query_lower = intent.detected_query.lower()
        
        for qi in quote_intents:
            # Check if query words appear in intent
            if any(word in qi.lower() for word in query_lower.split() if len(word) > 3):
                score += 3.0
                break
        
        # 5. Text similarity (simple keyword match in quote)
        quote_text_lower = quote.get('quote', '').lower()
        matched_keywords = sum(1 for kw in intent.keywords if kw in quote_text_lower)
        score += matched_keywords * 1.0
        
        return score
    
    def get_by_id(self, quote_id: str) -> Dict[str, Any]:
        """Get a specific quote by ID"""
        return self.kb.get_quote_by_id(quote_id)
    
    def get_by_theme(self, theme: str) -> List[Dict[str, Any]]:
        """Get quotes by theme"""
        return self.kb.get_quotes_by_theme(theme)
    
    def get_all_themes(self) -> List[str]:
        """Get all available themes"""
        return self.kb.get_themes()

# Global instance
_retriever_instance = None

def get_quote_retriever() -> QuoteRetriever:
    """Get global retriever instance"""
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = QuoteRetriever()
    return _retriever_instance

