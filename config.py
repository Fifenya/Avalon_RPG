# config.py
import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# ===== ТОКЕН БОТА (из переменных окружения) =====
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден! Создай файл .env")

# ===== АДМИНИСТРАТОРЫ =====
ADMINS = [int(x.strip()) for x in os.getenv("ADMINS", "").split(",") if x.strip()]

# ===== ФАЙЛЫ =====
DATA_FILE = "avalon_data.json"
LOGS_DIR = "battle_logs"
BACKUP_DIR = "backups"

# ===== ЭКОНОМИКА =====
START_MONEY = 500
CLAN_CREATION_PRICE = 20000

# ===== БОЕВЫЕ ПАРАМЕТРЫ =====
CRIT_CHANCE_BASE = 0.05
CRIT_MULTIPLIER = 1.5
DODGE_CHANCE_BASE = 0.05
BLOCK_CHANCE_BASE = 0.05
DEATH_REGEN_DELAY = 300
DEATH_PENALTY_MONEY = 0.1
DEATH_PENALTY_EXP = 0.05

# ===== РЕГЕНЕРАЦИЯ =====
REGEN_INTERVAL = 60

# ===== ТАВЕРНА =====
ALE_PRICE = 40
ALE_BUFF_DURATION = 300
ALE_DEBUFF_THRESHOLD = 5
ALE_MAX_STACK = 10

# ===== ПРОКСИ =====
PROXY_URL = os.getenv("PROXY_URL")          # socks5://user:pass@host:port или http://host:port
PROXY_LIST_RAW = os.getenv("PROXY_LIST", "")  # через запятую: socks5://h1:p1,socks5://h2:p2
PROXY_ENABLED = bool(PROXY_URL or PROXY_LIST_RAW)
PROXY_LIST = [x.strip() for x in PROXY_LIST_RAW.split(",") if x.strip()]
PROXY_FALLBACK = os.getenv("PROXY_FALLBACK", "1") == "1"  # при падении прокси работать напрямую

# ===== НАСТРОЙКИ РЕЙТИНГА =====
ARENA_SEASON_DAYS = 30
ARENA_MIN_BET = 100
ARENA_MAX_BET = 10000

# ===== ЕЖЕДНЕВНЫЕ КВЕСТЫ =====
DAILY_QUEST_COUNT = 3
DAILY_QUEST_RESET_HOUR = 4

# ===== ПРОКСИ =====
PROXY_CHECK_INTERVAL = 300      # Проверка каждые 5 минут
PROXY_FAILURE_THRESHOLD = 3     # После 3 ошибок прокси считается мёртвым
MAX_PROXY_AGE_HOURS = 48        # Максимальный возраст прокси (часов)

# ===== СОЗДАЁМ ПАПКИ =====
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs("images/locations", exist_ok=True)
os.makedirs("images/enemies", exist_ok=True)
os.makedirs("images/items", exist_ok=True)
os.makedirs("images/destiny", exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# ===== ДИАГНОСТИКА =====
print(f"🔍 Конфигурация загружена:")
print(f"   📁 DATA_FILE: {DATA_FILE}")
print(f"   📁 LOGS_DIR: {LOGS_DIR}")
print(f"   👥 ADMINS: {ADMINS}")
print(f"   🔑 TOKEN: {TOKEN[:10]}... (скрыто)")
print(f"   🌐 PROXY_ENABLED: {PROXY_ENABLED}")

# ===== AI СИСТЕМА =====
AI_ENGINE = "ollama"  # "phone" или "ollama"
OLLAMA_FALLBACK = True  # если Ollama упала, использовать phone AI
