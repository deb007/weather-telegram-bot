from typing import Dict, Type
from .base import WeatherProvider
from .openweathermap import OpenWeatherMapProvider
from .open_meteo import OpenMeteoProvider


class WeatherProviderFactory:
    """Factory class for creating weather provider instances."""
    
    _providers: Dict[str, Type[WeatherProvider]] = {
        'openweathermap': OpenWeatherMapProvider,
        'open_meteo': OpenMeteoProvider,
    }
    
    @classmethod
    def create_provider(cls, provider_name: str, api_key: str = None) -> WeatherProvider:
        """Create a weather provider instance.
        
        Args:
            provider_name: Name of the provider ('openweathermap' or 'open_meteo')
            api_key: API key (required for some providers like OpenWeatherMap)
            
        Returns:
            WeatherProvider instance
            
        Raises:
            ValueError: If provider name is not supported
        """
        provider_name = provider_name.lower()
        
        if provider_name not in cls._providers:
            available = ', '.join(cls._providers.keys())
            raise ValueError(f"Unsupported weather provider '{provider_name}'. Available providers: {available}")
        
        provider_class = cls._providers[provider_name]
        return provider_class(api_key)
    
    @classmethod
    def get_available_providers(cls) -> list:
        """Get list of available provider names."""
        return list(cls._providers.keys())