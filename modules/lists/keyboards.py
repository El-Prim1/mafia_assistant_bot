from aiogram import types
from modules.lists.states import RoleSelectCallback, NumberCallback
from modules.lists.texts import TRUE_MAFIA_ROLES


def build_keyboard_for_true_mafia() -> types.InlineKeyboardMarkup:
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    
    for role in TRUE_MAFIA_ROLES:
        builder.button(text=role, callback_data=RoleSelectCallback(role=role).pack())

    builder.adjust(5, 5, 3, 3, 2, 2, 1)
    return builder.as_markup()


def get_dump_menu_keyboard(players_map: dict[int, str]) -> types.InlineKeyboardMarkup:
    """Генерация клавиатуры с кнопками игроков и кнопками Управления (Готово, Сброс, Назад)."""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()

    # 1. Циферблат игроков
    for num in range(1, 31):
        player_name = players_map.get(num)
        btn_text = f"{num}. {player_name[:7]}" if player_name else str(num)
        builder.button(text=btn_text, callback_data=NumberCallback(number=num).pack())
    
    builder.adjust(5, 5, 5, 5)

    # 2. Кнопки действия
    action_builder = InlineKeyboardBuilder()
    action_builder.button(text="✅ Готово", callback_data="dump_list_ready")
    action_builder.button(text="🔄 Сбросить", callback_data="dump_list_reset")
    action_builder.button(text="🔙 Назад", callback_data="navigation_back")
    action_builder.adjust(2, 1)

    builder.attach(action_builder)
    return builder.as_markup()
