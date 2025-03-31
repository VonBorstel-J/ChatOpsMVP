"""
Configuration management for the ChatOps MVP application.
"""
from functools import lru_cache
from typing import Optional, List
from pydantic_settings import BaseSettings
import json
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import os
from datetime import datetime
import traceback
from pythonjsonlogger import jsonlogger

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for structured logging."""
    
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['logger'] = record.name
        log_record['level'] = record.levelname
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        if record.exc_info:
            log_record['exception'] = traceback.format_exception(*record.exc_info)
        if hasattr(record, 'duration'):
            log_record['duration_ms'] = record.duration * 1000

class Settings(BaseSettings):
    """Application settings and configuration."""
    
    # Environment Configuration
    ENVIRONMENT: str = "development"
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "ChatOps MVP"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:8000"]
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(process)d | %(threadName)s | %(message)s"
    LOG_FILE: str = "logs/app.log"
    LOG_ERROR_FILE: str = "logs/error.log"
    LOG_JSON_FILE: str = "logs/json.log"
    LOG_PERF_FILE: str = "logs/performance.log"
    LOG_MAX_SIZE: int = 10 * 1024 * 1024  # 10 MB
    LOG_BACKUP_COUNT: int = 5
    LOG_JSON_ENABLED: bool = True
    LOG_PERF_ENABLED: bool = True
    LOG_REQUEST_BODY_ENABLED: bool = True
    LOG_RESPONSE_BODY_ENABLED: bool = True
    LOG_SENSITIVE_FIELDS: List[str] = ["password", "token", "api_key", "secret"]
    
    # LLM Configuration
    MOCK_LLM: bool = False
    LLM_PROVIDER: str = "openai"  # Options: openai, anthropic, etc.
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    PERPLEXITY_API_KEY: Optional[str] = None
    
    # API Timeouts
    API_TIMEOUT: int = 30
    STREAM_TIMEOUT: int = 300
    
    # Mock Configuration
    MOCK_RESPONSE_DELAY: float = 0.5
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns:
        Settings: Application settings
    """
    return Settings()

def setup_logging(settings: Settings = get_settings()):
    """
    Configure application logging with enhanced features.
    
    Args:
        settings (Settings): Application settings
    """
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Create formatters
    detailed_formatter = logging.Formatter(settings.LOG_FORMAT)
    json_formatter = CustomJsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s')
    
    # Configure rotating file handler for main log file
    file_handler = RotatingFileHandler(
        settings.LOG_FILE,
        maxBytes=settings.LOG_MAX_SIZE,
        backupCount=settings.LOG_BACKUP_COUNT
    )
    file_handler.setFormatter(detailed_formatter)
    file_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Configure rotating file handler for error log file
    error_handler = RotatingFileHandler(
        settings.LOG_ERROR_FILE,
        maxBytes=settings.LOG_MAX_SIZE,
        backupCount=settings.LOG_BACKUP_COUNT
    )
    error_handler.setFormatter(detailed_formatter)
    error_handler.setLevel(logging.ERROR)
    
    # Configure JSON log handler
    if settings.LOG_JSON_ENABLED:
        json_handler = TimedRotatingFileHandler(
            settings.LOG_JSON_FILE,
            when='midnight',
            interval=1,
            backupCount=settings.LOG_BACKUP_COUNT
        )
        json_handler.setFormatter(json_formatter)
        json_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
        root_logger.addHandler(json_handler)
    
    # Configure performance log handler
    if settings.LOG_PERF_ENABLED:
        perf_handler = RotatingFileHandler(
            settings.LOG_PERF_FILE,
            maxBytes=settings.LOG_MAX_SIZE,
            backupCount=settings.LOG_BACKUP_COUNT
        )
        perf_handler.setFormatter(json_formatter)
        perf_handler.setLevel(logging.INFO)
        root_logger.addHandler(perf_handler)
    
    # Configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(detailed_formatter)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(console_handler)
    
    # Create logger instance
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configured successfully",
        extra={
            "environment": settings.ENVIRONMENT,
            "log_level": settings.LOG_LEVEL,
            "json_logging": settings.LOG_JSON_ENABLED,
            "performance_logging": settings.LOG_PERF_ENABLED
        }
    )
    logger.info(
        "Log files initialized",
        extra={
            "main_log": settings.LOG_FILE,
            "error_log": settings.LOG_ERROR_FILE,
            "json_log": settings.LOG_JSON_FILE if settings.LOG_JSON_ENABLED else None,
            "perf_log": settings.LOG_PERF_FILE if settings.LOG_PERF_ENABLED else None
        }
    ) 