import logging
from aiogram import Bot, types
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError
from aiogram.fsm.context import FSMContext
from utils.keyboards import add_back_button

logger = logging.getLogger(__name__)

HISTORY_KEY = "_navigation_history"
CURRENT_SCREEN_KEY = "_navigation_current_screen"
MAIN_MESSAGE_ID_KEY = "main_message_id"


async def reset_workflow_state(state: FSMContext) -> None:
    """Clear workflow fields while retaining the current screen/navigation context."""
    data = await state.get_data()
    preserved = {
        key: data[key]
        for key in (HISTORY_KEY, CURRENT_SCREEN_KEY, MAIN_MESSAGE_ID_KEY)
        if key in data
    }
    await state.clear()
    if preserved:
        await state.update_data(**preserved)


def _screen_snapshot(
    data: dict,
    state_name: str | None,
) -> dict:
    workflow_data = {
        key: value
        for key, value in data.items()
        if key not in {HISTORY_KEY, CURRENT_SCREEN_KEY, MAIN_MESSAGE_ID_KEY}
    }
    return {"state": state_name, "data": workflow_data}


def _same_screen(left: dict | None, right: dict) -> bool:
    if not left:
        return False
    return all(left.get(key) == right.get(key) for key in (
        "state",
        "data",
        "text",
        "parse_mode",
        "reply_markup",
    ))


async def send_or_edit_screen(
    bot: Bot,
    chat_id: int,
    state: FSMContext,
    text: str,
    reply_markup: types.InlineKeyboardMarkup | None = None,
    parse_mode: str | None = "HTML",
    record_history: bool = True,
    show_back: bool = True,
    force_new: bool = False,
) -> types.Message | None:
    """
    Универсальная функция Single Screen.
    Редактирует сохраненное сообщение или отправляет новое с сохранением message_id в FSM.
    """
    data = await state.get_data()
    if not record_history:
        data[HISTORY_KEY] = []
        await state.update_data(**{HISTORY_KEY: []})
    main_message_id = data.get(MAIN_MESSAGE_ID_KEY)
    state_name = await state.get_state()
    current_snapshot = data.get(CURRENT_SCREEN_KEY)
    next_snapshot = _screen_snapshot(data, state_name)

    rendered_markup = add_back_button(reply_markup) if show_back else reply_markup
    next_snapshot.update({
        "text": text,
        "parse_mode": parse_mode,
        "reply_markup": rendered_markup.model_dump() if rendered_markup else None,
    })

    if record_history:
        history = list(data.get(HISTORY_KEY, []))
        if current_snapshot and not _same_screen(current_snapshot, next_snapshot):
            # Transition to a different screen — record the previous screen
            # so the Back button can restore it.
            history.append({
                "screen": current_snapshot,
                "text": current_snapshot.get("text", ""),
                "parse_mode": current_snapshot.get("parse_mode"),
                "reply_markup": current_snapshot.get("reply_markup"),
            })
        elif not current_snapshot:
            # First screen setup (current_snapshot is None, e.g. after start_msg with
            # message.answer() that bypassed send_or_edit_screen, or after a full
            # reset_workflow_state where no snapshot was preserved).
            # Record the initial screen so Back navigation works.
            if not history:  # Avoid duplicate entries from a previous workflow
                history.append({
                    "screen": next_snapshot,
                    "text": next_snapshot.get("text", ""),
                    "parse_mode": next_snapshot.get("parse_mode"),
                    "reply_markup": next_snapshot.get("reply_markup"),
                })
        await state.update_data(**{HISTORY_KEY: history[-30:]})

    await state.update_data(**{CURRENT_SCREEN_KEY: next_snapshot})

    if main_message_id and not force_new:
        try:
            return await bot.edit_message_text(
                text=text,
                chat_id=chat_id,
                message_id=main_message_id,
                reply_markup=rendered_markup,
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
            reply_markup=rendered_markup,
            parse_mode=parse_mode
        )
        # Запоминаем новый ID главного экрана
        await state.update_data(**{MAIN_MESSAGE_ID_KEY: new_message.message_id})
        return new_message
    except TelegramAPIError as e:
        logger.error(f"Failed to send new screen message: {e}")
        return None
