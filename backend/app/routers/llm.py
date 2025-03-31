from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict
from ..llm.factory import llm_factory
from ..llm.utils.rate_limiter import UserRateLimiter
import json
import logging
import time
import uuid
from datetime import datetime
from app.config import get_settings, Settings

# Initialize logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/llm", tags=["llm"])

# Initialize rate limiter with 60 requests per minute per user
rate_limiter = UserRateLimiter(requests_per_minute=60)

class GenerateRequest(BaseModel):
    """Request model for text generation."""
    provider: str
    model: str
    prompt: str
    stream: bool = False
    parameters: Optional[Dict] = None

    def to_log_dict(self):
        """Convert request to a loggable dictionary."""
        return {
            "provider": self.provider,
            "model": self.model,
            "prompt_length": len(self.prompt),
            "stream": self.stream,
            "parameters": self.parameters
        }

async def get_user_id(request: Request) -> str:
    """
    Get user ID from request for rate limiting.
    
    Args:
        request (Request): FastAPI request object
        
    Returns:
        str: User identifier
    """
    # TODO: Implement proper user authentication
    return request.client.host

@router.post("/generate")
async def generate_text(
    request: Request,
    generate_request: GenerateRequest,
    settings: Settings = Depends(get_settings)
):
    """
    Generate text from LLM.
    
    Args:
        request (Request): FastAPI request object
        generate_request (GenerateRequest): Generation request
        settings (Settings): Application settings
        
    Returns:
        Union[Dict, StreamingResponse]: Generated text or streaming response
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    user_id = await get_user_id(request)
    
    # Log incoming request
    logger.info(
        "LLM generation request received",
        extra={
            "request_id": request_id,
            "user_id": user_id,
            "client_host": request.client.host,
            "request_data": generate_request.to_log_dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    user_limiter = rate_limiter.get_limiter(user_id)
    
    if not await user_limiter.acquire():
        logger.warning(
            "Rate limit exceeded",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "client_host": request.client.host,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later."
        )
    
    try:
        # Get API key from environment variables or config
        # TODO: Implement proper API key management
        api_key = "mock-key" if generate_request.provider == "mock" else None
        if not api_key:
            logger.error(
                "API key not configured",
                extra={
                    "request_id": request_id,
                    "provider": generate_request.provider,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            raise HTTPException(
                status_code=401,
                detail=f"API key not configured for provider: {generate_request.provider}"
            )
        
        provider = llm_factory.get_provider(
            generate_request.provider,
            api_key,
            generate_request.model
        )
        
        if generate_request.stream:
            async def stream_response():
                chunk_count = 0
                total_tokens = 0
                stream_start = time.time()
                
                try:
                    async for chunk in provider.generate_stream(
                        generate_request.prompt,
                        **(generate_request.parameters or {})
                    ):
                        chunk_count += 1
                        total_tokens += len(chunk.split())
                        yield f"data: {json.dumps({'text': chunk})}\n\n"
                        
                    stream_duration = time.time() - stream_start
                    logger.info(
                        "Stream generation completed",
                        extra={
                            "request_id": request_id,
                            "duration": stream_duration,
                            "duration_ms": stream_duration * 1000,
                            "chunk_count": chunk_count,
                            "total_tokens": total_tokens,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
                except Exception as e:
                    logger.error(
                        "Stream generation failed",
                        extra={
                            "request_id": request_id,
                            "error": str(e),
                            "error_type": e.__class__.__name__,
                            "chunk_count": chunk_count,
                            "timestamp": datetime.utcnow().isoformat()
                        },
                        exc_info=True
                    )
                    raise
                    
            return StreamingResponse(
                stream_response(),
                media_type="text/event-stream"
            )
        else:
            response = await provider.generate_text(
                generate_request.prompt,
                **(generate_request.parameters or {})
            )
            
            # Calculate processing time
            duration = time.time() - start_time
            
            # Log successful response
            logger.info(
                "Text generation completed",
                extra={
                    "request_id": request_id,
                    "duration": duration,
                    "duration_ms": duration * 1000,
                    "response_length": len(response),
                    "token_count": len(response.split()),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Log performance metrics if request was slow
            if settings.LOG_PERF_ENABLED and duration > 2.0:
                logger.warning(
                    "Slow LLM request detected",
                    extra={
                        "request_id": request_id,
                        "duration": duration,
                        "duration_ms": duration * 1000,
                        "provider": generate_request.provider,
                        "model": generate_request.model,
                        "prompt_length": len(generate_request.prompt),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            
            return {"text": response}
            
    except ValueError as e:
        # Log validation error
        logger.error(
            "Validation error in LLM request",
            extra={
                "request_id": request_id,
                "error": str(e),
                "error_type": "ValueError",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Calculate error duration
        duration = time.time() - start_time
        
        # Log error details
        logger.error(
            "LLM request failed",
            extra={
                "request_id": request_id,
                "error": str(e),
                "error_type": e.__class__.__name__,
                "duration": duration,
                "duration_ms": duration * 1000,
                "request_data": generate_request.to_log_dict(),
                "timestamp": datetime.utcnow().isoformat()
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/providers")
async def list_providers():
    """
    List available LLM providers.
    
    Returns:
        Dict: Available providers and their details
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        providers = llm_factory.list_providers()
        provider_list = {
            name: {
                "models": ["mock-model"] if name == "mock" else []
            }
            for name in providers.keys()
        }
        
        # Calculate processing time
        duration = time.time() - start_time
        
        # Log successful response
        logger.info(
            "Provider list retrieved",
            extra={
                "request_id": request_id,
                "duration": duration,
                "duration_ms": duration * 1000,
                "provider_count": len(providers),
                "providers": list(providers.keys()),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return provider_list
        
    except Exception as e:
        # Calculate error duration
        duration = time.time() - start_time
        
        # Log error details
        logger.error(
            "Failed to list providers",
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
            status_code=500,
            detail=f"Error listing providers: {str(e)}"
        ) 