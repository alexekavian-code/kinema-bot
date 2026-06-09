import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from handlers import router

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не задан! Укажи его в переменных окружения.")
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    
    print("🎬 Кинема-бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
