import asyncio
from datetime import datetime

from lxml import etree


class Ticket:
    def __init__(self, date, time, amount):
        self.date = date
        self.time = time
        self.amount = amount

    def __str__(self):
        return f"{self.amount} шт на {self.date} в {self.time}"


BASE_URL = 'https://tickets.lakhta.events/event/23FA307410B1F9BE84842D1ABE30D6AB48EA2CF8'


async def get_html(driver, url):
    await asyncio.to_thread(driver.execute_script, f"window.open('{url}');")

    await asyncio.to_thread(driver.switch_to.window, driver.window_handles[-1])

    await asyncio.sleep(2)

    html_content = driver.page_source

    await asyncio.to_thread(driver.close)

    await asyncio.to_thread(driver.switch_to.window, driver.window_handles[0])

    return html_content


def get_link_by_timestamp(date):
    return f"{BASE_URL}/{date.strftime('%Y-%m-%d')}"


def get_link_by_date_string(date_string, time_string=None):
    return f"{BASE_URL}/{date_string}" if time_string is None else f"{BASE_URL}/{date_string}/{time_string}"


async def get_dates(driver):
    month_replacements = {
        "января": "01",
        "февраля": "02",
        "марта": "03",
        "апреля": "04",
        "мая": "05",
        "июня": "06",
        "июля": "07",
        "августа": "08",
        "сентября": "09",
        "октября": "10",
        "ноября": "11",
        "декабря": "12",
    }

    current = datetime.now()

    EXEC_URL = get_link_by_timestamp(current)
    html = await get_html(driver, EXEC_URL)

    tree = etree.HTML(html)

    dates = []
    for slide in tree.xpath('//div[@class="swiper-wrapper"]/div[contains(@class, "swiper-slide")]'):
        day_element = slide.xpath('.//div[@class="slide__day"]/text()')
        month_element = slide.xpath('.//div[@class="slide__month"]/text()')
        day = day_element[0].strip().zfill(2)
        month = month_replacements[month_element[0].strip()]
        year = current.year
        if day and month and year:
            dates.append(f"{year}-{month}-{day}")

    return dates


async def get_tickets(driver, date):
    EXEC_URL = get_link_by_date_string(date)
    html = await get_html(driver, EXEC_URL)

    tree = etree.HTML(html)
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

    return tickets
