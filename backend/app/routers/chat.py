"""
Chat endpoints for handling chat interactions.
"""
from fastapi import APIRouter, HTTPException, Depends, Request, status
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional
from datetime import datetime
import logging
import time
import uuid
from app.config import get_settings, Settings
import json

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

    @classmethod
    def validate_request(cls, data: dict) -> "ChatRequest":
        """Validate request data and return instance or raise appropriate error."""
        try:
            return cls(**data)
        except ValidationError as e:
            logger.warning(
                "Chat request validation failed",
                extra={
                    "error": str(e),
                    "error_type": "ValidationError",
                    "request_data": data,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e)
            )
        except Exception as e:
            logger.error(
                "Chat request parsing failed",
                extra={
                    "error": str(e),
                    "error_type": e.__class__.__name__,
                    "request_data": data,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid request format"
            )

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
    request: Request,
    settings: Settings = Depends(get_settings)
):
    """
    Create a new chat message.
    
    Args:
        request (Request): Raw request object for validation
        settings (Settings): Application settings
    
    Returns:
        ChatResponse: Response containing assistant's message
    
    Raises:
        HTTPException: If there's an error processing the chat request
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # Parse and validate request body
        body = await request.json()
        chat_request = ChatRequest.validate_request(body)
        
        # Log incoming request
        logger.info(
            "Chat request received",
            extra={
                "request_id": request_id,
                "client_host": request.client.host,
                "request_data": chat_request.to_log_dict(),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
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
                    "message_count": len(chat_request.messages),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        return response
        
    except json.JSONDecodeError as e:
        # Handle invalid JSON format
        duration = time.time() - start_time
        logger.warning(
            "Invalid JSON in chat request",
            extra={
                "request_id": request_id,
                "error": str(e),
                "error_type": "JSONDecodeError",
                "duration": duration,
                "duration_ms": duration * 1000,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON format"
        )
        
    except HTTPException as e:
        # Re-raise HTTP exceptions (like validation errors)
        duration = time.time() - start_time
        logger.warning(
            "Chat request failed with HTTP exception",
            extra={
                "request_id": request_id,
                "error": str(e),
                "status_code": e.status_code,
                "duration": duration,
                "duration_ms": duration * 1000,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        raise
        
    except Exception as e:
        # Handle unexpected errors
        duration = time.time() - start_time
        logger.error(
            "Chat request failed",
            extra={
                "request_id": request_id,
                "error": str(e),
                "error_type": e.__class__.__name__,
                "duration": duration,
                "duration_ms": duration * 1000,
                "timestamp": datetime.utcnow().isoformat()
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error processing chat request: {str(e)}"
        ) 