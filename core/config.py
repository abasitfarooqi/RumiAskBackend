"""
Core configuration and GPU management for Ask Rumi Backend
Handles device detection, configuration, and GPU switching.
"""

import os
import torch
import json
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeviceConfig(BaseModel):
    """Device configuration model"""
    device: str
    device_name: str
    is_available: bool
    memory_info: Optional[Dict[str, Any]] = None

class AppConfig(BaseModel):
    """Main application configuration"""
    app_name: str = "Ask Rumi Backend"
    version: str = "1.0.0"
    debug: bool = False
    max_concurrent_requests: int = 10
    model_timeout: int = 300  # 5 minutes
    ollama_base_url: str = "http://localhost:11434"
    data_dir: str = "data"
    models_dir: str = "models"
    
    # GPU settings
    prefer_gpu: bool = True
    fallback_to_cpu: bool = True
    max_gpu_memory: Optional[float] = None  # GB

class GPUManager:
    """Manages GPU detection and device switching"""
    
    def __init__(self):
        self.current_device = self._detect_best_device()
        self.device_info = self._get_device_info()
        
    def _detect_best_device(self) -> str:
        """Detect the best available device"""
        if torch.backends.mps.is_available():
            logger.info("Apple Metal Performance Shaders (MPS) detected")
            return "mps"
        elif torch.cuda.is_available():
            logger.info(f"CUDA detected with {torch.cuda.device_count()} device(s)")
            return "cuda"
        else:
            logger.info("Using CPU")
            return "cpu"
    
    def _get_device_info(self) -> Dict[str, Any]:
        """Get detailed device information"""
        device_info = {
            "mps": {
                "available": torch.backends.mps.is_available(),
                "device": "mps" if torch.backends.mps.is_available() else None
            },
            "cuda": {
                "available": torch.cuda.is_available(),
                "device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
                "current_device": torch.cuda.current_device() if torch.cuda.is_available() else None,
                "device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
            },
            "cpu": {
                "available": True,
                "device": "cpu"
            }
        }
        
        # Add memory info for current device
        if self.current_device == "cuda" and torch.cuda.is_available():
            device_info["cuda"]["memory_allocated"] = torch.cuda.memory_allocated(0)
            device_info["cuda"]["memory_reserved"] = torch.cuda.memory_reserved(0)
            device_info["cuda"]["max_memory"] = torch.cuda.max_memory_allocated(0)
        
        return device_info
    
    def get_current_device(self) -> str:
        """Get current device"""
        return self.current_device
    
    def set_device(self, device: str) -> bool:
        """Set device (cpu, mps, cuda)"""
        if device == "cpu":
            self.current_device = "cpu"
            logger.info("Switched to CPU")
            return True
        elif device == "mps" and torch.backends.mps.is_available():
            self.current_device = "mps"
            logger.info("Switched to Apple Metal (MPS)")
            return True
        elif device == "cuda" and torch.cuda.is_available():
            self.current_device = "cuda"
            logger.info("Switched to CUDA")
            return True
        else:
            logger.warning(f"Device {device} not available")
            return False
    
    def get_device_config(self) -> DeviceConfig:
        """Get current device configuration"""
        device_info = self.device_info.get(self.current_device, {})
        
        return DeviceConfig(
            device=self.current_device,
            device_name=device_info.get("device_name", self.current_device.upper()),
            is_available=device_info.get("available", True),
            memory_info=device_info
        )
    
    def get_all_devices(self) -> Dict[str, DeviceConfig]:
        """Get configuration for all available devices"""
        devices = {}
        for device_name, info in self.device_info.items():
            devices[device_name] = DeviceConfig(
                device=device_name,
                device_name=info.get("device_name", device_name.upper()),
                is_available=info.get("available", True),
                memory_info=info
            )
        return devices

# Global instances
config = AppConfig()
gpu_manager = GPUManager()

def get_config() -> AppConfig:
    """Get application configuration"""
    return config

def get_gpu_manager() -> GPUManager:
    """Get GPU manager instance"""
    return gpu_manager

def load_config_from_file(config_path: str = "config.json") -> AppConfig:
    """Load configuration from JSON file"""
    config_file = Path(config_path)
    if config_file.exists():
        with open(config_file, 'r') as f:
            config_data = json.load(f)
            return AppConfig(**config_data)
    return config

def save_config_to_file(config: AppConfig, config_path: str = "config.json") -> None:
    """Save configuration to JSON file"""
    config_file = Path(config_path)
    with open(config_file, 'w') as f:
        json.dump(config.dict(), f, indent=2)
