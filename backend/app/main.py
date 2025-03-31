"""
Main FastAPI application module.
"""
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from app.config import get_settings, setup_logging
from app.routers import chat, health, llm
import logging
import time
from datetime import datetime
import uuid
import json
import psutil
import traceback
from typing import Dict, Any

# Initialize settings and logging
settings = get_settings()
setup_logging(settings)

# Initialize logger
logger = logging.getLogger(__name__)

def sanitize_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """Sanitize sensitive information from headers."""
    sensitive_fields = settings.LOG_SENSITIVE_FIELDS
    sanitized = {}
    for key, value in headers.items():
        if any(field.lower() in key.lower() for field in sensitive_fields):
            sanitized[key] = "***REDACTED***"
        else:
            sanitized[key] = value
    return sanitized

def get_system_metrics() -> Dict[str, Any]:
    """Get current system performance metrics."""
    process = psutil.Process()
    return {
        "cpu_percent": process.cpu_percent(),
        "memory_percent": process.memory_percent(),
        "open_files": len(process.open_files()),
        "threads": process.num_threads(),
        "connections": len(process.connections())
    }

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming HTTP requests and their responses with enhanced metrics."""
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Get request body if enabled
    request_body = None
    if settings.LOG_REQUEST_BODY_ENABLED:
        try:
            body_bytes = await request.body()
            if body_bytes:
                request_body = body_bytes.decode()
                # Try to parse and sanitize JSON body
                try:
                    body_json = json.loads(request_body)
                    for field in settings.LOG_SENSITIVE_FIELDS:
                        if field in body_json:
                            body_json[field] = "***REDACTED***"
                    request_body = json.dumps(body_json)
                except json.JSONDecodeError:
                    # If the request is to a JSON endpoint but has invalid JSON, return 400
                    if request.headers.get("content-type") == "application/json":
                        return JSONResponse(
                            status_code=400,
                            content={"detail": "Invalid JSON format"}
                        )
        except Exception as e:
            logger.warning(f"Failed to read request body: {str(e)}")
    
    # Log request details
    logger.info(
        "Request started",
        extra={
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_host": request.client.host if request.client else None,
            "client_port": request.client.port if request.client else None,
            "headers": sanitize_headers(dict(request.headers)),
            "body": request_body if settings.LOG_REQUEST_BODY_ENABLED else None,
            "timestamp": datetime.utcnow().isoformat(),
            "system_metrics": get_system_metrics()
        }
    )
    
    try:
        # Process the request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Get response body if enabled and possible
        response_body = None
        if settings.LOG_RESPONSE_BODY_ENABLED and not isinstance(response, StreamingResponse):
            try:
                if hasattr(response, "body"):
                    response_body = response.body.decode()
            except Exception as e:
                logger.warning(f"Failed to decode response body: {str(e)}")
        
        # Log successful response
        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "duration": duration,
                "duration_ms": duration * 1000,
                "headers": sanitize_headers(dict(response.headers)),
                "body": response_body if settings.LOG_RESPONSE_BODY_ENABLED else None,
                "timestamp": datetime.utcnow().isoformat(),
                "system_metrics": get_system_metrics()
            }
        )
        
        # Log performance metrics if request was slow
        if settings.LOG_PERF_ENABLED and duration > 1.0:  # Log slow requests
            logger.warning(
                "Slow request detected",
                extra={
                    "request_id": request_id,
                    "duration": duration,
                    "duration_ms": duration * 1000,
                    "path": request.url.path,
                    "method": request.method,
                    "system_metrics": get_system_metrics()
                }
            )
        
        return response
        
    except HTTPException as e:
        # Handle HTTP exceptions (like validation errors)
        duration = time.time() - start_time
        logger.warning(
            "Request failed with HTTP exception",
            extra={
                "request_id": request_id,
                "error": str(e),
                "status_code": e.status_code,
                "duration": duration,
                "duration_ms": duration * 1000,
                "path": request.url.path,
                "method": request.method,
                "timestamp": datetime.utcnow().isoformat(),
                "system_metrics": get_system_metrics()
            }
        )
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": str(e)}
        )
    except Exception as e:
        # Calculate duration
        duration = time.time() - start_time
        
        # Log error with full details
        logger.error(
            "Request failed",
            extra={
                "request_id": request_id,
                "error": str(e),
                "error_type": e.__class__.__name__,
                "error_traceback": traceback.format_exc(),
                "duration": duration,
                "duration_ms": duration * 1000,
                "path": request.url.path,
                "method": request.method,
                "timestamp": datetime.utcnow().isoformat(),
                "system_metrics": get_system_metrics()
            },
            exc_info=True
        )
        return JSONResponse(
            status_code=422,
            content={"detail": f"Error processing request: {str(e)}"}
        )

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure this appropriately in production
)

# Include routers
app.include_router(health.router, prefix=settings.API_V1_PREFIX)
app.include_router(chat.router, prefix=settings.API_V1_PREFIX)
app.include_router(llm.router, prefix=settings.API_V1_PREFIX)

# Log application startup with detailed information
logger.info(
    "Application started",
    extra={
        "environment": settings.ENVIRONMENT,
        "debug_mode": settings.DEBUG,
        "version": "1.0.0",
        "host": settings.HOST,
        "port": settings.PORT,
        "api_prefix": settings.API_V1_PREFIX,
        "cors_origins": settings.BACKEND_CORS_ORIGINS,
        "system_metrics": get_system_metrics(),
        "timestamp": datetime.utcnow().isoformat()
    }
) 