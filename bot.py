import os
import asyncio

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from handlers.callback import call_router
from handlers.handlers import router

async def main():
    load_dotenv()
    token= os.getenv('BOT_TOKEN')
    bot = Bot(token)
    dp = Dispatcher()
    try:
        dp.include_router(router)
        dp.include_router(call_router)
        print("Bot Start")
        await dp.start_polling(bot)
    except Exception as ex:
        print(f"There is an Exception: {ex}")
        
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")