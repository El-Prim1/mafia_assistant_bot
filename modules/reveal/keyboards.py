from .states import NumberCallback
from aiogram import types

def get_number_keyboard(players_map: dict[int, str] | None = None) -> types.InlineKeyboardMarkup:
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    players_map = players_map or {}

    for num in range(1, 31):
        # Если имя под номером есть в дампе — пишем его на кнопке, иначе просто номер
        player_name = players_map.get(num)
        btn_text = f"{num}. {player_name[:7]}" if player_name else str(num)

        builder.button(
            text=btn_text,
            callback_data=NumberCallback(number=num).pack()
        )

    builder.adjust(5, 5, 5, 5)
        
    return builder.as_markup()