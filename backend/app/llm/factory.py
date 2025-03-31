from typing import Dict, Optional, Type
from .providers.base import LLMProvider
from .providers.mock import MockLLMProvider

class LLMFactory:
    """Factory class for creating and managing LLM providers."""
    
    def __init__(self):
        """Initialize the LLM factory."""
        self._providers: Dict[str, Type[LLMProvider]] = {
            "mock": MockLLMProvider,
        }
        self._instances: Dict[str, LLMProvider] = {}
        
    def register_provider(self, name: str, provider_class: Type[LLMProvider]):
        """
        Register a new provider class.
        
        Args:
            name (str): Provider name
            provider_class (Type[LLMProvider]): Provider class
        """
        self._providers[name] = provider_class
        
    def get_provider(
        self,
        name: str,
        api_key: str,
        model: str,
        force_new: bool = False
    ) -> LLMProvider:
        """
        Get or create a provider instance.
        
        Args:
            name (str): Provider name
            api_key (str): API key for the provider
            model (str): Model identifier
            force_new (bool): Force creation of new instance
            
        Returns:
            LLMProvider: Provider instance
            
        Raises:
            ValueError: If provider name is not registered
        """
        if name not in self._providers:
            raise ValueError(f"Provider '{name}' not registered")
            
        instance_key = f"{name}:{api_key}:{model}"
        
        if force_new or instance_key not in self._instances:
            provider_class = self._providers[name]
            self._instances[instance_key] = provider_class(api_key, model)
            
        return self._instances[instance_key]
        
    def list_providers(self) -> Dict[str, Type[LLMProvider]]:
        """
        Get dictionary of registered providers.
        
        Returns:
            Dict[str, Type[LLMProvider]]: Registered providers
        """
        return self._providers.copy()
        
# Global factory instance
llm_factory = LLMFactory() 