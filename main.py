import asyncio
import contextlib
import logging
import os
import time
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.types.error_event import ErrorEvent
from dotenv import load_dotenv

from handlers import main_router
from middlewares.last_activity import LastActivityMiddleware, FSM_TTL_SECONDS

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


async def fsm_cleanup_task(storage, interval: float = 60.0) -> None:
    """
    Реclaim заброшенные FSM-сессии из MemoryStorage.

    MemoryStorage не имеет встроенного TTL, поэтому записи FSM накапливаются в
    памяти навсегда. Задача периодически удаляет сессии, не показывавшие
    активности дольше FSM_TTL_SECONDS (последняя активность помечается
    LastActivityMiddleware).
    """
    while True:
        await asyncio.sleep(interval)
        now = time.time()
        stale = []
        for key, record in list(storage.storage.items()):
            last_activity = (record.data or {}).get("_last_activity", 0)
            if now - last_activity > FSM_TTL_SECONDS:
                stale.append(key)
        for key in stale:
            del storage.storage[key]
        if stale:
            logging.info("FSM cleanup: removed %d stale sessions", len(stale))


# --- ТОЧКА ВХОДА ---
async def main():
    # 1. Запускаем HTTP-сервер для прохождения Health Check на Render
    await start_web_server()

    # 2. Инициализируем бота и диспетчер
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    dp.include_router(main_router)

    # Отмечаем время последней активности в каждой FSM-сессии, чтобы
    # фоновая задача ниже могла reclaim заброшенные сессии (MemoryStorage
    # не имеет встроенного TTL и растёт в памяти без ограничений).
    dp.update.middleware(LastActivityMiddleware())

    # Фоновая очистка устаревших FSM-сессий.
    cleanup_task = asyncio.create_task(fsm_cleanup_task(dp.storage))

    # Глобальный обработчик ошибок: ловит исключения из любого хэндлера
    # и не даёт им терять смысл / становиться полностью silent failures
    @dp.errors()
    async def global_error_handler(event: ErrorEvent) -> None:
        logger.exception(
            "Unhandled exception while processing Telegram update %s: %s",
            event.update.update_id,
            event.exception,
        )

    # 3. Сбрасываем неиспользованные вебхуки и запускаем Long Polling
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Starting Telegram Bot Polling...")
    try:
        await dp.start_polling(bot)
    finally:
        cleanup_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await cleanup_task


if __name__ == "__main__":
    asyncio.run(main())