import logging
from aiogram import Bot, types
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError
from aiogram.fsm.context import FSMContext

logger = logging.getLogger(__name__)


async def send_or_edit_screen(
    bot: Bot,
    chat_id: int,
    state: FSMContext,
    text: str,
    reply_markup: types.InlineKeyboardMarkup | None = None,
    parse_mode: str | None = "HTML"
) -> types.Message | None:
    """
    Универсальная функция Single Screen.
    Редактирует сохраненное сообщение или отправляет новое с сохранением message_id в FSM.
    """
    data = await state.get_data()
    main_message_id = data.get("main_message_id")

    if main_message_id:
        try:
            return await bot.edit_message_text(
                text=text,
                chat_id=chat_id,
                message_id=main_message_id,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        except TelegramBadRequest as e:
            err_msg = str(e).lower()
            # 1. Текст и клавиатура не изменились — тихо игнорируем
            if "message is not modified" in err_msg:
                return None
            
            # 2. Сообщение невозможно отредактировать (удалено, устарело, некорректно)
            if any(phrase in err_msg for phrase in [
                "message to edit not found", 
                "message can't be edited",
                "message to delete not found",
                "chat not found"
            ]):
                logger.warning(f"Message {main_message_id} lost or uneditable. Sending new screen.")
            else:
                # Прочие ошибки TelegramBadRequest пробрасываем выше
                raise e
        except TelegramAPIError as e:
            logger.error(f"Telegram API Error during edit: {e}")

    # Если сообщения не было или отредактировать не удалось — отправляем новое
    try:
        new_message = await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
        # Запоминаем новый ID главного экрана
        await state.update_data(main_message_id=new_message.message_id)
        return new_message
    except TelegramAPIError as e:
        logger.error(f"Failed to send new screen message: {e}")
        return None