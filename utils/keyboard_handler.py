from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

class KeyboardHandler:
    @staticmethod
    def get_main_menu() -> InlineKeyboardMarkup:
        """Create the main menu keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("🌤️ Clima Actual", callback_data="weather"),
                InlineKeyboardButton("📅 Pronóstico", callback_data="forecast")
            ],
            [
                InlineKeyboardButton("⚙️ Configuración", callback_data="settings"),
                InlineKeyboardButton("🔔 Alertas", callback_data="alerts")
            ],
            [
                InlineKeyboardButton("❓ Ayuda", callback_data="help")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_settings_menu() -> InlineKeyboardMarkup:
        """Create the settings menu keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("📍 Cambiar Ubicación", callback_data="change_location"),
                InlineKeyboardButton("🌡️ Unidad de Temperatura", callback_data="change_unit")
            ],
            [
                InlineKeyboardButton("🕒 Notificaciones Diarias", callback_data="daily_notification"),
                InlineKeyboardButton("🌍 Idioma", callback_data="change_language")
            ],
            [
                InlineKeyboardButton("« Volver al Menú Principal", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_temperature_unit_menu() -> InlineKeyboardMarkup:
        """Create the temperature unit selection keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("Celsius (°C)", callback_data="unit_C"),
                InlineKeyboardButton("Fahrenheit (°F)", callback_data="unit_F")
            ],
            [
                InlineKeyboardButton("« Volver a Configuración", callback_data="settings")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_language_menu() -> InlineKeyboardMarkup:
        """Create the language selection keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es"),
                InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")
            ],
            [
                InlineKeyboardButton("« Volver a Configuración", callback_data="settings")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_alert_menu() -> InlineKeyboardMarkup:
        """Create the alerts menu keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("🌡️ Alertas de Temperatura", callback_data="temp_alerts"),
                InlineKeyboardButton("📅 Resumen Diario", callback_data="daily_summary")
            ],
            [
                InlineKeyboardButton("❌ Desactivar Alertas", callback_data="disable_alerts")
            ],
            [
                InlineKeyboardButton("« Volver al Menú Principal", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
