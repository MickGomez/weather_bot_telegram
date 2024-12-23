# Weather Chatbot

A Telegram-based weather bot that provides weather forecasts and personalized weather alerts.

## Features

- Get current weather information
- View 3-day weather forecasts
- Set location preferences
- Receive personalized temperature alerts
- Daily weather notifications
- Multiple language support (English/Spanish)
- Temperature unit conversion (Celsius/Fahrenheit)
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

## Deployment on Railway

1. Create a Railway account at https://railway.app
2. Install Railway CLI (optional)
3. Create a new project in Railway
4. Set up environment variables in Railway dashboard:
   - `TELEGRAM_BOT_TOKEN`
   - `WEATHER_API_KEY`
5. Deploy using one of these methods:
   
   **Option 1 - Using GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   # Create a GitHub repository and push to it
   git remote add origin your-github-repo-url
   git push -u origin main
   ```
   Then connect your GitHub repository in Railway dashboard.

   **Option 2 - Using Railway CLI:**
   ```bash
   railway login
   railway init
   railway up
   ```



## Features and Error Handling

- **Interactive Menu System**
  - Main menu with weather, forecast, and settings options
  - Settings menu for location, units, and language preferences
  - Alert configuration menu

- **Error Handling**
  - Invalid user inputs
  - API request failures
  - Invalid location queries
  - Network connectivity issues
  - Duplicate button click handling
  - Message modification errors

- **Data Persistence**
  - User preferences storage
  - Weather data caching
  - Session state management

## Project Structure

```
weather_chatbot/
├── weather_bot.py        # Main bot logic
├── requirements.txt      # Python dependencies
├── .env                 # Environment variables
├── .env.example         # Example environment file
├── utils/
│   └── keyboard_handler.py  # Keyboard layouts
├── models/
│   ├── user_preferences.py  # User settings
│   └── weather_cache.py     # Weather data cache
├── data/                # Data storage
└── logs/                # Log files
```
<<<<<<< HEAD

=======
>>>>>>> bb5b8717857bdf1e673f5c799d414b8fd8954561
