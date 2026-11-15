from aiogram import Router, F, types, Bot
from aiogram.fsm.context import FSMContext

from utils.keyboards import make_inline_buttons
from utils.single_screen import reset_workflow_state, send_or_edit_screen
from middlewares.auto_delete import AutoDeleteInputMiddleware

from modules.reveal.logic import process_role_selection, process_forwarded_reveal, process_number_click
from modules.reveal.states import NumberCallback, RoleCallback, RevealState
from modules.reveal.texts import ROLE_NAMES, DUMP_PATTERN
from utils.table_dump import parse_table_dump
from modules.reveal.keyboards import get_number_keyboard
from modules.reveal.states import TemplateSelectCallback
from modules.reveal.logic import process_template_selection

reveal_router = Router()
reveal_router.message.middleware(AutoDeleteInputMiddleware())


@reveal_router.callback_query(F.data == "dummy_reveal")
async def process_dummy_reveal_start(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    await reset_workflow_state(state)
    
    buttons = {
        ROLE_NAMES["sherif"]: RoleCallback(role_key="sherif").pack(),
        ROLE_NAMES["doctor"]: RoleCallback(role_key="doctor").pack(),
        ROLE_NAMES["homeless"]: RoleCallback(role_key="homeless").pack(),
        ROLE_NAMES["mistress"]: RoleCallback(role_key="mistress").pack(),
        "🔙 Назад": "navigation_back",
    }

    await send_or_edit_screen(
        bot=bot,
        chat_id=callback.message.chat.id,
        state=state,
        text="<b>🦹 Вскрыться за...</b>\n\nВыбери роль:",
        reply_markup=make_inline_buttons(buttons=buttons, sizes=(2, 2, 1)),
        parse_mode="HTML"
    )
    await callback.answer()


@reveal_router.callback_query(RoleCallback.filter())
async def role_selection(callback: types.CallbackQuery, callback_data: RoleCallback, state: FSMContext, bot: Bot):
    await process_role_selection(callback=callback, callback_data=callback_data, state=state, bot=bot)


@reveal_router.callback_query(RevealState.waiting_for_number_or_forward, NumberCallback.filter())
async def number_click(callback: types.CallbackQuery, callback_data: NumberCallback, state: FSMContext, bot : Bot):
    await process_number_click(callback=callback, callback_data=callback_data, state=state, bot=bot)


@reveal_router.callback_query(TemplateSelectCallback.filter())
async def template_selection(callback: types.CallbackQuery, callback_data: TemplateSelectCallback, state: FSMContext, bot: Bot):
    await process_template_selection(callback=callback, callback_data=callback_data, state=state, bot=bot)


# --- 1. Обработка ПЕРЕСЛАННЫХ сообщений (вынесена наверх, чтобы не перехватывалась дампом) ---
@reveal_router.message(RevealState.waiting_for_number_or_forward, F.forward_origin)
async def forwarded_reveal(message: types.Message, state: FSMContext, bot: Bot):
    await process_forwarded_reveal(message=message, state=state, bot=bot)


# --- 2. Парсер дампа стола из обычного текстового сообщения ---
@reveal_router.message(RevealState.waiting_for_number_or_forward, F.text | F.caption)
async def process_table_dump(message: types.Message, state: FSMContext, bot: Bot):
    text = message.text or message.caption or ""
    matches = DUMP_PATTERN.findall(text)
    
    if matches:
        table_players = parse_table_dump(text)
        await state.update_data(table_players=table_players)
        
        await send_or_edit_screen(
            bot=bot,
            chat_id=message.chat.id,
            state=state,
            text=f"✅ Успешно загружено игроков: <b>{len(table_players)}</b>.\n"
                 f"Теперь выбери нужного игрока на клавиатуре:",
            reply_markup=get_number_keyboard(table_players),
            parse_mode="HTML"
        )
    else:
        await send_or_edit_screen(
            bot=bot,
            chat_id=message.chat.id,
            state=state,
            text="Не удалось распарсить список. Используй формат:\n1. Имя1\n2. Имя2"
        )
