import re
import unicodedata


class AdvocateHelper:
    STRICT_PLAYER_PATTERN = re.compile(r"^\d+\.\s*(.+)$")
    
    @staticmethod
    def normalize_text(text: str) -> str:
        if not text:
            return ""
            
        # 1. NFKD декомпозиция (переводит стилизованные буквы 𝑰 в обычные I)
        normalized = unicodedata.normalize('NFKD', text)
        
        # 2. Удаление диакритических знаков (категория Mn)
        cleaned_chars = [c for c in normalized if unicodedata.category(c) != 'Mn']
        normalized = "".join(cleaned_chars)
        
        # 3. Перевод в нижний регистр
        normalized = normalized.lower()
        
        # 4. Удаление пунктуации, но сохранение букв, цифр, пробелов и ЭМОДЗИ/символов
        # Удаляем только стандартные знаки препинания вместо агрессивного r'[^\w\s]'
        cleaned = re.sub(r'[!\"#$%&\'()*+,\-./:;<=>?@\[\\\]^_`{|}~]', '', normalized)
        
        # 5. Схлопывание пробелов
        return " ".join(cleaned.split())

    @classmethod
    def parse_initial_players(cls, raw_text: str) -> list[str]:
        if not raw_text:
            return []
            
        players = []
        for line in raw_text.splitlines():
            line_str = line.strip()
            match = cls.STRICT_PLAYER_PATTERN.match(line_str)
            if match:
                player_name = match.group(1).strip()
                if player_name:
                    players.append(player_name)

        return players

    @classmethod
    def filter_players_by_log(cls, current_players: list[str], log_text: str) -> tuple[list[str], list[str]]:
        normalized_log = cls.normalize_text(log_text)
        raw_log_lower = log_text.lower()
        
        remaining_players = []
        excluded_players = []

        for player in current_players:
            # 1. Поиск по юзернейму @username
            if "@" in player:
                username_match = re.search(r"@\w+", player)
                if username_match:
                    clean_username = cls.normalize_text(username_match.group(0)[1:])
                    if clean_username and clean_username in normalized_log:
                        excluded_players.append(player)
                        continue

            # 2. Поиск по нормализованному имени
            norm_player = cls.normalize_text(player)
            
            # Проверяем нормализованное имя без ограничения на >= 2 символа
            if norm_player:
                pattern = r"(?:^|\s)" + re.escape(norm_player) + r"(?:$|\s)"
                if re.search(pattern, normalized_log):
                    excluded_players.append(player)
                    continue
            
            # 3. Фоллбэк: если нормализация стёрла имя полностью или не дала совпадений,
            # ищем прямое вхождение исходного имени в лог
            if player.lower() in raw_log_lower:
                excluded_players.append(player)
                continue

            remaining_players.append(player)

        return remaining_players, excluded_players