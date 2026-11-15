from aiogram import Router, F, types, html, Bot
from aiogram.fsm.context import FSMContext
from utils.single_screen import send_or_edit_screen
from utils.keyboards import make_inline_buttons

from modules.advocate.advo_module import AdvocateHelper
from middlewares.auto_delete import AutoDeleteInputMiddleware

from modules.advocate.logic import process_game_log
from modules.advocate.states import AdvocateState
from modules.advocate.keyboards import get_advocate_menu_kb

advocate_router = Router()
advocate_router.message.middleware(AutoDeleteInputMiddleware())


# --- Старт работы с адвокатом ---
@advocate_router.callback_query(F.data == "advocate_help")
async def start_advocate(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    await state.set_state(AdvocateState.waiting_for_players_list)
    await send_or_edit_screen(
        bot=bot,
        chat_id=callback.message.chat.id,
        state=state,
        text="<b>🧑‍⚖️ Помощь Адвокату</b>\n\n"
             "Отправь мне <b>исходный список игроков (1. Имя, 2. Имя...)</b>",
        reply_markup=make_inline_buttons(buttons={"🔙 Назад": "navigation_back"}, sizes=(1,)),
        parse_mode="HTML"
    )
    await callback.answer()


# --- Шаг 1: Загрузка списка участников ---
@advocate_router.message(AdvocateState.waiting_for_players_list, F.text | F.caption)
async def process_initial_list(message: types.Message, state: FSMContext, bot: Bot):
    text_content = message.text or message.caption or ""
    players = AdvocateHelper.parse_initial_players(text_content)
    
    if not players:
        await send_or_edit_screen(
            bot=bot,
            chat_id=message.chat.id,
            state=state,
            text="⚠️ <b>Формат не распознан!</b>\n\n"
                 "Список должен содержать строки строго формата:\n"
                 "<code>1. Вася\n2. Кирилл\n3. Маша</code>\n\n"
                 "Попробуй отправить список ещё раз.",
            parse_mode="HTML"
        )
        return

    # Сбрасываем накопленных исключённых при новом старте
    await state.update_data(players=players, all_excluded=[])
    await state.set_state(AdvocateState.active_session)

    formatted_list = "\n".join([f"{i+1}. {p}" for i, p in enumerate(players)])
    
    await send_or_edit_screen(
        bot=bot,
        chat_id=message.chat.id,
        state=state,
        text=f"✅ <b>Список сохранен! Всего игроков: {len(players)}</b>\n\n"
             f"Теперь пересылай мне сообщения/логи бота.\n"
             f"Я буду автоматически исключать задействованных людей.\n\n"
             f"<b>Текущий список:</b>\n<code>{html.quote(formatted_list)}</code>",
        reply_markup=get_advocate_menu_kb(),
        parse_mode="HTML"
    )


# --- Шаг 2 & 3: Фильтрация по логам ведущего ---
# Заменено с F.text на (F.text | F.caption) для приема сообщений с медиа
@advocate_router.message(AdvocateState.active_session, F.text | F.caption)
async def game_log(message: types.Message, state: FSMContext, bot: Bot):
    await process_game_log(message=message, state=state, bot=bot)
   

# --- Сброс сессии ---
@advocate_router.callback_query(AdvocateState.active_session, F.data == "advocate_reset")
async def reset_advocate(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    await state.set_state(AdvocateState.waiting_for_players_list)
    await send_or_edit_screen(
        bot=bot,
        chat_id=callback.message.chat.id,
        state=state,
        text="🔄 Сессия сброшена. Отправь новый список игроков:",
        reply_markup=make_inline_buttons(
            buttons={"🏠 Главное меню": "back_main_menu"},
            sizes=(1,)
        )
    )
    await callback.answer()
