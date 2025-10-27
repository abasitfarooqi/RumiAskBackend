"""
GPU Manager for Ask Rumi Backend
Handles device detection, GPU switching, and memory management.
"""

import torch
import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import psutil

logger = logging.getLogger(__name__)

class DeviceInfo(BaseModel):
    """Device information model"""
    device_type: str
    device_name: str
    is_available: bool
    memory_total: Optional[float] = None  # GB
    memory_used: Optional[float] = None   # GB
    memory_free: Optional[float] = None  # GB
    compute_capability: Optional[str] = None

class GPUManager:
    """Manages GPU detection, switching, and memory monitoring"""
    
    def __init__(self):
        self.current_device = self._detect_best_device()
        self.device_info = self._get_all_device_info()
        logger.info(f"GPU Manager initialized with device: {self.current_device}")
    
    def _detect_best_device(self) -> str:
        """Detect the best available device for inference"""
        # Check Apple Metal Performance Shaders (MPS) - preferred for Apple Silicon
        if torch.backends.mps.is_available():
            logger.info("Apple Metal Performance Shaders (MPS) detected")
            return "mps"
        
        # Check CUDA - preferred for NVIDIA GPUs
        elif torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            logger.info(f"CUDA detected with {device_count} device(s)")
            return "cuda"
        
        # Fallback to CPU
        else:
            logger.info("No GPU detected, using CPU")
            return "cpu"
    
    def _get_all_device_info(self) -> Dict[str, DeviceInfo]:
        """Get comprehensive information about all available devices"""
        devices = {}
        
        # CPU Information
        cpu_count = psutil.cpu_count()
        memory = psutil.virtual_memory()
        devices["cpu"] = DeviceInfo(
            device_type="cpu",
            device_name=f"CPU ({cpu_count} cores)",
            is_available=True,
            memory_total=memory.total / (1024**3),  # Convert to GB
            memory_used=memory.used / (1024**3),
            memory_free=memory.available / (1024**3)
        )
        
        # Apple Metal Performance Shaders (MPS)
        if torch.backends.mps.is_available():
            devices["mps"] = DeviceInfo(
                device_type="mps",
                device_name="Apple Metal Performance Shaders",
                is_available=True,
                memory_total=None,  # MPS doesn't expose memory info directly
                memory_used=None,
                memory_free=None
            )
        
        # CUDA Information
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            for i in range(device_count):
                device_name = torch.cuda.get_device_name(i)
                memory_total = torch.cuda.get_device_properties(i).total_memory / (1024**3)
                memory_allocated = torch.cuda.memory_allocated(i) / (1024**3)
                memory_reserved = torch.cuda.memory_reserved(i) / (1024**3)
                
                devices[f"cuda:{i}"] = DeviceInfo(
                    device_type="cuda",
                    device_name=device_name,
                    is_available=True,
                    memory_total=memory_total,
                    memory_used=memory_allocated,
                    memory_free=memory_total - memory_reserved,
                    compute_capability=f"{torch.cuda.get_device_properties(i).major}.{torch.cuda.get_device_properties(i).minor}"
                )
        
        return devices
    
    def get_current_device(self) -> str:
        """Get the current active device"""
        return self.current_device
    
    def set_device(self, device: str) -> bool:
        """Switch to a specific device"""
        if device == "cpu":
            self.current_device = "cpu"
            logger.info("Switched to CPU")
            return True
        
        elif device == "mps":
            if torch.backends.mps.is_available():
                self.current_device = "mps"
                logger.info("Switched to Apple Metal (MPS)")
                return True
            else:
                logger.warning("MPS not available")
                return False
        
        elif device.startswith("cuda"):
            if torch.cuda.is_available():
                # Extract device index if specified
                if ":" in device:
                    device_idx = int(device.split(":")[1])
                    if device_idx < torch.cuda.device_count():
                        torch.cuda.set_device(device_idx)
                        self.current_device = device
                        logger.info(f"Switched to CUDA device {device_idx}")
                        return True
                else:
                    self.current_device = "cuda:0"
                    logger.info("Switched to CUDA device 0")
                    return True
            else:
                logger.warning("CUDA not available")
                return False
        
        else:
            logger.warning(f"Unknown device: {device}")
            return False
    
    def get_device_info(self, device: Optional[str] = None) -> DeviceInfo:
        """Get information about a specific device"""
        target_device = device or self.current_device
        return self.device_info.get(target_device, self.device_info["cpu"])
    
    def get_all_devices(self) -> Dict[str, DeviceInfo]:
        """Get information about all available devices"""
        return self.device_info
    
    def get_available_devices(self) -> List[str]:
        """Get list of available device names"""
        return [name for name, info in self.device_info.items() if info.is_available]
    
    def get_memory_usage(self, device: Optional[str] = None) -> Dict[str, float]:
        """Get memory usage for a specific device"""
        target_device = device or self.current_device
        device_info = self.device_info.get(target_device)
        
        if not device_info:
            return {"error": "Device not found"}
        
        if target_device == "cpu":
            memory = psutil.virtual_memory()
            return {
                "total": memory.total / (1024**3),
                "used": memory.used / (1024**3),
                "free": memory.available / (1024**3),
                "percent": memory.percent
            }
        
        elif target_device.startswith("cuda"):
            device_idx = int(target_device.split(":")[1]) if ":" in target_device else 0
            if torch.cuda.is_available():
                memory_allocated = torch.cuda.memory_allocated(device_idx) / (1024**3)
                memory_reserved = torch.cuda.memory_reserved(device_idx) / (1024**3)
                memory_total = torch.cuda.get_device_properties(device_idx).total_memory / (1024**3)
                
                return {
                    "total": memory_total,
                    "allocated": memory_allocated,
                    "reserved": memory_reserved,
                    "free": memory_total - memory_reserved
                }
        
        elif target_device == "mps":
            # MPS doesn't expose memory info directly
            return {"note": "MPS memory info not available"}
        
        return {"error": "Unknown device type"}
    
    def clear_cache(self, device: Optional[str] = None):
        """Clear GPU cache for a specific device"""
        target_device = device or self.current_device
        
        if target_device.startswith("cuda"):
            device_idx = int(target_device.split(":")[1]) if ":" in target_device else 0
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                logger.info(f"Cleared CUDA cache for device {device_idx}")
        
        elif target_device == "mps":
            # MPS doesn't have explicit cache clearing
            logger.info("MPS cache clearing not available")
        
        else:
            logger.info("No cache to clear for CPU")
    
    def get_recommended_device(self) -> str:
        """Get the recommended device based on available hardware"""
        if torch.backends.mps.is_available():
            return "mps"  # Apple Silicon Macs
        elif torch.cuda.is_available():
            return "cuda:0"  # NVIDIA GPUs
        else:
            return "cpu"  # Fallback

# Global instance
gpu_manager = GPUManager()

def get_gpu_manager() -> GPUManager:
    """Get the global GPU manager instance"""
    return gpu_manager
