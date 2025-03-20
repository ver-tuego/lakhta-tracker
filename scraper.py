import asyncio
import os
import tempfile

from lxml import etree
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


class Ticket:
    def __init__(self, date, time, amount):
        self.date = date
        self.time = time
        self.amount = amount

    def __str__(self):
        return f"{self.amount} билета(ов) на {self.date.strftime('%Y-%m-%d')} в {self.time}"


BASE_URL = 'https://tickets.lakhta.events/event/23FA307410B1F9BE84842D1ABE30D6AB48EA2CF8'

def get_link(date):
    return f"{BASE_URL}/{date.strftime('%Y-%m-%d')}"


async def get_tickets(date):
    user_data_dir = tempfile.mkdtemp()
    chrome_options = Options()
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
    # chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")

    CHROMEDRIVER_PATH = os.getenv('CHROMEDRIVER_PATH', '/usr/bin/chromedriver')
    driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=chrome_options)

    EXEC_URL = get_link(date)

    await asyncio.to_thread(driver.get, EXEC_URL)
    await asyncio.sleep(2)

    tree = etree.HTML(driver.page_source)
    divs = tree.xpath('//div[contains(@class, "times__item")]')

    tickets = []

    for div in divs:
        time_element = div.xpath('.//span[@class="times__time"]/text()')
        amount_element = div.xpath('.//span[@class="times__amount"]/text()')

        if not time_element or not amount_element:
            continue

        time_text = time_element[0].strip()
        amount_int = int(amount_element[0].strip().split(' ')[0])

        tickets.append(Ticket(date, time_text, amount_int))

    driver.close()
    return tickets
