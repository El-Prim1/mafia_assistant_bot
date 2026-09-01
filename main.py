import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from handlers import main_router

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Загружаем переменные из .env (если работаем локально)
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
# Render передает PORT автоматически (по умолчанию 10000)
PORT = int(os.getenv("PORT", 8080))

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not configured. Set it in the environment or .env file.")


# --- ФЕЙКОВЫЙ HTTP-СЕРВЕР ДЛЯ RENDER ---
async def handle_ping(request):
    """Возвращает 200 OK для проверки жизнеспособности со стороны Render и UptimeRobot"""
    return web.Response(text="Bot is alive!")


async def start_web_server():
    """Запуск фонового веб-сервера на порту Render"""
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logging.info(f"Fake HTTP server started on port {PORT}")


# --- ТОЧКА ВХОДА ---
async def main():
    # 1. Запускаем HTTP-сервер для прохождения Health Check на Render
    await start_web_server()

    # 2. Инициализируем бота и диспетчер
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    dp.include_router(main_router)

    # 3. Сбрасываем неиспользованные вебхуки и запускаем Long Polling
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Starting Telegram Bot Polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())