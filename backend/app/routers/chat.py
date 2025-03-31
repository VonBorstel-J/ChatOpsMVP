"""
Chat endpoints for handling chat interactions.
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import logging
import time
import uuid
from app.config import get_settings, Settings

# Initialize logger
logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])

class Message(BaseModel):
    """Chat message model."""
    role: str = Field(..., description="Role of the message sender (user/assistant)")
    content: str = Field(..., description="Content of the message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    def to_log_dict(self):
        """Convert message to a loggable dictionary."""
        return {
            "role": self.role,
            "content_length": len(self.content),
            "timestamp": self.timestamp.isoformat()
        }

class ChatRequest(BaseModel):
    """Chat request model."""
    messages: List[Message] = Field(..., description="List of chat messages")
    stream: bool = Field(default=False, description="Whether to stream the response")
    system_prompt: Optional[str] = Field(None, description="Optional system prompt")

    def to_log_dict(self):
        """Convert request to a loggable dictionary."""
        return {
            "message_count": len(self.messages),
            "stream": self.stream,
            "has_system_prompt": self.system_prompt is not None,
            "messages": [msg.to_log_dict() for msg in self.messages]
        }

class ChatResponse(BaseModel):
    """Chat response model."""
    message: Message
    conversation_id: str = Field(..., description="Unique conversation identifier")

    def to_log_dict(self):
        """Convert response to a loggable dictionary."""
        return {
            "conversation_id": self.conversation_id,
            "message": self.message.to_log_dict()
        }

@router.post("/chat", response_model=ChatResponse)
async def create_chat(
    request: ChatRequest,
    fastapi_request: Request,
    settings: Settings = Depends(get_settings)
):
    """
    Create a new chat message.
    
    Args:
        request (ChatRequest): Chat request containing messages and options
        fastapi_request (Request): FastAPI request object for logging
        settings (Settings): Application settings
    
    Returns:
        ChatResponse: Response containing assistant's message
    
    Raises:
        HTTPException: If there's an error processing the chat request
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Log incoming request
    logger.info(
        "Chat request received",
        extra={
            "request_id": request_id,
            "client_host": fastapi_request.client.host,
            "request_data": request.to_log_dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    try:
        # This is a placeholder response - we'll implement actual LLM integration in Phase 3
        conversation_id = str(uuid.uuid4())
        response = ChatResponse(
            message=Message(
                role="assistant",
                content="This is a placeholder response. LLM integration coming in Phase 3!"
            ),
            conversation_id=conversation_id
        )
        
        # Calculate processing time
        duration = time.time() - start_time
        
        # Log successful response
        logger.info(
            "Chat request completed",
            extra={
                "request_id": request_id,
                "conversation_id": conversation_id,
                "duration": duration,
                "duration_ms": duration * 1000,
                "response_data": response.to_log_dict(),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Log performance metrics if request was slow
        if settings.LOG_PERF_ENABLED and duration > 1.0:
            logger.warning(
                "Slow chat request detected",
                extra={
                    "request_id": request_id,
                    "conversation_id": conversation_id,
                    "duration": duration,
                    "duration_ms": duration * 1000,
                    "message_count": len(request.messages),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        return response
        
    except Exception as e:
        # Calculate error duration
        duration = time.time() - start_time
        
        # Log error details
        logger.error(
            "Chat request failed",
            extra={
                "request_id": request_id,
                "error": str(e),
                "error_type": e.__class__.__name__,
                "duration": duration,
                "duration_ms": duration * 1000,
                "request_data": request.to_log_dict(),
                "timestamp": datetime.utcnow().isoformat()
            },
            exc_info=True
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat request: {str(e)}"
        ) 