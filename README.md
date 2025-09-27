# Weather Telegram Bot 🌤️

A Python-based weather bot that sends automated daily weather reports to your Telegram chat. The bot provides both morning forecasts and evening actual temperature summaries with forecast accuracy comparisons.

## Features ✨

- **🌅 Morning Reports**: Daily weather forecasts with hourly breakdowns
- **🌆 Evening Reports**: Actual temperature summaries with forecast vs actual comparisons
- **📊 Data Tracking**: Stores temperature readings throughout the day for accurate reporting
- **🔄 Automated Scheduling**: Runs automatically using GitHub Actions
- **🌍 Global Coverage**: Supports any city worldwide via OpenWeatherMap API
- **📱 Telegram Integration**: Sends formatted reports directly to your Telegram chat

## Prerequisites 📋

Before setting up this bot, you'll need:

1. **GitHub Account** - To fork and run the repository
2. **OpenWeatherMap API Key** - For weather data ([Get it here](https://openweathermap.org/api))
3. **Telegram Bot Token** - For sending messages ([Create bot with @BotFather](https://t.me/botfather))
4. **Telegram Chat ID** - Where to send the reports

## Quick Setup Guide 🚀

### 1. Fork and Clone the Repository

1. **Fork this repository** to your GitHub account
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/weather-telegram-bot.git
   cd weather-telegram-bot
   ```

### 2. Get Required API Keys and IDs

#### OpenWeatherMap API Key
1. Visit [OpenWeatherMap](https://openweathermap.org/api)
2. Sign up for a free account
3. Go to API Keys section and copy your API key

#### Telegram Bot Token
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow the instructions
3. Copy the bot token provided

#### Telegram Chat ID
1. Start a chat with your bot
2. Send any message to your bot
3. Visit: `https://api.telegram.org/bot<YourBOTToken>/getUpdates`
4. Look for `"chat":{"id":` in the response - this is your chat ID

### 3. Configure GitHub Secrets

In your forked repository on GitHub:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** and add each of the following:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `OPENWEATHER_API_KEY` | Your OpenWeatherMap API key | `abcd1234efgh5678` |
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token | `123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11` |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID | `123456789` |
| `CITY` | City name for weather reports | `London` or `New York` |

### 4. Enable GitHub Actions

1. Go to the **Actions** tab in your repository
2. Click **"I understand my workflows, go ahead and enable them"**
3. The bot will now run automatically:
   - **Morning reports**: 8:00 AM UTC daily
   - **Evening reports**: 8:00 PM UTC daily

## Manual Testing 🧪

You can manually trigger the bot to test your setup:

1. Go to **Actions** tab in your repository
2. Click on **"Daily Weather Reports"** workflow
3. Click **"Run workflow"** button
4. Choose **morning** or **evening** report type
5. Click **"Run workflow"**

## Local Development 💻

To run the bot locally for testing:

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables**:
   ```bash
   export OPENWEATHER_API_KEY="your_api_key"
   export TELEGRAM_BOT_TOKEN="your_bot_token"
   export TELEGRAM_CHAT_ID="your_chat_id"
   export CITY="your_city"
   export REPORT_TYPE="morning"  # or "evening"
   ```

3. **Run the bot**:
   ```bash
   python main.py
   ```

## Configuration Options ⚙️

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENWEATHER_API_KEY` | ✅ Yes | - | OpenWeatherMap API key |
| `TELEGRAM_BOT_TOKEN` | ✅ Yes | - | Telegram bot token |
| `TELEGRAM_CHAT_ID` | ✅ Yes | - | Telegram chat ID for reports |
| `CITY` | ❌ No | `London` | City name for weather reports |
| `REPORT_TYPE` | ❌ No | `morning` | Report type: `morning` or `evening` |

### Customizing Schedule

To change when reports are sent, edit `.github/workflows/weather.yml`:

```yaml
on:
  schedule:
    - cron: '0 8 * * *'   # Morning report at 8:00 AM UTC
    - cron: '0 20 * * *'  # Evening report at 8:00 PM UTC
```

Use [crontab.guru](https://crontab.guru/) to generate custom cron expressions.

## Sample Output 📱

### Morning Report
```
🌅 Good Morning! Today's Weather Forecast
📍 London - December 15, 2023

🌡️ Temperature Forecast:
   📈 Max: 12.5°C
   📉 Min: 8.2°C
   🌡️ Current: 10.1°C

☁️ Conditions: Partly Cloudy

⏰ Hourly Forecast:
   09:00 - 10.5°C (partly cloudy)
   12:00 - 11.8°C (overcast)
   15:00 - 12.5°C (light rain)
   18:00 - 11.2°C (cloudy)

Have a great day! 🌟
```

### Evening Report
```
🌆 Evening Weather Summary
📍 London - December 15, 2023

🌡️ Today's Actual Temperatures:
   📈 Max: 13.1°C
   📉 Min: 7.9°C
   🌡️ Current: 9.8°C

☁️ Current Conditions: Clear Sky

📊 Data Summary:
   📋 Total readings: 12
   ⏰ First reading: 08:15
   ⏰ Last reading: 20:00

📊 Forecast vs Actual:
   Max: Predicted 12.5°C, Actual 13.1°C (📈+0.6°C)
   Min: Predicted 8.2°C, Actual 7.9°C (📉-0.3°C)

Sleep well! 😴
```

## Troubleshooting 🔧

### Common Issues

**Bot not sending messages:**
- Check that all GitHub Secrets are correctly set
- Verify your Telegram bot token is valid
- Ensure the chat ID is correct (try the method in setup guide)
- Check GitHub Actions logs for error details

**Weather data not loading:**
- Verify OpenWeatherMap API key is valid and active
- Check if city name is spelled correctly
- Ensure you haven't exceeded API rate limits (1000 calls/day for free tier)

**GitHub Actions not running:**
- Make sure GitHub Actions are enabled in your repository
- Check that the workflow file syntax is correct
- Verify repository secrets are set up properly

### Getting Help

1. **Check GitHub Actions logs**: Go to Actions tab → Failed workflow → View logs
2. **Validate API keys**: Test them manually with curl or API testing tools
3. **Test locally**: Run the bot locally to debug issues
4. **Check rate limits**: Ensure you're not exceeding API quotas

## Data Storage 💾

The bot stores two types of data files in the repository:

- **`temp_readings.json`**: Temperature readings throughout the day
- **`morning_forecast.json`**: Morning forecasts for evening comparison

These files are automatically managed by the bot and committed back to the repository.

## Contributing 🤝

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and test them
4. **Commit your changes**: `git commit -m 'Add amazing feature'`
5. **Push to the branch**: `git push origin feature/amazing-feature`
6. **Open a Pull Request**

### Development Guidelines

- Follow Python PEP 8 style guidelines
- Add comments for complex logic
- Test your changes with different cities and weather conditions
- Update documentation if you add new features

## License 📄

This project is open source and available under the [MIT License](LICENSE).

## Acknowledgments 🙏

- [OpenWeatherMap](https://openweathermap.org/) for weather data API
- [Telegram Bot API](https://core.telegram.org/bots/api) for messaging capabilities
- [GitHub Actions](https://github.com/features/actions) for automation

---

**Happy Weather Tracking!** 🌈

If you find this bot useful, please ⭐ star the repository and share it with others!