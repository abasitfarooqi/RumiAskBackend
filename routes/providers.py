"""
Providers API routes for Ask Rumi Backend
Handles model providers and external service integration.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import logging
from datetime import datetime

from core.model_manager import get_model_registry

logger = logging.getLogger(__name__)

router = APIRouter()

class ProviderInfo(BaseModel):
    """Provider information model"""
    name: str
    display_name: str
    description: str
    type: str  # "local", "online", "hybrid"
    status: str  # "available", "unavailable", "error"
    models_count: int
    capabilities: List[str]
    config: Dict[str, Any]

class ProviderConfig(BaseModel):
    """Provider configuration model"""
    name: str
    enabled: bool
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_requests_per_minute: Optional[int] = None
    timeout: Optional[int] = None
    fallback_enabled: bool = True

# Load providers configuration
def load_providers_config() -> Dict[str, ProviderConfig]:
    """Load providers configuration from file"""
    try:
        with open("data/providers.config.json", "r") as f:
            data = json.load(f)
            return {
                name: ProviderConfig(**config) 
                for name, config in data.get("providers", {}).items()
            }
    except FileNotFoundError:
        # Return default configuration
        return {
            "ollama": ProviderConfig(
                name="ollama",
                enabled=True,
                base_url="http://localhost:11434",
                timeout=300,
                fallback_enabled=True
            ),
            "openai": ProviderConfig(
                name="openai",
                enabled=False,
                timeout=30,
                max_requests_per_minute=60,
                fallback_enabled=True
            ),
            "huggingface": ProviderConfig(
                name="huggingface",
                enabled=True,
                timeout=60,
                fallback_enabled=True
            )
        }
    except Exception as e:
        logger.error(f"Error loading providers config: {e}")
        return {}

def save_providers_config(config: Dict[str, ProviderConfig]):
    """Save providers configuration to file"""
    try:
        data = {
            "providers": {
                name: config.dict() 
                for name, config in config.items()
            },
            "last_updated": datetime.now().isoformat()
        }
        with open("data/providers.config.json", "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving providers config: {e}")

@router.get("/")
async def list_providers():
    """List all available providers"""
    try:
        registry = get_model_registry()
        providers_config = load_providers_config()
        
        providers = []
        
        # Ollama provider
        ollama_models = [m for m in registry.get_all_models().values() if m.provider == "ollama"]
        ollama_config = providers_config.get("ollama", ProviderConfig(name="ollama", enabled=True))
        
        providers.append(ProviderInfo(
            name="ollama",
            display_name="Ollama",
            description="Local model inference using Ollama",
            type="local",
            status="available" if ollama_config.enabled else "unavailable",
            models_count=len(ollama_models),
            capabilities=["chat", "streaming", "local"],
            config=ollama_config.dict()
        ))
        
        # HuggingFace provider
        hf_models = [m for m in registry.get_all_models().values() if m.provider == "huggingface"]
        hf_config = providers_config.get("huggingface", ProviderConfig(name="huggingface", enabled=True))
        
        providers.append(ProviderInfo(
            name="huggingface",
            display_name="HuggingFace",
            description="Open-source models from HuggingFace Hub",
            type="hybrid",
            status="available" if hf_config.enabled else "unavailable",
            models_count=len(hf_models),
            capabilities=["chat", "embedding", "transcription"],
            config=hf_config.dict()
        ))
        
        # OpenAI provider (if configured)
        openai_config = providers_config.get("openai")
        if openai_config and openai_config.enabled:
            providers.append(ProviderInfo(
                name="openai",
                display_name="OpenAI",
                description="Premium AI models from OpenAI",
                type="online",
                status="available" if openai_config.api_key else "unavailable",
                models_count=0,  # Would be dynamic in real implementation
                capabilities=["chat", "embedding", "transcription"],
                config=openai_config.dict()
            ))
        
        return {
            "providers": [provider.dict() for provider in providers],
            "total": len(providers)
        }
    except Exception as e:
        logger.error(f"Error listing providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{provider_name}")
async def get_provider_info(provider_name: str):
    """Get detailed information about a specific provider"""
    try:
        registry = get_model_registry()
        providers_config = load_providers_config()
        
        if provider_name == "ollama":
            models = [m for m in registry.get_all_models().values() if m.provider == "ollama"]
            config = providers_config.get("ollama", ProviderConfig(name="ollama", enabled=True))
            
            return ProviderInfo(
                name="ollama",
                display_name="Ollama",
                description="Local model inference using Ollama",
                type="local",
                status="available" if config.enabled else "unavailable",
                models_count=len(models),
                capabilities=["chat", "streaming", "local"],
                config=config.dict()
            )
        
        elif provider_name == "huggingface":
            models = [m for m in registry.get_all_models().values() if m.provider == "huggingface"]
            config = providers_config.get("huggingface", ProviderConfig(name="huggingface", enabled=True))
            
            return ProviderInfo(
                name="huggingface",
                display_name="HuggingFace",
                description="Open-source models from HuggingFace Hub",
                type="hybrid",
                status="available" if config.enabled else "unavailable",
                models_count=len(models),
                capabilities=["chat", "embedding", "transcription"],
                config=config.dict()
            )
        
        elif provider_name == "openai":
            config = providers_config.get("openai")
            if not config:
                raise HTTPException(status_code=404, detail="OpenAI provider not configured")
            
            return ProviderInfo(
                name="openai",
                display_name="OpenAI",
                description="Premium AI models from OpenAI",
                type="online",
                status="available" if config.api_key else "unavailable",
                models_count=0,
                capabilities=["chat", "embedding", "transcription"],
                config=config.dict()
            )
        
        else:
            raise HTTPException(status_code=404, detail=f"Provider {provider_name} not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting provider info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{provider_name}/models")
async def get_provider_models(provider_name: str):
    """Get models available from a specific provider"""
    try:
        registry = get_model_registry()
        all_models = registry.get_all_models()
        
        provider_models = [
            model for model in all_models.values() 
            if model.provider == provider_name
        ]
        
        return {
            "provider": provider_name,
            "models": [
                {
                    "name": model.name,
                    "display_name": model.display_name,
                    "description": model.description,
                    "size_gb": model.size_gb,
                    "status": model.status,
                    "tags": model.tags,
                    "capabilities": model.capabilities
                }
                for model in provider_models
            ],
            "total": len(provider_models)
        }
    except Exception as e:
        logger.error(f"Error getting provider models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{provider_name}/configure")
async def configure_provider(provider_name: str, config: ProviderConfig):
    """Configure a provider"""
    try:
        providers_config = load_providers_config()
        providers_config[provider_name] = config
        save_providers_config(providers_config)
        
        return {
            "message": f"Provider {provider_name} configured successfully",
            "config": config.dict()
        }
    except Exception as e:
        logger.error(f"Error configuring provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{provider_name}/enable")
async def enable_provider(provider_name: str):
    """Enable a provider"""
    try:
        providers_config = load_providers_config()
        
        if provider_name not in providers_config:
            raise HTTPException(status_code=404, detail=f"Provider {provider_name} not found")
        
        providers_config[provider_name].enabled = True
        save_providers_config(providers_config)
        
        return {"message": f"Provider {provider_name} enabled"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{provider_name}/disable")
async def disable_provider(provider_name: str):
    """Disable a provider"""
    try:
        providers_config = load_providers_config()
        
        if provider_name not in providers_config:
            raise HTTPException(status_code=404, detail=f"Provider {provider_name} not found")
        
        providers_config[provider_name].enabled = False
        save_providers_config(providers_config)
        
        return {"message": f"Provider {provider_name} disabled"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{provider_name}/test")
async def test_provider(provider_name: str):
    """Test if a provider is working correctly"""
    try:
        providers_config = load_providers_config()
        config = providers_config.get(provider_name)
        
        if not config:
            raise HTTPException(status_code=404, detail=f"Provider {provider_name} not found")
        
        if not config.enabled:
            return {
                "provider": provider_name,
                "test_passed": False,
                "message": "Provider is disabled"
            }
        
        # Test based on provider type
        if provider_name == "ollama":
            # Test Ollama connection
            import subprocess
            try:
                result = subprocess.run(
                    ["ollama", "list"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                success = result.returncode == 0
                message = "Ollama is working correctly" if success else "Ollama connection failed"
            except Exception as e:
                success = False
                message = f"Ollama test failed: {e}"
        
        elif provider_name == "huggingface":
            # Test HuggingFace connection
            try:
                import requests
                response = requests.get("https://huggingface.co/api/models", timeout=10)
                success = response.status_code == 200
                message = "HuggingFace API is accessible" if success else "HuggingFace API not accessible"
            except Exception as e:
                success = False
                message = f"HuggingFace test failed: {e}"
        
        elif provider_name == "openai":
            # Test OpenAI connection
            try:
                import openai
                # This would require actual API key testing
                success = bool(config.api_key)
                message = "OpenAI API key configured" if success else "OpenAI API key not configured"
            except Exception as e:
                success = False
                message = f"OpenAI test failed: {e}"
        
        else:
            success = False
            message = f"Unknown provider: {provider_name}"
        
        return {
            "provider": provider_name,
            "test_passed": success,
            "message": message
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Provider test error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def providers_health():
    """Health check for providers service"""
    try:
        providers_config = load_providers_config()
        enabled_providers = [name for name, config in providers_config.items() if config.enabled]
        
        return {
            "status": "healthy",
            "total_providers": len(providers_config),
            "enabled_providers": len(enabled_providers),
            "providers": list(providers_config.keys())
        }
    except Exception as e:
        logger.error(f"Providers health check error: {e}")
        return {"status": "unhealthy", "error": str(e)}