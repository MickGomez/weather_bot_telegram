# Weather Chatbot

A Telegram-based weather bot that provides weather forecasts and personalized weather alerts.

## Features

- Get current weather information
- View 3-day weather forecasts
- Set location preferences
- Receive personalized temperature alerts
- Simple and intuitive command interface

## Prerequisites

- Python 3.7+
- Telegram Bot Token (from @BotFather)
- WeatherAPI API Key (from weatherapi.com)

## Setup

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with the following content:
   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   WEATHER_API_KEY=your_weatherapi_key
   ```

4. Run the bot:
   ```
   python weather_bot.py
   ```

## Available Commands

- `/start` - Start the bot and see available commands
- `/help` - Show help message
- `/setlocation [city]` - Set your location
- `/weather` - Get current weather
- `/forecast` - Get 3-day forecast
- `/setalert [temp_min] [temp_max]` - Set temperature alerts

## Error Handling

The bot includes comprehensive error handling for:
- Invalid user inputs
- API request failures
- Invalid location queries
- Network connectivity issues
