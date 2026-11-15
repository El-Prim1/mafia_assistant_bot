from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_advocate_menu_kb() -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Сбросить / Новая игра", callback_data="advocate_reset")
    builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="navigation_back"))
    return builder.as_markup()

