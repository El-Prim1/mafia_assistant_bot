import re
import asyncio
from aiogram import types, Bot, html
from aiogram.fsm.context import FSMContext
from aiogram.enums import MessageOriginType
from utils.table_dump import parse_table_dump
from utils.single_screen import send_or_edit_screen
from utils.keyboards import make_inline_buttons, get_copy_keyboard
from modules.lists.states import CreateList, RoleSelectCallback
from modules.lists.keyboards import get_dump_menu_keyboard 
from modules.lists.texts import REQUIRED_WORDS, VICTIM_WORDS, LIST_TEMPLATE

TAG_CLEANER = re.compile(r"<[^>]+>")
DUMP_PATTERN = re.compile(r"(\d{1,2})\s*[\.\)\-:]\s*@?([^\n\r]+)")


def build_reveal_texts(template: str, **kwargs) -> tuple[str, str]:
    raw_text = template.format(**kwargs)
    safe_kwargs = {k: html.quote(v) for k, v in kwargs.items()}
    formatted_template = template.format(**safe_kwargs)
    return raw_text, formatted_template


async def process_forwarded_message_or_text(
    message: types.Message,
    state: FSMContext,
    bot: Bot
):
    text = message.text or message.caption
    if not text:
        return

    matches = DUMP_PATTERN.findall(text)
    
    if matches:
        table_players = parse_table_dump(text)
        
        await state.set_state(CreateList.table_dump_ready)
        await state.update_data(manual_list=[], table_players=table_players)
        
        await send_or_edit_screen(
            bot=bot,
            chat_id=message.chat.id,
            state=state,
            text=f"✅ Успешно загружено игроков: <b>{len(table_players)}</b>\n"
                 "Выбери игрока, которому присвоишь роль:",
            reply_markup=get_dump_menu_keyboard(table_players),
            parse_mode="HTML"
        )
        return

    origin = message.forward_origin
    if not origin:
        return

    sender_name = None
    if origin.type == MessageOriginType.USER and origin.sender_user:
        sender_name = origin.sender_user.first_name
    elif origin.type == MessageOriginType.HIDDEN_USER:
        sender_name = origin.sender_user_name
    elif origin.type == MessageOriginType.CHANNEL and origin.chat:
        sender_name = origin.chat.title
    elif origin.type == MessageOriginType.CHAT:
        sender_name = origin.author_signature or "Аноним"

    if not sender_name:
        return

    words = [re.sub(r"[^\w]", "", w).lower() for w in text.lower().split()]
    contains = any(word in REQUIRED_WORDS for word in words)

    if contains:
        for i, word in enumerate(words):
            if word == "мирный" and i + 1 < len(words) and words[i + 1] == "житель":
                role = "мж"
                break
            
            if word in VICTIM_WORDS:
                role = "битый"
                break
            
            if word in REQUIRED_WORDS:
                role = word

    data = await state.get_data()
    roles_dict = dict(data.get("roles_dict", {}))
    
    safe_name = html.quote(sender_name)
    roles_dict[safe_name] = role
    
    await state.update_data(roles_dict=roles_dict)

    # --- Предпросмотр накопленного списка ---
    roles_list = [
        f"• <i><b>{name}</b></i> — {r}"
        for name, r in roles_dict.items()
    ]
    preview_text = f"<blockquote>{'\n'.join(roles_list)}</blockquote>"

    await send_or_edit_screen(
        bot=bot,
        chat_id=message.chat.id,
        state=state,
        text=f"📋 <b>Предпросмотр списка ({len(roles_dict)}):</b>\n\n"
             f"{preview_text}\n\n"
             "Перешли следующее сообщение или нажми <b>✅ Готово</b> для получения копируемого списка.",
        reply_markup=make_inline_buttons(
            buttons={"✅ Готово": "list_ready", "🔙 Назад": "navigation_back"},
            sizes=(1, 1)
        ),
        parse_mode="HTML"
    )
        

async def process_ready_button(
    callback: types.CallbackQuery,
    state: FSMContext,
    bot: Bot
):
    def make_clear_text(text_to_copy: str) -> str:
        return TAG_CLEANER.sub("", text_to_copy)

    data = await state.get_data()
    roles_dict = data.get("roles_dict", {})

    if roles_dict:
        roles_list = [
            f"•<i><b>{name}</b></i> — {role}"
            for name, role in roles_dict.items()
        ]
        result_text = "\n".join(roles_list)
        result_html = f"<blockquote>{result_text}</blockquote>"
        amount_text = f"✅ Игроков в списке: <b>{len(roles_list)}</b>\n\n"

        cleaned_result_text = make_clear_text(result_text)

        if callback.message:
            # Отправка готового списка сообщением в чат с кнопкой в 1 тап
            await callback.message.answer(
                amount_text + result_html,
                parse_mode="HTML",
                reply_markup=get_copy_keyboard(cleaned_result_text)
            )

            # Очищаем сохраненный список
            await state.update_data(roles_dict={})

            text = (
                "Список сформирован! Можешь пересылать сообщения для нового списка 😉\n\n"
                "Как закончишь, нажми <b>✅ Готово</b>"
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
    else:
        await callback.answer("Вы еще не переслали ни одного сообщения с ролями!", show_alert=True)

    await callback.answer()


async def process_role_click(
    callback: types.CallbackQuery,
    callback_data: RoleSelectCallback,
    state: FSMContext,
    bot: Bot
):
    data = await state.get_data()
    name = data.get("selected_player_name")
    
    if not name:
        await callback.answer("Сначала выбери номер игрока!", show_alert=True)
        return

    role = callback_data.role
    
    item_raw, item_html = build_reveal_texts(LIST_TEMPLATE["list"], name=name, role=role)
    
    manual_list = list(data.get("manual_list", []))
    manual_list.append((item_raw, item_html))
    
    table_players = data.get("table_players", {})
    await state.update_data(manual_list=manual_list, selected_player_name=None)
    
    current_preview_items = "\n".join(item[1] for item in manual_list)
    current_preview = f"<blockquote>{current_preview_items}</blockquote>"
    
    if callback.message:
        await send_or_edit_screen(
            bot=bot,
            chat_id=callback.message.chat.id,
            state=state,
            text=f"✅ Накоплено ролей: <b>{len(manual_list)}</b>\n\n"
                 f"<b>Текущий список:</b>\n{current_preview}\n\n"
                 f"Выбери следующего игрока или нажми <b>✅ Готово</b>:",
            reply_markup=get_dump_menu_keyboard(table_players),
            parse_mode="HTML"
        )
    await callback.answer()
