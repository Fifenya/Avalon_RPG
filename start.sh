#!/bin/bash

# ============================================
# ЗАПУСК АВАЛОН + MINI APP (локальный хостинг)
# ============================================

echo "=========================================="
echo "🏰 ЗАПУСК АВАЛОН + MINI APP"
echo "=========================================="

# Переходим в папку с ботом
cd ~/avalon_bot

# Останавливаем предыдущие процессы (если есть)
echo "🛑 Останавливаем старые процессы..."
pkill -f "python -m http.server" 2>/dev/null
pkill -f "python main.py" 2>/dev/null
sleep 2

# Запускаем HTTP сервер для Mini App (порт 8080)
echo "📡 Запускаем HTTP сервер для Mini App..."
python -m http.server 8000 --bind 0.0.0.0 &
HTTP_PID=$!
echo "   ✅ HTTP сервер запущен (PID: $HTTP_PID)"
echo "   📱 Mini App доступен по адресу: http://localhost:8080/prestige.html"

# Получаем IP телефона
IP_ADDR=$(ip addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v 127.0.0.1 | head -1)
if [ -n "$IP_ADDR" ]; then
    echo "   🌐 Внешний адрес: http://$IP_ADDR:8080/prestige.html"
    echo "   💡 Этот адрес нужно дать BotFather"
else
    echo "   ⚠️ Не удалось определить IP телефона"
    echo "   🔍 Попробуй: ifconfig | grep inet"
fi

echo ""

# Запускаем бота
echo "🤖 Запускаем бота Авалон..."
python main.py

# Остановка сервера при завершении бота
echo ""
echo "🛑 Останавливаем HTTP сервер..."
kill $HTTP_PID 2>/dev/null
echo "✅ Готово!"