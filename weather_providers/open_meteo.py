import requests
from datetime import datetime, date, timedelta, timezone
from typing import Dict, Tuple, Any
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
        params = {"name": city, "count": 1}

        response = requests.get(geo_url, params=params)
        response.raise_for_status()

        data = response.json()
        if not data.get("results"):
            raise Exception(f"City '{city}' not found")

        result = data["results"][0]
        return result["latitude"], result["longitude"]

    def get_today_forecast(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get today's forecast using Open-Meteo forecast API."""
        url = "https://api.open-meteo.com/v1/forecast"
        today_str = date.today().isoformat()

        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min",
            "timezone": "auto",  # location local time
            "timeformat": "unixtime",  # easier for downstream timezone conversion
            "start_date": today_str,
            "end_date": today_str,
        }

        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Extract utc offset (seconds) for location local time
        offset_seconds = data.get("utc_offset_seconds", 0)
        # Extract hourly data
        hourly_times = data["hourly"]["time"]  # list of unix timestamps (seconds)
        hourly_temps = data["hourly"]["temperature_2m"]
        hourly_codes = data["hourly"]["weather_code"]

        # Current times
        now_utc = datetime.now(timezone.utc)
        location_now_local = now_utc + timedelta(seconds=offset_seconds)
        location_today = location_now_local.date()

        detailed_forecast = []
        future_temps = []

        for i, ts in enumerate(hourly_times):
            # ts is unix epoch seconds in UTC
            forecast_dt_utc = datetime.fromtimestamp(ts, tz=timezone.utc)
            forecast_dt_local = forecast_dt_utc + timedelta(seconds=offset_seconds)
            if (
                forecast_dt_local.date() == location_today
                and forecast_dt_utc >= now_utc
            ):
                future_temps.append(hourly_temps[i])
                detailed_forecast.append(
                    {
                        "temp": round(hourly_temps[i], 1),
                        "timestamp": int(ts),  # UTC epoch seconds
                        "description": self._weather_code_to_description(
                            hourly_codes[i]
                        ),
                    }
                )

        # Get daily min/max
        daily_max = data["daily"]["temperature_2m_max"][0]
        daily_min = data["daily"]["temperature_2m_min"][0]

        # Current temperature (use first future forecast or fallback to first hourly entry)
        current_temp = future_temps[0] if future_temps else hourly_temps[0]

        # Use actual forecasted max/min or calculated from remaining temps
        if future_temps:
            forecasted_max = max(max(future_temps), daily_max)
            forecasted_min = min(min(future_temps), daily_min)
        else:
            forecasted_max = daily_max
            forecasted_min = daily_min

        return {
            "forecasted_max": round(forecasted_max, 1),
            "forecasted_min": round(forecasted_min, 1),
            "current_temp": round(current_temp, 1),
            "description": detailed_forecast[0]["description"]
            if detailed_forecast
            else self._weather_code_to_description(hourly_codes[0]),
            "detailed_forecast": detailed_forecast,
        }

    def get_current_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get current weather using Open-Meteo current weather API."""
        url = "https://api.open-meteo.com/v1/forecast"
        today_str = date.today().isoformat()

        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min",
            "timezone": "auto",
            "timeformat": "unixtime",
            "start_date": today_str,
            "end_date": today_str,
        }

        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        current_temp = data["current"]["temperature_2m"]
        current_code = data["current"]["weather_code"]
        daily_max = data["daily"]["temperature_2m_max"][0]
        daily_min = data["daily"]["temperature_2m_min"][0]

        return {
            "temp": current_temp,
            "temp_max": daily_max,
            "temp_min": daily_min,
            "description": self._weather_code_to_description(current_code),
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
            99: "thunderstorm with heavy hail",
        }

        return code_map.get(code, f"unknown weather code {code}")

    def get_daily_summary(self, lat: float, lon: float) -> Dict[str, Any]:
        """Return today's actual max/min, current conditions, and tomorrow's forecast (max/min + description).

        Returns keys:
            today_max, today_min, current_temp, current_description,
            tomorrow_max, tomorrow_min, tomorrow_description
        """
        url = "https://api.open-meteo.com/v1/forecast"
        # Request two days of daily data plus current
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min,weather_code",
            "timezone": "auto",
            "forecast_days": 2,
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        current_temp = data["current"]["temperature_2m"]
        current_code = data["current"]["weather_code"]
        today_max = data["daily"]["temperature_2m_max"][0]
        today_min = data["daily"]["temperature_2m_min"][0]
        today_code = data["daily"]["weather_code"][0]

        # Tomorrow may not exist (late in dataset) – guard
        if len(data["daily"]["temperature_2m_max"]) > 1:
            tomorrow_max = data["daily"]["temperature_2m_max"][1]
            tomorrow_min = data["daily"]["temperature_2m_min"][1]
            tomorrow_code = data["daily"]["weather_code"][1]
        else:
            tomorrow_max = tomorrow_min = today_max  # Fallback
            tomorrow_code = today_code

        return {
            "today_max": round(today_max, 1),
            "today_min": round(today_min, 1),
            "current_temp": round(current_temp, 1),
            "current_description": self._weather_code_to_description(current_code),
            "tomorrow_max": round(tomorrow_max, 1),
            "tomorrow_min": round(tomorrow_min, 1),
            "tomorrow_description": self._weather_code_to_description(tomorrow_code),
        }
