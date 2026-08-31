import asyncio
from aiogram.fsm.context import FSMContext
from aiogram import types, Bot, html
from utils.single_screen import send_or_edit_screen
from modules.advocate.keyboards import get_advocate_menu_kb
from modules.advocate.advo_module import AdvocateHelper 

BATCH_DEBOUNCE_DELAY = 0.8

async def process_game_log(
    message: types.Message,
    state: FSMContext,
    bot: Bot
):
    log_text = message.text or message.caption
    if not log_text:
        return

    data = await state.get_data()
    current_players = data.get("players", [])

    if not current_players:
        await send_or_edit_screen(
            bot=bot,
            chat_id=message.chat.id,
            state=state,
            text="Список игроков пуст! Нажмите кнопку сброса.",
            reply_markup=get_advocate_menu_kb()
        )
        return

    # 1. Фильтрация
    remaining, newly_excluded = AdvocateHelper.filter_players_by_log(current_players, log_text)

    # 2. Обновление состояния при наличии изменений
    if newly_excluded:
        all_excluded = list(data.get("all_excluded", [])) + newly_excluded
        last_msg_id = message.message_id

        await state.update_data(
            players=remaining,
            all_excluded=all_excluded,
            last_processed_msg_id=last_msg_id
        )

        # 3. Дебаунс
        await asyncio.sleep(BATCH_DEBOUNCE_DELAY)

        # 4. Проверка последнего обработанного сообщения
        updated_data = await state.get_data()
        if updated_data.get("last_processed_msg_id") != last_msg_id:
            return

    # 5. Формирование и вывод итогового экрана
    updated_data = await state.get_data()
    final_players = updated_data.get("players", [])
    total_excluded = updated_data.get("all_excluded", [])
    unique_excluded = list(dict.fromkeys(total_excluded))

    if final_players:
        raw_list = "\n".join([f"{i+1}. {p}" for i, p in enumerate(final_players)])
        display_list = html.quote(raw_list)
        
        msg_text = (
            f"❌ <b>Всего исключено ({len(unique_excluded)}):</b> {', '.join([html.quote(e) for e in unique_excluded])}\n\n"
            f"🎯 <b>Возможных мафиози ({len(final_players)}):</b>\n"
            f"<code>{display_list}</code>"
        )
    else:
        msg_text = (
            f"❌ <b>Исключены все игроки! ({len(unique_excluded)})</b>\n\n"
            f"Выбыли: {', '.join([html.quote(e) for e in unique_excluded])}"
        )

    await send_or_edit_screen(
        bot=bot,
        chat_id=message.chat.id,
        state=state,
        text=msg_text,
        reply_markup=get_advocate_menu_kb(),
        parse_mode="HTML"
    )