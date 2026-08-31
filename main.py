import asyncio
import logging
from aiogram import Bot, Dispatcher
from handlers import main_router
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not configured. Set it in the environment or .env file.")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not configured. Set it in the environment or .env file.")

if not TOKEN:
    print("BOT_TOKEN не найден в файле .env!")
    
async def main():
    logging.basicConfig(level=logging.INFO)
    
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    dp.include_router(main_router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
    
if __name__ == "__main__":
    asyncio.run(main())

































































# import os
# import sys
# import telebot
# from dotenv import load_dotenv
# from telebot import types

# # 1. Загружаем переменные из .env
# load_dotenv()

# TOKEN = os.getenv('TELEGRAM_TOKEN')
# if not TOKEN:
#     print("ОШИБКА: TELEGRAM_TOKEN не найден в .env!")
#     sys.exit(1)

# # 2. Инициализируем бота
# bot = telebot.TeleBot(TOKEN)

# def set_my_commands():
#     commands = [
#         types.BotCommand("start", "🚀 Запустить бота / Главное меню"),
#         types.BotCommand("help", "❓ Справка и помощь"),
#     ]
#     bot.set_my_commands(commands)

# set_my_commands()

# # Создание кнопок

# def makeReplyButtons(*buttons):
#     keyboard = types.ReplyKeyboardMarkup(resize_keyboard = True, row_width=2)
#     btns = [types.KeyboardButton(button) for button in buttons]
#     keyboard.add(*btns)
#     return keyboard

# def makeInlineButtons(*buttons):
#     markup = types.InlineKeyboardMarkup(row_width=1)
#     btns = []
#     for item in buttons:
#         text, callback_data = item
#         btns.append(
#             types.InlineKeyboardButton(text = text, callback_data = callback_data) 
#         )
#     markup.add(*btns)
#     return markup

# # Обработка команд

# @bot.message_handler(commands=['start'])
# def start_cmd(message):
#     startText = """ 
# <b>🎭 Привет! Я твой персональный ассистент для игры в мафию.</b>

# Помогу сфабриковать алиби, быстро сгенерировать фейковый лог проверок и буду давать различные советы, чтобы повысить твои шансы на выигрыш.

# <b>⚡️ Что я делаю за пару кликов:</b>

# <i>🕵️‍♂️ Генератор вскрытий: Готовый текст проверки/логов для отправки в чат за 5 секунд до конца таймера.</i>

# <i>🛡 Контр-аргументы: Что написать в деф, если настоящий Комиссар вскрыл тебя.</i>

# <i>📊 Тактика и риски: Быстрый расчет математики стола и таймингов для блефа.</i>
# """

#     bot.send_message(message.chat.id, startText, reply_markup=makeReplyButtons("🕵️‍♂️ Кто я такой?", "🏠 Главное меню", "💼 Шпаргалка игрока") ,parse_mode="HTML")
#     bot.send_message(message.chat.id,
#                     "Жми кнопку ниже и забирай победу! 👇",
#                     reply_markup=makeInlineButtons(("🦹 Вскрыться за...", "dummy_reveal"), ("🛡 Нужен деф", "need_def"), ("📋 Сделать список", "make_list")))

# @bot.message_handler(commands=["help"])
# def help_msg(message):
#     help_text = """
# <b>📖 РУКОВОДСТВО ПО ИСПОЛЬЗОВАНИЮ</b>

# Бот создан для быстрой генерации аргументов и логов во время игры в <i>Mafia</i>.

# <b>🚀 Как это работает:</b>

# 1. <b>Выбери ситуацию:</b> Нажми нужную кнопку в Главном меню.
# 2. <b>Выбери роль/стратегию:</b> Укажи, под какую роль ты дефаешься (Камикадзе, Любовница, Сержант и т.д.).
# 3. <b>Скопируй в 1 тап:</b> Нажми на блок с текстом — он автоматически скопируется в буфер обмена.
# 4. <b>Вставь в чат игры:</b> Отправляй заготовку в игровой чат до окончания таймера!

# <blockquote>💡 <b>Подсказка:</b> Не жди последних 5 секунд дня. Готовь деф или фейк-чек заранее во время ночной фазы!</blockquote>

# <i>Возникла проблема или нашел баг? Пиши разработчику: @sk1nheady</i>
#     """

#     bot.send_message(message.chat.id, help_text, parse_mode="HTML")

# @bot.message_handler(commands=['stop'])
# def stop_bot(message):
#     bot.send_message(message.chat.id, "Работа бота остановлена")
#     bot.stop_polling()
#     sys.exit(0)

# # Обработка сообщений

# @bot.callback_query_handler(func=lambda call: True)
# def chooseCommand(call):
#     bot.answer_callback_query(callback_query_id=call.id)

#     if call.data == "dummy_reveal":
#         bot.edit_message_text(
#             chat_id = call.message.chat.id,
#             message_id = call.message.message_id,
#             text = "На выбор предлагаю тебе 4 роли:",
#             reply_markup=makeInlineButtons(("🕵️‍♂️ Комиссар", "sherif"), ("👨🏼‍⚕️ Доктор", "doctor"), ("🍺 Божм", "homeless"), ("💃🏼 Любовница", "mistress"), ("🔙 Назад", "back_dummy_reveal"))
#         )

#     elif call.data == "need_def":
#         bot.edit_message_text(
#             chat_id=call.message.chat.id,
#             message_id = call.message.message_id,
#             text = "Какова сейчас ситуация в игре?",
#             reply_markup = makeInlineButtons(("Настоящий ком уже всем известен", "com_known"), ("Настоящий ком еще неизвестен", "com_unknown"), ("🔙 Назад", "back_def"))
#         )
#     elif call.data == "com_known":
#         bot.edit_message_text(
#             chat_id=call.message.chat.id,
#             message_id=call.message.message_id,
#             text="""
# В таком случае наиболее лучший вариант для тебя это — запутать город.
            
# Например:

# <em>1) Показать негодование/злость на мирного. Типо он твой тиммейт и такой далбан, что голосует в своего, когда можно было бы сравнять голоса.</em>

# <em>2) Тупо заспамить фейк-чеками(парочку, чтоб не забанили :) )</em>    
# """, 
# parse_mode="HTML",
# reply_markup=makeInlineButtons(("🔙 Назад", "back_com_known"))
# )
#     elif call.data == "com_unknown":
#         bot.edit_message_text(
#             chat_id=call.message.chat.id,
#             message_id=call.message.message_id,
#             text="У тебя есть шансы на победу. Нужно сделать контр-вскрытие Комиссаром. Перешли сообщение настоящего Шерифа",
#             reply_markup=makeInlineButtons(("🔙 Назад", "back_com_unknown"))
#         )
#     elif call.data == "back_dummy_reveal":
#         bot.edit_message_text(
#             chat_id=call.message.chat.id,
#             message_id=call.message.message_id,
#             text="Жми кнопку ниже и забирай победу! 👇",
#             reply_markup = makeInlineButtons(("🦹 Вскрыться за...", "dummy_reveal"), ("🛡 Нужен деф", "need_def"), ("❓ Как это работает?", "how_works"))
#         )
#     elif call.data == "back_com_known":
#         bot.edit_message_text(
#             chat_id=call.message.chat.id,
#             message_id=call.message.message_id,
#             text="Какова сейчас ситуация в игре?",
#             reply_markup = makeInlineButtons(("Настоящий ком уже всем известен", "com_known"), ("Настоящий ком еще неизвестен", "com_unknown"), ("🔙 Назад", "back_def"))
#             )
#     elif call.data == "back_def":
#         bot.edit_message_text(
#             chat_id=call.message.chat.id,
#             message_id=call.message.message_id,
#             text="Жми кнопку ниже и забирай победу! 👇",
#             reply_markup=makeInlineButtons(("🦹 Вскрыться за...", "dummy_reveal"), ("🛡 Нужен деф", "need_def"), ("❓ Как это работает?", "how_works"))
#             )        

#     elif call.data == "back_com_unknown":
#         bot.edit_message_text(
#             chat_id=call.message.chat.id,
#             message_id=call.message.message_id,
#             text="Какова сейчас ситуация в игре?",
#             reply_markup = makeInlineButtons(("Настоящий ком всем известен", "com_known"), ("Меня раскрыли первым", "com_unknown"), ("🔙 Назад", "back_def"))
#             )        

# @bot.message_handler(func=lambda msg: True)
# def analyzeMessage(message):
#     if message.forward_from:
#         first_name = message.forward_from.first_name
#         text1 = f""" 
# <code>Кого будем проверять? 

# Ты ушёл проверять {first_name}

# {first_name} - 🤵🏼 <b>Мафия</b></code>
# """

#         bot.send_message(
#             message.chat.id,
#             text1,
#             parse_mode="HTML"
#         )
       
#     elif message.text == "💼 Шпаргалка игрока":
#         suggestions = """
#         <blockquote>🧠 Базовый мануал по блефу:</blockquote>

# <b>1. Заготавливай чеки заранее 🌙</b>

# Никогда не вбивай ники во время дня. Готовь текст в Ночь 2, чтобы дать заготовку в первую секунду Утра.

# <b>2. Управляй таймингом ⏱️</b>

# Вскрытие Комиссаром за 10 секунд до конца дня = 100% слив. Задержка простительна только Доктору или Камикадзе.

# <b>3. Не дефайся «насухо» 🗣️</b>

# Фраза «Я мирный, поверьте» не работает. Пиши роли, называй конкретные ники и угрожай сплитом голосов.

# <b>4. Запутывай Город 🔨</b>

# Если тебя раскрыли, твоя задача — не спастись любой ценой, а заставить Город сомневаться хотя бы на один круг.
#         """
        
#         bot.send_message(message.chat.id, suggestions, parse_mode="HTML")
        
#     elif message.text == "🏠 Главное меню":
#         start_cmd(message)
        
#     elif message.text == "🕵️‍♂️ Кто я такой?":
#         resume = """
# <b>🕵️‍♂️ О ПРОЕКТЕ</b>

# <b>Mafia Assistant</b> — это быстрый генератор игровых аргументов, алиби и лже-вскрытий.

# <b>⚙️ Главные задачи сервиса:</b>

# 1. <b>Экономия времени:</b> Выдача готовых блоков текста в 1 клик для моментальной отправки в чат.

# 2. <b>Шаблоны дефов:</b> Готовые аргументы, чтобы сбить голоса и выжить на дневном голосовании.

# 3. <b>Агрессивный блеф:</b> Помощь Мафии в ликвидации влияния реального Комиссара.
#         """
        
#         bot.send_message(message.chat.id, resume, parse_mode="HTML")

# # === ЗАПУСК ===

# print("Скрипт стартует...")
# print("Запускаем infinity_polling()...")

# bot.infinity_polling(skip_pending=True)
