"""
Generate Rumi-style responses using retrieved quotes
"""

from typing import List, Dict, Any
from services.query_analyzer import QueryIntent
from services.rumi_config import get_config, RumiConfig
from services.behavior_config import get_behavior_config

class RumiResponder:
    """Generate Rumi-style responses"""
    
    def __init__(self, config: RumiConfig = None):
        """Initialize responder with configuration"""
        self.config = config if config else get_config()
        self.behavior_config = get_behavior_config()
    
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
    
    def generate_casual_prompt(self, query: str, conversation_history: List[str] = None) -> str:
        """Generate prompt for casual chat (no quotes, just friendly)"""
        history = ""
        if conversation_history:
            history = "\nPrevious messages:\n" + "\n".join(conversation_history[-2:])
        
        # Load from config
        template = self.behavior_config.get('prompt_templates.casual', {})
        role = template.get('role', 'friendly, approachable person')
        instructions = template.get('instructions', 'Respond naturally. Vary your responses. Be warm, engaging, and conversational (5-6 sentences).')
        
        return f"""You are {role}, engaged in a warm, natural conversation.
{history}

User just said: "{query}"

RESPOND NOW with 4-6 complete sentences:
- Acknowledge what they said warmly
- Share something about yourself or your perspective
- Ask them a thoughtful follow-up question
- Show genuine interest in their response
- Make it natural, engaging, and conversational

Target: 80-180 words. Be authentic and engaging."""
    
    def generate_empathetic_prompt(self, query: str, quotes: List[Dict[str, Any]] = None, conversation_history: List[str] = None) -> str:
        """Generate empathetic support prompt for emotional distress"""
        history = ""
        if conversation_history:
            # Only get last message to avoid confusion
            if len(conversation_history) >= 1:
                history = f"\nPrevious context: {conversation_history[-1]}\n"
        
        # Load from config
        template = self.behavior_config.get('prompt_templates.empathetic', {})
        role = template.get('role', 'caring, wise companion speaking to someone in distress')
        structure = template.get('structure_instructions', '')
        word_limit = template.get('word_limit', [140, 200])
        
        # Format wisdom for natural integration
        if quotes:
            quotes_text = self._format_quotes(quotes[:2])
            wisdom_instruction = f"""They said: "{query}"

Respond with genuine empathy:
1. First acknowledge their emotion warmly (2-3 sentences)
2. Then naturally weave in this wisdom to offer perspective:
{quotes_text}

Make it complete and rich (180-280 words total)."""
        else:
            wisdom_instruction = f"""They said: "{query}"

1. Acknowledge their emotion with gentle understanding (2-3 sentences)
2. Validate their experience
3. Offer thoughtful perspective

Respond with genuine empathy and understanding. (100-180 words)"""
        
        return f"""You are {role}.
{history}
CURRENT message you need to respond to:
{wisdom_instruction}"""
    
    def generate_wisdom_prompt(self, query: str, quotes: List[Dict[str, Any]], intent: QueryIntent, conversation_history: List[str] = None) -> str:
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
        
        # Build conversation context - LIMIT to avoid confusion
        history_text = ""
        if conversation_history and len(conversation_history) > 0:
            # Only get LAST exchange to avoid confusing context
            recent = conversation_history[-1:] if len(conversation_history) >= 1 else []
            if recent:
                history_text = f"Context from previous message:\n{recent[0]}"
        
        # Load from config
        template = self.behavior_config.get('prompt_templates.wisdom', {})
        role = template.get('role', 'Rumi')
        structure = template.get('structure_instructions', '')
        word_limit = template.get('word_limit', [100, 180])
        quote_source = template.get('quote_source', 'rumi_knowledge_base.json')
        
        # Get guidelines
        guidelines = self.behavior_config.get('response_guidelines', {})
        emphasize = guidelines.get('emphasize_current_question', True)
        ignore_old = guidelines.get('ignore_old_questions', True)
        
        # Prompt that ALWAYS uses quotes from knowledge base - NATURAL RUMI
        if history_text:
            prompt = f"""You are Rumi. Someone asks: "{query}"

Your teachings to guide you:
{quotes_text}

Respond as Rumi would. First engage with them conversationally (2-3 sentences), then naturally weave in your teachings from above. Make it complete and rich (150-250 words)."""
        else:
            prompt = f"""You are Rumi. Someone asks: "{query}"

Your teachings to guide you:
{quotes_text}

Respond as Rumi would. First engage with them conversationally (2-3 sentences), then naturally weave in your teachings from above. Make it complete and rich (150-250 words)."""
        
        return prompt
    
    def _format_quotes(self, quotes: List[Dict[str, Any]]) -> str:
        """Format quotes for prompt - uses config for formatting"""
        if not quotes:
            return "No specific wisdom for this, but respond as Rumi would."
        
        # Load formatting config
        formatting = self.behavior_config.get('quote_formatting', {})
        header = formatting.get('header', 'YOUR TEACHINGS (use these directly):')
        max_display = formatting.get('max_display', 3)
        show_ids = formatting.get('show_ids', True)
        show_sources = formatting.get('show_sources', True)
        
        formatted = []
        formatted.append(header)
        for i, quote in enumerate(quotes[:max_display], 1):
            quote_text = quote.get('quote', '')
            quote_id = quote.get('id', '')
            source = quote.get('source_ref', '')
            
            if show_ids and show_sources:
                formatted.append(f"{i}. [{quote_id}] {quote_text}\n   Source: {source}")
            elif show_ids:
                formatted.append(f"{i}. [{quote_id}] {quote_text}")
            else:
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
        # Load post-processing config
        post_config = self.behavior_config.get('post_processing', {})
        markers = post_config.get('markers_to_remove', [])
        skip_patterns = post_config.get('skip_patterns', [])
        max_words = post_config.get('max_word_limit', 150)
        min_words = post_config.get('min_word_limit', 30)
        trim_to_sentence = post_config.get('trim_to_sentence', True)
        
        # Clean up common issues
        response = response.strip()
        
        # Remove any system prompt remnants
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
            if not any(skip in line.lower() for skip in skip_patterns):
                if line.strip() and line.strip() not in ['', '...']:
                    cleaned_lines.append(line.strip())
        
        response = '\n'.join(cleaned_lines).strip()
        
        # If response is still empty or just artifacts, give fallback
        if not response or response == '' or len(response) < min_words:
            pass
        
        # Count words and trim if too long
        words = response.split()
        if len(words) > max_words:
            if trim_to_sentence:
                # Find a good stopping point at sentence end
                for i in range(max_words - 30, min(max_words, len(words))):
                    if i < len(words) and words[i][-1] in '.!?':
                        response = ' '.join(words[:i+1])
                        break
                else:
                    # No sentence end found, cut at max_words
                    response = ' '.join(words[:max_words])
            else:
                response = ' '.join(words[:max_words])
        
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

