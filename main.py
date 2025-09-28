import requests
import os
from datetime import datetime, timedelta
import sys
import json
import pytz
from weather_providers.factory import WeatherProviderFactory

class WeatherTelegramBot:
    def __init__(self):
        self.openweather_api_key = os.environ.get('OPENWEATHER_API_KEY')
        self.telegram_bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        self.city = os.environ.get('CITY', 'London')
        self.user_timezone = os.environ.get('USER_TIMEZONE', 'UTC')
        self.report_type = os.environ.get('REPORT_TYPE', 'auto')  # 'morning', 'evening', or 'auto'
        self.weather_provider_name = os.environ.get('WEATHER_PROVIDER', 'openweathermap').lower()
        
        # Initialize timezone
        try:
            self.timezone = pytz.timezone(self.user_timezone)
        except pytz.UnknownTimeZoneError:
            print(f"Warning: Unknown timezone '{self.user_timezone}', using UTC instead")
            self.timezone = pytz.UTC
            self.user_timezone = 'UTC'
        
        # Validate required environment variables based on provider
        if not all([self.telegram_bot_token, self.telegram_chat_id]):
            raise ValueError("Missing required environment variables: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID")
        
        # Create weather provider instance
        api_key = self.openweather_api_key if self.weather_provider_name == 'openweathermap' else None
        if self.weather_provider_name == 'openweathermap' and not api_key:
            raise ValueError("OPENWEATHER_API_KEY is required when using OpenWeatherMap provider")
        
        try:
            self.weather_provider = WeatherProviderFactory.create_provider(self.weather_provider_name, api_key)
        except ValueError as e:
            raise ValueError(f"Weather provider error: {e}")
    
    def get_user_current_time(self):
        """Get current time in user's timezone"""
        utc_now = datetime.now(pytz.UTC)
        return utc_now.astimezone(self.timezone)
    
    def determine_report_type(self):
        """Determine if it should be morning or evening report based on user's current time"""
        if self.report_type.lower() != 'auto':
            return self.report_type.lower()
        
        user_time = self.get_user_current_time()
        current_hour = user_time.hour
        
        # Morning report: 5 AM to 12 PM (5-11)
        # Evening report: 5 PM to 11 PM (17-23)
        # Default to morning for other times
        if 17 <= current_hour <= 23:
            return 'evening'
        else:
            return 'morning'
    
    def get_coordinates(self):
        """Get city coordinates using the configured weather provider"""
        return self.weather_provider.get_coordinates(self.city)
    
    def get_today_forecast(self, lat, lon):
        """Get today's forecast using the configured weather provider"""
        return self.weather_provider.get_today_forecast(lat, lon)
    
    def get_today_actual_temps(self):
        """Get actual temperatures recorded today (evening report)"""
        # Read stored temperature data from throughout the day
        temp_data = self.read_temp_storage()
        
        # Get current temperature and add to our records
        lat, lon = self.get_coordinates()
        current_data = self.weather_provider.get_current_weather(lat, lon)
        
        current_temp = round(current_data['temp'], 1)
        user_time = self.get_user_current_time()
        current_time = user_time.strftime('%H:%M')
        
        # Add current reading to our data
        today_str = user_time.strftime('%Y-%m-%d')
        if today_str not in temp_data:
            temp_data[today_str] = []
        
        temp_data[today_str].append({
            'time': current_time,
            'temp': current_temp,
            'description': current_data['description']
        })
        
        # Save updated data
        self.save_temp_storage(temp_data)
        
        # Calculate actual max/min from today's readings
        today_readings = temp_data.get(today_str, [])
        if today_readings:
            temps = [reading['temp'] for reading in today_readings]
            return {
                'actual_max': round(max(temps), 1),
                'actual_min': round(min(temps), 1),
                'current_temp': current_temp,
                'total_readings': len(today_readings),
                'first_reading': today_readings[0]['time'],
                'last_reading': today_readings[-1]['time'],
                'description': current_data['description']
            }
        else:
            return {
                'actual_max': current_temp,
                'actual_min': current_temp,
                'current_temp': current_temp,
                'total_readings': 1,
                'first_reading': current_time,
                'last_reading': current_time,
                'description': current_data['description']
            }
    
    def read_temp_storage(self):
        """Read temperature storage file"""
        try:
            if os.path.exists('temp_readings.json'):
                with open('temp_readings.json', 'r') as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def save_temp_storage(self, data):
        """Save temperature data to storage file"""
        try:
            # Keep only last 7 days of data to avoid file getting too large
            user_time = self.get_user_current_time()
            cutoff_date = (user_time - timedelta(days=7)).strftime('%Y-%m-%d')
            filtered_data = {
                date: readings for date, readings in data.items() 
                if date >= cutoff_date
            }
            
            with open('temp_readings.json', 'w') as f:
                json.dump(filtered_data, f, indent=2)
        except Exception as e:
            print(f"Could not save temperature data: {e}")
    
    def create_morning_message(self, forecast_data):
        """Create morning forecast message"""
        user_time = self.get_user_current_time()
        today_date = user_time.strftime("%B %d, %Y")
        timezone_name = self.user_timezone
        
        message = f"""🌅 *Good Morning! Today's Weather Forecast*
📍 *{self.city}* - {today_date} ({timezone_name})

🌡️ **Temperature Forecast:**
   📈 Max: `{forecast_data['forecasted_max']}°C`
   📉 Min: `{forecast_data['forecasted_min']}°C`
   🌡️ Current: `{forecast_data['current_temp']}°C`

☁️ **Conditions:** `{forecast_data['description'].title()}`"""

        if forecast_data['detailed_forecast']:
            message += "\n\n⏰ **Hourly Forecast:**"
            for forecast in forecast_data['detailed_forecast']:
                message += f"\n   `{forecast['time']}` - {forecast['temp']}°C ({forecast['description']})"
        
        message += "\n\nHave a great day! 🌟"
        return message
    
    def create_evening_message(self, actual_data):
        """Create evening actual temperature report"""
        user_time = self.get_user_current_time()
        today_date = user_time.strftime("%B %d, %Y")
        timezone_name = self.user_timezone
        
        message = f"""🌆 *Evening Weather Summary*
📍 *{self.city}* - {today_date} ({timezone_name})

🌡️ **Today's Actual Temperatures:**
   📈 Max: `{actual_data['actual_max']}°C`
   📉 Min: `{actual_data['actual_min']}°C`
   🌡️ Current: `{actual_data['current_temp']}°C`

☁️ **Current Conditions:** `{actual_data['description'].title()}`

📊 **Data Summary:**
   📋 Total readings: {actual_data['total_readings']}
   ⏰ First reading: {actual_data['first_reading']}
   ⏰ Last reading: {actual_data['last_reading']}

Sleep well! 😴"""
        return message
    
    def get_comparison_message(self, actual_data):
        """Get comparison with morning forecast if available"""
        try:
            if os.path.exists('morning_forecast.json'):
                with open('morning_forecast.json', 'r') as f:
                    forecast_data = json.load(f)
                
                user_time = self.get_user_current_time()
                today_str = user_time.strftime('%Y-%m-%d')
                if today_str in forecast_data:
                    morning_forecast = forecast_data[today_str]
                    
                    max_diff = actual_data['actual_max'] - morning_forecast['forecasted_max']
                    min_diff = actual_data['actual_min'] - morning_forecast['forecasted_min']
                    
                    comparison = f"\n\n📊 **Forecast vs Actual:**"
                    comparison += f"\n   Max: Predicted `{morning_forecast['forecasted_max']}°C`, Actual `{actual_data['actual_max']}°C` "
                    comparison += f"({'📈+' if max_diff > 0 else '📉'}{max_diff:+.1f}°C)"
                    comparison += f"\n   Min: Predicted `{morning_forecast['forecasted_min']}°C`, Actual `{actual_data['actual_min']}°C` "
                    comparison += f"({'📈+' if min_diff > 0 else '📉'}{min_diff:+.1f}°C)"
                    
                    return comparison
        except:
            pass
        return ""
    
    def save_morning_forecast(self, forecast_data):
        """Save morning forecast for evening comparison"""
        try:
            data = {}
            if os.path.exists('morning_forecast.json'):
                with open('morning_forecast.json', 'r') as f:
                    data = json.load(f)
            
            user_time = self.get_user_current_time()
            today_str = user_time.strftime('%Y-%m-%d')
            data[today_str] = forecast_data
            
            # Keep only last 7 days
            cutoff_date = (user_time - timedelta(days=7)).strftime('%Y-%m-%d')
            data = {date: forecast for date, forecast in data.items() if date >= cutoff_date}
            
            with open('morning_forecast.json', 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Could not save forecast data: {e}")
    
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
    
    def run_morning_report(self):
        """Run morning forecast report"""
        try:
            print("Getting city coordinates...")
            lat, lon = self.get_coordinates()
            print(f"Coordinates for {self.city}: {lat}, {lon}")
            
            print("Getting today's forecast...")
            forecast_data = self.get_today_forecast(lat, lon)
            
            print("Saving forecast for evening comparison...")
            self.save_morning_forecast(forecast_data)
            
            print("Creating morning message...")
            message = self.create_morning_message(forecast_data)
            
            print("Sending morning report to Telegram...")
            self.send_telegram_message(message)
            
            print("✅ Morning weather report completed successfully!")
            
        except Exception as e:
            error_message = f"❌ *Morning Weather Report Error*\n\nFailed to generate morning report for {self.city}:\n`{str(e)}`"
            try:
                self.send_telegram_message(error_message)
            except:
                print(f"Failed to send error message: {e}")
            sys.exit(1)
    
    def run_evening_report(self):
        """Run evening actual temperature report"""
        try:
            print("Getting today's actual temperatures...")
            actual_data = self.get_today_actual_temps()
            
            print("Creating evening message...")
            message = self.create_evening_message(actual_data)
            
            # Add comparison with morning forecast
            comparison = self.get_comparison_message(actual_data)
            message += comparison
            
            print("Sending evening report to Telegram...")
            self.send_telegram_message(message)
            
            print("✅ Evening weather report completed successfully!")
            
        except Exception as e:
            error_message = f"❌ *Evening Weather Report Error*\n\nFailed to generate evening report for {self.city}:\n`{str(e)}`"
            try:
                self.send_telegram_message(error_message)
            except:
                print(f"Failed to send error message: {e}")
            sys.exit(1)
    
    def run(self):
        """Main function - decides whether to run morning or evening report"""
        actual_report_type = self.determine_report_type()
        user_time = self.get_user_current_time()
        
        print(f"User timezone: {self.user_timezone}")
        print(f"User local time: {user_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"Report type setting: {self.report_type}")
        print(f"Determined report type: {actual_report_type}")
        
        if actual_report_type == 'evening':
            self.run_evening_report()
        else:
            self.run_morning_report()

if __name__ == "__main__":
    bot = WeatherTelegramBot()
    bot.run()
