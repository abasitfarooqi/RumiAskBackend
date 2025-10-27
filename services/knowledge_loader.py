"""
Load and manage Rumi knowledge base
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from pydantic import BaseModel

class Quote(BaseModel):
    """Quote data model"""
    id: str
    core_pillar: str
    primary_theme: str
    quote: str
    micro_tags: List[str]
    emotion_tags: List[str]
    source_ref: str
    quote_type: str
    query_intent: List[str]
    user_questions: List[str]

class KnowledgeBase:
    """Manage Rumi knowledge base"""
    
    def __init__(self, kb_path: str = "data/rumi_knowledge_base.json"):
        self.kb_path = Path(kb_path)
        self.quotes: List[Dict[str, Any]] = []
        self.load()
    
    def load(self):
        """Load knowledge base from JSON"""
        if not self.kb_path.exists():
            raise FileNotFoundError(f"Knowledge base not found: {self.kb_path}")
        
        with open(self.kb_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.quotes = data.get('quotes', [])
        return len(self.quotes)
    
    def get_all_quotes(self) -> List[Dict[str, Any]]:
        """Get all quotes"""
        return self.quotes
    
    def get_quote_by_id(self, quote_id: str) -> Dict[str, Any]:
        """Get a specific quote by ID"""
        for quote in self.quotes:
            if quote['id'] == quote_id:
                return quote
        return None
    
    def get_quotes_by_theme(self, theme: str) -> List[Dict[str, Any]]:
        """Get quotes by primary theme"""
        return [q for q in self.quotes if theme.lower() in q.get('primary_theme', '').lower()]
    
    def get_quotes_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Get quotes containing a specific tag"""
        tag_lower = tag.lower()
        results = []
        for quote in self.quotes:
            # Check micro_tags
            if any(tag_lower in t.lower() for t in quote.get('micro_tags', [])):
                results.append(quote)
            # Check emotion_tags
            elif any(tag_lower in t.lower() for t in quote.get('emotion_tags', [])):
                results.append(quote)
        return results
    
    def get_themes(self) -> List[str]:
        """Get all unique themes"""
        return sorted(set([q.get('primary_theme', '') for q in self.quotes if q.get('primary_theme', '')]))
    
    def get_pillars(self) -> List[str]:
        """Get all unique pillars"""
        return sorted(set([q.get('core_pillar', '') for q in self.quotes if q.get('core_pillar', '')]))
    
    def count(self) -> int:
        """Get total quote count"""
        return len(self.quotes)

# Global instance
_kb_instance = None

def get_knowledge_base() -> KnowledgeBase:
    """Get global knowledge base instance"""
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = KnowledgeBase()
    return _kb_instance

