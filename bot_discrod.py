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

import os
import asyncio
import discord

class scrape_data_website:
    def __init__ (self, web_chrome,message_chat):
        """Initialization of chrome webdriver

        Parameter(s):
        -----------------
        web_chrome = chrome webdriver [format = '']

        """
        self.driver = web_chrome
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

    def scrape_data(self):
        i = 0
        list_data = {}
        iteration_loop = 10

        datetime_object = datetime.strptime(self.message_parse, "%Y-%m-%d")

        while i < iteration_loop:
            main_driver, status_connection = self.open_new_website(self.driver, 'https://widget.loket.com/widget/hangjebatvaksin2/', "//*[@id='main']/div[2]/div[3]//input[@value='Submit']")
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
                    print('No vaccination on this date. Please contact Kemenkes (119) for the detail')
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
        return list_data

class MyClient(discord.Client):

    async def on_ready(self):
        print(f'{client.user} has connected to Discord!')

    async def on_message(self,message):
        username = str(message.author).split('#')[0]
        message_chat = str(message.content)

        if message.author == client.user:
            return

        if message_chat.lower() == '!vaksin_2':
            response = f"Hai {username}, kapan anda mau vaksinasi? (Masukkan tanggal estimasi anda. Misal: 2021-10-05)"
            await message.channel.send(response)

            try:
                message_response = await client.wait_for("message", check=lambda x:x.content, timeout=20.0)
                message_response_date = message_response.content

                # CHECK DATE format
                datetime.strptime(message_response_date, "%Y-%m-%d")

                response = f"Anda rencana vaksin tanggal {message_response_date}. Akan bot carikan slotnya"
                await message.channel.send(response)

                # chrome_options = webdriver.ChromeOptions()
                # chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
                # chrome_options.add_argument('--headless')
                # chrome_options.add_argument('--no-sandbox')
                # chrome_options.add_argument('--disable-dev-shm-usage')
                # chrome_options.add_argument("--window-size=1920x1080")
                # chrome_options.add_argument("--disable-notifications")
                # chrome_options.add_argument("--disable-gpu")
                # chrome_options.add_argument("--start-maximized")
                # chrome_options.add_experimental_option("useAutomationExtension", False)
                # chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                # driver_web = webdriver.Chrome(executable_path=os.environ.get('CHROMEDRIVER_PATH'), options=chrome_options)
                # list_scrape_result = scrape_data_website(driver_web,message_response_date).scrape_data()

                # str_response = ''
                # if len(list_scrape_result) == 0:
                #     response_vacc = f"Vaksinasi dari tanggal {message_response_date} sampai 10 hari ke depan sudah penuh"
                #     await message.channel.send(response_vacc)
                # else:
                #     for date in list_scrape_result.keys():
                #         if len(list_scrape_result[date]) == 0:
                #             str_response = str_response + 'Slot sudah penuh untuk hari ini'
                #         else:
                #             str_response = str_response + 'Ada ' + str(len(list_scrape_result[date])) + ' slot di tanggal ' + date + ' : ' + ', '.join(list_scrape_result[date]) + '\n'

                #     response_vacc = f"Berikut hasil pencarian bot dari situs Hang Jabat sampai 10 hari kedepan 😁\n{str_response}"
                #     await message.channel.send(response_vacc)

            except asyncio.TimeoutError:
                response = f"{username} silahkan mencari ulang"
                await message.channel.send(response)

            except ValueError:
                response = f"Format tanggal yang {username} masukkan salah"
                await message.channel.send(response)

            # msg = await bot.wait_for("message", check=check)
        elif message_chat.lower() == '!help':
            response = \
            f"""
            Hi {username}, silahkan pilih command yang dibutuhkan: \n1. !vaksin_1 (untuk vaksin pertama) \n2. !vaksin_2 (untuk vaksin kedua)
            """

            await message.channel.send(response)
            return

TOKEN = os.environ.get('TOKEN')
client = MyClient()
client.run(TOKEN)