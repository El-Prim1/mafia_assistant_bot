from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup
from texts import MAIN_MENU_TEXT
from utils.keyboards import make_inline_buttons
from utils.single_screen import (
    HISTORY_KEY,
    CURRENT_SCREEN_KEY,
    MAIN_MESSAGE_ID_KEY,
    reset_workflow_state,
    send_or_edit_screen,
)

back_btn_router = Router()


@back_btn_router.callback_query(F.data == "back_main_menu")
async def back_to_main_menu(callback: types.CallbackQuery, state: FSMContext):
    await reset_workflow_state(state)
    await send_or_edit_screen(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        state=state,
        text=MAIN_MENU_TEXT,
        reply_markup=make_inline_buttons(
            buttons={
                "🦹 Вскрыться за...": "dummy_reveal",
                "🧑‍⚖️ Помощь Адвокату": "advocate_help",
                "📋 Сделать список": "make_list",
            },
            sizes=(2, 1),
        ),
        parse_mode="HTML",
        show_back=False,
        record_history=False,
        force_new=True,
    )
    await callback.answer()

@back_btn_router.callback_query(F.data == "navigation_back")
async def navigate_back(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_screen = data.get(CURRENT_SCREEN_KEY)
    current_message_id = data.get(MAIN_MESSAGE_ID_KEY)

    # Result/template messages are sometimes sent separately from the tracked
    # single-screen message. Restore the active screen directly in that message.
    callback_message_id = getattr(callback.message, "message_id", None)
    if current_screen and callback_message_id != current_message_id:
        restored_data = dict(current_screen.get("data", {}))
        restored_data.update({
            HISTORY_KEY: data.get(HISTORY_KEY, []),
            CURRENT_SCREEN_KEY: current_screen,
            MAIN_MESSAGE_ID_KEY: callback_message_id,
        })
        await state.set_data(restored_data)
        previous_state = current_screen.get("state")
        if previous_state:
            await state.set_state(previous_state)
        else:
            await state.clear()
            await state.set_data(restored_data)
        markup = current_screen.get("reply_markup")
        await callback.message.edit_text(
            current_screen.get("text", ""),
            reply_markup=InlineKeyboardMarkup.model_validate(markup) if markup else None,
            parse_mode=current_screen.get("parse_mode"),
        )
        await callback.answer()
        return

    history = list(data.get(HISTORY_KEY, []))
    if not history:
        await callback.answer("Предыдущего экрана нет.", show_alert=True)
        return

    previous = history.pop()
    screen = previous["screen"]
    restored_data = dict(screen.get("data", {}))
    restored_data.update({
        HISTORY_KEY: history,
        CURRENT_SCREEN_KEY: screen,
        MAIN_MESSAGE_ID_KEY: data.get(MAIN_MESSAGE_ID_KEY),
    })

    await state.set_data(restored_data)
    previous_state = screen.get("state")
    if previous_state:
        await state.set_state(previous_state)
    else:
        await state.clear()
        await state.set_data(restored_data)

    markup = screen.get("reply_markup")
    await callback.message.edit_text(
        screen.get("text", ""),
        reply_markup=InlineKeyboardMarkup.model_validate(markup) if markup else None,
        parse_mode=screen.get("parse_mode"),
    )
    await callback.answer()
