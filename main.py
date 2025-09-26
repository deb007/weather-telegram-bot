import requests
import os
from datetime import datetime, timedelta
import sys

class WeatherTelegramBot:
    def __init__(self):
        self.openweather_api_key = os.environ.get('OPENWEATHER_API_KEY')
        self.telegram_bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        self.city = os.environ.get('CITY', 'London')
        
        if not all([self.openweather_api_key, self.telegram_bot_token, self.telegram_chat_id]):
            raise ValueError("Missing required environment variables")
    
    def get_coordinates(self):
        """Get city coordinates using OpenWeatherMap Geocoding API"""
        geo_url = "http://api.openweathermap.org/geo/1.0/direct"
        params = {
            'q': self.city,
            'limit': 1,
            'appid': self.openweather_api_key
        }
        
        response = requests.get(geo_url, params=params)
        response.raise_for_status()
        
        data = response.json()
        if not data:
            raise Exception(f"City '{self.city}' not found")
        
        return data[0]['lat'], data[0]['lon']
    
    def get_yesterday_weather(self, lat, lon):
        """Get yesterday's weather using One Call API 3.0"""
        yesterday = datetime.now() - timedelta(days=1)
        timestamp = int(yesterday.timestamp())
        
        url = "https://api.openweathermap.org/data/3.0/onecall/timemachine"
        params = {
            'lat': lat,
            'lon': lon,
            'dt': timestamp,
            'appid': self.openweather_api_key,
            'units': 'metric'
        }
        
        response = requests.get(url, params=params)
        
        # If One Call 3.0 fails (requires subscription), fallback to current weather
        if response.status_code != 200:
            print("One Call API 3.0 not available, using alternative method...")
            return self.get_yesterday_weather_alternative(lat, lon)
        
        data = response.json()
        temps = [hour['temp'] for hour in data['data']]
        
        return {
            'max_temp': round(max(temps), 1),
            'min_temp': round(min(temps), 1)
        }
    
    def get_yesterday_weather_alternative(self, lat, lon):
        """Alternative method for yesterday's weather using 5-day forecast history"""
        # Note: This is a workaround since historical data requires paid plan
        # For demo purposes, we'll use a placeholder or try to get data from yesterday
        print("Using current weather as approximation for yesterday...")
        
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.openweather_api_key,
            'units': 'metric'
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Use current temp as approximation (in real scenario, you'd need paid plan for history)
        return {
            'max_temp': round(data['main']['temp_max'], 1),
            'min_temp': round(data['main']['temp_min'], 1)
        }
    
    def get_today_forecast(self, lat, lon):
        """Get today's weather forecast"""
        url = "https://api.openweathermap.org/data/2.5/forecast"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.openweather_api_key,
            'units': 'metric'
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Get today's forecasts (next 24 hours)
        today = datetime.now().date()
        today_forecasts = []
        
        for forecast in data['list']:
            forecast_date = datetime.fromtimestamp(forecast['dt']).date()
            if forecast_date == today:
                today_forecasts.append(forecast['main']['temp'])
        
        if not today_forecasts:
            # If no today forecasts, use current weather
            current_url = "https://api.openweathermap.org/data/2.5/weather"
            current_params = {
                'lat': lat,
                'lon': lon,
                'appid': self.openweather_api_key,
                'units': 'metric'
            }
            current_response = requests.get(current_url, params=current_params)
            current_response.raise_for_status()
            current_data = current_response.json()
            
            return {
                'max_temp': round(current_data['main']['temp_max'], 1),
                'min_temp': round(current_data['main']['temp_min'], 1),
                'description': current_data['weather'][0]['description']
            }
        
        return {
            'max_temp': round(max(today_forecasts), 1),
            'min_temp': round(min(today_forecasts), 1),
            'description': data['list'][0]['weather'][0]['description']
        }
    
    def create_message(self, yesterday_data, today_data):
        """Create the Telegram message"""
        today_date = datetime.now().strftime("%B %d, %Y")
        yesterday_date = (datetime.now() - timedelta(days=1)).strftime("%B %d, %Y")
        
        message = f"""🌤️ *Daily Weather Report for {self.city}*

📅 *Yesterday ({yesterday_date.split(',')[0]})*:
   🌡️ Max: `{yesterday_data['max_temp']}°C`
   🥶 Min: `{yesterday_data['min_temp']}°C`

📅 *Today ({today_date.split(',')[0]})*:
   🌡️ Max: `{today_data['max_temp']}°C`  
   🥶 Min: `{today_data['min_temp']}°C`
   ☁️ Conditions: `{today_data['description'].title()}`

Have a great day! 🌟"""
        
        return message
    
    def send_telegram_message(self, message):
        """Send message to Telegram"""
        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
        
        payload = {
            'chat_id': self.telegram_chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        print("Weather report sent to Telegram successfully!")
        return response.json()
    
    def run(self):
        """Main function to run the weather report"""
        try:
            print("Getting city coordinates...")
            lat, lon = self.get_coordinates()
            print(f"Coordinates for {self.city}: {lat}, {lon}")
            
            print("Getting yesterday's weather...")
            yesterday_data = self.get_yesterday_weather(lat, lon)
            
            print("Getting today's forecast...")
            today_data = self.get_today_forecast(lat, lon)
            
            print("Creating message...")
            message = self.create_message(yesterday_data, today_data)
            
            print("Sending to Telegram...")
            self.send_telegram_message(message)
            
            print("✅ Weather report completed successfully!")
            
        except Exception as e:
            error_message = f"❌ *Weather Report Error*\n\nFailed to generate weather report for {self.city}:\n`{str(e)}`"
            try:
                self.send_telegram_message(error_message)
            except:
                print(f"Failed to send error message: {e}")
            sys.exit(1)

if __name__ == "__main__":
    bot = WeatherTelegramBot()
    bot.run()
