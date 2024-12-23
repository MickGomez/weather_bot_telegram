from datetime import datetime, timedelta
from typing import Dict, Optional
from cachetools import TTLCache

class WeatherCache:
    def __init__(self, ttl_seconds: int = 300):  # Cache for 5 minutes by default
        self.current_weather_cache = TTLCache(maxsize=100, ttl=ttl_seconds)
        self.forecast_cache = TTLCache(maxsize=100, ttl=ttl_seconds * 2)  # Cache forecast for longer

    def get_current_weather(self, location: str) -> Optional[Dict]:
        """Get cached current weather data for a location."""
        return self.current_weather_cache.get(location)

    def set_current_weather(self, location: str, data: Dict):
        """Cache current weather data for a location."""
        self.current_weather_cache[location] = data

    def get_forecast(self, location: str) -> Optional[Dict]:
        """Get cached forecast data for a location."""
        return self.forecast_cache.get(location)

    def set_forecast(self, location: str, data: Dict):
        """Cache forecast data for a location."""
        self.forecast_cache[location] = data

    def is_current_weather_cached(self, location: str) -> bool:
        """Check if current weather data is cached for a location."""
        return location in self.current_weather_cache

    def is_forecast_cached(self, location: str) -> bool:
        """Check if forecast data is cached for a location."""
        return location in self.forecast_cache
