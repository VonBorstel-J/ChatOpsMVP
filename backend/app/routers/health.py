"""
Health check endpoints for monitoring application status.
"""
from fastapi import APIRouter, status, Request, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime
import logging
import time
import uuid
import psutil
import platform
from typing import Dict, Any
from app.config import get_settings, Settings

# Initialize logger
logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])

class SystemMetrics(BaseModel):
    """System metrics model."""
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    open_files: int
    active_threads: int
    active_connections: int
    python_version: str
    platform_info: str

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    version: str = "1.0.0"
    uptime_seconds: float
    system_metrics: SystemMetrics

    def to_log_dict(self):
        """Convert response to a loggable dictionary."""
        return {
            "status": self.status,
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
            "uptime_seconds": self.uptime_seconds,
            "system_metrics": {
                "cpu_percent": self.system_metrics.cpu_percent,
                "memory_percent": self.system_metrics.memory_percent,
                "disk_usage_percent": self.system_metrics.disk_usage_percent,
                "open_files": self.system_metrics.open_files,
                "active_threads": self.system_metrics.active_threads,
                "active_connections": self.system_metrics.active_connections
            }
        }

def get_system_metrics() -> SystemMetrics:
    """Get detailed system metrics."""
    process = psutil.Process()
    disk = psutil.disk_usage('/')
    
    return SystemMetrics(
        cpu_percent=psutil.cpu_percent(),
        memory_percent=psutil.virtual_memory().percent,
        disk_usage_percent=disk.percent,
        open_files=len(process.open_files()),
        active_threads=process.num_threads(),
        active_connections=len(process.connections()),
        python_version=platform.python_version(),
        platform_info=platform.platform()
    )

@router.get("/health", response_model=HealthResponse)
async def health_check(
    request: Request,
    settings: Settings = Depends(get_settings)
):
    """
    Health check endpoint to verify API status.
    
    Args:
        request (Request): FastAPI request object
        settings (Settings): Application settings
    
    Returns:
        HealthResponse: Health check response containing status and system metrics
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # Get system metrics
        metrics = get_system_metrics()
        
        # Create response
        response = HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            uptime_seconds=time.time() - psutil.boot_time(),
            system_metrics=metrics
        )
        
        # Calculate processing time
        duration = time.time() - start_time
        
        # Log health check
        logger.info(
            "Health check completed",
            extra={
                "request_id": request_id,
                "client_host": request.client.host,
                "duration": duration,
                "duration_ms": duration * 1000,
                "health_data": response.to_log_dict(),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Log warning if system metrics are concerning
        if (metrics.cpu_percent > 80 or 
            metrics.memory_percent > 80 or 
            metrics.disk_usage_percent > 80):
            logger.warning(
                "System resources running high",
                extra={
                    "request_id": request_id,
                    "cpu_percent": metrics.cpu_percent,
                    "memory_percent": metrics.memory_percent,
                    "disk_usage_percent": metrics.disk_usage_percent,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        return response
        
    except Exception as e:
        # Calculate error duration
        duration = time.time() - start_time
        
        # Log error details
        logger.error(
            "Health check failed",
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
            detail=f"Error performing health check: {str(e)}"
        ) 