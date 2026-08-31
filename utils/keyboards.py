from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup
from aiogram import types

def make_reply_buttons(
    buttons: list[str],
    sizes: tuple[int, ...] = (2,),
    placeholder: str | None = None,
    resize_keyboard: bool = True
) -> ReplyKeyboardMarkup:
    
    builder = ReplyKeyboardBuilder()
    for button_text in buttons:
        builder.button(text=button_text)
        
    builder.adjust(*sizes)
    
    return builder.as_markup(
        resize_keyboard=resize_keyboard,
        placeholder=placeholder
    )


def make_inline_buttons(
    buttons: dict[str, str],
    sizes: tuple[int, ...] = (2,)
) -> InlineKeyboardMarkup:
    
    builder = InlineKeyboardBuilder()
    for button_text, callback_data in buttons.items():
        builder.button(text=button_text, callback_data=callback_data)
        
    builder.adjust(*sizes)
    
    return builder.as_markup()

def get_copy_keyboard(text_to_copy: str) -> types.InlineKeyboardMarkup:
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    # Кнопка с встроенным механизмом копирования текста в буфер
    builder.button(
        text="📋 Скопировать текст",
        copy_text=types.CopyTextButton(text=text_to_copy),
    )
    builder.button(
        text="🏠 На главную", callback_data="back_main_menu"
    )
    
    builder.adjust(1,)
        
    return builder.as_markup()