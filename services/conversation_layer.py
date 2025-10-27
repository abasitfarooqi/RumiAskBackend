"""
Conversation Layer - Smart routing between casual chat and Rumi wisdom
"""

from services.query_analyzer import QueryIntent, get_query_analyzer

class ConversationLayer:
    """Manage casual chat vs Rumi wisdom layers"""
    
    def __init__(self):
        self.analyzer = get_query_analyzer()
    
    def needs_empathetic_support(self, query: str) -> bool:
        """Detect if query needs empathetic support before wisdom"""
        query_lower = query.lower().strip()
        
        # Emotional distress patterns - EXPANDED for better detection
        distress_patterns = [
            # Physical/emotional pain
            "i'm in pain", "i feel pain", "i am in pain", "in pain", "hurts",
            "i'm hurt", "i feel hurt", "hurting", "suffering", "struggling",
            "feeling sorry", "i'm sorry", "i feel sorry", "feel sorry",
            
            # Fear and anxiety
            "i'm scared", "i'm afraid", "afraid", "scared", "worried",
            "anxious", "overwhelmed", "can't cope", "can't handle",
            
            # Sadness and despair
            "feeling sad", "i'm sad", "i feel sad", "sad", "depressed", 
            "down", "low", "feeling low", "hopeless", "lost",
            
            # Confusion and uncertainty
            "don't know", "dont know", "i don't know", "dunno",
            "don't understand", "confused", "lost", "stuck",
            
            # Help-seeking
            "can't deal with", "can't handle", "too much", "overwhelmed",
            "help me", "i need help", "what should i do",
            
            # Emoticons (check in original query)
            ":(", ":'(", "😢", "😭", "😰", "😞", "😔", "😓",
        ]
        
        # Check original query for emoticons (not just lowercase)
        has_emoticons = any(emoji in query for emoji in [":(", ":'(", "😢", "😭", "😰", "😞", "😔", "😓"])
        
        # Check for emotional distress patterns
        has_distress_pattern = any(pattern in query_lower for pattern in distress_patterns)
        
        return has_distress_pattern or has_emoticons
    
    def should_use_rumi_wisdom(self, query: str) -> bool:
        """
        Determine if query needs Rumi wisdom or just casual response
        
        Returns:
            True = Use Rumi wisdom (quotes, sources)
            False = Casual chat (simple response)
        """
        query_lower = query.lower().strip()
        
        # EXPLICIT casual patterns - never use wisdom
        casual_patterns = ["hi", "hello", "hey", "how are you", "what's up", "sup"]
        if any(pattern in query_lower for pattern in casual_patterns):
            return False
        
        # Name questions = casual
        if "name" in query_lower or "who are you" in query_lower:
            return False
        
        # Deep/emotional indicators = Rumi wisdom
        deep_indicators = [
            "meaning", "purpose", "life", "death", "soul", "love", "truth",
            "spiritual", "wisdom", "heart", "journey", "path", "beauty",
            "sad", "sadness", "happy", "happiness", "fear", "afraid", "hope", 
            "transformation", "desire", "longing", "pain", "hurt", "angry", "anger"
        ]
        
        # Also check for emotion patterns like "I feel..."
        emotion_patterns = ["i feel", "i'm feeling", "i am feeling", "makes me feel"]
        has_emotion = any(pattern in query_lower for pattern in emotion_patterns)
        
        has_deep_theme = any(indicator in query_lower for indicator in deep_indicators) or has_emotion
        
        # If no deep theme, check if question is philosophical (longer)
        is_philosophical = len(query.split()) > 4 and "?" in query
        
        return has_deep_theme or is_philosophical

