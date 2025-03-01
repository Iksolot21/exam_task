FROM python:3.10-slim

WORKDIR /app

# Установка системных зависимостей для OpenCV и других библиотек
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Копирование файлов проекта
COPY . /app/

# Установка зависимостей Python
RUN pip install --no-cache-dir -r requirements.txt

# Опция для запрета интерактивного режима matplotlib
ENV MPLBACKEND=Agg

# Открытие порта приложения
EXPOSE 5000

# Запуск приложения
CMD ["python", "app.py"]