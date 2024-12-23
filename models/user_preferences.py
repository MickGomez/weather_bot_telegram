from datetime import time
from typing import Optional, Tuple
from pydantic import BaseModel

class UserPreferences(BaseModel):
    user_id: int
    location: Optional[str] = None
    language: str = "es"  # Default to Spanish
    temperature_unit: str = "C"  # C for Celsius, F for Fahrenheit
    notification_time: Optional[time] = None
    temp_alert_thresholds: Optional[Tuple[float, float]] = None
    daily_forecast: bool = False

    def to_dict(self) -> dict:
        """Convert the model to a dictionary for storage."""
        return {
            "user_id": self.user_id,
            "location": self.location,
            "language": self.language,
            "temperature_unit": self.temperature_unit,
            "notification_time": self.notification_time.strftime("%H:%M") if self.notification_time else None,
            "temp_alert_thresholds": self.temp_alert_thresholds,
            "daily_forecast": self.daily_forecast
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserPreferences":
        """Create a UserPreferences instance from a dictionary."""
        if data.get("notification_time"):
            hour, minute = map(int, data["notification_time"].split(":"))
            data["notification_time"] = time(hour, minute)
        return cls(**data)
