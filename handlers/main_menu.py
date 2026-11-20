from aiogram import types, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from texts import HELLO_TEXT, MAIN_MENU_TEXT, POSSIBILITIES_TEXT
from utils.keyboards import (
    ABOUT_REPLY_BUTTON_TEXT,
    MAIN_MENU_REPLY_BUTTON_TEXT,
    MAIN_MENU_REPLY_BUTTON_TEXTS,
    make_inline_buttons,
    make_reply_buttons,
)
from utils.single_screen import reset_workflow_state, send_or_edit_screen

base_router = Router()

# Хэндлеры команд
@base_router.message(CommandStart())
async def start_msg(message: types.Message, state: FSMContext):
    await reset_workflow_state(state)
    await message.answer(HELLO_TEXT, parse_mode="HTML",
                           reply_markup=make_reply_buttons(
                               buttons=list(MAIN_MENU_REPLY_BUTTON_TEXTS),
                               sizes=(2,)
                           ))
    
    await message.answer("Жми на кнопку ниже и забирай победу! 👇",
                        reply_markup=make_inline_buttons(
                            buttons = {"🦹 Вскрыться за..." : "dummy_reveal",
                                        "🧑‍⚖️ Помощь Адвокату" : "advocate_help",
                                        "📋 Сделать список" : "make_list"},
                            sizes=(2,1)
                        ),
                        show_back=False,
                        record_history=False)
    
#Обработка reply-кнопок  
    
@base_router.message(F.text == MAIN_MENU_REPLY_BUTTON_TEXT)
async def main_menu(message : types.Message, state: FSMContext):
    await reset_workflow_state(state)
    await send_or_edit_screen(
        bot=message.bot,
        chat_id=message.chat.id,
        state=state,
        text=MAIN_MENU_TEXT,
        reply_markup=make_inline_buttons(
            buttons = {"🦹 Вскрыться за..." : "dummy_reveal",
                        "🧑‍⚖️ Помощь Адвокату" : "advocate_help",
                        "📋 Сделать список" : "make_list"},
            sizes=(2,1)
        ),
        parse_mode="HTML",
        show_back=False,
        record_history=False,
        force_new=True
    )
    
@base_router.message(F.text == ABOUT_REPLY_BUTTON_TEXT)
async def about(message : types.Message, state: FSMContext):
    await reset_workflow_state(state)
    await send_or_edit_screen(
        bot=message.bot,
        chat_id=message.chat.id,
        state=state,
        text=POSSIBILITIES_TEXT,
        parse_mode="HTML",
        show_back=False,
        force_new=True
    )
