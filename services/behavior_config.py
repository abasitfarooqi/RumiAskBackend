"""
Manage LLM Behavior Configuration
Loads and saves settings from JSON
"""

import json
from typing import Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class BehaviorConfig:
    """Manage LLM behavior configuration from JSON"""
    
    def __init__(self, config_path: str = "data/llm_behavior_config.json"):
        self.config_path = Path(config_path)
        self.config = self.load()
    
    def load(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"Config file not found at {self.config_path}, using defaults")
                return self.default_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self.default_config()
    
    def save(self) -> bool:
        """Save current configuration to JSON file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def get(self, key: str, default=None):
        """Get a configuration value"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def update(self, updates: Dict[str, Any]) -> bool:
        """Update configuration values with deep merge support"""
        def deep_merge(base: dict, update: dict) -> dict:
            """Deep merge two dictionaries"""
            result = base.copy()
            for key, value in update.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result
        
        self.config = deep_merge(self.config, updates)
        return self.save()
    
    def default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            "conversation_history_depth": 2,
            "max_tokens_wisdom": 200,
            "max_tokens_empathetic": 220,
            "max_tokens_casual": 80,
            "temperature": 0.8,
            "max_quotes_retrieved": 3,
            "max_quotes_for_empathetic": 2,
            "response_types": {
                "casual": {
                    "max_tokens": 80,
                    "temperature": 0.8,
                    "enable_quotes": False
                },
                "empathetic": {
                    "max_tokens": 220,
                    "temperature": 0.8,
                    "enable_quotes": True,
                    "max_quotes": 2
                },
                "wisdom": {
                    "max_tokens": 200,
                    "temperature": 0.8,
                    "enable_quotes": True,
                    "max_quotes": 3
                }
            },
            "prompt_guidelines": {
                "word_limit_wisdom": [100, 180],
                "word_limit_empathetic": [140, 200],
                "word_limit_casual": [20, 80]
            }
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Return full config as dictionary"""
        return self.config.copy()

# Global instance
_behavior_config = None

def get_behavior_config() -> BehaviorConfig:
    """Get global behavior config instance"""
    global _behavior_config
    if _behavior_config is None:
        _behavior_config = BehaviorConfig()
    return _behavior_config

