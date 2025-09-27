from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any


class WeatherProvider(ABC):
    """Abstract base class for weather providers."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
    
    @abstractmethod
    def get_coordinates(self, city: str) -> Tuple[float, float]:
        """Get city coordinates (latitude, longitude)."""
        pass
    
    @abstractmethod
    def get_today_forecast(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get today's weather forecast.
        
        Returns:
            Dict with keys:
            - forecasted_max: float
            - forecasted_min: float  
            - current_temp: float
            - description: str
            - detailed_forecast: List[Dict] (optional)
        """
        pass
    
    @abstractmethod
    def get_current_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get current weather data.
        
        Returns:
            Dict with keys:
            - temp: float
            - description: str
            - temp_max: float (optional)
            - temp_min: float (optional)
        """
        pass