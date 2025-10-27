"""
Local Runner for Ask Rumi Backend
Handles local model inference using Ollama and other local providers.
"""

import asyncio
import subprocess
import json
import logging
from typing import Dict, Any, Optional, List, AsyncGenerator
from pydantic import BaseModel
import aiofiles
from datetime import datetime

logger = logging.getLogger(__name__)

class InferenceRequest(BaseModel):
    """Inference request model"""
    model: str
    prompt: str
    max_tokens: Optional[int] = None
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    stream: bool = False
    context: Optional[str] = None

class InferenceResponse(BaseModel):
    """Inference response model"""
    model: str
    response: str
    tokens_used: Optional[int] = None
    inference_time: Optional[float] = None
    timestamp: str
    success: bool
    error: Optional[str] = None

class LocalRunner:
    """Handles local model inference"""
    
    def __init__(self):
        self.active_processes: Dict[str, subprocess.Popen] = {}
        self.inference_history: List[InferenceResponse] = []
        self.max_history = 100
    
    async def run_inference(self, request: InferenceRequest) -> InferenceResponse:
        """Run inference on a local model"""
        start_time = datetime.now()
        
        try:
            # Check if model is available
            if not await self._check_model_availability(request.model):
                return InferenceResponse(
                    model=request.model,
                    response="",
                    timestamp=start_time.isoformat(),
                    success=False,
                    error=f"Model {request.model} not available"
                )
            
            # Run inference based on model provider
            if await self._is_ollama_model(request.model):
                response_text = await self._run_ollama_inference(request)
            else:
                response_text = await self._run_generic_inference(request)
            
            end_time = datetime.now()
            inference_time = (end_time - start_time).total_seconds()
            
            response = InferenceResponse(
                model=request.model,
                response=response_text,
                inference_time=inference_time,
                timestamp=end_time.isoformat(),
                success=True
            )
            
            # Add to history
            self._add_to_history(response)
            
            return response
            
        except Exception as e:
            logger.error(f"Inference failed for model {request.model}: {e}")
            return InferenceResponse(
                model=request.model,
                response="",
                timestamp=start_time.isoformat(),
                success=False,
                error=str(e)
            )
    
    async def run_streaming_inference(self, request: InferenceRequest) -> AsyncGenerator[str, None]:
        """Run streaming inference on a local model"""
        try:
            if not await self._check_model_availability(request.model):
                yield json.dumps({
                    "error": f"Model {request.model} not available",
                    "success": False
                })
                return
            
            if await self._is_ollama_model(request.model):
                async for chunk in self._run_ollama_streaming(request):
                    yield chunk
            else:
                # For non-Ollama models, simulate streaming
                response = await self._run_generic_inference(request)
                for word in response.split():
                    yield json.dumps({
                        "content": word + " ",
                        "success": True
                    })
                    await asyncio.sleep(0.05)  # Simulate streaming delay
                    
        except Exception as e:
            logger.error(f"Streaming inference failed: {e}")
            yield json.dumps({
                "error": str(e),
                "success": False
            })
    
    async def _check_model_availability(self, model_name: str) -> bool:
        """Check if model is available for inference"""
        try:
            if await self._is_ollama_model(model_name):
                result = await asyncio.create_subprocess_exec(
                    "ollama", "list",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, _ = await result.communicate()
                return model_name in stdout.decode()
            else:
                # Check other providers
                return True  # Placeholder
        except Exception as e:
            logger.error(f"Failed to check model availability: {e}")
            return False
    
    async def _is_ollama_model(self, model_name: str) -> bool:
        """Check if model is an Ollama model"""
        # Simple heuristic - could be improved with registry lookup
        ollama_models = ["phi3-mini", "mistral", "llama3", "codellama", "gemma", "qwen", "tinyllama"]
        return any(model_name.startswith(prefix) for prefix in ollama_models)
    
    async def _run_ollama_inference(self, request: InferenceRequest) -> str:
        """Run inference using Ollama"""
        try:
            # Use Ollama API instead of command line
            import requests
            import json
            
            # Prepare the request payload
            payload = {
                "model": request.model,
                "prompt": request.prompt,
                "stream": False
            }
            
            # Add optional parameters
            if request.temperature is not None:
                payload["options"] = {
                    "temperature": request.temperature
                }
            if request.max_tokens is not None:
                if "options" not in payload:
                    payload["options"] = {}
                payload["options"]["num_predict"] = request.max_tokens
            
            logger.info(f"Running Ollama inference for model: {request.model}")
            
            # Make API request to Ollama
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "").strip()
                logger.info(f"Ollama inference completed successfully")
                return response_text
            else:
                error_msg = f"Ollama API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"Ollama inference error: {e}")
            raise
    
    async def _run_ollama_streaming(self, request: InferenceRequest) -> AsyncGenerator[str, None]:
        """Run streaming inference using Ollama"""
        try:
            cmd = ["ollama", "run", request.model]
            
            if request.temperature is not None:
                cmd.extend(["--temperature", str(request.temperature)])
            if request.max_tokens is not None:
                cmd.extend(["--num-predict", str(request.max_tokens)])
            
            logger.info(f"Running Ollama streaming inference: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Send prompt
            process.stdin.write(request.prompt.encode())
            await process.stdin.drain()
            process.stdin.close()
            
            # Stream response
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                
                try:
                    # Try to parse as JSON (Ollama streaming format)
                    data = json.loads(line.decode().strip())
                    if "response" in data:
                        yield json.dumps({
                            "content": data["response"],
                            "success": True
                        })
                except json.JSONDecodeError:
                    # If not JSON, treat as plain text
                    content = line.decode().strip()
                    if content:
                        yield json.dumps({
                            "content": content,
                            "success": True
                        })
            
            # Wait for process to complete
            await process.wait()
            
        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            yield json.dumps({
                "error": str(e),
                "success": False
            })
    
    async def _run_generic_inference(self, request: InferenceRequest) -> str:
        """Run inference using generic method (placeholder)"""
        # This would be implemented for other model providers
        # For now, return a placeholder response
        await asyncio.sleep(1)  # Simulate inference time
        return f"Generic inference response for model {request.model}: {request.prompt[:50]}..."
    
    def _add_to_history(self, response: InferenceResponse):
        """Add response to inference history"""
        self.inference_history.append(response)
        
        # Keep only recent history
        if len(self.inference_history) > self.max_history:
            self.inference_history = self.inference_history[-self.max_history:]
    
    def get_inference_history(self, limit: Optional[int] = None) -> List[InferenceResponse]:
        """Get inference history"""
        if limit:
            return self.inference_history[-limit:]
        return self.inference_history.copy()
    
    def clear_history(self):
        """Clear inference history"""
        self.inference_history.clear()
    
    async def stop_inference(self, model: str):
        """Stop running inference for a model"""
        if model in self.active_processes:
            process = self.active_processes[model]
            process.terminate()
            await process.wait()
            del self.active_processes[model]
            logger.info(f"Stopped inference for model {model}")
    
    def get_model_info(self, model: str) -> Dict[str, Any]:
        """Get information about a model"""
        # This would typically query the model registry
        return {
            "name": model,
            "provider": "ollama" if self._is_ollama_model(model) else "unknown",
            "status": "available" if self._check_model_availability(model) else "not_available"
        }
    
    async def test_model(self, model: str) -> bool:
        """Test if a model is working correctly"""
        try:
            test_request = InferenceRequest(
                model=model,
                prompt="Hello, how are you?",
                max_tokens=50
            )
            
            response = await self.run_inference(test_request)
            return response.success
            
        except Exception as e:
            logger.error(f"Model test failed for {model}: {e}")
            return False

# Global instance
local_runner = LocalRunner()

def get_local_runner() -> LocalRunner:
    """Get the global local runner instance"""
    return local_runner