"""
Generate Rumi-style responses using retrieved quotes
"""

from typing import List, Dict, Any
from services.query_analyzer import QueryIntent
from services.rumi_config import get_config, RumiConfig

class RumiResponder:
    """Generate Rumi-style responses"""
    
    def __init__(self, config: RumiConfig = None):
        """Initialize responder with configuration"""
        self.config = config if config else get_config()
    
    RUMI_SYSTEM_PROMPT = """You are Jalaluddin Rumi, the 13th-century Persian mystic and poet.

Your responses are:
- Concise and profound (40-120 words)
- Poetic and metaphorical
- Thematically aligned with the quotes provided
- Compassionate yet direct
- Reflective of mystical wisdom
- Use natural, flowing language

Context Quotes:
{quotes}

User's Current State:
{emotion_context}

Respond as Rumi would, weaving these themes into your answer. Be authentic, poetic, and transformative."""
    
    def generate_prompt(self, query: str, quotes: List[Dict[str, Any]], intent: QueryIntent, conversation_history: List[str] = None, config: RumiConfig = None) -> str:
        """
        Generate conversational prompt for LLM
        
        Args:
            query: Original user query
            quotes: Retrieved relevant quotes
            intent: Analyzed query intent
            conversation_history: Previous messages for context
            
        Returns:
            Complete conversational prompt for LLM
        """
        # Format quotes as knowledge base
        quotes_text = self._format_quotes(quotes)
        
        # Get emotion context
        emotion_context = self._format_emotion_context(intent)
        
        # Build conversation context
        history_text = ""
        if conversation_history and len(conversation_history) > 0:
            history_text = "\nRecent conversation:\n" + "\n".join(conversation_history[-2:])
        
        # Create the prompt as a conversational system
        # Different prompts for simple vs deep queries
        if intent.is_simple:
            # SIMPLE QUERY: Just conversational, no deep philosophy
            history_part = ""
            if history_text:
                history_part = history_text + "\n"
            
            prompt = f"""You are Rumi, having a conversation.

{history_part}They say: "{query}"

Respond naturally and warmly. For simple greetings or introductions:
- If they say their name → Acknowledge warmly, like "Welcome, dear Clara" or "Ah, beautiful name, Clara"
- If they greet you → Greet back warmly, ask how you can help
- Keep it SHORT (20-50 words)
- Be human, warm, personal - NO deep philosophy for simple things
- Just continue the conversation naturally"""
        elif history_text:
            # DEEP QUERY WITH HISTORY: Use wisdom and context
            prompt = f"""You are Rumi in deep conversation with this seeker.

YOUR CONVERSATION SO FAR:
{history_text}

NOW THEY ASK: "{query}"

YOUR WISDOM TO WEAVE IN:
{quotes_text}

Respond as Rumi would:
- Use wisdom from teachings naturally
- Reference what they've shared
- Be profound but accessible (80-150 words)
- Speak to their specific question
- Use their name when relevant"""
        else:
            # DEEP QUERY: No history yet
            prompt = f"""You are Rumi speaking to a seeker.

They ask: "{query}"

YOUR WISDOM:
{quotes_text}

Respond deeply and profoundly as Rumi (80-150 words)."""
        
        return prompt
    
    def _format_quotes(self, quotes: List[Dict[str, Any]]) -> str:
        """Format quotes for prompt"""
        if not quotes:
            return "None available."
        
        formatted = []
        for i, quote in enumerate(quotes[:3], 1):  # Top 3 quotes
            quote_text = quote.get('quote', '')
            theme = quote.get('primary_theme', '')
            formatted.append(f"{i}. {quote_text}")
        
        return "\n".join(formatted)
    
    def _format_emotion_context(self, intent: QueryIntent) -> str:
        """Format emotion context for prompt"""
        emotions = intent.emotions
        
        if not emotions:
            return "seeking guidance"
        
        # Create natural language description
        if len(emotions) == 1:
            return emotions[0]
        
        # Join multiple emotions
        if "fear" in emotions:
            joined_emotions = " and ".join(emotions)
            return f"feeling {joined_emotions}"
        
        return ", ".join(emotions)
    
    def post_process_response(self, response: str) -> str:
        """Post-process LLM response for quality and conversational flow"""
        # Clean up common issues
        response = response.strip()
        
        # Remove any system prompt remnants
        markers = [
            "Your response:", "Begin your response:", "Response:",
            "You are Rumi", "The seeker asks", "Response:", "Your wisdom",
            "[Your wisdom]", "Your wisdom to draw upon"
        ]
        
        for marker in markers:
            if marker in response:
                parts = response.split(marker)
                if len(parts) > 1:
                    response = parts[-1].strip()
                    break
        
        # Remove any remaining prompt artifacts
        lines = response.split('\n')
        cleaned_lines = []
        for line in lines:
            skip_patterns = [
                'you are', 'rules:', 'seeker\'s', 'teaching:', 'answer as',
                '[your wisdom]', '[conversation context]', 'conversation so far:'
            ]
            if not any(skip in line.lower() for skip in skip_patterns):
                if line.strip() and line.strip() not in ['', '...']:
                    cleaned_lines.append(line.strip())
        
        response = '\n'.join(cleaned_lines).strip()
        
        # If response is still empty or just artifacts, give fallback
        if not response or response == '' or len(response) < 30:
            # Let it pass through even if short - might be a valid short answer
            pass
        
        # Count words and trim if too long, but preserve conversational flow
        words = response.split()
        # Allow longer responses (up to 180 words for conversational flow)
        if len(words) > 180:
            # Find a good stopping point at sentence end
            for i in range(150, min(180, len(words))):
                if i < len(words) and words[i][-1] in '.!?':
                    response = ' '.join(words[:i+1])
                    break
            else:
                # No sentence end found, cut at 150 words
                response = ' '.join(words[:150])
        
        # Remove excessive whitespace but keep single line breaks for paragraph structure
        response = ' '.join(response.split())
        
        return response

# Global instance
_responder_instance = None

def get_rumi_responder() -> RumiResponder:
    """Get global responder instance"""
    global _responder_instance
    if _responder_instance is None:
        _responder_instance = RumiResponder()
    return _responder_instance

