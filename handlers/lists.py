from aiogram import Router, F, types, Bot, html
from aiogram.fsm.context import FSMContext

from utils.keyboards import make_inline_buttons, get_copy_keyboard
from utils.single_screen import send_or_edit_screen

from middlewares.auto_delete import AutoDeleteInputMiddleware

from modules.lists.logic import process_forwarded_message_or_text, process_ready_button, process_role_click
from modules.lists.states import RoleSelectCallback, CreateList, NumberCallback
from modules.lists.keyboards import build_keyboard_for_true_mafia, get_dump_menu_keyboard 

list_builder_router = Router()
list_builder_router.message.middleware(AutoDeleteInputMiddleware())


@list_builder_router.callback_query(F.data == "make_list")
async def start_make_list(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    if not callback.message:
        await callback.answer("Ошибка доступа к сообщению", show_alert=True)
        return

    await state.set_state(CreateList.waiting_for_messages)
    await state.update_data(roles_dict={}, manual_list=[], table_players={})

    text = (
        "<b>📋 Сделать список</b>\n\n"
        "• Перешли сообщения людей, которые открылись, а я сделаю список\n"
        "• <b>ИЛИ</b> отправь сюда текстовый список всех игроков (1. Имя, 2. Имя...) и составь его сам\n"
        "• Как закончишь, нажми <b>✅ Готово</b>"
    )
    
    await send_or_edit_screen(
        bot=bot,
        chat_id=callback.message.chat.id,
        state=state,
        text=text,
        reply_markup=make_inline_buttons(
            buttons={"✅ Готово": "list_ready", "🔙 Назад": "navigation_back"},
            sizes=(1,)
        ),
        parse_mode="HTML"
    )
    await callback.answer()


# Заменено на (F.text | F.caption) для корректного отлова медиа с подписью
@list_builder_router.message(CreateList.waiting_for_messages, F.text | F.caption)
async def forwarded_message_or_text(message: types.Message, state: FSMContext, bot: Bot):
    await process_forwarded_message_or_text(message=message, state=state, bot=bot)


@list_builder_router.callback_query(CreateList.waiting_for_messages, F.data == "list_ready")
async def ready_button(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    await process_ready_button(callback=callback, state=state, bot=bot)
    

# 1. Шаг выбора НОМЕРА игрока
@list_builder_router.callback_query(CreateList.table_dump_ready, NumberCallback.filter())
async def process_number_click(callback: types.CallbackQuery, callback_data: NumberCallback, state: FSMContext, bot: Bot):
    if not callback.message:
        await callback.answer("Ошибка доступа к сообщению", show_alert=True)
        return

    data = await state.get_data()
    table_players = data.get("table_players", {})
    
    num = callback_data.number
    name = table_players.get(num, f"игрок №{num}")
    
    await state.update_data(selected_player_name=name)
    
    await send_or_edit_screen(
        bot=bot,
        chat_id=callback.message.chat.id,
        state=state,
        text=f"<i><b>{html.quote(name)}</b></i> является...",
        reply_markup=build_keyboard_for_true_mafia(),
        parse_mode="HTML"
    )
    await callback.answer()


# 2. Накопление записи в список при выборе РОЛИ
@list_builder_router.callback_query(CreateList.table_dump_ready, RoleSelectCallback.filter())
async def role_click(callback: types.CallbackQuery, callback_data: RoleSelectCallback, state: FSMContext, bot: Bot):
    await process_role_click(callback=callback, callback_data=callback_data, state=state, bot=bot)


# 3. Финал: Отправка готового списка по кнопке «✅ Готово»
@list_builder_router.callback_query(CreateList.table_dump_ready, F.data == "dump_list_ready")
async def process_dump_ready(callback: types.CallbackQuery, state: FSMContext):
    if not callback.message:
        await callback.answer("Ошибка доступа к сообщению", show_alert=True)
        return

    data = await state.get_data()
    manual_list = data.get("manual_list", [])
    
    if not manual_list:
        await callback.answer("Список пуст! Сначала добавьте роли игрокам.", show_alert=True)
        return

    clean_text = "\n".join([item[0] for item in manual_list])
    html_text = "\n".join([item[1] for item in manual_list])

    await callback.message.answer(
        f"Список готов! Скопируй в один клик 👇\n\n<blockquote>{html_text}</blockquote>",
        reply_markup=get_copy_keyboard(clean_text),
        parse_mode="HTML"
    )
    await callback.answer()
    
    await state.update_data(manual_list=[])
    
    table_players = data.get("table_players", {})
    await send_or_edit_screen(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        state=state,
        text="Список отправлен! Можешь собрать новый или выбрать игроков заново:",
        reply_markup=get_dump_menu_keyboard(table_players),
        parse_mode="HTML"
    )


# 4. Сброс накопленного списка по кнопке «🔄 Сбросить»
@list_builder_router.callback_query(CreateList.table_dump_ready, F.data == "dump_list_reset")
async def process_dump_reset(callback: types.CallbackQuery, state: FSMContext):
    if not callback.message:
        await callback.answer("Ошибка доступа к сообщению", show_alert=True)
        return

    await state.update_data(manual_list=[], selected_player_name=None)
    table_players = (await state.get_data()).get("table_players", {})
    
    await send_or_edit_screen(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        state=state,
        text="🔄 Список очищен. Выбери игрока для присвоения роли:",
        reply_markup=get_dump_menu_keyboard(table_players),
        parse_mode="HTML"
    )
    await callback.answer("Список сброшен")
