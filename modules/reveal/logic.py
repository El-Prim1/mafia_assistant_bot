from aiogram import types, Bot, html
from aiogram.enums import MessageOriginType
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .texts import ROLE_NAMES, REVEAL_TEMPLATES, DUMP_PATTERN
from .states import RevealState, RoleCallback, NumberCallback, TemplateSelectCallback
from .keyboards import get_number_keyboard
from .parser import build_reveal_texts
from utils.single_screen import reset_workflow_state, send_or_edit_screen
from utils.keyboards import make_inline_buttons, get_copy_keyboard
from utils.table_dump import parse_table_dump


async def _send_sheriff_options(
    chat_id: int, 
    target_name: str, 
    bot: Bot, 
    state: FSMContext
):
    """Вспомогательная функция для генерации и отправки 3 вариантов для комиссара."""
    sent_msg_ids = []
    templates = REVEAL_TEMPLATES["sherif"]
    
    for idx, tmpl in enumerate(templates):
        row_text, html_text = build_reveal_texts(tmpl, target=target_name)
        
        # Получаем стандартную кнопку копирования
        copy_kb = get_copy_keyboard(row_text)
        builder = InlineKeyboardBuilder.from_markup(copy_kb)
        
        # Добавляем кнопку выбора данного варианта
        builder.button(
            text="✅ Оставить этот вариант", 
            callback_data=TemplateSelectCallback(idx=idx).pack()
        )
        builder.adjust(1)

        msg = await bot.send_message(
            chat_id=chat_id,
            text=f"Вариант #{idx + 1}:\n\n{html_text}",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        sent_msg_ids.append(msg.message_id)

    # Сохраняем ID сообщений для последующего удаления невыбранных
    await state.update_data(sheriff_messages=sent_msg_ids)


async def process_template_selection(
    callback: types.CallbackQuery,
    callback_data: TemplateSelectCallback,
    state: FSMContext,
    bot: Bot
):
    """Удаляет невыбранные сообщения и оставляет только выбранное."""
    if not callback.message:
        return

    data = await state.get_data()
    msg_ids: list[int] = data.get("sheriff_messages", [])
    selected_msg_id = callback.message.message_id

    # Удаляем все сообщения из списка, кроме выбранного
    for msg_id in msg_ids:
        if msg_id != selected_msg_id:
            try:
                await bot.delete_message(chat_id=callback.message.chat.id, message_id=msg_id)
            except Exception:
                pass

    # Убираем лишнюю кнопку "Оставить этот вариант", оставляя копирование
    if callback.message.reply_markup:
        # Оставляем только первую строчку клавиатуры (кнопка скопировать)
        new_markup = types.InlineKeyboardMarkup(
            inline_keyboard=[callback.message.reply_markup.inline_keyboard[0],
                             callback.message.reply_markup.inline_keyboard[1]]
        )
        await callback.message.edit_reply_markup(reply_markup=new_markup)

    await callback.answer("Вариант выбран!")
    await state.update_data(sheriff_messages=[])


async def process_role_selection(
    callback: types.CallbackQuery,
    callback_data: RoleCallback, 
    state: FSMContext, 
    bot: Bot
):
    if not callback.message:
        await callback.answer("Ошибка доступа к сообщению", show_alert=True)
        return

    role_key = callback_data.role_key
    await state.set_state(RevealState.waiting_for_number_or_forward)
    await state.update_data(
        selected_role=role_key, 
        table_players={}, 
        homeless_first_target=None,
        sheriff_messages=[]
    )

    role_title = ROLE_NAMES.get(role_key, "Неизвестная роль")
    extra_text = "к которому придешь\n" if role_title == "🍺 Бомж" else "\n"

    await send_or_edit_screen(
        bot=bot,
        chat_id=callback.message.chat.id,
        state=state,
        text=f"Выбрана роль: <b>{role_title}</b>\n\n"
             f"• Перешли сообщение игрока {extra_text}"
             f"• <b>ИЛИ</b> отправь сюда текстовый список всех игроков (1. Имя, 2. Имя...)",
        reply_markup=make_inline_buttons(buttons={"🔙 Назад": "navigation_back"}, sizes=(1,)),
        parse_mode="HTML"
    )
    await callback.answer()
    
    
async def process_number_click(
    callback: types.CallbackQuery,
    callback_data: NumberCallback,
    state: FSMContext, 
    bot: Bot
):
    if not callback.message:
        await callback.answer("Ошибка доступа к сообщению", show_alert=True)
        return

    data = await state.get_data()
    role_key = data.get("selected_role")
    table_players = data.get("table_players", {})

    if not role_key or role_key not in REVEAL_TEMPLATES:
        await callback.answer("Ошибка: роль не выбрана.", show_alert=True)
        await send_or_edit_screen(
            bot=bot,
            chat_id=callback.message.chat.id,
            state=state,
            text="Ошибка контекста. Выбери роль заново.",
            reply_markup=make_inline_buttons(buttons={"🔙 Назад": "navigation_back"}, sizes=(1,)),
        )
        await reset_workflow_state(state)
        return

    num = callback_data.number
    target_name = table_players.get(num, f"игрок №{num}")
    
    if role_key == "sherif":
        await _send_sheriff_options(
            chat_id=callback.message.chat.id, 
            target_name=target_name, 
            bot=bot, 
            state=state
        )
    elif role_key == "homeless":
        first_target = data.get("homeless_first_target")
        
        if not first_target:
            await state.update_data(homeless_first_target=target_name)
            await send_or_edit_screen(
                bot=bot,
                chat_id=callback.message.chat.id,
                state=state,
                text=f"К кому пришел: <b>{html.quote(target_name)}</b>\n\n"
                     f"Теперь выбери <b>кого ты там увидел</b> (второго игрока):",
                reply_markup=get_number_keyboard(table_players),
                parse_mode="HTML"
            )
            await callback.answer()
            return
        else:
            row_text, html_text = build_reveal_texts(
                REVEAL_TEMPLATES["homeless"], 
                target1=first_target, 
                target2=target_name
            )
            await callback.message.answer(
                f"Заготовка готова! Скопируй в 1 клик 👇\n\n{html_text}",
                reply_markup=get_copy_keyboard(row_text),
                parse_mode="HTML"
            )
    else:
        row_text, html_text = build_reveal_texts(
            REVEAL_TEMPLATES[role_key], 
            target=target_name
        )
        await callback.message.answer(
            f"Заготовка готова! Скопируй в 1 клик 👇\n\n{html_text}",
            reply_markup=get_copy_keyboard(row_text),
            parse_mode="HTML"
        )
        
    await callback.answer()
    await state.update_data(homeless_first_target=None)


async def process_forwarded_reveal(
    message: types.Message, 
    state: FSMContext,
    bot: Bot
):
    # Парсинг дампа стола в пересланном сообщении
    matches = DUMP_PATTERN.findall(message.text)
    if matches:
        table_players = parse_table_dump(message.text)
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

    data = await state.get_data()
    role_key = data.get("selected_role")

    if not role_key or role_key not in REVEAL_TEMPLATES:
        await send_or_edit_screen(
            bot=bot,
            chat_id=message.chat.id,
            state=state,
            text="Ошибка контекста. Выбери роль заново."
        )
        await reset_workflow_state(state)
        return

    origin = message.forward_origin
    if not origin:
        await send_or_edit_screen(
            bot=bot,
            chat_id=message.chat.id,
            state=state,
            text="Пожалуйста, перешли сообщение игрока или отправь список."
        )
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
        await send_or_edit_screen(
            bot=bot,
            chat_id=message.chat.id,
            state=state,    
            text="Не удалось определить имя из сообщения."
        )
        return

    if role_key == "sherif":
        await _send_sheriff_options(
            chat_id=message.chat.id, 
            target_name=sender_name, 
            bot=bot, 
            state=state
        )
    elif role_key == "homeless":
        first_target = data.get("homeless_first_target")
        
        if not first_target:
            await state.update_data(homeless_first_target=sender_name)
            await send_or_edit_screen(
                bot=bot,
                chat_id=message.chat.id,
                state=state,
                text=f"К кому пришел: <b>{html.quote(sender_name)}</b>\n\n"
                     f"Теперь перешли сообщение того, <b>кого ты там увидел</b>:",
                parse_mode="HTML"
            )
            return
        else:
            row_text, html_text = build_reveal_texts(
                REVEAL_TEMPLATES["homeless"], 
                target1=first_target, 
                target2=sender_name
            )
            await message.answer(
                f"Заготовка готова! Скопируй в 1 тап 👇\n\n{html_text}",
                reply_markup=get_copy_keyboard(row_text),
                parse_mode="HTML"
            )
    else:
        row_text, html_text = build_reveal_texts(
            REVEAL_TEMPLATES[role_key], 
            target=sender_name
        )
        await message.answer(
            f"Заготовка готова! Скопируй в 1 тап 👇\n\n{html_text}",
            reply_markup=get_copy_keyboard(row_text),
            parse_mode="HTML"
        )

    await state.update_data(homeless_first_target=None)
