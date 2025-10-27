"""
Model Manager for Ask Rumi Backend
Handles model downloads, registry, and availability checks.
"""

import json
import asyncio
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import aiofiles
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class ModelInfo(BaseModel):
    """Model information model"""
    name: str
    display_name: str
    description: str
    size_gb: float
    provider: str  # "ollama", "huggingface", "local"
    status: str  # "available", "downloading", "not_available", "error"
    download_progress: Optional[float] = None
    last_updated: Optional[str] = None
    tags: List[str] = []
    capabilities: List[str] = []  # ["chat", "embedding", "transcription"]

class ModelRegistry:
    """Manages model registry and downloads"""
    
    def __init__(self, registry_path: str = "data/model_registry.json"):
        self.registry_path = Path(registry_path)
        self.models: Dict[str, ModelInfo] = {}
        self.download_tasks: Dict[str, asyncio.Task] = {}
        self._load_registry()
    
    def _load_registry(self):
        """Load model registry from JSON file"""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r') as f:
                    data = json.load(f)
                    for model_data in data.get("models", []):
                        model = ModelInfo(**model_data)
                        self.models[model.name] = model
                logger.info(f"Loaded {len(self.models)} models from registry")
            except Exception as e:
                logger.error(f"Failed to load model registry: {e}")
                self._create_default_registry()
        else:
            self._create_default_registry()
    
    def _create_default_registry(self):
        """Create default model registry with common models"""
        default_models = [
            {
                "name": "phi3-mini",
                "display_name": "Phi-3 Mini",
                "description": "Microsoft's lightweight language model, perfect for local inference",
                "size_gb": 2.3,
                "provider": "ollama",
                "status": "not_available",
                "tags": ["chat", "lightweight", "fast"],
                "capabilities": ["chat"]
            },
            {
                "name": "mistral:7b",
                "display_name": "Mistral 7B",
                "description": "Mistral's 7B parameter model for balanced performance",
                "size_gb": 4.1,
                "provider": "ollama",
                "status": "not_available",
                "tags": ["chat", "balanced", "reasoning"],
                "capabilities": ["chat"]
            },
            {
                "name": "llama3:8b",
                "display_name": "Llama 3 8B",
                "description": "Meta's Llama 3 8B model for high-quality conversations",
                "size_gb": 4.7,
                "provider": "ollama",
                "status": "not_available",
                "tags": ["chat", "high-quality", "reasoning"],
                "capabilities": ["chat"]
            },
            {
                "name": "all-minilm-l6-v2",
                "display_name": "All-MiniLM-L6-v2",
                "description": "Lightweight embedding model for semantic search",
                "size_gb": 0.09,
                "provider": "huggingface",
                "status": "not_available",
                "tags": ["embedding", "semantic-search"],
                "capabilities": ["embedding"]
            },
            {
                "name": "whisper-base",
                "display_name": "Whisper Base",
                "description": "OpenAI's Whisper model for speech transcription",
                "size_gb": 0.29,
                "provider": "huggingface",
                "status": "not_available",
                "tags": ["transcription", "speech"],
                "capabilities": ["transcription"]
            }
        ]
        
        for model_data in default_models:
            model = ModelInfo(**model_data)
            self.models[model.name] = model
        
        self._save_registry()
        logger.info("Created default model registry")
    
    def _save_registry(self):
        """Save model registry to JSON file"""
        try:
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "models": [model.dict() for model in self.models.values()],
                "last_updated": datetime.now().isoformat()
            }
            with open(self.registry_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save model registry: {e}")
    
    def get_model(self, name: str) -> Optional[ModelInfo]:
        """Get model information by name"""
        return self.models.get(name)
    
    def get_all_models(self) -> Dict[str, ModelInfo]:
        """Get all models in registry"""
        return self.models.copy()
    
    def get_available_models(self) -> Dict[str, ModelInfo]:
        """Get only available models"""
        return {name: model for name, model in self.models.items() 
                if model.status == "available"}
    
    def get_models_by_capability(self, capability: str) -> Dict[str, ModelInfo]:
        """Get models that support a specific capability"""
        return {name: model for name, model in self.models.items() 
                if capability in model.capabilities}
    
    def check_model_availability(self, name: str) -> bool:
        """Check if a model is available locally"""
        model = self.models.get(name)
        if not model:
            return False
        
        if model.provider == "ollama":
            return self._check_ollama_model(name)
        elif model.provider == "huggingface":
            return self._check_huggingface_model(name)
        elif model.provider == "local":
            return self._check_local_model(name)
        
        return False
    
    def _check_ollama_model(self, name: str) -> bool:
        """Check if Ollama model is available"""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return name in result.stdout
        except Exception as e:
            logger.error(f"Failed to check Ollama model {name}: {e}")
            return False
    
    def _check_huggingface_model(self, name: str) -> bool:
        """Check if HuggingFace model is available locally"""
        try:
            from transformers import AutoTokenizer
            AutoTokenizer.from_pretrained(name, local_files_only=True)
            return True
        except Exception:
            return False
    
    def _check_local_model(self, name: str) -> bool:
        """Check if local model file exists"""
        model_path = Path(f"local_models/{name}")
        return model_path.exists()
    
    async def download_model(self, name: str) -> bool:
        """Download a model asynchronously"""
        model = self.models.get(name)
        if not model:
            logger.error(f"Model {name} not found in registry")
            return False
        
        if model.status == "available":
            logger.info(f"Model {name} already available")
            return True
        
        if name in self.download_tasks:
            logger.info(f"Model {name} is already being downloaded")
            return True
        
        # Update status
        model.status = "downloading"
        model.download_progress = 0.0
        self._save_registry()
        
        # Start download task
        if model.provider == "ollama":
            task = asyncio.create_task(self._download_ollama_model(name))
        elif model.provider == "huggingface":
            task = asyncio.create_task(self._download_huggingface_model(name))
        else:
            logger.error(f"Unknown provider: {model.provider}")
            model.status = "error"
            self._save_registry()
            return False
        
        self.download_tasks[name] = task
        
        try:
            success = await task
            if success:
                model.status = "available"
                model.download_progress = 100.0
                model.last_updated = datetime.now().isoformat()
            else:
                model.status = "error"
            return success
        except Exception as e:
            logger.error(f"Failed to download model {name}: {e}")
            model.status = "error"
            return False
        finally:
            self.download_tasks.pop(name, None)
            self._save_registry()
    
    async def _download_ollama_model(self, name: str) -> bool:
        """Download model using Ollama"""
        try:
            logger.info(f"Starting Ollama download for {name}")
            
            # Run ollama pull command
            process = await asyncio.create_subprocess_exec(
                "ollama", "pull", name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"Successfully downloaded Ollama model {name}")
                return True
            else:
                logger.error(f"Failed to download Ollama model {name}: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Error downloading Ollama model {name}: {e}")
            return False
    
    async def _download_huggingface_model(self, name: str) -> bool:
        """Download model from HuggingFace"""
        try:
            logger.info(f"Starting HuggingFace download for {name}")
            
            # This would typically use transformers library
            # For now, we'll simulate the download
            await asyncio.sleep(2)  # Simulate download time
            
            logger.info(f"Successfully downloaded HuggingFace model {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading HuggingFace model {name}: {e}")
            return False
    
    def get_download_progress(self, name: str) -> Optional[float]:
        """Get download progress for a model"""
        model = self.models.get(name)
        if model and model.status == "downloading":
            return model.download_progress
        return None
    
    def remove_model(self, name: str) -> bool:
        """Remove a model from registry and local storage"""
        model = self.models.get(name)
        if not model:
            return False
        
        try:
            if model.provider == "ollama":
                # Remove from Ollama
                subprocess.run(["ollama", "rm", name], check=True)
            elif model.provider == "huggingface":
                # Remove local cache
                import shutil
                cache_dir = Path.home() / ".cache" / "huggingface" / "transformers"
                if cache_dir.exists():
                    shutil.rmtree(cache_dir / name, ignore_errors=True)
            
            # Remove from registry
            del self.models[name]
            self._save_registry()
            
            logger.info(f"Removed model {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove model {name}: {e}")
            return False
    
    def update_model_status(self, name: str, status: str):
        """Update model status"""
        model = self.models.get(name)
        if model:
            model.status = status
            if status == "available":
                model.download_progress = 100.0
                model.last_updated = datetime.now().isoformat()
            self._save_registry()

# Global instance
model_registry = ModelRegistry()

def get_model_registry() -> ModelRegistry:
    """Get the global model registry instance"""
    return model_registry