# Bot_vaccine
This bot is used to know when the available slot for vaccination (first or second dose) is ready. The bot will scrape all of the slots from Hang Jebat Kemenkes (which is currently collaborating with loket.com) from the initial date (you can define it by yourself) until 10 days later. The bot is connected to the discord server to make it more easily to use.

## Deploy the bot
Currently, I am using Heroku platform. To deploy it:
1. Connect your current repo app with Heroku
2. Set 'heroku ps:scale worker=1 -a xxxxxx'. xxxxx = your app name

## Buildpack
- https://github.com/heroku/heroku-buildpack-google-chrome for google chrome
- https://github.com/heroku/heroku-buildpack-chromedriver for chromedriver
- TOKEN. Your discord channel token

## Configuration Variables
- CHROMEDRIVER_PATH = /app/.chromedriver/bin/chromedriver
- GOOGLE_CHROME_BIN = /app/.apt/usr/bin/google-chrome
