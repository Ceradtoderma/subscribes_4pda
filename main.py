import logging
from aiogram import executor
from func import send_news
import handlers
import asyncio
from bot import bot, dp


logging.basicConfig(level=logging.INFO)





if __name__ == "__main__":

    # Запуск бота
    loop = asyncio.get_event_loop()
    loop.create_task(send_news(5), name='Имя')
    executor.start_polling(dp, skip_updates=True)

