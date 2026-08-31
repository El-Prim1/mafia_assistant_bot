from .texts import DUMP_PATTERN
from aiogram import html


def parse_table_dump(text: str) -> dict[int, str]:
    """Парсит список формата '1. Имя' в словарь {1: 'Имя'}."""
    matches = DUMP_PATTERN.findall(text)
    return{int(num): name.strip() for num, name in matches if 1 <= int(num) <= 20}


def build_reveal_texts(template: str, **kwargs) -> tuple[str, str]:
    raw_text = template.format(**kwargs)

    safe_kwargs = {k: html.quote(v) for k, v in kwargs.items()}
    formatted_template = template.format(**safe_kwargs)
    
    html_text = f"<code>{formatted_template}</code>"

    return raw_text, html_text
