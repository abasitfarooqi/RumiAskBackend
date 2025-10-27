"""
Configuration for Rumi Conversational System
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class RumiConfig:
    """Configuration for Rumi conversational responses"""
    
    # Response length settings
    min_words: int = 60
    max_words: int = 150
    simple_exchange_max: int = 200  # For simple statements
    deep_question_max: int = 250  # For philosophical questions
    
    # Conversational settings
    use_name_in_responses: bool = True
    acknowledge_previous_topics: bool = True
    vary_openings: bool = True
    
    # LLM settings
    temperature: float = 0.95
    max_tokens: int = 550
    
    # Quote usage
    quotes_per_response: int = 3
    emphasize_wisdom: bool = True
    
    # Style settings
    poetic_intensity: str = "balanced"  # light, balanced, intense
    metaphorical_threshold: str = "moderate"  # low, moderate, high
    
    # Conversational behavior
    always_greet_first_message: bool = True
    reference_previous_messages: bool = True
    ask_follow_up_questions: bool = True
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "min_words": self.min_words,
            "max_words": self.max_words,
            "simple_exchange_max": self.simple_exchange_max,
            "deep_question_max": self.deep_question_max,
            "use_name_in_responses": self.use_name_in_responses,
            "acknowledge_previous_topics": self.acknowledge_previous_topics,
            "vary_openings": self.vary_openings,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "quotes_per_response": self.quotes_per_response,
            "emphasize_wisdom": self.emphasize_wisdom,
            "poetic_intensity": self.poetic_intensity,
            "metaphorical_threshold": self.metaphorical_threshold,
            "always_greet_first_message": self.always_greet_first_message,
            "reference_previous_messages": self.reference_previous_messages,
            "ask_follow_up_questions": self.ask_follow_up_questions,
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create from dictionary"""
        return cls(**data)
    
    def update(self, **kwargs):
        """Update configuration"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

# Global default config
default_config = RumiConfig()

# Preset configurations
CONFIG_PRESETS = {
    "conversational": RumiConfig(
        min_words=60,
        max_words=120,
        temperature=0.85,
        use_name_in_responses=True,
        ask_follow_up_questions=True,
        poetic_intensity="light"
    ),
    "philosophical": RumiConfig(
        min_words=100,
        max_words=150,
        temperature=0.8,
        emphasize_wisdom=True,
        poetic_intensity="intense",
        metaphorical_threshold="high"
    ),
    "brief": RumiConfig(
        min_words=40,
        max_words=80,
        temperature=0.9,
        quotes_per_response=2,
        poetic_intensity="light"
    ),
    "deep": RumiConfig(
        min_words=120,
        max_words=200,
        temperature=0.75,
        quotes_per_response=4,
        emphasize_wisdom=True,
        poetic_intensity="intense",
        metaphorical_threshold="high"
    )
}

def get_config(preset: str = None) -> RumiConfig:
    """Get configuration, optionally from a preset"""
    if preset and preset in CONFIG_PRESETS:
        return CONFIG_PRESETS[preset]
    return default_config

