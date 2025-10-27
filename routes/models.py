"""
Models API routes for Ask Rumi Backend
Handles model management, downloads, and inference.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import json
import logging
from datetime import datetime

from core.model_manager import get_model_registry, ModelInfo
from core.local_runner import get_local_runner, InferenceRequest
from core.queue_manager import get_queue_manager, TaskPriority

logger = logging.getLogger(__name__)

router = APIRouter()

class ModelRunRequest(BaseModel):
    """Model run request"""
    model: str
    prompt: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 500
    stream: bool = False

class ModelRunResponse(BaseModel):
    """Model run response"""
    model: str
    response: str
    tokens_used: Optional[int] = None
    inference_time: Optional[float] = None
    timestamp: str
    success: bool
    error: Optional[str] = None

class ModelDownloadRequest(BaseModel):
    """Model download request"""
    model: str
    priority: Optional[str] = "normal"

class ModelDownloadResponse(BaseModel):
    """Model download response"""
    model: str
    task_id: str
    status: str
    message: str

@router.get("/")
async def list_models():
    """List all available models"""
    try:
        registry = get_model_registry()
        models = registry.get_all_models()
        
        return {
            "models": [
                {
                    "name": model.name,
                    "display_name": model.display_name,
                    "description": model.description,
                    "size_gb": model.size_gb,
                    "provider": model.provider,
                    "status": model.status,
                    "tags": model.tags,
                    "capabilities": model.capabilities,
                    "last_updated": model.last_updated
                }
                for model in models.values()
            ],
            "total": len(models)
        }
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/available")
async def list_available_models():
    """List only available models"""
    try:
        registry = get_model_registry()
        models = registry.get_available_models()
        
        return {
            "models": [
                {
                    "name": model.name,
                    "display_name": model.display_name,
                    "description": model.description,
                    "size_gb": model.size_gb,
                    "provider": model.provider,
                    "tags": model.tags,
                    "capabilities": model.capabilities
                }
                for model in models.values()
            ],
            "total": len(models)
        }
    except Exception as e:
        logger.error(f"Error listing available models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{model_name}")
async def get_model_info(model_name: str):
    """Get detailed information about a specific model"""
    try:
        registry = get_model_registry()
        model = registry.get_model(model_name)
        
        if not model:
            raise HTTPException(status_code=404, detail=f"Model {model_name} not found")
        
        # Check current availability
        is_available = registry.check_model_availability(model_name)
        
        return {
            "name": model.name,
            "display_name": model.display_name,
            "description": model.description,
            "size_gb": model.size_gb,
            "provider": model.provider,
            "status": model.status,
            "is_available": is_available,
            "tags": model.tags,
            "capabilities": model.capabilities,
            "last_updated": model.last_updated,
            "download_progress": model.download_progress
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run", response_model=ModelRunResponse)
async def run_model(request: ModelRunRequest):
    """Run inference on a model"""
    try:
        # Validate model
        registry = get_model_registry()
        model = registry.get_model(request.model)
        if not model:
            raise HTTPException(status_code=404, detail=f"Model {request.model} not found")
        
        if model.status != "available":
            raise HTTPException(status_code=400, detail=f"Model {request.model} is not available")
        
        # Create inference request
        inference_request = InferenceRequest(
            model=request.model,
            prompt=request.prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=request.stream
        )
        
        # Run inference
        local_runner = get_local_runner()
        response = await local_runner.run_inference(inference_request)
        
        return ModelRunResponse(
            model=response.model,
            response=response.response,
            tokens_used=response.tokens_used,
            inference_time=response.inference_time,
            timestamp=response.timestamp,
            success=response.success,
            error=response.error
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Model run error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run/stream")
async def run_model_stream(request: ModelRunRequest):
    """Run inference on a model with streaming response"""
    try:
        # Validate model
        registry = get_model_registry()
        model = registry.get_model(request.model)
        if not model:
            raise HTTPException(status_code=404, detail=f"Model {request.model} not found")
        
        if model.status != "available":
            raise HTTPException(status_code=400, detail=f"Model {request.model} is not available")
        
        # Create streaming inference request
        inference_request = InferenceRequest(
            model=request.model,
            prompt=request.prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=True
        )
        
        async def generate_stream():
            """Generate streaming response"""
            local_runner = get_local_runner()
            
            try:
                async for chunk in local_runner.run_streaming_inference(inference_request):
                    yield f"data: {chunk}\n\n"
                
                # Send completion signal
                yield f"data: {json.dumps({'done': True})}\n\n"
                
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                yield f"data: {json.dumps({'error': str(e), 'success': False})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Model stream error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/download", response_model=ModelDownloadResponse)
async def download_model(request: ModelDownloadRequest, background_tasks: BackgroundTasks):
    """Download a model"""
    try:
        registry = get_model_registry()
        model = registry.get_model(request.model)
        
        if not model:
            raise HTTPException(status_code=404, detail=f"Model {request.model} not found")
        
        if model.status == "available":
            return ModelDownloadResponse(
                model=request.model,
                task_id="",
                status="already_available",
                message=f"Model {request.model} is already available"
            )
        
        if model.status == "downloading":
            return ModelDownloadResponse(
                model=request.model,
                task_id="",
                status="downloading",
                message=f"Model {request.model} is already being downloaded"
            )
        
        # Start download in background
        queue_manager = get_queue_manager()
        
        # Register download function if not already registered
        if "download_model" not in queue_manager.registered_functions:
            queue_manager.register_function("download_model", registry.download_model)
        
        # Determine priority
        priority_map = {
            "low": TaskPriority.LOW,
            "normal": TaskPriority.NORMAL,
            "high": TaskPriority.HIGH,
            "urgent": TaskPriority.URGENT
        }
        priority = priority_map.get(request.priority, TaskPriority.NORMAL)
        
        # Enqueue download task
        task_id = await queue_manager.enqueue_task(
            name=f"Download {request.model}",
            function="download_model",
            args={"name": request.model},
            priority=priority
        )
        
        return ModelDownloadResponse(
            model=request.model,
            task_id=task_id,
            status="queued",
            message=f"Download task queued for {request.model}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{model_name}/status")
async def get_download_status(model_name: str):
    """Get download status for a model"""
    try:
        registry = get_model_registry()
        model = registry.get_model(model_name)
        
        if not model:
            raise HTTPException(status_code=404, detail=f"Model {model_name} not found")
        
        progress = registry.get_download_progress(model_name)
        
        return {
            "model": model_name,
            "status": model.status,
            "progress": progress,
            "last_updated": model.last_updated
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting download status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{model_name}")
async def remove_model(model_name: str):
    """Remove a model"""
    try:
        registry = get_model_registry()
        success = registry.remove_model(model_name)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Model {model_name} not found")
        
        return {"message": f"Model {model_name} removed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{model_name}/test")
async def test_model(model_name: str):
    """Test if a model is working correctly"""
    try:
        registry = get_model_registry()
        model = registry.get_model(model_name)
        
        if not model:
            raise HTTPException(status_code=404, detail=f"Model {model_name} not found")
        
        if model.status != "available":
            raise HTTPException(status_code=400, detail=f"Model {model_name} is not available")
        
        # Run a simple test
        local_runner = get_local_runner()
        success = await local_runner.test_model(model_name)
        
        return {
            "model": model_name,
            "test_passed": success,
            "message": "Model test completed successfully" if success else "Model test failed"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Model test error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/capabilities/{capability}")
async def get_models_by_capability(capability: str):
    """Get models that support a specific capability"""
    try:
        registry = get_model_registry()
        models = registry.get_models_by_capability(capability)
        
        return {
            "capability": capability,
            "models": [
                {
                    "name": model.name,
                    "display_name": model.display_name,
                    "description": model.description,
                    "status": model.status,
                    "provider": model.provider
                }
                for model in models.values()
            ],
            "total": len(models)
        }
    except Exception as e:
        logger.error(f"Error getting models by capability: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def models_health():
    """Health check for models service"""
    try:
        registry = get_model_registry()
        local_runner = get_local_runner()
        
        return {
            "status": "healthy",
            "total_models": len(registry.get_all_models()),
            "available_models": len(registry.get_available_models()),
            "inference_history_count": len(local_runner.get_inference_history())
        }
    except Exception as e:
        logger.error(f"Models health check error: {e}")
        return {"status": "unhealthy", "error": str(e)}