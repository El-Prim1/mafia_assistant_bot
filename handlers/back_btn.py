from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from utils.keyboards import make_inline_buttons
from texts import MAIN_MENU_TEXT

back_btn_router = Router()

@back_btn_router.callback_query(F.data == "back_main_menu")
async def back_to_main_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    
    await callback.message.edit_text(
        MAIN_MENU_TEXT,
        reply_markup=make_inline_buttons(
            buttons={
                "🦹 Вскрыться за...": "dummy_reveal",
                "🧑‍⚖️ Помощь Адвокату" : "advocate_help",
                "📋 Сделать список": "make_list"
            },
            sizes=(2, 1)
        ),
        parse_mode="HTML"
    )
    await callback.answer()