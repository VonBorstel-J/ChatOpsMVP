from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Optional
import logging
import time
import json
from datetime import datetime

class LLMProvider(ABC):
    """Base class for LLM providers with common interface methods."""
    
    def __init__(self, api_key: str, model: str):
        """
        Initialize the LLM provider.
        
        Args:
            api_key (str): API key for the provider
            model (str): Model identifier to use
        """
        self.api_key = api_key
        self.model = model
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    async def _log_request(self, prompt: str, **kwargs) -> float:
        """Log request details and return start time."""
        start_time = time.time()
        request_id = f"{int(start_time * 1000)}"
        
        self.logger.info(
            "LLM request initiated",
            extra={
                "request_id": request_id,
                "model": self.model,
                "prompt_length": len(prompt),
                "parameters": json.dumps(kwargs),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        return start_time, request_id
        
    async def _log_response(self, start_time: float, request_id: str, response: str, error: Optional[Exception] = None):
        """Log response details including timing and errors."""
        duration = time.time() - start_time
        
        if error:
            self.logger.error(
                "LLM request failed",
                extra={
                    "request_id": request_id,
                    "duration_seconds": duration,
                    "error": str(error),
                    "error_type": error.__class__.__name__,
                    "timestamp": datetime.utcnow().isoformat()
                },
                exc_info=True
            )
        else:
            self.logger.info(
                "LLM request completed",
                extra={
                    "request_id": request_id,
                    "duration_seconds": duration,
                    "response_length": len(response),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    
    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text response from the LLM.
        
        Args:
            prompt (str): Input prompt for the LLM
            **kwargs: Additional model-specific parameters
            
        Returns:
            str: Generated text response
            
        Raises:
            Exception: If text generation fails
        """
        start_time, request_id = await self._log_request(prompt, **kwargs)
        try:
            response = await self._generate_text_impl(prompt, **kwargs)
            await self._log_response(start_time, request_id, response)
            return response
        except Exception as e:
            await self._log_response(start_time, request_id, "", error=e)
            raise
    
    @abstractmethod
    async def _generate_text_impl(self, prompt: str, **kwargs) -> str:
        """Internal implementation of text generation."""
        pass
        
    @abstractmethod
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        Stream text response from the LLM.
        
        Args:
            prompt (str): Input prompt for the LLM
            **kwargs: Additional model-specific parameters
            
        Yields:
            str: Chunks of generated text
            
        Raises:
            Exception: If streaming fails
        """
        start_time, request_id = await self._log_request(prompt, **kwargs)
        accumulated_response = []
        try:
            async for chunk in self._generate_stream_impl(prompt, **kwargs):
                accumulated_response.append(chunk)
                yield chunk
            await self._log_response(start_time, request_id, "".join(accumulated_response))
        except Exception as e:
            await self._log_response(start_time, request_id, "".join(accumulated_response), error=e)
            raise
    
    @abstractmethod
    async def _generate_stream_impl(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Internal implementation of stream generation."""
        pass
        
    @abstractmethod
    async def validate_api_key(self) -> bool:
        """
        Validate the API key.
        
        Returns:
            bool: True if API key is valid, False otherwise
        """
        start_time = time.time()
        request_id = f"{int(start_time * 1000)}_validate"
        
        self.logger.info(
            "API key validation started",
            extra={
                "request_id": request_id,
                "model": self.model,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        try:
            is_valid = await self._validate_api_key_impl()
            self.logger.info(
                "API key validation completed",
                extra={
                    "request_id": request_id,
                    "duration_seconds": time.time() - start_time,
                    "is_valid": is_valid,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            return is_valid
        except Exception as e:
            self.logger.error(
                "API key validation failed",
                extra={
                    "request_id": request_id,
                    "duration_seconds": time.time() - start_time,
                    "error": str(e),
                    "error_type": e.__class__.__name__,
                    "timestamp": datetime.utcnow().isoformat()
                },
                exc_info=True
            )
            return False
    
    @abstractmethod
    async def _validate_api_key_impl(self) -> bool:
        """Internal implementation of API key validation."""
        pass
        
    @property
    @abstractmethod
    def default_params(self) -> Dict:
        """
        Get default parameters for the model.
        
        Returns:
            Dict: Default parameters
        """
        pass 