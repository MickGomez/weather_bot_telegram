import os
import logging
import sys
import traceback
from datetime import datetime, time
import pytz
import requests
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, error as telegram_error
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from models.user_preferences import UserPreferences
from models.weather_cache import WeatherCache
from utils.logger import setup_logger
from utils.storage import Storage
from utils.keyboard_handler import KeyboardHandler

# Configure exception handling
def handle_exception(exc_type, exc_value, exc_traceback):
    logger.error("Uncaught exception:", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

# Load environment variables
load_dotenv()

# Setup logging
logger = setup_logger('weather_bot')

# Constants
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')  # Updated to match .env file
WEATHER_BASE_URL = 'http://api.weatherapi.com/v1'
PORT = int(os.environ.get('PORT', '8443'))

class WeatherBot:
    def __init__(self):
        self.cache = WeatherCache()
        self.storage = Storage()
        self.keyboard_handler = KeyboardHandler()
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /start is issued."""
        user_id = update.effective_user.id
        preferences = self.storage.get_user_preferences(user_id)
        
        if not preferences:
            preferences = UserPreferences(user_id=user_id)
            self.storage.save_user_preferences(preferences)

        welcome_message = (
            "¡Bienvenido al Bicho_Bot del Clima!\n\n"
            "Selecciona una opción del menú:"
        )
        await update.message.reply_text(
            welcome_message,
            reply_markup=self.keyboard_handler.get_main_menu()
        )

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button presses."""
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        preferences = self.storage.get_user_preferences(user_id)

        if query.data == "weather":
            await self.get_weather(update, context)
        elif query.data == "forecast":
            await self.get_forecast(update, context)
        elif query.data == "settings":
            await query.edit_message_text(
                "Configuración\n\nSelecciona una opción:",
                reply_markup=self.keyboard_handler.get_settings_menu()
            )
        elif query.data == "alerts":
            await query.edit_message_text(
                "Configuración de Alertas\n\nSelecciona una opción:",
                reply_markup=self.keyboard_handler.get_alert_menu()
            )
        elif query.data == "main_menu":
            await query.edit_message_text(
                "Menú Principal:",
                reply_markup=self.keyboard_handler.get_main_menu()
            )
        elif query.data == "change_location":
            context.user_data['expecting_location'] = True
            await query.edit_message_text(
                "Por favor, envía el nombre de tu ciudad.\n"
                "Ejemplo: Madrid",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("« Volver", callback_data="settings")
                ]])
            )
        elif query.data == "change_unit":
            await query.edit_message_text(
                "Selecciona tu unidad de temperatura preferida:",
                reply_markup=self.keyboard_handler.get_temperature_unit_menu()
            )
        elif query.data.startswith("unit_"):
            unit = query.data.split("_")[1]
            if preferences:
                preferences.temperature_unit = unit
                self.storage.save_user_preferences(preferences)
                await query.edit_message_text(
                    f"Unidad de temperatura cambiada a {unit}°",
                    reply_markup=self.keyboard_handler.get_settings_menu()
                )
        elif query.data == "daily_notification":
            await query.edit_message_text(
                "Configura el horario para recibir el pronóstico diario:\n\n"
                "Por favor, envía la hora en formato HH:MM (24h)\n"
                "Ejemplo: 08:00",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("« Volver", callback_data="settings")
                ]])
            )
            context.user_data['expecting_time'] = True
        elif query.data == "change_language":
            await query.edit_message_text(
                "Selecciona tu idioma preferido:",
                reply_markup=self.keyboard_handler.get_language_menu()
            )
        elif query.data.startswith("lang_"):
            lang = query.data.split("_")[1]
            if preferences:
                preferences.language = lang
                self.storage.save_user_preferences(preferences)
                message = "Language changed to English" if lang == "en" else "Idioma cambiado a Español"
                await query.edit_message_text(
                    message,
                    reply_markup=self.keyboard_handler.get_settings_menu()
                )
        elif query.data == "temp_alerts":
            await query.edit_message_text(
                "Configura las alertas de temperatura\n\n"
                "Envía los límites de temperatura en formato: MIN MAX\n"
                "Ejemplo: 15 25",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("« Volver", callback_data="alerts")
                ]])
            )
            context.user_data['expecting_temp_limits'] = True
        elif query.data == "daily_summary":
            if not preferences or not preferences.location:
                await query.edit_message_text(
                    "Primero debes configurar tu ubicación en el menú de configuración.",
                    reply_markup=self.keyboard_handler.get_alert_menu()
                )
            else:
                preferences.daily_forecast = not preferences.daily_forecast
                self.storage.save_user_preferences(preferences)
                status = "activado" if preferences.daily_forecast else "desactivado"
                await query.edit_message_text(
                    f"Resumen diario {status}",
                    reply_markup=self.keyboard_handler.get_alert_menu()
                )
        elif query.data == "disable_alerts":
            if preferences:
                preferences.temp_alert_thresholds = None
                preferences.daily_forecast = False
                self.storage.save_user_preferences(preferences)
            await query.edit_message_text(
                "Todas las alertas han sido desactivadas",
                reply_markup=self.keyboard_handler.get_alert_menu()
            )
        elif query.data == "help":
            help_text = (
                "Ayuda del Bicho_Bot del Clima\n\n"
                "Clima Actual: Ver el clima actual en tu ubicación\n"
                "Pronóstico: Ver pronóstico de 3 días\n"
                "Configuración: Cambiar ubicación, unidades, etc.\n"
                "Alertas: Configurar alertas de temperatura\n\n"
                "Para cambiar tu ubicación:\n"
                "1. Ve a Configuración\n"
                "2. Selecciona 'Cambiar Ubicación'\n"
                "3. Envía el nombre de tu ciudad\n\n"
                "Para configurar alertas:\n"
                "1. Ve a Alertas\n"
                "2. Elige el tipo de alerta\n"
                "3. Sigue las instrucciones en pantalla"
            )
            await query.edit_message_text(
                help_text,
                reply_markup=self.keyboard_handler.get_main_menu()
            )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages."""
        if not context.user_data:
            await update.message.reply_text(
                "Por favor, usa el menú principal:",
                reply_markup=self.keyboard_handler.get_main_menu()
            )
            return

        user_id = update.effective_user.id
        preferences = self.storage.get_user_preferences(user_id)
        
        if context.user_data.get('expecting_location'):
            location = update.message.text.strip()
            try:
                # Verify location with API
                url = f"{WEATHER_BASE_URL}/current.json"
                params = {'key': WEATHER_API_KEY, 'q': location}
                response = requests.get(url, params=params)
                response.raise_for_status()
                
                if preferences:
                    preferences.location = location
                    self.storage.save_user_preferences(preferences)
                
                await update.message.reply_text(
                    f"Ubicación establecida en: {location}",
                    reply_markup=self.keyboard_handler.get_main_menu()
                )
            except Exception as e:
                logger.error(f"Error validating location: {str(e)}")
                await update.message.reply_text(
                    "No se pudo encontrar esa ubicación. Por favor, intenta con otra.",
                    reply_markup=self.keyboard_handler.get_main_menu()
                )
            finally:
                context.user_data['expecting_location'] = False

        elif context.user_data.get('expecting_time'):
            try:
                time_str = update.message.text.strip()
                hour, minute = map(int, time_str.split(':'))
                notification_time = time(hour, minute)
                
                if preferences:
                    preferences.notification_time = notification_time
                    self.storage.save_user_preferences(preferences)
                    await self.set_daily_notification(user_id, notification_time)
                
                await update.message.reply_text(
                    f"Notificaciones diarias configuradas para las {time_str}",
                    reply_markup=self.keyboard_handler.get_main_menu()
                )
            except ValueError:
                await update.message.reply_text(
                    "Formato de hora inválido. Por favor, usa el formato HH:MM (ejemplo: 08:00)",
                    reply_markup=self.keyboard_handler.get_main_menu()
                )
            finally:
                context.user_data['expecting_time'] = False

        elif context.user_data.get('expecting_temp_limits'):
            try:
                temp_min, temp_max = map(float, update.message.text.strip().split())
                if temp_min >= temp_max:
                    raise ValueError("Min temperature must be less than max temperature")
                
                if preferences:
                    preferences.temp_alert_thresholds = (temp_min, temp_max)
                    self.storage.save_user_preferences(preferences)
                
                await update.message.reply_text(
                    f"Alertas de temperatura configuradas:\n"
                    f"Mínima: {temp_min}°{preferences.temperature_unit}\n"
                    f"Máxima: {temp_max}°{preferences.temperature_unit}",
                    reply_markup=self.keyboard_handler.get_main_menu()
                )
            except ValueError:
                await update.message.reply_text(
                    "Formato inválido. Por favor, envía dos números separados por espacio (ejemplo: 15 25)",
                    reply_markup=self.keyboard_handler.get_main_menu()
                )
            finally:
                context.user_data['expecting_temp_limits'] = False

    async def get_weather(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get current weather for user's location."""
        if update.callback_query:
            user_id = update.callback_query.from_user.id
        else:
            user_id = update.message.from_user.id

        preferences = self.storage.get_user_preferences(user_id)

        if not preferences or not preferences.location:
            await self.request_location(update, context)
            return

        try:
            # Check cache first
            cached_weather = self.cache.get_current_weather(preferences.location)
            if cached_weather:
                weather_data = cached_weather
            else:
                # Make API request if not cached
                url = f"{WEATHER_BASE_URL}/current.json"
                params = {
                    'key': WEATHER_API_KEY,
                    'q': preferences.location
                }
                response = requests.get(url, params=params)
                response.raise_for_status()
                weather_data = response.json()
                self.cache.set_current_weather(preferences.location, weather_data)

            # Format weather message
            current = weather_data['current']
            location_data = weather_data['location']
            
            temp = current['temp_c']
            if preferences.temperature_unit == 'F':
                temp = current['temp_f']
            
            weather_message = (
                f"Clima en {location_data['name']}, {location_data['country']}\n"
                f"Temperatura: {temp}°{preferences.temperature_unit}\n"
                f"Condición: {self.translate_condition(current['condition']['text'])}\n"
                f"Humedad: {current['humidity']}%\n"
                f"Viento: {current['wind_kph']} km/h"
            )

            # Check if this is a callback query or direct command
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    weather_message,
                    reply_markup=self.keyboard_handler.get_main_menu()
                )
            else:
                await update.message.reply_text(
                    weather_message,
                    reply_markup=self.keyboard_handler.get_main_menu()
                )

        except Exception as e:
            logger.error(f"Error fetching weather: {str(e)}")
            error_message = "Lo siento, hubo un error al obtener los datos del clima. Por favor, intenta nuevamente más tarde."
            if update.callback_query:
                await update.callback_query.edit_message_text(error_message)
            else:
                await update.message.reply_text(error_message)

    async def request_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Request location from user."""
        message = (
            "Por favor, establece primero tu ubicación.\n"
            "Introduce el nombre de tu ciudad.\n"
            "Ejemplo: Madrid"
        )
        
        # Set the flag to expect location input
        if context:
            context.user_data['expecting_location'] = True
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("« Volver", callback_data="main_menu")
                ]])
            )
        else:
            await update.message.reply_text(
                message,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("« Volver", callback_data="main_menu")
                ]])
            )

    async def get_forecast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get weather forecast for user's location."""
        if update.callback_query:
            user_id = update.callback_query.from_user.id
        else:
            user_id = update.message.from_user.id

        preferences = self.storage.get_user_preferences(user_id)

        if not preferences or not preferences.location:
            await self.request_location(update, context)
            return

        try:
            url = f"{WEATHER_BASE_URL}/forecast.json"
            params = {
                'key': WEATHER_API_KEY,
                'q': preferences.location,
                'days': 3
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            forecast_data = response.json()

            forecast_message = f"Pronóstico de 3 días para {forecast_data['location']['name']}:\n\n"
            
            for day in forecast_data['forecast']['forecastday']:
                date = datetime.strptime(day['date'], '%Y-%m-%d').strftime('%A, %d de %B')
                # Translate weekday names
                date = date.replace('Monday', 'Lunes').replace('Tuesday', 'Martes').replace('Wednesday', 'Miércoles')
                date = date.replace('Thursday', 'Jueves').replace('Friday', 'Viernes').replace('Saturday', 'Sábado')
                date = date.replace('Sunday', 'Domingo')
                # Translate month names
                date = date.replace('January', 'enero').replace('February', 'febrero').replace('March', 'marzo')
                date = date.replace('April', 'abril').replace('May', 'mayo').replace('June', 'junio')
                date = date.replace('July', 'julio').replace('August', 'agosto').replace('September', 'septiembre')
                date = date.replace('October', 'octubre').replace('November', 'noviembre').replace('December', 'diciembre')
                
                temp_max = day['day']['maxtemp_c']
                temp_min = day['day']['mintemp_c']
                if preferences.temperature_unit == 'F':
                    temp_max = day['day']['maxtemp_f']
                    temp_min = day['day']['mintemp_f']

                forecast_message += (
                    f"{date}\n"
                    f"Máxima: {temp_max}°{preferences.temperature_unit}\n"
                    f"Mínima: {temp_min}°{preferences.temperature_unit}\n"
                    f"Condición: {self.translate_condition(day['day']['condition']['text'])}\n"
                    f"Probabilidad de lluvia: {day['day']['daily_chance_of_rain']}%\n\n"
                )

            try:
                await update.callback_query.edit_message_text(
                    forecast_message,
                    reply_markup=self.keyboard_handler.get_main_menu()
                )
            except telegram_error.BadRequest as e:
                if "Message is not modified" not in str(e):
                    raise e

        except Exception as e:
            logger.error(f"Error fetching forecast: {str(e)}")
            error_message = "Lo siento, hubo un error al obtener el pronóstico. Por favor, intenta nuevamente más tarde."
            try:
                await update.callback_query.edit_message_text(
                    error_message,
                    reply_markup=self.keyboard_handler.get_main_menu()
                )
            except telegram_error.BadRequest as e:
                if "Message is not modified" not in str(e):
                    raise e

    async def set_daily_notification(self, user_id: int, notification_time: time):
        """Schedule daily weather notification."""
        job_id = f"daily_{user_id}"
        
        # Remove existing job if any
        self.scheduler.remove_job(job_id)
        
        # Add new job
        self.scheduler.add_job(
            self.send_daily_notification,
            'cron',
            hour=notification_time.hour,
            minute=notification_time.minute,
            args=[user_id],
            id=job_id
        )

    async def send_daily_notification(self, user_id: int):
        """Send daily weather notification."""
        preferences = self.storage.get_user_preferences(user_id)
        if preferences and preferences.location and preferences.daily_forecast:
            try:
                # Get weather data
                url = f"{WEATHER_BASE_URL}/forecast.json"
                params = {
                    'key': WEATHER_API_KEY,
                    'q': preferences.location,
                    'days': 1
                }
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                # Format message
                current = data['current']
                forecast = data['forecast']['forecastday'][0]['day']
                location_name = data['location']['name']
                
                temp = current['temp_c']
                temp_max = forecast['maxtemp_c']
                temp_min = forecast['mintemp_c']
                if preferences.temperature_unit == 'F':
                    temp = current['temp_f']
                    temp_max = forecast['maxtemp_f']
                    temp_min = forecast['mintemp_f']

                message = (
                    f"Buenos días! Aquí está tu pronóstico diario para {location_name}:\n\n"
                    f"Temperatura actual: {temp}°{preferences.temperature_unit}\n"
                    f"Máxima: {temp_max}°{preferences.temperature_unit}\n"
                    f"Mínima: {temp_min}°{preferences.temperature_unit}\n"
                    f"Condición: {self.translate_condition(forecast['condition']['text'])}\n"
                    f"Probabilidad de lluvia: {forecast['daily_chance_of_rain']}%"
                )

                # Send message
                application = Application.builder().token(TELEGRAM_TOKEN).build()
                async with application:
                    await application.bot.send_message(chat_id=user_id, text=message)

            except Exception as e:
                logger.error(f"Error sending daily notification: {str(e)}")

    def translate_condition(self, condition):
        """Translate weather conditions to Spanish."""
        translations = {
            'Clear': 'Despejado',
            'Sunny': 'Soleado',
            'Partly cloudy': 'Parcialmente nublado',
            'Cloudy': 'Nublado',
            'Overcast': 'Cubierto',
            'Mist': 'Neblina',
            'Patchy rain possible': 'Posible lluvia dispersa',
            'Patchy rain nearby': 'Lluvia cerca',
            'Patchy snow possible': 'Posible nieve dispersa',
            'Patchy sleet possible': 'Posible aguanieve dispersa',
            'Patchy freezing drizzle possible': 'Posible llovizna helada dispersa',
            'Patchy snow nearby': 'Nieve cerca',
            'Patchy drizzle nearby': 'Llovizna cerca', 
            'Light rain with thunder': 'Lluvia ligera con truenos',
            'Thunderstorm': 'Tormenta eléctrica',
            'Heavy thunderstorm': 'Tormenta eléctrica intensa',
            'Drizzle': 'Llovizna',
            'Heavy drizzle': 'Llovizna intensa',
            'Rain': 'Lluvia',
            'Snow': 'Nieve',
            'Sleet': 'Aguanieve',
            'Thunderstorm with rain': 'Tormenta eléctrica con lluvia',
            'Thunderstorm with drizzle': 'Tormenta eléctrica con llovizna',
            'Thunderstorm with hail': 'Tormenta eléctrica con granizo',
            'Patchy light drizzle': 'Llovizna ligera dispersa',
            'Moderate drizzle': 'Llovizna moderada',
            'Moderate rain at times': 'Lluvia moderada por momentos',
            'Heavy rain at times': 'Lluvia intensa por momentos',
            'Moderate or heavy snow showers': 'Nevadas moderadas o intensas',
            'Thundery outbreaks possible': 'Posibles tormentas eléctricas',
            'Blowing snow': 'Ventisca',
            'Blizzard': 'Tormenta de nieve',
            'Fog': 'Niebla',
            'Freezing fog': 'Niebla helada',
            'Light drizzle': 'Llovizna ligera',
            'Freezing drizzle': 'Llovizna helada',
            'Heavy freezing drizzle': 'Llovizna helada intensa',
            'Light rain': 'Lluvia ligera',
            'Moderate rain': 'Lluvia moderada',
            'Heavy rain': 'Lluvia intensa',
            'Light freezing rain': 'Lluvia helada ligera',
            'Moderate or heavy freezing rain': 'Lluvia helada moderada o intensa',
            'Light sleet': 'Aguanieve ligera',
            'Moderate or heavy sleet': 'Aguanieve moderada o intensa',
            'Light snow': 'Nieve ligera',
            'Moderate snow': 'Nieve moderada',
            'Heavy snow': 'Nieve intensa',
            'Ice pellets': 'Granizo',
            'Light rain shower': 'Lluvia ligera intermitente',
            'Moderate or heavy rain shower': 'Lluvia moderada o intensa intermitente',
            'Torrential rain shower': 'Lluvia torrencial',
            'Light sleet showers': 'Aguanieve ligera intermitente',
            'Moderate or heavy sleet showers': 'Aguanieve moderada o intensa intermitente',
            'Light snow showers': 'Nevada ligera intermitente',
            'Moderate or heavy snow showers': 'Nevada moderada o intensa intermitente',
            'Light showers of ice pellets': 'Granizo ligero intermitente',
            'Moderate or heavy showers of ice pellets': 'Granizo moderado o intenso intermitente',
            'Patchy light rain with thunder': 'Lluvia ligera dispersa con truenos',
            'Moderate or heavy rain with thunder': 'Lluvia moderada o intensa con truenos',
            'Patchy light snow with thunder': 'Nieve ligera dispersa con truenos',
            'Moderate or heavy snow with thunder': 'Nieve moderada o intensa con truenos'
        }
        return translations.get(condition, condition)

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors."""
        logger.error(f"Error: {context.error}")
        
        try:
            if isinstance(context.error, telegram_error.BadRequest):
                if "Message is not modified" in str(context.error):
                    # Ignore this error - it happens when user clicks the same button multiple times
                    return
                
            # For any other error, send a message to the user
            error_message = "Lo siento, ha ocurrido un error. Por favor, intenta nuevamente."
            if update and update.effective_chat:
                if update.callback_query:
                    await update.callback_query.answer(error_message)
                else:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=error_message,
                        reply_markup=self.keyboard_handler.get_main_menu()
                    )
        except Exception as e:
            logger.error(f"Error in error handler: {e}")

def main():
    """Start the bot."""
    try:
        # Debug logging for environment variables
        logger.info("Checking environment variables...")
        if not TELEGRAM_TOKEN:
            logger.error("TELEGRAM_BOT_TOKEN is not set!")
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")
        if not WEATHER_API_KEY:
            logger.error("WEATHER_API_KEY is not set!")
            raise ValueError("WEATHER_API_KEY environment variable is not set")
        
        logger.info("Environment variables loaded successfully")
        
        # Create the bot instance
        weather_bot = WeatherBot()
        
        # Create the Application and pass it your bot's token
        application = Application.builder().token(TELEGRAM_TOKEN).build()

        # Add handlers
        application.add_handler(CommandHandler("start", weather_bot.start))
        application.add_handler(CallbackQueryHandler(weather_bot.button_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, weather_bot.handle_message))
        
        # Add error handler
        application.add_error_handler(weather_bot.error_handler)

        logger.info("Starting bot...")
        
        # Start the Bot with webhook (for Railway)
        if os.environ.get('RAILWAY_STATIC_URL'):
            railway_url = os.environ.get('RAILWAY_STATIC_URL')
            webhook_url = f"{railway_url}/{TELEGRAM_TOKEN}"
            logger.info(f"Starting webhook on Railway URL: {webhook_url}")
            
            # Start the webhook
            application.run_webhook(
                listen="0.0.0.0",
                port=int(os.environ.get('PORT', '8443')),
                url_path=TELEGRAM_TOKEN,
                webhook_url=webhook_url
            )
        else:
            # For local development
            logger.info("Starting polling mode for local development")
            application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
            
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise e

if __name__ == '__main__':
    main()
