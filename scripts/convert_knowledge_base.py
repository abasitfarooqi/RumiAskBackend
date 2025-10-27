"""
Convert Rumi knowledge base from Markdown to structured JSON.
Handles both Knowledge Data.md and Knowledge DATAset2.md files.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

class RumiKnowledgeConverter:
    """Convert Markdown knowledge base to structured JSON"""
    
    def __init__(self):
        self.quotes = []
        self.current_pillar = ""
        self.current_theme = ""
        
    def parse_markdown_file(self, file_path: str):
        """Parse a Markdown knowledge base file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Detect pillar
            if line.startswith('RUMi - Pillar') or line.startswith('RUMi-Pillar'):
                self._extract_pillar(line)
                i += 1
                continue
            
            # Detect primary theme
            if 'Primary Theme' in line:
                self._extract_theme(line)
                i += 1
                continue
            
            # Detect table headers
            if line.startswith('| [LLM_ID]') or line.startswith('|| [LLM_ID]'):
                # Skip table header
                i += 2  # Skip header and separator
                continue
            
            # Parse quote entries (table rows starting with |)
            if line.startswith('| '):
                self._parse_quote_line(line)
            
            i += 1
    
    def _extract_pillar(self, line: str):
        """Extract pillar name from line"""
        match = re.search(r'Pillar\s+([IVX]+):\s*(.+)', line)
        if match:
            self.current_pillar = f"{match.group(1)}. {match.group(2).strip()}"
    
    def _extract_theme(self, line: str):
        """Extract primary theme from line"""
        match = re.search(r'Primary Theme\s+\d+:?\s*(.+)', line)
        if match:
            self.current_theme = match.group(1).strip()
    
    def _parse_quote_line(self, line: str):
        """Parse a quote entry from table row"""
        # Split by | and clean up
        parts = [part.strip() for part in line.split('|') if part.strip()]
        
        if len(parts) < 4:
            return  # Not a valid quote line
        
        # Skip header rows and separators
        if parts[0] in ['[LLM_ID]', '---'] or not parts[0]:
            return
        
        # Check if first part is an ID (format: DLV001, HLV002, etc.)
        if not re.match(r'^[A-Z]+\d+$', parts[0]):
            return
        
        quote_id = parts[0]
        quote_text = parts[1].strip('"')
        tags_str = parts[2]
        source = parts[3] if len(parts) > 3 else ""
        
        # Parse tags (format: ["#Tag1", "#Tag2", "#Tag3"])
        # Extract tags from array format
        tag_matches = re.findall(r'#([^\s,\]]+)', tags_str)
        micro_tags = tag_matches if tag_matches else []
        
        # Generate emotion tags based on quote content
        emotion_tags = self._generate_emotion_tags(quote_text, micro_tags)
        
        # Generate query intents
        query_intents = self._generate_query_intents(quote_text, micro_tags, self.current_theme)
        
        quote_data = {
            "id": quote_id,
            "core_pillar": self.current_pillar,
            "primary_theme": self.current_theme,
            "quote": quote_text,
            "micro_tags": micro_tags,
            "emotion_tags": emotion_tags,
            "source_ref": source,
            "quote_type": "Short-Quote",
            "query_intent": query_intents,
            "user_questions": query_intents  # Can expand later
        }
        
        self.quotes.append(quote_data)
    
    def _generate_emotion_tags(self, quote: str, micro_tags: List[str]) -> List[str]:
        """Generate emotion tags based on quote content and micro tags"""
        emotions = []
        quote_lower = quote.lower()
        
        # Emotion mappings
        emotion_keywords = {
            "longing": ["longing", "ache", "yearn", "miss", "homesick"],
            "surrender": ["surrender", "give up", "surrender", "yield", "submit"],
            "joy": ["joy", "laugh", "happiness", "ecstasy", "delight"],
            "love": ["love", "beloved", "heart", "adore", "cherish"],
            "wisdom": ["know", "understand", "wisdom", "realize", "learn"],
            "sadness": ["weep", "sorrow", "grief", "tears", "pain"],
            "fear": ["fear", "afraid", "anxiety", "worried", "scared"],
            "courage": ["courage", "brave", "dare", "bold", "strength"],
            "peace": ["peace", "calm", "tranquil", "serene", "stillness"],
            "realization": ["realize", "understand", "recognize", "awaken", "discover"],
            "seeking": ["search", "seek", "find", "look", "hunt"],
            "transformation": ["transform", "change", "become", "evolve", "grow"],
            "unity": ["union", "one", "whole", "unite", "merge"],
            "freedom": ["free", "liberate", "release", "escape", "freedom"],
            "devotion": ["devotion", "commit", "dedicate", "sacrifice", "serve"]
        }
        
        for emotion, keywords in emotion_keywords.items():
            if any(keyword in quote_lower for keyword in keywords):
                if emotion not in emotions:
                    emotions.append(emotion)
        
        # Add from micro tags
        for tag in micro_tags:
            tag_lower = tag.lower()
            if tag_lower in ["yearning", "longing", "seeking", "hungry"]:
                if "longing" not in emotions:
                    emotions.append("longing")
            if tag_lower in ["sacrifice", "devotion", "surrender"]:
                if "surrender" not in emotions:
                    emotions.append("surrender")
        
        return emotions if emotions else ["contemplation"]
    
    def _generate_query_intents(self, quote: str, micro_tags: List[str], theme: str) -> List[str]:
        """Generate potential query intents that this quote answers"""
        intents = []
        
        # Base intents from theme
        theme_intents = {
            "Divine Love": [
                "How do I find God?",
                "Where is the Divine?",
                "How do I love the Beloved?",
                "I'm searching for meaning",
                "How do I surrender?"
            ],
            "Human Love": [
                "How do I love someone?",
                "Should I be vulnerable?",
                "What is true love?",
                "How do I commit?",
                "I'm afraid to love"
            ],
            "Self-Discovery": [
                "Who am I?",
                "How do I find myself?",
                "What is my true nature?",
                "I feel lost",
                "How do I discover my path?"
            ],
            "Wisdom": [
                "How do I become wise?",
                "What is wisdom?",
                "How do I understand life?",
                "I need guidance",
                "How do I gain knowledge?"
            ],
            "Purpose": [
                "What's my purpose?",
                "Why am I here?",
                "What should I do with my life?",
                "I feel without direction",
                "What is my destiny?"
            ]
        }
        
        # Add intents based on tags
        tag_intents = {
            "Longing": ["I feel empty inside", "Why do I long?", "What is this ache?"],
            "Fear": ["I'm afraid", "How do I overcome fear?", "How do I take risks?"],
            "Surrender": ["How do I let go?", "What does surrender mean?"],
            "Searching": ["Where do I look?", "I'm searching for answers"],
            "Separation": ["Why do I feel alone?", "How do I feel whole?"]
        }
        
        # Get theme-specific intents
        for key, values in theme_intents.items():
            if key in theme:
                intents.extend(values[:3])  # Limit to 3
        
        # Add tag-specific intents
        for tag in micro_tags:
            for key, values in tag_intents.items():
                if key in tag:
                    intents.extend(values[:2])  # Limit to 2
        
        # Generic fallback
        if not intents:
            intents = [f"What does Rumi say about {theme}?"]
        
        return list(set(intents))[:5]  # Return unique, max 5
    
    def save_to_json(self, output_path: str):
        """Save quotes to JSON file"""
        output_data = {
            "version": "1.0",
            "metadata": {
                "total_quotes": len(self.quotes),
                "pillars": list(set([q["core_pillar"] for q in self.quotes])),
                "themes": list(set([q["primary_theme"] for q in self.quotes])),
                "last_updated": datetime.now().isoformat()
            },
            "quotes": self.quotes
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Converted {len(self.quotes)} quotes to {output_path}")

def main():
    """Main conversion process"""
    print("🔄 Starting knowledge base conversion...")
    
    # Paths
    kb1_path = Path("knowledge_base/Knowledge Data.md")
    kb2_path = Path("knowledge_base/Knowledge DATAset2.md")
    output_path = Path("data/rumi_knowledge_base.json")
    
    # Check if files exist
    if not kb1_path.exists():
        print(f"❌ Error: {kb1_path} not found")
        return
    
    if not kb2_path.exists():
        print(f"❌ Error: {kb2_path} not found")
        return
    
    # Convert
    converter = RumiKnowledgeConverter()
    
    print(f"📖 Parsing {kb1_path.name}...")
    converter.parse_markdown_file(str(kb1_path))
    
    print(f"📖 Parsing {kb2_path.name}...")
    converter.parse_markdown_file(str(kb2_path))
    
    print(f"💾 Saving to {output_path.name}...")
    converter.save_to_json(str(output_path))
    
    print(f"\n✅ Conversion complete!")
    print(f"   Total quotes: {len(converter.quotes)}")
    print(f"   Output: {output_path}")

if __name__ == "__main__":
    main()

