"""
Analyze user queries for intent, emotion, and themes
"""

import re
from typing import Dict, List, Any
from dataclasses import dataclass
from typing import Optional

@dataclass
class QueryIntent:
    """Query analysis result"""
    intent_type: str  # "seeking_guidance", "sharing", "question"
    emotions: List[str]
    themes: List[str]
    keywords: List[str]
    detected_query: str
    is_simple: bool = False  # True for simple greetings, false for deep questions

class QueryAnalyzer:
    """Analyze user queries for intelligent matching"""
    
    def __init__(self):
        # Intent keywords
        self.intent_patterns = {
            "seeking_guidance": [
                "help", "guide", "advice", "should i", "how do i", "what should",
                "tell me", "show me", "need", "wondering"
            ],
            "sharing": [
                "i feel", "i'm", "i am", "i've", "experienced", "going through"
            ],
            "question": [
                "what is", "why", "where", "how", "when", "who"
            ]
        }
        
        # Emotion keywords
        self.emotion_keywords = {
            "fear": ["afraid", "scared", "worried", "anxiety", "terrified", "frightened"],
            "love": ["love", "beloved", "adore", "cherish", "deeply", "heart"],
            "longing": ["miss", "long", "yearn", "crave", "ache", "homesick"],
            "sadness": ["sad", "depressed", "down", "melancholy", "sorrow", "grief"],
            "joy": ["happy", "joy", "ecstatic", "delighted", "bliss", "elated"],
            "seeking": ["search", "seek", "find", "look", "hunt", "pursue"],
            "uncertainty": ["lost", "confused", "uncertain", "don't know", "unclear"],
            "peace": ["calm", "peace", "tranquil", "serene", "still", "quiet"],
            "wisdom": ["understand", "learn", "wisdom", "know", "realize"],
            "transformation": ["change", "grow", "evolve", "become", "transform"]
        }
        
        # Theme keywords
        self.theme_keywords = {
            "love": ["love", "beloved", "heart", "romance", "relationship", "affection"],
            "self-discovery": ["self", "identity", "who am i", "finding myself", "true self"],
            "spirituality": ["soul", "divine", "god", "spiritual", "sacred", "holiness"],
            "wisdom": ["wisdom", "knowledge", "understand", "learn", "truth"],
            "purpose": ["purpose", "meaning", "destiny", "why", "reason", "path"],
            "friendship": ["friend", "companion", "together", "bond", "connection"],
            "unity": ["one", "unite", "whole", "together", "same", "union"]
        }
    
    def analyze(self, query: str) -> QueryIntent:
        """Analyze a user query"""
        query_lower = query.lower()
        
        # Detect intent
        intent_type = self._detect_intent(query_lower)
        
        # Detect emotions
        emotions = self._detect_emotions(query_lower)
        
        # Detect themes
        themes = self._detect_themes(query_lower, query)
        
        # Extract keywords
        keywords = self._extract_keywords(query_lower)
        
        # Detect depth/simplicity
        is_simple = self._is_simple_query(query_lower, query)
        
        return QueryIntent(
            intent_type=intent_type,
            emotions=emotions,
            themes=themes,
            keywords=keywords,
            detected_query=query,
            is_simple=is_simple
        )
    
    def _detect_intent(self, query_lower: str) -> str:
        """Detect query intent type"""
        # Check sharing patterns first (most specific)
        if any(pattern in query_lower for pattern in self.intent_patterns["sharing"]):
            return "sharing"
        
        # Then check seeking guidance
        if any(pattern in query_lower for pattern in self.intent_patterns["seeking_guidance"]):
            return "seeking_guidance"
        
        # Then questions
        if any(pattern in query_lower for pattern in self.intent_patterns["question"]):
            return "question"
        
        return "seeking_guidance"  # Default
    
    def _detect_emotions(self, query_lower: str) -> List[str]:
        """Detect emotions in query"""
        detected = []
        
        for emotion, keywords in self.emotion_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                detected.append(emotion)
        
        # Also check for explicit emotion mentions
        if "fear" in query_lower and "fear" not in detected:
            detected.append("fear")
        if "afraid" in query_lower and "fear" not in detected:
            detected.append("fear")
        
        return detected if detected else ["seeking"]  # Default emotion
    
    def _detect_themes(self, query_lower: str, original_query: str) -> List[str]:
        """Detect themes in query"""
        detected = []
        
        for theme, keywords in self.theme_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                detected.append(theme)
        
        # If no theme detected, try inference
        if not detected:
            # Default based on common patterns
            if "i" in query_lower or "my" in query_lower:
                detected.append("self-discovery")
            else:
                detected.append("wisdom")
        
        return detected
    
    def _extract_keywords(self, query_lower: str) -> List[str]:
        """Extract important keywords"""
        # Remove common stop words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "is", "am", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will", "would",
            "should", "could", "may", "might", "must", "can", "how", "what", "why",
            "where", "when", "who", "whom", "which", "that", "this", "these", "those",
            "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them",
            "my", "your", "his", "her", "its", "our", "their"
        }
        
        # Split into words and filter
        words = re.findall(r'\b\w+\b', query_lower)
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        return keywords[:10]  # Return top 10 keywords
    
    def _is_simple_query(self, query_lower: str, original_query: str) -> bool:
        """Detect if query is simple (greeting, introduction) vs deep (philosophical)"""
        simple_indicators = [
            "hi", "hello", "hey", "good morning", "good evening",
            "my name is", "i'm", "im ", "i am",
            "how are you", "how's it going", "what's up",
            "thanks", "thank you", "bye", "goodbye"
        ]
        
        # Check if it's a simple greeting/intro
        if any(indicator in query_lower for indicator in simple_indicators):
            return True
        
        # Check query length and structure
        words = query_lower.split()
        if len(words) <= 3 and "?" not in original_query:
            return True
        
        return False

# Global instance
_analyzer_instance = None

def get_query_analyzer() -> QueryAnalyzer:
    """Get global analyzer instance"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = QueryAnalyzer()
    return _analyzer_instance

