import re

REVEAL_TEMPLATES = {
    "sherif": [
        "{target} - 🤵🏼 Мафия",
        "Кого будем проверять? \n\nТы ушёл проверять {target}\n\n{target} - 🤵🏼 Мафия",
        "Кого будем проверять? \n\nТы ушёл проверять {target}\n\n{target} - 🤵🏻 Дон",
    ],
    "mistress": "С кем будем спать? \n\nТы выбрал {target}",
    "homeless": "Ночью ты пришёл за бутылкой к {target1} и увидел там {target2}",
    "doctor": "Кого будем лечить? \n\nТы выбрал {target}",
}

ROLE_NAMES = {
    "sherif": "🕵️‍♂️ Комиссар",
    "mistress": "💃🏼 Любовница",
    "homeless": "🍺 Бомж",
    "doctor": "👨🏼‍⚕️ Доктор",
}

DUMP_PATTERN = re.compile(r"(\d{1,2})\s*[\.\)\-:]\s*@?([^\n\r]+)")
TAG_CLEANER = re.compile(r"<[^>]+>")