# -*- coding: utf-8 -*-

import os
import re
import pandas as pd
import telegram_bot
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from multiprocessing import Pool
import threading
from datetime import datetime
import time
import warnings
import logging
from useragent import chose_agent
import json


DF_PATH = 'cache\\data.csv'
CATEGORIES = os.listdir(f'{os.getcwd()}\\new_links')
COLUMNS = ['title', 'price', 'link']
EXC_WORDS = []
LAST_TITLE = ""

logging.basicConfig(
    filename='errors.log',
    filemode='a',
    level=logging.ERROR,
)

class ParserBeru:
    def __init__(self, category):
        self.category = category

        """ Chromium """
        self.options = webdriver.ChromeOptions()
        self.options.add_argument("--headless")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("start-maximized")
        self.options.add_argument("--disable-infobars")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-browser-side-navigation")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument(f'user-agent={chose_agent()}')
        self.options.add_argument("--enable-automation")
        self.browser = webdriver.Chrome(chrome_options=self.options)

        # """ Firefox """
        # fireFoxOptions = webdriver.FirefoxOptions()
        # fireFoxOptions.add_argument('-profile')
        # fireFoxOptions.add_argument(r'C:\Users\andrey\AppData\Roaming\Mozilla\Firefox\Profiles\5qxitw65.10579')
        # fireFoxOptions.headless = True
        # self.driver = webdriver.Firefox(firefox_options=fireFoxOptions,
        #                                 executable_path=r'C:\WebDrivers\geckodriver.exe',
        #                                 service_args=["--marionette-port", "2828"])


    def run(self):
        URLS = [line.rstrip('\n') for line in open(f'{os.getcwd()}\\new_links\\{self.category}', 'r')]
        while True:
            process = self.category.split('/')[-1]
            print(f"Process: {process} | {datetime.now()}")
            df_loaded = self.load_df()
            for url in URLS:
                self.browser.get(url)
                self.parse_page(df_loaded, url)


    def load_df(self):
        load_df = pd.read_csv(DF_PATH)
        return load_df

    def parse_page(self, df, main_url):
        elements = self.browser.find_elements_by_xpath("//div[@class = 'catalog-listing__items']/div")
        #  check type of the page
        if elements:
            # print('+')
            for elem in elements:
                try:
                    title_temp = elem.find_element_by_xpath(".//div[@class = 'item-title desktop-only']/a")
                    title = title_temp.get_attribute('title').replace(',', '.')
                    url_temp = elem.find_element_by_xpath(".//div[@class = 'item-title desktop-only']/a")
                    url = url_temp.get_attribute('href')
                    ne_v_nalichii = elem.find_elements_by_xpath(".//div[@class = 'item-title empty']")
                    if ne_v_nalichii:
                        pass
                        # price = ne_v_nalichii[0].text
                    else:
                        price_temp = elem.find_element_by_xpath(".//div[@class = 'item-price']").get_attribute('textContent')
                        price = re.sub("^\s+|\n|\r|\s+$|₽| |р|у|б|[.]", '', price_temp).split()[-1]

                        if (url not in list(df['link'])):
                            message = [title, price, url]
                            self.send_message(message)
                except NoSuchElementException:
                    print(f'no such element: {main_url}')


        else:
            elements = self.browser.find_elements_by_xpath("//div[@class = 'catalog-listing-container']/div")
            # print('-')
            for elem in elements:
                try:
                    title_temp = elem.find_element_by_xpath(".//header[@class = 'card-prod--title ddl_product_link']/a")
                    title = title_temp.get_attribute('title').replace(',', '.')
                    url_temp = elem.find_element_by_xpath(".//header[@class = 'card-prod--title ddl_product_link']/a")
                    url = url_temp.get_attribute('href')
                    v_nalichii = elem.find_elements_by_xpath(".//div[@class = 'current notAvailable hide']")
                    if v_nalichii:
                        price_temp = elem.find_elements_by_xpath(".//div[@class = 'favoritePrice current']")
                        if price_temp:
                            price_temp = price_temp[0].get_attribute('textContent')
                        else:
                            price_temp = elem.find_elements_by_xpath(".//div[@class = 'favoritePrice current hasBpg2']")
                            price_temp = price_temp[0].get_attribute('textContent')
                        price = re.sub("^\s+|\n|\r|\s+$|₽| |р|у|б|[.]", '', price_temp).split()[-1]

                        if (url not in list(df['link'])):
                            message = [title, price, url]
                            self.send_message(message)
                    else:
                        pass
                except NoSuchElementException:
                    print(f'no such element: {main_url}')


    def send_message(self, item):
        df = pd.DataFrame([item], columns=COLUMNS)
        df.to_csv(DF_PATH, mode='a', header=None, index=False, encoding='utf-8')
        message_text = f'{item[0]}\r\nЦена: {item[1]}\r\n{item[2]}'
        if any(ext in item[0].lower().split() for ext in EXC_WORDS):
            pass
        else:
            # pass
            print(message_text)
            # telegram_bot.send_message(message_text)

def run_pricess(category):
    parser = ParserBeru(category=category)
    parser.run()

def main():
    with Pool(len(CATEGORIES)) as process:
        process.map(run_pricess, CATEGORIES)


if __name__ == '__main__':
        try:
            main()
        except Exception as e:
            print(f'Ошибка чтения страницы. Пожалуйста подождите...\n{e}')
            time.sleep(3)
            main()

