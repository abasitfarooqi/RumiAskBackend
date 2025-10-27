"""
System API routes for Ask Rumi Backend
Handles system information, device management, and health checks.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import psutil
import platform
import torch
from datetime import datetime

from core.gpu_manager import get_gpu_manager, DeviceInfo
from core.model_manager import get_model_registry
from core.queue_manager import get_queue_manager
from core.local_runner import get_local_runner

logger = logging.getLogger(__name__)

router = APIRouter()

class SystemInfo(BaseModel):
    """System information model"""
    platform: str
    python_version: str
    torch_version: str
    cpu_count: int
    memory_total: float  # GB
    memory_available: float  # GB
    memory_used_percent: float
    disk_total: float  # GB
    disk_available: float  # GB
    disk_used_percent: float

class DeviceStatus(BaseModel):
    """Device status model"""
    current_device: str
    available_devices: List[str]
    device_info: Dict[str, DeviceInfo]
    memory_usage: Dict[str, Any]

class HealthStatus(BaseModel):
    """Health status model"""
    status: str
    timestamp: str
    services: Dict[str, str]
    system_load: Dict[str, float]
    memory_usage: Dict[str, Any]

@router.get("/info")
async def get_system_info():
    """Get comprehensive system information"""
    try:
        # Get system information
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        system_info = SystemInfo(
            platform=f"{platform.system()} {platform.release()}",
            python_version=platform.python_version(),
            torch_version=torch.__version__,
            cpu_count=psutil.cpu_count(),
            memory_total=memory.total / (1024**3),
            memory_available=memory.available / (1024**3),
            memory_used_percent=memory.percent,
            disk_total=disk.total / (1024**3),
            disk_available=disk.free / (1024**3),
            disk_used_percent=(disk.used / disk.total) * 100
        )
        
        return system_info.dict()
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/device")
async def get_device_status():
    """Get current device status and information"""
    try:
        gpu_manager = get_gpu_manager()
        
        device_status = DeviceStatus(
            current_device=gpu_manager.get_current_device(),
            available_devices=gpu_manager.get_available_devices(),
            device_info={
                name: device.dict() 
                for name, device in gpu_manager.get_all_devices().items()
            },
            memory_usage=gpu_manager.get_memory_usage()
        )
        
        return device_status.dict()
    except Exception as e:
        logger.error(f"Error getting device status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/device")
async def set_device(device: str = Query(..., description="Device to switch to (cpu, mps, cuda, cuda:0, etc.)")):
    """Switch to a specific device"""
    try:
        gpu_manager = get_gpu_manager()
        success = gpu_manager.set_device(device)
        
        if not success:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to switch to device {device}. Device may not be available."
            )
        
        return {
            "message": f"Successfully switched to device {device}",
            "current_device": gpu_manager.get_current_device(),
            "available_devices": gpu_manager.get_available_devices()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting device: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memory")
async def get_memory_usage(device: Optional[str] = Query(None, description="Specific device to check")):
    """Get memory usage for a specific device or all devices"""
    try:
        gpu_manager = get_gpu_manager()
        
        if device:
            memory_info = gpu_manager.get_memory_usage(device)
            return {
                "device": device,
                "memory": memory_info
            }
        else:
            # Get memory info for all devices
            all_devices = gpu_manager.get_all_devices()
            memory_info = {}
            
            for device_name in all_devices.keys():
                memory_info[device_name] = gpu_manager.get_memory_usage(device_name)
            
            return {
                "devices": memory_info,
                "current_device": gpu_manager.get_current_device()
            }
    except Exception as e:
        logger.error(f"Error getting memory usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/memory/clear")
async def clear_memory_cache(device: Optional[str] = Query(None, description="Device to clear cache for")):
    """Clear memory cache for a specific device"""
    try:
        gpu_manager = get_gpu_manager()
        gpu_manager.clear_cache(device)
        
        return {
            "message": f"Memory cache cleared for device {device or 'current device'}",
            "current_device": gpu_manager.get_current_device()
        }
    except Exception as e:
        logger.error(f"Error clearing memory cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def get_health_status():
    """Get comprehensive health status"""
    try:
        # Check system load
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Check services
        services = {}
        
        # Check GPU manager
        try:
            gpu_manager = get_gpu_manager()
            services["gpu_manager"] = "healthy"
        except Exception as e:
            services["gpu_manager"] = f"unhealthy: {e}"
        
        # Check model registry
        try:
            model_registry = get_model_registry()
            services["model_registry"] = "healthy"
        except Exception as e:
            services["model_registry"] = f"unhealthy: {e}"
        
        # Check queue manager
        try:
            queue_manager = get_queue_manager()
            services["queue_manager"] = "healthy" if queue_manager.is_running else "stopped"
        except Exception as e:
            services["queue_manager"] = f"unhealthy: {e}"
        
        # Check local runner
        try:
            local_runner = get_local_runner()
            services["local_runner"] = "healthy"
        except Exception as e:
            services["local_runner"] = f"unhealthy: {e}"
        
        # Determine overall status
        unhealthy_services = [name for name, status in services.items() if "unhealthy" in status]
        overall_status = "healthy" if not unhealthy_services else "degraded"
        
        health_status = HealthStatus(
            status=overall_status,
            timestamp=datetime.now().isoformat(),
            services=services,
            system_load={
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "load_average": psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0.0
            },
            memory_usage={
                "total": memory.total / (1024**3),
                "available": memory.available / (1024**3),
                "used_percent": memory.percent
            }
        )
        
        return health_status.dict()
    except Exception as e:
        logger.error(f"Error getting health status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_system_stats():
    """Get system statistics and metrics"""
    try:
        # System stats
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Model stats
        model_registry = get_model_registry()
        all_models = model_registry.get_all_models()
        available_models = model_registry.get_available_models()
        
        # Queue stats
        queue_manager = get_queue_manager()
        queue_stats = await queue_manager.get_queue_stats()
        
        # Inference stats
        local_runner = get_local_runner()
        inference_history = local_runner.get_inference_history(limit=10)
        
        return {
            "system": {
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": memory.total / (1024**3),
                "memory_available_gb": memory.available / (1024**3),
                "memory_used_percent": memory.percent,
                "disk_total_gb": disk.total / (1024**3),
                "disk_available_gb": disk.free / (1024**3),
                "disk_used_percent": (disk.used / disk.total) * 100
            },
            "models": {
                "total_models": len(all_models),
                "available_models": len(available_models),
                "downloading_models": len([m for m in all_models.values() if m.status == "downloading"]),
                "failed_models": len([m for m in all_models.values() if m.status == "error"])
            },
            "queue": queue_stats,
            "inference": {
                "recent_inferences": len(inference_history),
                "last_inference": inference_history[-1].timestamp if inference_history else None
            }
        }
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/version")
async def get_version_info():
    """Get version information"""
    try:
        import sys
        import fastapi
        import uvicorn
        
        return {
            "app_version": "1.0.0",
            "python_version": sys.version,
            "fastapi_version": fastapi.__version__,
            "uvicorn_version": uvicorn.__version__,
            "torch_version": torch.__version__,
            "platform": platform.platform(),
            "architecture": platform.architecture()[0]
        }
    except Exception as e:
        logger.error(f"Error getting version info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/restart")
async def restart_services():
    """Restart core services"""
    try:
        # Restart queue manager
        queue_manager = get_queue_manager()
        if queue_manager.is_running:
            await queue_manager.stop()
            await queue_manager.start()
        
        # Clear GPU cache
        gpu_manager = get_gpu_manager()
        gpu_manager.clear_cache()
        
        return {
            "message": "Services restarted successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error restarting services: {e}")
        raise HTTPException(status_code=500, detail=str(e))