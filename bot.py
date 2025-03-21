import json
import logging
import os
import sys
from datetime import datetime, timedelta

import pytz
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from scraper import get_tickets, get_link

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
FREQUENCY = int(os.getenv('FREQUENCY', 5))
DATA_DIR = '/app/data'
SUBSCRIBERS_FILE = os.path.join(DATA_DIR, 'subscribers.json')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

moscow_tz = pytz.timezone('Europe/Moscow')


def load_subscribers():
    try:
        with open(SUBSCRIBERS_FILE, 'r') as file:
            logger.info("Начата загрузка подписчиков")
            subscribers_set = set(json.load(file))
            logger.info("Подписчики загружены")
            return subscribers_set
    except FileNotFoundError:
        logger.error("Не найден файл с подписчиками")
        return set()


def save_subscribers(subscribers_set):
    with open(SUBSCRIBERS_FILE, 'w') as file:
        logger.info("Начата запись подписчиков")
        json.dump(list(subscribers_set), file)
        logger.info("Подписчики записаны")


subscribers = load_subscribers()

scheduler = AsyncIOScheduler()


async def broadcast_all(ticket, message=None):
    logger.info(f"Найден билет: {ticket}")
    if ticket.amount > 0:
        message_text = f"Найден билет: {ticket}. Ссылка: {get_link(ticket.date)}"
        for user_id in subscribers:
            await bot.send_message(user_id, message_text)
            logger.info(f"Сообщение отправлено пользователю {user_id}")


async def broadcast_raw(ticket, message=None):
    logger.info(f"Raw вывод {ticket}")
    await message.answer(str(ticket))


async def regular_check(operation, message=None):
    logger.info("Начата регулярная проверка")
    current = datetime.now(moscow_tz)
    start = 0
    if current.hour >= 18:
        start = 1
    for days in range(start, 3):
        check_time = current + timedelta(days=days)
        tickets = await get_tickets(check_time)
        logger.info(f"Найдено билетов: {len(tickets)}")
        for ticket in tickets:
            await operation(ticket, message)


@dp.message(Command("start"))
async def send_welcome(message: Message):
    logger.info("Команда /start")
    user_id = message.from_user.id
    if user_id not in subscribers:
        subscribers.add(user_id)
        save_subscribers(subscribers)
        logger.info("Пользователь подписался на рассылку")
        await message.answer("Вы подписались на рассылку.")
    else:
        logger.info("Пользователь переподписался на рассылку")
        await message.answer("Вы уже подписаны на рассылку.")


@dp.message(Command("stop"))
async def stop_messages(message: Message):
    logger.info("Команда /stop")
    user_id = message.from_user.id
    if user_id in subscribers:
        subscribers.remove(user_id)
        save_subscribers(subscribers)
        logger.info("Пользователь отписался от рассылки")
        await message.answer("Вы отписались от рассылки.")
    else:
        logger.info("Пользователь попытался отписаться от рассылки, но не был подписан")
        await message.answer("Вы и так не были подписаны на рассылку.")


@dp.message(Command("raw"))
async def stop_messages(message: Message):
    logger.info("Команда /raw")
    await regular_check(broadcast_raw, message)


@dp.message(Command("status"))
async def stop_messages(message: Message):
    logger.info("Команда /status")
    await message.answer("Бот жив.")
    jobs = scheduler.get_jobs()
    if jobs:
        next_run_time = jobs[0].next_run_time
        next_run_time_formatted = next_run_time.astimezone(moscow_tz)
        await message.answer(f"Время следующей рассылки: {next_run_time_formatted}")


async def main():
    logger.info("Бот запущен")
    logger.info("Добавлена задача регулярной проверки")
    scheduler.add_job(regular_check, 'interval', minutes=FREQUENCY, args=[broadcast_all])
    scheduler.start()
    await dp.start_polling(bot)


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
