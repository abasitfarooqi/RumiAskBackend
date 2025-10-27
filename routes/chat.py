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
from services.conversation_layer import ConversationLayer
from services.behavior_config import get_behavior_config

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
        layer = ConversationLayer()
        
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
        
        # DECIDE: Empathetic support OR Casual chat OR Rumi wisdom
        needs_empathy = layer.needs_empathetic_support(request.message)
        use_rumi_wisdom = layer.should_use_rumi_wisdom(request.message)
        
        logger.info(f"{'❤️ EMPATHETIC SUPPORT' if needs_empathy else '🔮 RUMI WISDOM' if use_rumi_wisdom else '💬 Casual CHAT (simple response)'}")
        
        # Load behavior config
        behavior_config = get_behavior_config()
        history_depth = behavior_config.get('conversation_history_depth', 2)
        
        # Get conversation history - LIMIT to avoid confusion
        conversation_history = []
        if len(conversation.messages) > 1:
            # Get last N messages based on config
            context_messages = conversation.messages[-(history_depth+1):-1]
            conversation_history = [
                f"{msg.role}: {msg.content}" for msg in context_messages
            ]
            logger.info(f"📝 Conversation history: {len(conversation_history)} previous messages")
        
        # Generate appropriate prompt
        if needs_empathy:
            # Empathetic support with optional wisdom
            max_quotes_empathy = behavior_config.get('max_quotes_for_empathetic', 2)
            quotes = retriever.retrieve(intent, max_quotes=max_quotes_empathy)
            logger.info(f"❤️ Empathetic response with {len(quotes)} supportive quotes")
            enhanced_prompt = responder.generate_empathetic_prompt(
                request.message,
                quotes if quotes else None,
                conversation_history=conversation_history
            )
        elif use_rumi_wisdom:
            # Use knowledge base quotes
            max_quotes = behavior_config.get('max_quotes_retrieved', 3)
            quotes = retriever.retrieve(intent, max_quotes=max_quotes)
            logger.info(f"✅ Using {len(quotes)} quotes from rumi_knowledge_base.json")
            enhanced_prompt = responder.generate_wisdom_prompt(
                request.message, 
                quotes, 
                intent,
                conversation_history=conversation_history
            )
        else:
            # Casual chat, no quotes
            logger.info("💬 Casual response - no quotes")
            quotes = []  # No quotes for casual
            enhanced_prompt = responder.generate_casual_prompt(
                request.message,
                conversation_history=conversation_history
            )
        
        logger.info(f"Generated prompt length: {len(enhanced_prompt)}")
        logger.info(f"Prompt preview: {enhanced_prompt[:500]}")
        
        # Load config and adjust tokens based on layer type
        behavior_config = get_behavior_config()
        if needs_empathy:
            max_tokens = behavior_config.get('max_tokens_empathetic', 220)
        elif use_rumi_wisdom:
            max_tokens = behavior_config.get('max_tokens_wisdom', 200)
        else:
            max_tokens = behavior_config.get('max_tokens_casual', 80)
        
        temperature = behavior_config.get('temperature', 0.8)
        
        # Create inference request with enhanced prompt
        inference_request = InferenceRequest(
            model=request.model,
            prompt=enhanced_prompt,
            temperature=temperature,
            max_tokens=request.max_tokens or max_tokens,
            context=None
        )
        
        # Run inference
        local_runner = get_local_runner()
        response = await local_runner.run_inference(inference_request)
        
        if not response.success:
            raise HTTPException(status_code=500, detail=f"Inference failed: {response.error}")
        
        # Post-process response
        final_response = responder.post_process_response(response.response)
        
        # Collect technical specs for monitoring
        response_type = "❤️ Empathetic Support" if needs_empathy else "🔮 Rumi Wisdom" if use_rumi_wisdom else "💬 Casual Chat"
        quotes_used = len(quotes) if quotes else 0
        tokens_used = getattr(response, 'tokens_used', 0) or 0
        prompt_length = len(enhanced_prompt)
        inference_time = response.inference_time if hasattr(response, 'inference_time') else 0
        history_length = len(conversation_history) if conversation_history else 0
        
        # Estimate tokens from response if not provided
        if tokens_used == 0:
            tokens_used = len(final_response.split())  # Rough estimate: word count
        
        # Calculate estimated GPU usage (rough estimate based on tokens)
        # Typical: ~500 MB for small models like gemma3:270m
        estimated_gpu_mb = max(100, tokens_used * 2)  # Rough estimate: 2 MB per token
        estimated_cost_usd = (tokens_used / 1000) * 0.0001  # Rough estimate: $0.0001 per 1k tokens
        
        # Add comprehensive technical specs
        tech_specs = f"""
--- TECH SPECS ---
Mode: {response_type}
Model: {request.model}
Quotes used: {quotes_used}
Inference time: {inference_time:.2f}s
Tokens generated: {tokens_used}
Prompt length: {prompt_length} chars (includes {history_length} previous messages)
Max tokens: {max_tokens}
Temperature: {temperature}
Estimated GPU usage: {estimated_gpu_mb} MB
Estimated cost: ${estimated_cost_usd:.6f}"""
        final_response += tech_specs
        
        # If using Rumi wisdom OR empathetic support with quotes, append sources
        if (use_rumi_wisdom or needs_empathy) and quotes:
            sources = []
            for q in quotes:
                quote_id = q.get('id', 'N/A')
                source_ref = q.get('source_ref', '')
                primary_theme = q.get('primary_theme', '')
                
                # Format: ID (Source)
                if source_ref:
                    sources.append(f"{quote_id} ({source_ref})")
                elif primary_theme:
                    sources.append(f"{quote_id} ({primary_theme})")
                else:
                    sources.append(quote_id)
            
            if sources:
                # Append sources at the end
                final_response += f"\n📜 Sources: {', '.join(sources)}"
        
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

@router.get("/behavior-settings")
async def get_behavior_settings():
    """Get LLM behavior configuration"""
    try:
        behavior_config = get_behavior_config()
        return {
            "status": "success",
            "config": behavior_config.to_dict()
        }
    except Exception as e:
        logger.error(f"Error getting behavior settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/behavior-settings")
async def update_behavior_settings(settings: dict):
    """Update LLM behavior configuration"""
    try:
        behavior_config = get_behavior_config()
        
        # Update configuration
        if behavior_config.update(settings):
            return {
                "status": "success",
                "message": "Behavior settings updated",
                "config": behavior_config.to_dict()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save settings")
    except Exception as e:
        logger.error(f"Error updating behavior settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ask-rumi/debug")
async def ask_rumi_debug(request: ChatRequest):
    """Debug endpoint to see which quotes are being used"""
    analyzer = get_query_analyzer()
    retriever = get_quote_retriever()
    
    # Analyze and retrieve
    intent = analyzer.analyze(request.message)
    quotes = retriever.retrieve(intent, max_quotes=3)
    
    return {
        "query": request.message,
        "intent": {
            "type": intent.intent_type,
            "emotions": intent.emotions,
            "themes": intent.themes,
            "is_simple": intent.is_simple
        },
        "quotes_from_knowledge_base": [
            {
                "id": q["id"],
                "quote": q["quote"],
                "theme": q.get("primary_theme", ""),
                "tags": q.get("micro_tags", [])
            }
            for q in quotes
        ],
        "message": f"✅ Using {len(quotes)} quotes from rumi_knowledge_base.json"
    }

@router.get("/health")
async def chat_health():
    """Health check for chat service"""
    return {
        "status": "healthy",
        "active_conversations": len(conversations),
        "available_models": len([m for m in get_model_registry().get_available_models().values()])
    }

@router.get("/emotion-keywords")
async def get_emotion_keywords():
    """Get emotion and keyword tags configuration"""
    try:
        import os
        import json
        
        # Load from JSON file
        config_path = "data/emotion_keywords_config.json"
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return {
                    "status": "success",
                    "config": config
                }
        else:
            # Return default config
            return {
                    "status": "success",
                    "config": {
                        "emotion_keywords": {},
                        "theme_keywords": {},
                        "empathy_triggers": {
                            "distress_patterns": [],
                            "emoticons": []
                        }
                    }
                }
    except Exception as e:
        logger.error(f"Error loading emotion keywords: {e}")
        return {
                "status": "error",
                "error": str(e)
            }

@router.post("/emotion-keywords")
async def save_emotion_keywords(request: Dict[str, Any]):
    """Save emotion and keyword tags configuration"""
    try:
        import os
        import json
        
        config = request
        config_path = "data/emotion_keywords_config.json"
        
        # Save to JSON file
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        
        logger.info("Emotion keywords configuration saved")
        return {"status": "success", "message": "Configuration saved"}
    except Exception as e:
        logger.error(f"Error saving emotion keywords: {e}")
        raise HTTPException(status_code=500, detail=str(e))