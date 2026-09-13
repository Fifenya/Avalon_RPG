# utils.py - ДОБАВЛЕН ПРОПУЩЕННЫЙ ИМПОРТ
import json
import os
from datetime import datetime
from functools import wraps
from config import LOGS_DIR
from telegram import Update


def get_player_address(player, name=None):
    """Возвращает обращение к игроку в зависимости от пола"""
    if name is None:
        name = player.get('name', 'Игрок')
    gender = player.get('gender', '')
    if 'Мужской' in gender:
        return f"братец {name}"
    elif 'Женский' in gender:
        return f"сестрица {name}"
    return name


def is_resource_item(item):
    """Проверяет, является ли предмет ресурсом"""
    if not isinstance(item, dict):
        return False
    
    if item.get('type') in ['material', 'ore', 'shard', 'ingot', 'resource']:
        return True
    
    resource_ids = [
        'leather', 'cloth', 'coal', 'iron_ore', 'copper_ore', 
        'iron_shard', 'copper_shard', 'iron_ingot', 'steel_ingot',
        'small_magic_stone', 'medium_magic_stone', 'large_magic_stone',
        'dragon_scale', 'magic_cloth', 'wood', 'herb',
        'gold_ore', 'gold_shard', 'gold_ingot', 'silver_ore',
        'silver_shard', 'silver_ingot', 'mithril_ore', 'mithril_shard', 'mithril_ingot'
    ]
    
    if item.get('id') in resource_ids:
        return True
    
    resource_names = ['руда', 'осколок', 'слиток', 'кожа', 'ткань', 'камень', 
                     'уголь', 'шкура', 'чешуя', 'перо', 'кость', 'древесина', 'трава']
    
    item_name = item.get('name', '').lower()
    for name in resource_names:
        if name in item_name:
            return True
    
    if 'stats' in item:
        if 'value' in item['stats']:
            return True
        has_combat_stats = any(stat in item['stats'] for stat in 
                              ['power', 'armor', 'damage', 'crit', 'dodge', 'block', 'spell_damage'])
        if not has_combat_stats and len(item.get('stats', {})) > 0:
            return True
    
    return False


def save_battle_log(uid, battle_data):
    """Сохраняет лог боя в файл"""
    os.makedirs(LOGS_DIR, exist_ok=True)
    log_file = f"{LOGS_DIR}/battles_{uid}.json"
    
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            logs = json.load(f)
    else:
        logs = []
    
    battle_id = len(logs) + 1
    logs.append({
        "id": battle_id,
        "timestamp": datetime.now().isoformat(),
        "battle": battle_data
    })
    
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)
    
    return battle_id


def get_battle_logs(uid, limit=10):
    """Получить последние логи боёв игрока"""
    log_file = f"{LOGS_DIR}/battles_{uid}.json"
    
    if not os.path.exists(log_file):
        return []
    
    with open(log_file, 'r', encoding='utf-8') as f:
        logs = json.load(f)
    
    return logs[-limit:]


def format_hp_bar(current, maximum, length=10):
    """Форматирует полоску HP"""
    percent = current / maximum if maximum > 0 else 0
    filled = int(percent * length)
    return "🟥" * filled + "⬜" * (length - filled)


def format_exp_bar(current, needed, length=10):
    """Форматирует полоску опыта"""
    percent = current / needed if needed > 0 else 0
    filled = int(percent * length)
    return "🟨" * filled + "⬜" * (length - filled)


def get_level_exp_needed(level):
    """Опыт для следующего уровня"""
    return level * 100


def format_number(num):
    """Форматирует число с разделителями тысяч"""
    return f"{num:,}".replace(',', ' ')


def get_time_remaining(seconds):
    """Форматирует оставшееся время"""
    minutes = seconds // 60
    secs = seconds % 60
    if minutes > 0:
        return f"{minutes}м {secs}с"
    return f"{secs}с"


def apply_temp_buff(player, stat: str, value: int, duration: int):
    """Применяет временный бафф к игроку"""
    from datetime import datetime, timedelta
    
    if 'temp_buffs' not in player.data:
        player['temp_buffs'] = {}
    
    current_time = datetime.now()
    expire_time = current_time + timedelta(minutes=duration * 2)
    
    player['temp_buffs'][f"buff_{stat}"] = {
        'stat': stat,
        'value': value,
        'expires': expire_time.isoformat()
    }
    
    player[stat] = player.get(stat, 0) + value


async def update_message(update, context, text, reply_markup=None, parse_mode='Markdown'):
    """Редактирует последнее сообщение или отправляет новое"""
    user_id = update.effective_user.id
    
    if 'last_message_id' in context.user_data and context.user_data['last_message_id']:
        try:
            await context.bot.edit_message_text(
                chat_id=user_id,
                message_id=context.user_data['last_message_id'],
                text=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
            return
        except Exception:
            pass
    
    if update.callback_query:
        msg = await update.callback_query.message.reply_text(text, parse_mode=parse_mode, reply_markup=reply_markup)
    elif update.message:
        msg = await update.message.reply_text(text, parse_mode=parse_mode, reply_markup=reply_markup)
    else:
        msg = await context.bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup
        )
    
    context.user_data['last_message_id'] = msg.message_id


async def delete_last_message(update, context):
    """Удаляет последнее сообщение бота"""
    if 'last_message_id' in context.user_data and context.user_data['last_message_id']:
        try:
            await context.bot.delete_message(
                chat_id=update.effective_user.id,
                message_id=context.user_data['last_message_id']
            )
            context.user_data['last_message_id'] = None
        except:
            pass


def get_item_emoji_by_type(item_type: str) -> str:
    """Возвращает эмодзи для типа предмета"""
    emojis = {
        'weapon': '⚔️',
        'armor': '🛡️',
        'helmet': '⛑️',
        'boots': '👢',
        'gloves': '🧤',
        'shield': '🛡️',
        'staff': '🔮',
        'wand': '🪄',
        'bow': '🏹',
        'potion': '🧪',
        'accessory': '💍',
        'ring': '💍',
        'amulet': '🔮',
        'artifact': '🔮',
        'material': '📦',
        'ore': '⛏️',
        'shard': '🔮',
        'ingot': '🏭'
    }
    return emojis.get(item_type, '📦')


# ========== ДЕКОРАТОР ДЛЯ ЗАЩИТЫ ОТ ПРИЗРАКОВ ==========

def require_character(func):
    """Декоратор: проверяет, есть ли у игрока персонаж.
    Применять ко всем callback-обработчикам и командам."""
    @wraps(func)
    async def wrapper(update: Update, context, *args, **kwargs):
        from database import Player  # Импорт внутри функции чтобы избежать циклических импортов
        uid = str(update.effective_user.id)
        player = Player(uid)
        
        # Если у игрока нет расы — он не создал персонажа
        if not player.get('race'):
            if update.callback_query:
                await update.callback_query.answer("❌ Сначала создай персонажа через /start", show_alert=True)
            elif update.message:
                await update.message.reply_text("❌ Сначала создай персонажа через /start")
            return
        
        return await func(update, context, *args, **kwargs)
    return wrapper


# ========== ЭМОДЗИ ДЛЯ РАС И КЛАССОВ ==========

# Карта классов
CLASS_EMOJI_MAP = {
    'warrior': '🗡️',
    'mage': '🔮',
    'archer': '🏹',
    'tank': '🛡️',
    'rogue': '🗡️',
    'priest': '🙏',
}

# Карта рас (полное название -> эмодзи)
RACE_EMOJI_MAP = {
    '🧝 Эльф': '🧝',
    '👹 Демон': '👹',
    '🧙 Человек': '🧙',
    '🐺 Волколюд': '🐺',
    '🐱 Кошколюд': '🐱',
    '🐻 Медведолюд': '🐻',
    '🦊 Лисолюд': '🦊',
    '🐉 Драконолюд': '🐉',
    '🐦 Птицелюд': '🐦',
    '🐍 Змеелюд': '🐍',
    '🐗 Кабанолюд': '🐗',
    '🦌 Оленелюд': '🦌',
}

# Карта коротких названий (для миграции)
RACE_MIGRATION_MAP = {
    'beast': '🐱 Кошколюд',
    'Волколюд': '🐺 Волколюд',
    'Кошколюд': '🐱 Кошколюд',
    'Медведолюд': '🐻 Медведолюд',
    'Лисолюд': '🦊 Лисолюд',
    'Драконолюд': '🐉 Драконолюд',
    'Птицелюд': '🐦 Птицелюд',
    'Змеелюд': '🐍 Змеелюд',
    'Кабанолюд': '🐗 Кабанолюд',
    'Оленелюд': '🦌 Оленелюд',
    'Эльф': '🧝 Эльф',
    'Демон': '👹 Демон',
    'Человек': '🧙 Человек',
}


def get_race_emoji(race_name: str) -> str:
    """Возвращает эмодзи для расы"""
    if not race_name:
        return '👤'
    
    if race_name in RACE_EMOJI_MAP:
        return RACE_EMOJI_MAP[race_name]
    
    for full_name, emoji in RACE_EMOJI_MAP.items():
        if full_name in race_name or race_name in full_name:
            return emoji
    
    if race_name and race_name[0] in '🧝👹🧙🐺🐱🐻🦊🐉🐦🐍🐗🦌':
        return race_name[0]
    
    return '👤'


def get_class_emoji(class_value) -> str:
    """Возвращает эмодзи для класса"""
    if not class_value:
        return ''
    
    if hasattr(class_value, 'value'):
        class_value = class_value.value
    
    return CLASS_EMOJI_MAP.get(class_value, '')


def migrate_race_name(race_name: str) -> str:
    """Мигрирует старое название расы в новое"""
    if not race_name:
        return None
    
    if race_name in RACE_MIGRATION_MAP:
        return RACE_MIGRATION_MAP[race_name]
    
    if race_name in RACE_EMOJI_MAP:
        return race_name
    
    return race_name


def escape_markdown(text: str) -> str:
    """Экранирует спецсимволы Markdown"""
    special_chars = r'_*[]()~`>#+-=|{}.!'
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


def admin_only(func):
    """Декоратор: проверяет, является ли пользователь администратором"""
    from functools import wraps
    from telegram import Update
    from config import ADMINS
    
    @wraps(func)
    async def wrapper(update: Update, context, *args, **kwargs):
        if update.effective_user.id not in ADMINS:
            await update.message.reply_text("⛔ Нет доступа! Эта команда только для администраторов.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper