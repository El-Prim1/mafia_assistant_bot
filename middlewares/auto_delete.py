from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from aiogram.fsm.context import FSMContext
import logging

from aiogram.exceptions import TelegramAPIError

logger = logging.getLogger(__name__)

class AutoDeleteInputMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Проверяем, что входящее событие является именно Message
        if not isinstance(event, Message):
            return await handler(event, data)

        state: FSMContext | None = data.get("state")
        
        # Если FSM активен и состояние установлено — удаляем входящее сообщение
        if state:
            current_state = await state.get_state()
            if current_state is not None:
                try:
                    await event.delete()
                except TelegramAPIError:
                    # Покрывает TelegramBadRequest, TelegramForbiddenError и др.
                    pass
                except Exception:
                    # Защита от непредвиденных ошибок сети/рантайма
                    logger.exception("Unexpected error while deleting an input message")

        # Выполняем основной хэндлер
        return await handler(event, data)
