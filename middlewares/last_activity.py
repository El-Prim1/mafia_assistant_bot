from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
import time

logger = __import__("logging").getLogger(__name__)

FSM_TTL_SECONDS = 24 * 60 * 60  # Sessions inactive for 24 hours are considered stale


class LastActivityMiddleware(BaseMiddleware):
    """
    Stamps ``_last_activity`` (unix timestamp) into FSM data on every update
    that touches state. This lets a background cleanup task evict abandoned
    sessions from ``MemoryStorage``, which otherwise grows without bound.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        state: FSMContext | None = data.get("state")
        if state is not None:
            try:
                current = await state.get_data()
                current["_last_activity"] = time.time()
                await state.set_data(current)
            except Exception:  # pragma: no cover - defensive; never block the handler
                logger.exception("Failed to stamp _last_activity in FSM state")

        try:
            return await handler(event, data)
        except TelegramBadRequest as e:
            err_msg = str(e).lower()
            # 1. Сообщение не изменилось — тихо игнорируем (ошибка API Telegram),
            #    которая возникает при попытке отредактировать сообщение одинаковым контентом.
            if "message is not modified" in err_msg:
                logger.debug("Ignored Telegram 'message is not modified' error in middleware")
                return None
            raise
