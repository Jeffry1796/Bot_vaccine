from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import requests
from datetime import datetime
from dateutil.relativedelta import relativedelta
import re
from discord.ext import tasks

import os
import asyncio
import discord

class scrape_data_website:
    def __init__ (self, web_chrome,vaccine_dose,message_chat):
        """Initialization of chrome webdriver

        Parameter(s):
        -----------------
        web_chrome = chrome webdriver [format = '']
        vaccine_dose [format = string]
        message_chat [format = string]

        """
        self.driver = web_chrome
        self.dose = vaccine_dose
        self.message_parse = message_chat

    def open_new_website(self, driver_chrome, url, flag, status=False):
        """This function is used to determine whether the website can be accessed or not. If it can be accessed return True else False

        Parameter(s):
        -----------------
        driver_chrome = chrome webdriver [format = '']
        url = url website [format = str]
        flag = xpath from website [format = str]
        status = website current status (False) [format = boolean]

        Output:
        -----------------
        driver_chrome = chrome webdriver [format = '']
        status = True or False [format = boolean]

        """
        retry_connection = 0
        while True:
            try:
                driver_chrome.get(url)
                WebDriverWait(driver_chrome, 10).until(EC.presence_of_element_located((By.XPATH, flag)))
                status = True
                # print("URL: {} can be accessed".format(url))
                return (driver_chrome, status)
            except Exception as e:
                if retry_connection == 3:
                    print("URL: {} can't be accessed. End {}".format(url, '\n'))
                    return (driver_chrome, status)
                else:
                    print("URL: {} can't be accessed. Retry again".format(url))
                    retry_connection += 1
                    continue

    def scrape_data(self, iteration_loop = 10):
        """This function is used extract all available slot from the initial date up to 10 days from Hang Jabat website.

        Parameter(s):
        -----------------

        Output:
        -----------------
        list_data = dictionary contain with keys = date and value = available hours [format = dictionary]
        schedule_var = True or False [format = boolean]

        """
        i = 0
        list_data = {}
        schedule_var = 1

        datetime_object = datetime.strptime(self.message_parse, "%Y-%m-%d")

        while i < iteration_loop:
            url_hang_jabat = ''
            if self.dose == '!vaksin_1' or self.dose == 'first' or self.dose == '1':
                url_hang_jabat = 'https://widget.loket.com/widget/3kdkolxwjs53u4fh/'
            else:
                url_hang_jabat = 'https://widget.loket.com/widget/hangjebatvaksin2/'

            main_driver, status_connection = self.open_new_website(self.driver, url_hang_jabat, "//*[@id='main']/div[2]/div[3]//input[@value='Submit']")
            if status_connection:
                date_string = datetime_object+relativedelta(days=i)

                if date_string.strftime('%A') == 'Sunday':
                    iteration_loop+=1
                    i+=1
                    continue

                date_string = date_string.strftime('%Y-%m-%d')
                calender_input = main_driver.find_element_by_xpath('//*[@id="main"]/div[2]/div[3]//input[@id="arrival_date"]')
                calender_input.send_keys(date_string)

                calender_input.send_keys(Keys.ENTER)

                # IF NO VACCINATION SCHEDULE
                try:
                    main_driver.find_element_by_xpath('//*[@id="main"]/div[2]/div[@class="alert alert--red"]')
                    # print('No vaccination on this date. Please contact Kemenkes (119) for the detail')
                    schedule_var = 0
                    break
                except:
                    pass

                try:
                    WebDriverWait(main_driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="ticket_list"]/tbody')))
                except NoSuchElementException:
                    break

                list_tickets = main_driver.find_elements_by_xpath('//*[@id="ticket_list"]/tbody/tr')
                list_available_tickets = []

                for ticket in list_tickets:
                    try:
                        ticket.find_element_by_xpath('td[3]/select')
                        time = re.sub('jam', '', ticket.find_element_by_xpath('td[1]').text.split('\n')[0]).strip()
                        list_available_tickets.append(time)
                    except NoSuchElementException:
                        pass

                list_data[date_string] = list_available_tickets

                i += 1

            else:

                pass

        self.driver.quit()
        return (list_data,schedule_var)

class DoseNotCorrect(Exception):
    pass

class MyClient(discord.Client):
    """This function is to control Discord bot

    """

    async def create_response(self,message,list_scrape_result,status,message_response_date,vaccination):
        str_response,response_vacc = '',''
        if status == 0:

            if len(list_scrape_result) == 0:

                response_vacc = f"No vaccination schedule at {message_response_date} for the {vaccination}. Please contact Kemenkes (119) for the detail"
                await message.channel.send(response_vacc)

            else:

                for date in list_scrape_result.keys():
                    if len(list_scrape_result[date]) == 0:
                        str_response = str_response + 'There are no slots available at ' + date + '\n'
                    else:
                        str_response = str_response + 'There is/are ' + str(len(list_scrape_result[date])) + ' slots at ' + date + ' : ' + ', '.join(list_scrape_result[date]) + '\n'

                response_vacc = f"There is only {len(list_scrape_result)} scheduled dates from your initial date. Here is the available slots for the {vaccination} from Hang Jabat website 😁\n{str_response}"
                await message.channel.send(response_vacc)

        else:

            for date in list_scrape_result.keys():
                if len(list_scrape_result[date]) == 0:
                    str_response = str_response + 'There are no slots available at ' + date
                else:
                    str_response = str_response + 'There is/are ' + str(len(list_scrape_result[date])) + ' slots at ' + date + ' : ' + ', '.join(list_scrape_result[date]) + '\n'

            response_vacc = f"Here is the available slots for the {vaccination} from Hang Jabat website until 10 days later 😁\n{str_response}"
            await message.channel.send(response_vacc)

    async def background_task(self, username, message, date, dose):

        while True:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument("--window-size=1920x1080")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_experimental_option("useAutomationExtension", False)
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            driver_web = webdriver.Chrome(executable_path=os.environ.get('CHROMEDRIVER_PATH'), options=chrome_options)
            list_scrape_result,status = scrape_data_website(driver_web,dose,date).scrape_data()

            dose_str = ''
            if dose == 'first' or dose == '1':
                dose_str = 'first dose'
            else:
                dose_str = 'second dose'

            task_response = client.loop.create_task(self.create_response(message,list_scrape_result,status,date,dose_str))
            await asyncio.sleep(7)
            task_response.cancel()

            await asyncio.sleep(900)

    async def on_ready(self):
        response_ready = f"Bot is online. Send '!help' for the list of command. This bot will find available slots up to 10 days from your initial date"
        self.status_schedule = True
        await client.get_channel(id=761179509763473408).send(response_ready)

    async def on_message(self,message):
        username = str(message.author).split('#')[0]
        message_chat = str(message.content)

        if message.author == client.user:
            return

        if message_chat.lower() == '!vaksin_2' or message_chat.lower() == '!vaksin_1':
            response = f"Hi {username}, when do you plan to get vaccination? (Please enter the date using this format e.g 2021-10-05)"
            await message.channel.send(response)

            try:
                message_response = await client.wait_for("message", check=lambda x:x.content, timeout=20.0)
                message_response_date = message_response.content

                # CHECK DATE format
                datetime.strptime(message_response_date, "%Y-%m-%d")

                vaccination = ''
                if message_chat.lower() == '!vaksin_1':
                    vaccination = 'first dose'
                else:
                    vaccination = 'second dose'

                response = f"You plan to do vacctionation at {message_response_date}. The bot will find the available slots"
                await message.channel.send(response)

                chrome_options = webdriver.ChromeOptions()
                chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument("--window-size=1920x1080")
                chrome_options.add_argument("--disable-notifications")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--start-maximized")
                chrome_options.add_experimental_option("useAutomationExtension", False)
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                driver_web = webdriver.Chrome(executable_path=os.environ.get('CHROMEDRIVER_PATH'), options=chrome_options)
                list_scrape_result,status = scrape_data_website(driver_web,message_chat.lower(),message_response_date).scrape_data()

                task_response = client.loop.create_task(self.create_response(message,list_scrape_result,status,message_response_date,vaccination))
                await asyncio.sleep(7)
                task_response.cancel()

            except asyncio.TimeoutError:
                response = f"Hi {username}, please register again to find available slots"
                await message.channel.send(response)

            except ValueError:
                response = f"Hi {username}, your date format is wrong"
                await message.channel.send(response)

        elif message_chat.lower() == '!enable_schedule':
            try:
                response = f"Hi {username}, first or second dose?"
                await message.channel.send(response)

                message_response = await client.wait_for("message", check=lambda x:x.content, timeout=20.0)
                message_response_dose = message_response.content.lower()

                message_response_date = datetime.now().strftime('%Y-%m-%d')

                if ('first' in message_response_dose or message_response_dose == '1') and self.status_schedule:

                    response = f"Scheduler for the first dose has been enabled. You will be informed every 15 minutes"
                    await message.channel.send(response)

                    self.status_schedule = False

                    self.task = client.loop.create_task(self.background_task(username,message,message_response_date,message_response_dose))

                elif ('second' in message_response_dose or message_response_dose == '2') and self.status_schedule:

                    response = f"Scheduler for the second dose has been enabled. You will be informed every 15 minutes"
                    await message.channel.send(response)

                    self.status_schedule = False

                    self.task = client.loop.create_task(self.background_task(username,message,message_response_date,message_response_dose))
                elif self.status_schedule == False:
                    response = f"Please stop your current scheduler to activate it"
                    await message.channel.send(response)
                else:
                    raise DoseNotCorrect

            except asyncio.TimeoutError:
                response = f"Hi {username}, please register again to find available slots"
                await message.channel.send(response)

            except DoseNotCorrect:
                response = f"Hi {username}, there is no such dose. Please register again"
                await message.channel.send(response)

        elif message_chat.lower() == '!disable_schedule':
            try:
                self.task.cancel()
                self.status_schedule = True
                response = f"Hi {username}, scheduler will be disabled"
                await message.channel.send(response)
            except AttributeError:
                response = f"Please enable the scheduler first"
                await message.channel.send(response)

        elif message_chat.lower() == '!help':
            response_help = \
            f"""
            Hi {username}, here is some command in this bot: \n1. !vaksin_1 (for first dose vacctionation) \n2. !vaksin_2 (for second dose vaccination) \n3. !enable_schedule \n4. !disable_schedule
            """

            await message.channel.send(response_help)

TOKEN = os.environ.get('TOKEN')
client = MyClient()
client.run(TOKEN)