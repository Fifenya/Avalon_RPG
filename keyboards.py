# keyboards.py - ПОЛНАЯ РАБОЧАЯ ВЕРСИЯ
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_no_character_keyboard():
    """Клавиатура для игрока без персонажа"""
    return ReplyKeyboardMarkup([
        ["🌟 Создать персонажа", "📜 О боте"]
    ], resize_keyboard=True)

def get_races_inline():
    """Клавиатура для выбора расы"""
    keyboard = [
        [InlineKeyboardButton("🧝 Эльф", callback_data="race_🧝 Эльф")],
        [InlineKeyboardButton("👹 Демон", callback_data="race_👹 Демон")],
        [InlineKeyboardButton("🧙 Человек", callback_data="race_🧙 Человек")],
        [InlineKeyboardButton("🐾 ЗВЕРОЛЮДЫ", callback_data="race_🐾 ЗВЕРОЛЮДЫ")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_beast_folk_inline():
    """Клавиатура для выбора зверолюда"""
    from game_data import BEAST_FOLK
    keyboard = []
    row = []
    for i, race_name in enumerate(BEAST_FOLK.keys(), 1):
        row.append(InlineKeyboardButton(race_name, callback_data=f"beast_{race_name}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("◀️ Назад к расам", callback_data="back_to_races")])
    return InlineKeyboardMarkup(keyboard)

def get_genders_inline():
    """Клавиатура для выбора пола"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("♂️ Мужской", callback_data="gender_♂️ Мужской")],
        [InlineKeyboardButton("♀️ Женский", callback_data="gender_♀️ Женский")]
    ])

def get_class_keyboard():
    """Клавиатура для выбора класса"""
    from classes import CLASS_DATA
    keyboard = []
    for cls, cls_data in CLASS_DATA.items():
        keyboard.append([InlineKeyboardButton(
            cls_data['name'],
            callback_data=f"class_{cls.value}"
        )])
    return InlineKeyboardMarkup(keyboard)

def get_main_keyboard(location='city'):
    """Главный экран — ReplyKeyboardMarkup"""
    if location == 'dungeon':
        return ReplyKeyboardMarkup([
            ["🏚️ Рейд", "🗺️ Сменить локацию"],
            ["🏰 Кланы", "🏆 Топ"],
            ["📦 Инвентарь", "📦 Ресурсы"],
            ["⚔️ Экипировка", "📜 Профиль"]
        ], resize_keyboard=True)
    
    if location == 'tavern':
        return ReplyKeyboardMarkup([
            ["🍺 Сесть за стойку"],
            ["🚪 Выйти из таверны"]
        ], resize_keyboard=True)
    
    if location == 'hospital':
        return ReplyKeyboardMarkup([
            ["🗺️ Сменить локацию"]
        ], resize_keyboard=True)
    
    if location == 'forest':
        return ReplyKeyboardMarkup([
            ["🌿 Сбор ресурсов", "🗺️ Сменить локацию"],
            ["🏰 Кланы", "🏆 Топ"],
            ["📦 Инвентарь", "📦 Ресурсы"],
            ["⚔️ Экипировка", "📜 Профиль"],
        ], resize_keyboard=True)
    
    return ReplyKeyboardMarkup([
        ["💼 Работа", "🗺️ Сменить локацию"],
        ["🏪 Магазин", "🔨 Крафт"],
        ["🏰 Кланы", "🏆 Топ"],
        ["📦 Инвентарь", "📦 Ресурсы"],
        ["⚔️ Экипировка", "📜 Профиль"],
    ], resize_keyboard=True)

def get_locations_keyboard():
    """Клавиатура для выбора локации"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏰 Авалон", callback_data="loc_city"),
         InlineKeyboardButton("🌲 Дремучий лес", callback_data="loc_forest")],
        [InlineKeyboardButton("🍺 Таверна", callback_data="loc_tavern"),
         InlineKeyboardButton("🏚️ Подземелье", callback_data="loc_dungeon")],
        [InlineKeyboardButton("🔙 На главную", callback_data="main_screen")]
    ])

def get_profile_keyboard():
    """Клавиатура для профиля"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 На главную", callback_data="main_screen")]
    ])

def get_inventory_keyboard():
    """Клавиатура для инвентаря"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 На главную", callback_data="main_screen")]
    ])

def get_resources_keyboard():
    """Клавиатура для ресурсов"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 На главную", callback_data="main_screen")]
    ])

def get_equipment_keyboard():
    """Клавиатура для экрана экипировки"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Надеть предмет", callback_data="equip_wear")],
        [InlineKeyboardButton("❌ Снять предмет", callback_data="equip_remove")],
        [InlineKeyboardButton("⬆️ Улучшить ранг", callback_data="equip_upgrade")],
        [InlineKeyboardButton("🔙 На главную", callback_data="main_screen")]
    ])

def get_top_keyboard():
    """Клавиатура для топов"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Богачи", callback_data="top_money"),
         InlineKeyboardButton("⚔️ Силачи", callback_data="top_power")],
        [InlineKeyboardButton("⭐ По уровню", callback_data="top_level"),
         InlineKeyboardButton("👾 Охотники", callback_data="top_hunter")],
        [InlineKeyboardButton("🔙 На главную", callback_data="main_screen")]
    ])

def get_shop_keyboard():
    """Клавиатура для магазина"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧪 Расходники", callback_data="shop_consumables"),
         InlineKeyboardButton("⚔️ Оружие", callback_data="shop_weapons")],
        [InlineKeyboardButton("🛡️ Броня", callback_data="shop_armor"),
         InlineKeyboardButton("🔮 Магия", callback_data="shop_magic")],
        [InlineKeyboardButton("📦 Ресурсы", callback_data="shop_resources"),
         InlineKeyboardButton("✨ Особое", callback_data="shop_special")],
        [InlineKeyboardButton("🔙 На главную", callback_data="main_screen")]
    ])

def get_crafting_keyboard():
    """Клавиатура для крафта"""
    return ReplyKeyboardMarkup([
        ["🔥 Плавка", "🔨 Крафт слитков"],
        ["🔙 На главную"]
    ], resize_keyboard=True)

def get_work_keyboard(jobs_list):
    """Клавиатура для работы"""
    keyboard = []
    for job in jobs_list[:6]:
        keyboard.append([KeyboardButton(f"💼 {job['name']}")])
    keyboard.append([KeyboardButton("🔙 На главную")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_tavern_menu_keyboard():
    """Клавиатура меню таверны"""
    return ReplyKeyboardMarkup([
        ["🍺 Меню эля", "🍖 Закуска"],
        ["🎲 Сыграть в кости", "📜 Послушать истории"],
        ["🏆 Мои достижения", "🚪 Выйти из-за стойки"]
    ], resize_keyboard=True)

def get_clan_main_keyboard(has_clan=False):
    """Клавиатура для кланов"""
    if has_clan:
        return ReplyKeyboardMarkup([
            ["🏦 Банк клана", "⚙️ Управление кланом"],
            ["📋 Список кланов", "🏆 Топ кланов"],
            ["📤 Покинуть клан"],
            ["🔙 На главную"]
        ], resize_keyboard=True)
    return ReplyKeyboardMarkup([
        ["🏰 Создать клан", "🔍 Поиск клана"],
        ["📋 Список кланов", "🏆 Топ кланов"],
        ["🔙 На главную"]
    ], resize_keyboard=True)

def get_dungeon_keyboard():
    """Клавиатура для подземелья"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👾 Искать врага", callback_data="dungeon_search")],
        [InlineKeyboardButton("🏃 Выйти", callback_data="dungeon_exit")]
    ])

def get_battle_after_keyboard():
    """Клавиатура после боя"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👾 Ещё бой", callback_data="hunt_again")],
        [InlineKeyboardButton("🔙 На главную", callback_data="main_screen")]
    ])
def get_clan_bank_keyboard():
    """Клавиатура банка клана"""
    return ReplyKeyboardMarkup([
        ["📥 Положить", "📤 Взять"],
        ["📊 Статистика банка"],
        ["🔙 Назад к клану"]
    ], resize_keyboard=True)

def get_clan_confirm_keyboard():
    """Подтверждение создания клана"""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Создать", callback_data="clan_confirm_yes"),
        InlineKeyboardButton("❌ Отмена", callback_data="clan_confirm_no")
    ]])

def get_shop_items_keyboard(items, category_id):
    """Список предметов магазина"""
    keyboard = []
    for i, item in enumerate(items):
        keyboard.append([InlineKeyboardButton(
            f"{item['name']} — {item['price']}💰",
            callback_data=f"shop_buy_{category_id}_{i}"
        )])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="shop_back")])
    return InlineKeyboardMarkup(keyboard)

def get_drink_keyboard():
    """Меню эля за стойкой таверны"""
    from tavern import ALE_TYPES  # локальный импорт, чтобы не было циклического импорта
    keyboard = []
    row = []
    for ale_id, ale in ALE_TYPES.items():
        row.append(InlineKeyboardButton(
            f"{ale.get('emoji', '🍺')} {ale['name']} ({ale['price']}💰)",
            callback_data=f"order_ale_{ale_id}"
        ))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔙 Меню таверны", callback_data="tavern_menu")])
    return InlineKeyboardMarkup(keyboard)

def get_hidden_mode_keyboard():
    """Меню режима тени в бою"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💊 Зелье", callback_data="hide_use_potion"),
         InlineKeyboardButton("✨ Заклинание", callback_data="hide_use_spell")],
        [InlineKeyboardButton("🛡️ Бафф брони", callback_data="hide_use_armor"),
         InlineKeyboardButton("🧪 Пояс", callback_data="hide_belt")],
        [InlineKeyboardButton("⚔️ Оружие", callback_data="hide_change_weapon"),
         InlineKeyboardButton("🛡️ Броня", callback_data="hide_change_armor")],
        [InlineKeyboardButton("👢 Шлем/обувь", callback_data="hide_change_other"),
         InlineKeyboardButton("💍 Аксессуар", callback_data="hide_change_accessory")],
        [InlineKeyboardButton("🏃 Выйти из тени", callback_data="hide_exit")]
    ])

def _hide_back_row():
    return [InlineKeyboardButton("↩️ Назад", callback_data="hide_cancel")]

def get_hide_potion_keyboard(potions):
    keyboard = [[InlineKeyboardButton(
        f"💊 {p.get('name', 'Зелье')} (+{p.get('stats', {}).get('hp', 0)} HP)",
        callback_data=f"hide_potion_{i}")] for i, p in enumerate(potions)]
    keyboard.append(_hide_back_row())
    return InlineKeyboardMarkup(keyboard)

def get_hide_spell_keyboard(spells):
    keyboard = [[InlineKeyboardButton(
        f"✨ {s.get('name', 'Заклинание')} ({s.get('ap_cost', s.get('mana_cost', 0))} MP)",
        callback_data=f"hide_spell_{i}")] for i, s in enumerate(spells)]
    keyboard.append(_hide_back_row())
    return InlineKeyboardMarkup(keyboard)

def get_hide_armor_buff_keyboard(armor):
    keyboard = [[InlineKeyboardButton(
        f"🛡️ {b.get('name', 'Бафф')}",
        callback_data=f"hide_armor_buff_{i}")] for i, b in enumerate(armor.get('buffs', []))]
    keyboard.append(_hide_back_row())
    return InlineKeyboardMarkup(keyboard)

def get_hide_equip_keyboard(items, item_type):
    keyboard = [[InlineKeyboardButton(
        f"⚔️ {item.get('name', 'Предмет')}",
        callback_data=f"hide_equip_{item_type}_{i}")] for i, item in enumerate(items)]
    keyboard.append(_hide_back_row())
    return InlineKeyboardMarkup(keyboard)

def get_hide_belt_keyboard(potions):
    keyboard = [[InlineKeyboardButton(
        f"🧪 {p.get('name', 'Зелье')}",
        callback_data=f"hide_belt_{i}")] for i, p in enumerate(potions)]
    keyboard.append(_hide_back_row())
    return InlineKeyboardMarkup(keyboard)