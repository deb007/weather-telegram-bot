import requests
from datetime import datetime
from typing import Dict, List, Tuple, Any
from .base import WeatherProvider


class OpenWeatherMapProvider(WeatherProvider):
    """OpenWeatherMap weather provider implementation."""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        if not api_key:
            raise ValueError("OpenWeatherMap API key is required")
    
    def get_coordinates(self, city: str) -> Tuple[float, float]:
        """Get city coordinates using OpenWeatherMap Geocoding API."""
        geo_url = "http://api.openweathermap.org/geo/1.0/direct"
        params = {
            'q': city,
            'limit': 1,
            'appid': self.api_key
        }
        
        response = requests.get(geo_url, params=params)
        response.raise_for_status()
        
        data = response.json()
        if not data:
            raise Exception(f"City '{city}' not found")
        
        return data[0]['lat'], data[0]['lon']
    
    def get_today_forecast(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get today's forecast using OpenWeatherMap 5-day forecast API."""
        # Use 5-day forecast API to get today's detailed forecast
        url = "https://api.openweathermap.org/data/2.5/forecast"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.api_key,
            'units': 'metric'
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Get today's forecasts only
        today = datetime.now().date()
        today_forecasts = []
        
        for forecast in data['list']:
            forecast_datetime = datetime.fromtimestamp(forecast['dt'])
            if forecast_datetime.date() == today and forecast_datetime.hour >= datetime.now().hour:
                today_forecasts.append({
                    'temp': forecast['main']['temp'],
                    'feels_like': forecast['main']['feels_like'],
                    'temp_min': forecast['main']['temp_min'],
                    'temp_max': forecast['main']['temp_max'],
                    'time': forecast_datetime.strftime('%H:%M'),
                    'description': forecast['weather'][0]['description']
                })
        
        if not today_forecasts:
            # Fallback to current weather if no future forecasts for today
            current_data = self.get_current_weather(lat, lon)
            return {
                'forecasted_max': round(current_data.get('temp_max', current_data['temp']), 1),
                'forecasted_min': round(current_data.get('temp_min', current_data['temp']), 1),
                'current_temp': round(current_data['temp'], 1),
                'description': current_data['description'],
                'detailed_forecast': []
            }
        
        # Calculate max/min from remaining forecasts
        temps = [f['temp'] for f in today_forecasts]
        
        return {
            'forecasted_max': round(max(temps), 1),
            'forecasted_min': round(min(temps), 1),
            'current_temp': round(today_forecasts[0]['temp'], 1),
            'description': today_forecasts[0]['description'],
            'detailed_forecast': today_forecasts[:4]  # Next 4 time slots
        }
    
    def get_current_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get current weather using OpenWeatherMap current weather API."""
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.api_key,
            'units': 'metric'
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()  
        data = response.json()
        
        return {
            'temp': data['main']['temp'],
            'temp_max': data['main']['temp_max'],
            'temp_min': data['main']['temp_min'],
            'description': data['weather'][0]['description']
        }