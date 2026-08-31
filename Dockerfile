FROM python:3.11-slim

# Отключаем буферизацию вывода Python (чтобы логи сразу отображались в панели Koyeb)
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь исходный код проекта
COPY . .

# Команда запуска вашего бота (замените bot.py на ваш главный файл, например main.py)
CMD ["python", "main.py"]