import requests
from datetime import datetime, date
from typing import Dict, List, Tuple, Any
from .base import WeatherProvider


class OpenMeteoProvider(WeatherProvider):
    """Open-Meteo weather provider implementation (free, no API key required)."""
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        # Open-Meteo doesn't require an API key
    
    def get_coordinates(self, city: str) -> Tuple[float, float]:
        """Get city coordinates using Open-Meteo geocoding API."""
        # Use OpenStreetMap Nominatim API (used by Open-Meteo)
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {
            'name': city,
            'count': 1
        }
        
        response = requests.get(geo_url, params=params)
        response.raise_for_status()
        
        data = response.json()
        if not data.get('results'):
            raise Exception(f"City '{city}' not found")
        
        result = data['results'][0]
        return result['latitude'], result['longitude']
    
    def get_today_forecast(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get today's forecast using Open-Meteo forecast API."""
        url = "https://api.open-meteo.com/v1/forecast"
        today_str = date.today().isoformat()
        
        params = {
            'latitude': lat,
            'longitude': lon,
            'hourly': 'temperature_2m,weather_code',
            'daily': 'temperature_2m_max,temperature_2m_min',
            'timezone': 'auto',
            'start_date': today_str,
            'end_date': today_str
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Get current hour for filtering future forecasts
        current_hour = datetime.now().hour
        
        # Extract hourly data for today
        hourly_times = data['hourly']['time']
        hourly_temps = data['hourly']['temperature_2m']
        hourly_codes = data['hourly']['weather_code']
        
        # Get future hourly forecasts for today
        detailed_forecast = []
        future_temps = []
        
        for i, time_str in enumerate(hourly_times):
            forecast_time = datetime.fromisoformat(time_str.replace('T', ' '))
            if forecast_time.hour >= current_hour:
                future_temps.append(hourly_temps[i])
                if len(detailed_forecast) < 4:  # Next 4 time slots
                    detailed_forecast.append({
                        'temp': round(hourly_temps[i], 1),
                        'time': forecast_time.strftime('%H:%M'),
                        'description': self._weather_code_to_description(hourly_codes[i])
                    })
        
        # Get daily min/max
        daily_max = data['daily']['temperature_2m_max'][0]
        daily_min = data['daily']['temperature_2m_min'][0]
        
        # Current temperature (use first future forecast or current)
        current_temp = future_temps[0] if future_temps else hourly_temps[current_hour]
        
        # Use actual forecasted max/min or calculated from remaining temps
        if future_temps:
            forecasted_max = max(max(future_temps), daily_max)
            forecasted_min = min(min(future_temps), daily_min)
        else:
            forecasted_max = daily_max
            forecasted_min = daily_min
        
        return {
            'forecasted_max': round(forecasted_max, 1),
            'forecasted_min': round(forecasted_min, 1),
            'current_temp': round(current_temp, 1),
            'description': self._weather_code_to_description(hourly_codes[current_hour]),
            'detailed_forecast': detailed_forecast
        }
    
    def get_current_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get current weather using Open-Meteo current weather API."""
        url = "https://api.open-meteo.com/v1/forecast"
        today_str = date.today().isoformat()
        
        params = {
            'latitude': lat,
            'longitude': lon,
            'current': 'temperature_2m,weather_code',
            'daily': 'temperature_2m_max,temperature_2m_min',
            'timezone': 'auto',
            'start_date': today_str,
            'end_date': today_str
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        current_temp = data['current']['temperature_2m']
        current_code = data['current']['weather_code']
        daily_max = data['daily']['temperature_2m_max'][0]
        daily_min = data['daily']['temperature_2m_min'][0]
        
        return {
            'temp': current_temp,
            'temp_max': daily_max,
            'temp_min': daily_min,
            'description': self._weather_code_to_description(current_code)
        }
    
    def _weather_code_to_description(self, code: int) -> str:
        """Convert Open-Meteo weather code to description."""
        # WMO Weather interpretation codes
        code_map = {
            0: "clear sky",
            1: "mainly clear",
            2: "partly cloudy",
            3: "overcast",
            45: "fog",
            48: "depositing rime fog",
            51: "light drizzle",
            53: "moderate drizzle", 
            55: "dense drizzle",
            56: "light freezing drizzle",
            57: "dense freezing drizzle",
            61: "slight rain",
            63: "moderate rain",
            65: "heavy rain",
            66: "light freezing rain",
            67: "heavy freezing rain",
            71: "slight snow fall",
            73: "moderate snow fall",
            75: "heavy snow fall",
            77: "snow grains",
            80: "slight rain showers",
            81: "moderate rain showers",
            82: "violent rain showers",
            85: "slight snow showers",
            86: "heavy snow showers",
            95: "thunderstorm",
            96: "thunderstorm with slight hail",
            99: "thunderstorm with heavy hail"
        }
        
        return code_map.get(code, f"unknown weather code {code}")