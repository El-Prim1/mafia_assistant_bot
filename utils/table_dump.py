import re

DUMP_PATTERN = re.compile(r"(\d{1,2})\s*[\.\)\-:]\s*@?([^\n\r]+)")

def parse_table_dump(text: str) -> dict[int, str]:
    """Парсит список формата '1. Имя' в словарь {1: 'Имя'}."""
    matches = DUMP_PATTERN.findall(text)
    return{int(num): name.strip() for num, name in matches if 1 <= int(num) <= 30}