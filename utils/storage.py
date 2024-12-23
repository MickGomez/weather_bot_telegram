import json
import os
from typing import Dict, Optional
from models.user_preferences import UserPreferences

class Storage:
    def __init__(self, storage_file: str = "data/user_preferences.json"):
        self.storage_file = storage_file
        self._ensure_data_directory()
        self.data = self._load_data()

    def _ensure_data_directory(self):
        """Ensure the data directory exists."""
        os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)

    def _load_data(self) -> Dict:
        """Load data from storage file."""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading data: {e}")
            return {}

    def _save_data(self):
        """Save data to storage file."""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Error saving data: {e}")

    def get_user_preferences(self, user_id: int) -> Optional[UserPreferences]:
        """Get user preferences from storage."""
        if str(user_id) in self.data:
            return UserPreferences.from_dict(self.data[str(user_id)])
        return None

    def save_user_preferences(self, preferences: UserPreferences):
        """Save user preferences to storage."""
        self.data[str(preferences.user_id)] = preferences.to_dict()
        self._save_data()

    def delete_user_preferences(self, user_id: int):
        """Delete user preferences from storage."""
        if str(user_id) in self.data:
            del self.data[str(user_id)]
            self._save_data()
