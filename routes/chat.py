"""
Chat API routes for Ask Rumi Backend
Handles chat endpoints and conversation management.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import json
import logging
from datetime import datetime

from core.local_runner import get_local_runner, InferenceRequest
from core.queue_manager import get_queue_manager, TaskPriority
from core.model_manager import get_model_registry

# Import Rumi services
from services.query_analyzer import get_query_analyzer
from services.quote_retriever import get_quote_retriever
from services.rumi_responder import get_rumi_responder

logger = logging.getLogger(__name__)

router = APIRouter()

class ChatMessage(BaseModel):
    """Chat message model"""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    model: Optional[str] = "phi3-mini"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 500
    stream: bool = False
    context: Optional[str] = None
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    model: str
    conversation_id: str
    timestamp: str
    tokens_used: Optional[int] = None
    inference_time: Optional[float] = None

class Conversation(BaseModel):
    """Conversation model"""
    id: str
    messages: List[ChatMessage]
    created_at: str
    updated_at: str
    model: str

# In-memory conversation storage (replace with database in production)
conversations: Dict[str, Conversation] = {}

@router.post("/send", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """Send a chat message and get response"""
    try:
        # Validate model
        model_registry = get_model_registry()
        model_info = model_registry.get_model(request.model)
        if not model_info:
            raise HTTPException(status_code=404, detail=f"Model {request.model} not found")
        
        if model_info.status != "available":
            raise HTTPException(status_code=400, detail=f"Model {request.model} is not available")
        
        # Get or create conversation
        conversation_id = request.conversation_id or f"conv_{len(conversations) + 1}"
        if conversation_id not in conversations:
            conversations[conversation_id] = Conversation(
                id=conversation_id,
                messages=[],
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                model=request.model
            )
        
        conversation = conversations[conversation_id]
        
        # Add user message
        user_message = ChatMessage(
            role="user",
            content=request.message,
            timestamp=datetime.now().isoformat()
        )
        conversation.messages.append(user_message)
        
        # Prepare context from conversation history
        context_messages = conversation.messages[-10:]  # Last 10 messages
        context = "\n".join([f"{msg.role}: {msg.content}" for msg in context_messages])
        
        # Create inference request
        inference_request = InferenceRequest(
            model=request.model,
            prompt=request.message,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            context=context
        )
        
        # Run inference
        local_runner = get_local_runner()
        response = await local_runner.run_inference(inference_request)
        
        if not response.success:
            raise HTTPException(status_code=500, detail=f"Inference failed: {response.error}")
        
        # Add assistant response
        assistant_message = ChatMessage(
            role="assistant",
            content=response.response,
            timestamp=response.timestamp
        )
        conversation.messages.append(assistant_message)
        conversation.updated_at = datetime.now().isoformat()
        
        return ChatResponse(
            response=response.response,
            model=request.model,
            conversation_id=conversation_id,
            timestamp=response.timestamp,
            tokens_used=response.tokens_used,
            inference_time=response.inference_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stream")
async def stream_message(request: ChatRequest):
    """Send a chat message and stream the response"""
    try:
        # Validate model
        model_registry = get_model_registry()
        model_info = model_registry.get_model(request.model)
        if not model_info:
            raise HTTPException(status_code=404, detail=f"Model {request.model} not found")
        
        if model_info.status != "available":
            raise HTTPException(status_code=400, detail=f"Model {request.model} is not available")
        
        # Get or create conversation
        conversation_id = request.conversation_id or f"conv_{len(conversations) + 1}"
        if conversation_id not in conversations:
            conversations[conversation_id] = Conversation(
                id=conversation_id,
                messages=[],
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                model=request.model
            )
        
        conversation = conversations[conversation_id]
        
        # Add user message
        user_message = ChatMessage(
            role="user",
            content=request.message,
            timestamp=datetime.now().isoformat()
        )
        conversation.messages.append(user_message)
        
        # Prepare context
        context_messages = conversation.messages[-10:]
        context = "\n".join([f"{msg.role}: {msg.content}" for msg in context_messages])
        
        # Create streaming inference request
        inference_request = InferenceRequest(
            model=request.model,
            prompt=request.message,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=True,
            context=context
        )
        
        async def generate_stream():
            """Generate streaming response"""
            local_runner = get_local_runner()
            full_response = ""
            
            try:
                async for chunk in local_runner.run_streaming_inference(inference_request):
                    yield f"data: {chunk}\n\n"
                    
                    # Parse chunk to get content
                    try:
                        chunk_data = json.loads(chunk)
                        if chunk_data.get("success") and "content" in chunk_data:
                            full_response += chunk_data["content"]
                    except json.JSONDecodeError:
                        pass
                
                # Add final message to conversation
                assistant_message = ChatMessage(
                    role="assistant",
                    content=full_response.strip(),
                    timestamp=datetime.now().isoformat()
                )
                conversation.messages.append(assistant_message)
                conversation.updated_at = datetime.now().isoformat()
                
                # Send completion signal
                yield f"data: {json.dumps({'done': True, 'conversation_id': conversation_id})}\n\n"
                
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
        logger.error(f"Streaming chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations")
async def get_conversations():
    """Get all conversations"""
    return {
        "conversations": [
            {
                "id": conv.id,
                "message_count": len(conv.messages),
                "created_at": conv.created_at,
                "updated_at": conv.updated_at,
                "model": conv.model
            }
            for conv in conversations.values()
        ]
    }

@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get a specific conversation"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conversations[conversation_id]

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    del conversations[conversation_id]
    return {"message": "Conversation deleted"}

@router.post("/conversations/{conversation_id}/clear")
async def clear_conversation(conversation_id: str):
    """Clear messages from a conversation"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conversations[conversation_id].messages.clear()
    conversations[conversation_id].updated_at = datetime.now().isoformat()
    
    return {"message": "Conversation cleared"}

@router.post("/ask-rumi")
async def ask_rumi(request: ChatRequest):
    """Special endpoint for asking Rumi-style questions with intelligent retrieval"""
    try:
        # Initialize services
        analyzer = get_query_analyzer()
        retriever = get_quote_retriever()
        responder = get_rumi_responder()
        
        # Get conversation ID first
        conversation_id = request.conversation_id or f"conv_{len(conversations) + 1}"
        
        # Store message BEFORE processing (so context is available)
        if conversation_id not in conversations:
            conversations[conversation_id] = Conversation(
                id=conversation_id,
                messages=[],
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                model=request.model
            )
        
        conversation = conversations[conversation_id]
        
        # Store user message immediately for context
        user_message = ChatMessage(
            role="user",
            content=request.message,
            timestamp=datetime.now().isoformat()
        )
        conversation.messages.append(user_message)
        
        # Analyze query
        logger.info(f"Analyzing query: {request.message}")
        intent = analyzer.analyze(request.message)
        logger.info(f"Detected intent: {intent.intent_type}, emotions: {intent.emotions}, themes: {intent.themes}")
        
        # Retrieve relevant quotes
        quotes = retriever.retrieve(intent, max_quotes=3)
        logger.info(f"Retrieved {len(quotes)} quotes")
        
        # Get conversation history for context
        conversation_history = []
        if len(conversation.messages) > 1:  # More than just the current message
            # Get last few exchanges for conversational context
            context_messages = conversation.messages[-5:-1]  # Last few, excluding current
            conversation_history = [
                f"{msg.role}: {msg.content}" for msg in context_messages
            ]
        
        # Generate conversational prompt with history
        logger.info(f"Conversation history length: {len(conversation_history)}")
        logger.info(f"History: {conversation_history}")
        
        enhanced_prompt = responder.generate_prompt(
            request.message, 
            quotes, 
            intent,
            conversation_history=conversation_history
        )
        
        logger.info(f"Generated prompt length: {len(enhanced_prompt)}")
        logger.info(f"Prompt preview: {enhanced_prompt[:500]}")
        
        # Adjust max_tokens based on query depth
        # Simple queries (greetings) → shorter responses
        # Deep queries (philosophical) → longer responses
        if intent.is_simple:
            max_tokens = request.max_tokens or 100  # Short for greetings
        else:
            max_tokens = request.max_tokens or 250  # Long for deep questions
        
        # Create inference request with enhanced prompt
        # No explicit context - conversation history is in the prompt
        inference_request = InferenceRequest(
            model=request.model,
            prompt=enhanced_prompt,
            temperature=0.85,  # More conversational and natural
            max_tokens=max_tokens,  # Adjusted based on query depth
            context=None  # Context is now in the prompt itself
        )
        
        # Run inference
        local_runner = get_local_runner()
        response = await local_runner.run_inference(inference_request)
        
        if not response.success:
            raise HTTPException(status_code=500, detail=f"Inference failed: {response.error}")
        
        # Post-process response
        final_response = responder.post_process_response(response.response)
        
        # Add assistant response (user message already stored above)
        conversation.messages.append(ChatMessage(
            role="assistant",
            content=final_response,
            timestamp=response.timestamp
        ))
        conversation.updated_at = datetime.now().isoformat()
        
        return ChatResponse(
            response=final_response,
            model=request.model,
            conversation_id=conversation_id,
            timestamp=response.timestamp,
            tokens_used=response.tokens_used,
            inference_time=response.inference_time
        )
        
    except Exception as e:
        logger.error(f"Ask Rumi error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/settings")
async def get_rumi_settings():
    """Get Rumi conversation settings"""
    from services.rumi_config import get_config, CONFIG_PRESETS
    
    config = get_config()
    return {
        "current_settings": config.to_dict(),
        "available_presets": list(CONFIG_PRESETS.keys())
    }

@router.post("/settings")
async def update_rumi_settings(settings: dict):
    """Update Rumi conversation settings"""
    from services.rumi_config import get_config, RumiConfig
    
    # In a real app, you'd save this to persistent storage
    # For now, we'll just return success
    
    return {
        "status": "updated",
        "settings": settings,
        "message": "Settings will apply to new conversations"
    }

@router.get("/health")
async def chat_health():
    """Health check for chat service"""
    return {
        "status": "healthy",
        "active_conversations": len(conversations),
        "available_models": len([m for m in get_model_registry().get_available_models().values()])
    }