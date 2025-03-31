import asyncio
from typing import AsyncGenerator, Dict
import random
from .base import LLMProvider

class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing purposes."""
    
    def __init__(self, api_key: str = "mock-key", model: str = "mock-model"):
        """
        Initialize the mock provider.
        
        Args:
            api_key (str): Mock API key (defaults to "mock-key")
            model (str): Mock model name (defaults to "mock-model")
        """
        super().__init__(api_key, model)
        self._responses = [
            "This is a mock response.",
            "I am a test LLM model.",
            "This response is for testing purposes.",
            "Mock mode is active.",
        ]
        
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate a mock text response.
        
        Args:
            prompt (str): Input prompt (unused in mock)
            **kwargs: Additional parameters (unused in mock)
            
        Returns:
            str: Random mock response
        """
        await asyncio.sleep(1)  # Simulate API latency
        return random.choice(self._responses)
        
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        Stream a mock response word by word.
        
        Args:
            prompt (str): Input prompt (unused in mock)
            **kwargs: Additional parameters (unused in mock)
            
        Yields:
            str: Words from a random mock response
        """
        response = random.choice(self._responses)
        words = response.split()
        
        for word in words:
            await asyncio.sleep(0.2)  # Simulate streaming delay
            yield word + " "
            
    async def validate_api_key(self) -> bool:
        """
        Mock API key validation.
        
        Returns:
            bool: Always True for mock provider
        """
        await asyncio.sleep(0.5)  # Simulate validation delay
        return True
        
    @property
    def default_params(self) -> Dict:
        """
        Get mock default parameters.
        
        Returns:
            Dict: Mock parameters
        """
        return {
            "temperature": 0.7,
            "max_tokens": 100,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        } 