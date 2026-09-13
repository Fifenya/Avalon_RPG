# game/data.py
"""Все игровые данные в одном месте"""

import random
from typing import Dict, List, Optional, Tuple

# ===== РАСЫ =====
RACES = {
    '🧝 Эльф': {'mult': 1.1, 'bonus': 5, 'dodge': 0.05, 'city_id': 'elf_forest'},
    '👹 Демон': {'mult': 1.0, 'bonus': 15, 'power': 5, 'city_id': 'demon_gates'},
    '🧙 Человек': {'mult': 1.15, 'bonus': 0, 'luck': 0.02, 'city_id': 'human_citadel'},
    '🐺 Волколюд': {'mult': 1.05, 'bonus': 10, 'crit': 0.05, 'city_id': 'beast_woods'},
    '🐱 Кошколюд': {'mult': 1.08, 'bonus': 7, 'dodge': 0.08, 'crit': 0.02, 'city_id': 'moon_hollow'},
    '🐻 Медведолюд': {'mult': 1.0, 'bonus': 15, 'armor': 10, 'city_id': 'bear_mountains'},
    '🦊 Лисолюд': {'mult': 1.1, 'bonus': 5, 'luck': 0.07, 'dodge': 0.03, 'city_id': 'fox_mist'},
    '🐉 Драконолюд': {'mult': 0.95, 'bonus': 20, 'power': 10, 'city_id': 'dragon_peak'},
    '🐦 Птицелюд': {'mult': 1.15, 'bonus': 3, 'dodge': 0.10, 'city_id': 'sky_nest'},
    '🐍 Змеелюд': {'mult': 1.0, 'bonus': 12, 'crit': 0.07, 'city_id': 'serpent_temple'},
    '🐗 Кабанолюд': {'mult': 1.02, 'bonus': 12, 'armor': 8, 'power': 5, 'city_id': 'boar_marsh'},
    '🦌 Оленелюд': {'mult': 1.12, 'bonus': 4, 'dodge': 0.05, 'city_id': 'deer_meadow'},
}

# ===== ЛОКАЦИИ =====
LOCATIONS = {
    'city': {'name': '🏰 Авалон', 'desc': 'Величественный город...', 'can_hunt': False, 'can_work': True},
    'forest': {'name': '🌲 Дремучий лес', 'desc': 'Таинственный лес...', 'can_hunt': True, 'can_work': True},
    'tavern': {'name': '🍺 Таверна', 'desc': 'Уютное место...', 'can_hunt': False, 'can_work': True},
    'dungeon': {'name': '🏚️ Глубинная Бездна', 'desc': 'Тёмные подземелья...', 'can_hunt': False, 'can_work': False},
    'hospital': {'name': '🏥 Госпиталь Святого Клинка', 'desc': 'Святое место...', 'can_hunt': False, 'can_work': False},
}

# Добавляем города рас
for race_name, race_data in RACES.items():
    city_id = race_data.get('city_id')
    if city_id:
        LOCATIONS[city_id] = {
            'name': race_name,
            'desc': f'Родной город {race_name}',
            'can_hunt': True,
            'can_work': True,
            'is_race_city': True,
            'race': race_name
        }


def get_race_city(race_name: str) -> Optional[str]:
    """Возвращает ID города для расы"""
    race_data = RACES.get(race_name, {})
    return race_data.get('city_id')


def can_travel_to(from_city: str, to_city: str, player_race: str = None) -> Tuple[bool, str]:
    """Проверяет возможность перемещения между городами"""
    
    # В подземелье можно войти из любой локации
    if to_city == 'dungeon':
        return True, ""
    
    # Из подземелья можно выйти только в город
    if from_city == 'dungeon':
        if to_city == 'city':
            return True, ""
        return False, "🏚️ Из подземелья можно выйти только в Авалон!"
    
    # Авалон — центральный хаб
    if to_city == 'city' or from_city == 'city':
        return True, ""
    
    # Из больницы можно выйти только в город
    if from_city == 'hospital':
        if to_city == 'city':
            return True, ""
        return False, "🏥 Ты в больнице! Сначала вылечись, затем иди в Авалон."
    
    # В больницу можно попасть только при смерти
    if to_city == 'hospital':
        return False, "🏥 В больницу можно попасть только при смерти или ранении."
    
    # Из таверны можно выйти только в город
    if from_city == 'tavern':
        if to_city == 'city':
            return True, ""
        return False, "🍺 Из таверны можно попасть только в Авалон!"
    
    # Если игрок в своём родном городе
    if player_race:
        race_city = RACE_CITIES.get(player_race, {}).get("city_id")
        if from_city == race_city:
            if to_city == "city":
                return True, ""
            return False, f"🌍 Из твоего родного города можно попасть только в Авалон!"
    
    return False, "🌍 Этот путь недоступен! Сначала доберись до Авалона."


def get_city_travel_text(from_city: str, to_city: str) -> str:
    """Возвращает текст путешествия"""
    texts = {
        ('city', 'elf_forest'): "Ты входишь в древний Эльфийский лес...",
        ('city', 'demon_gates'): "Ты спускаешься к Вратам Бездны...",
        ('city', 'human_citadel'): "Ты идёшь к величественной цитадели людей...",
        ('city', 'beast_woods'): "Ты углубляешься в Лесную чащу...",
        ('city', 'moon_hollow'): "Лунный свет ведёт тебя в Лунную лощину...",
        ('city', 'bear_mountains'): "Ты поднимаешься в Медвежьи горы...",
        ('city', 'fox_mist'): "Туман расступается перед тобой...",
        ('city', 'dragon_peak'): "Ты чувствуешь древнюю силу Пика Дракона...",
        ('city', 'sky_nest'): "Лёгкий ветер поднимает тебя к Небесному гнезду...",
        ('city', 'serpent_temple'): "Тёмные тени ведут тебя к Храму Змея...",
        ('city', 'boar_marsh'): "Ты ступаешь на зыбкую почву Кабаньего болота...",
        ('city', 'deer_meadow'): "Солнечный свет озаряет Оленью лужайку...",
    }
    return texts.get((from_city, to_city), "Ты отправляешься в путь...")


# ===== ФУНКЦИИ ДЛЯ РАБОТЫ С МАГАЗИНОМ ИЗ race_cities.py =====

RACE_CITIES = RACES  # Для обратной совместимости

CITY_SHOPS = {
    "elf_forest": {
        "name": "🏹 Лесной дозор",
        "specialty": "🏹 Лучное дело",
        "items": [
            {"name": "🏹 Эльфийский лук", "price": 800, "type": "weapon", "stats": {"power": 12, "crit": 0.05}},
            {"name": "🌿 Зелье природы", "price": 60, "type": "potion", "stats": {"hp": 40, "mana": 20}},
            {"name": "🍃 Эльфийский плащ", "price": 500, "type": "armor", "stats": {"dodge": 0.08, "armor": 5}},
        ]
    },
    "demon_gates": {
        "name": "⚔️ Кузница Бездны",
        "specialty": "⚔️ Тяжёлое оружие",
        "items": [
            {"name": "🔥 Демонический клинок", "price": 1000, "type": "weapon", "stats": {"power": 18, "crit": 0.03}},
            {"name": "🛡️ Адская броня", "price": 1200, "type": "armor", "stats": {"armor": 25, "hp": 80}},
            {"name": "💀 Камень тьмы", "price": 300, "type": "accessory", "stats": {"power": 5, "spell_damage": 8}},
        ]
    },
    "human_citadel": {
        "name": "🏪 Торговая площадь",
        "specialty": "🔨 Ремёсла",
        "items": [
            {"name": "⚔️ Стальной меч", "price": 600, "type": "weapon", "stats": {"power": 10}},
            {"name": "🔧 Набор инструментов", "price": 200, "type": "item", "stats": {"craft_bonus": 0.1}},
            {"name": "📦 Сундук ресурсов", "price": 500, "type": "item", "stats": {"resources": 10}},
        ]
    },
    "beast_woods": {
        "name": "🏹 Охотничья заимка",
        "specialty": "🏹 Охота",
        "items": [
            {"name": "🏹 Лук охотника", "price": 700, "type": "weapon", "stats": {"power": 10, "crit": 0.07}},
            {"name": "🐺 Волчий амулет", "price": 400, "type": "accessory", "stats": {"hunt_reward": 0.15}},
            {"name": "🪤 Капкан", "price": 100, "type": "item", "stats": {"hunt_bonus": 0.1}},
        ]
    },
    "moon_hollow": {
        "name": "🗡️ Лунный коготь",
        "specialty": "🗡️ Лёгкое оружие",
        "items": [
            {"name": "🗡️ Когти луны", "price": 750, "type": "weapon", "stats": {"power": 9, "crit": 0.12}},
            {"name": "🌙 Амулет удачи", "price": 500, "type": "accessory", "stats": {"luck": 0.1, "crit": 0.03}},
            {"name": "💨 Плащ невидимости", "price": 800, "type": "armor", "stats": {"dodge": 0.15}},
        ]
    },
    "bear_mountains": {
        "name": "⛏️ Горная кузница",
        "specialty": "⛏️ Добыча",
        "items": [
            {"name": "⛏️ Кирка", "price": 300, "type": "tool", "stats": {"mining_bonus": 0.2}},
            {"name": "🛡️ Медвежья шкура", "price": 600, "type": "armor", "stats": {"armor": 18, "hp": 40}},
            {"name": "🗡️ Топор берсерка", "price": 900, "type": "weapon", "stats": {"power": 15, "crit": 0.04}},
        ]
    },
    "fox_mist": {
        "name": "🔮 Лавка чудес",
        "specialty": "🔮 Магия",
        "items": [
            {"name": "🔮 Хрустальный шар", "price": 800, "type": "weapon", "stats": {"spell_damage": 12, "power": 5}},
            {"name": "🍀 Зелье удачи", "price": 150, "type": "potion", "stats": {"luck": 0.2}},
            {"name": "🦊 Лисьи чары", "price": 400, "type": "accessory", "stats": {"dodge": 0.1, "luck": 0.05}},
        ]
    },
    "dragon_peak": {
        "name": "🐉 Драконье пламя",
        "specialty": "🐉 Драконья магия",
        "items": [
            {"name": "🐉 Коготь дракона", "price": 1500, "type": "weapon", "stats": {"power": 25, "fire_damage": 15}},
            {"name": "🔥 Дыхание дракона", "price": 600, "type": "spell", "stats": {"spell_damage": 20}},
            {"name": "🛡️ Чешуя дракона", "price": 1000, "type": "armor", "stats": {"armor": 30, "fire_resist": 0.5}},
        ]
    },
    "sky_nest": {
        "name": "☁️ Ветряная мастерская",
        "specialty": "💨 Скорость",
        "items": [
            {"name": "🏹 Ветряной лук", "price": 850, "type": "weapon", "stats": {"power": 11, "speed": 5}},
            {"name": "💨 Перья ветра", "price": 350, "type": "accessory", "stats": {"dodge": 0.12, "speed": 3}},
            {"name": "☁️ Облачный плащ", "price": 700, "type": "armor", "stats": {"dodge": 0.1, "speed": 4}},
        ]
    },
    "serpent_temple": {
        "name": "🐍 Змеиный клык",
        "specialty": "☠️ Яды",
        "items": [
            {"name": "🐍 Змеиный клинок", "price": 850, "type": "weapon", "stats": {"power": 12, "poison_damage": 5}},
            {"name": "☠️ Яд скорпиона", "price": 200, "type": "consumable", "stats": {"poison": 10}},
            {"name": "🐍 Амулет змеи", "price": 450, "type": "accessory", "stats": {"poison_resist": 0.3, "dark_resist": 0.2}},
        ]
    },
    "boar_marsh": {
        "name": "🌿 Травная лавка",
        "specialty": "🌿 Травничество",
        "items": [
            {"name": "🌿 Целительная трава", "price": 100, "type": "potion", "stats": {"hp": 50}},
            {"name": "🧪 Эликсир выносливости", "price": 300, "type": "potion", "stats": {"endurance": 20}},
            {"name": "📜 Рецепт зелья", "price": 500, "type": "item", "stats": {"craft": "heal_potion"}},
        ]
    },
    "deer_meadow": {
        "name": "🌾 Собирательский рынок",
        "specialty": "🌿 Сбор ресурсов",
        "items": [
            {"name": "🧺 Корзина сборщика", "price": 200, "type": "tool", "stats": {"gathering_bonus": 0.15}},
            {"name": "🌿 Священная трава", "price": 150, "type": "potion", "stats": {"hp": 45, "mana": 30}},
            {"name": "🦌 Рога оленя", "price": 400, "type": "accessory", "stats": {"speed": 3, "nature_power": 5}},
        ]
    }
}


def get_city_shop(city_id: str) -> Optional[dict]:
    """Возвращает магазин города"""
    return CITY_SHOPS.get(city_id)


def get_city_shop_keyboard(city_id: str):
    """Создаёт клавиатуру для магазина города"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    shop = CITY_SHOPS.get(city_id)
    if not shop:
        return None
    
    keyboard = []
    for i, item in enumerate(shop["items"]):
        keyboard.append([InlineKeyboardButton(
            f"{item['name']} — {item['price']}💰",
            callback_data=f"race_shop_buy_{city_id}_{i}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 На главную", callback_data="main_screen")])
    
    return InlineKeyboardMarkup(keyboard)


# ===== ВРАГИ =====
class Enemy:
    def __init__(self, name, hp, power, armor, reward, exp, level, element="physical", resistances=None, is_boss=False):
        self.name = name
        self.max_hp = self.hp = hp
        self.power = power
        self.armor = armor
        self.reward = reward
        self.exp = exp
        self.level = level
        self.element = element
        self.resistances = resistances or {}
        self.is_boss = is_boss
    
    def get_rank_display(self):
        from rank_system import RankSystem
        return RankSystem.format_monster_rank(self.level)


# Враги по уровням
ENEMIES_BY_LEVEL = {
    (1, 3): [
        {"name": "🐀 Крыса-мутант", "hp": 85, "power": 12, "armor": 5, "reward": 45, "exp": 6, "level": 1},
        {"name": "🦇 Летучая мышь", "hp": 70, "power": 10, "armor": 3, "reward": 40, "exp": 5, "level": 1},
        {"name": "🐺 Голодный волк", "hp": 120, "power": 18, "armor": 10, "reward": 75, "exp": 10, "level": 3},
    ],
    (4, 6): [
        {"name": "🧟 Зомби", "hp": 200, "power": 25, "armor": 15, "reward": 150, "exp": 18, "level": 4},
        {"name": "⚰️ Вампир", "hp": 240, "power": 28, "armor": 18, "reward": 180, "exp": 22, "level": 5},
        {"name": "🐗 Оборотень", "hp": 280, "power": 32, "armor": 22, "reward": 220, "exp": 26, "level": 6},
    ],
    (7, 9): [
        {"name": "🐉 Молодой дракон", "hp": 400, "power": 45, "armor": 25, "reward": 400, "exp": 35, "level": 8},
        {"name": "👹 Огр", "hp": 500, "power": 40, "armor": 30, "reward": 450, "exp": 38, "level": 7},
        {"name": "🧙 Тёмный маг", "hp": 300, "power": 55, "armor": 15, "reward": 550, "exp": 45, "level": 8},
    ],
    (10, 15): [
        {"name": "👁️ Древний ужас", "hp": 800, "power": 60, "armor": 40, "reward": 800, "exp": 55, "level": 12},
        {"name": "🐲 Дракон", "hp": 1200, "power": 80, "armor": 50, "reward": 1200, "exp": 80, "level": 15},
        {"name": "👾 Повелитель бездны", "hp": 1500, "power": 100, "armor": 60, "reward": 2000, "exp": 120, "level": 15},
    ],
}

# Боссы
BOSSES = [
    {"name": "👾 Ктулху", "hp": 3000, "power": 150, "armor": 80, "reward": 5000, "exp": 300, "level": 20, "is_boss": True},
    {"name": "🔥 Феникс", "hp": 2500, "power": 120, "armor": 40, "reward": 4000, "exp": 250, "level": 18, "is_boss": True},
    {"name": "💀 Король Личей", "hp": 3500, "power": 130, "armor": 60, "reward": 6000, "exp": 350, "level": 22, "is_boss": True},
    {"name": "🌑 Властелин Теней", "hp": 4000, "power": 140, "armor": 50, "reward": 7000, "exp": 400, "level": 25, "is_boss": True},
    {"name": "🏛️ Титан", "hp": 8000, "power": 200, "armor": 120, "reward": 15000, "exp": 800, "level": 30, "is_boss": True},
]


def get_random_enemy(player_level=1):
    """Получить случайного монстра под уровень игрока (с шансом на босса)"""
    # Шанс на босса (3% на уровне 10+, 1% ниже)
    boss_chance = 0.03 if player_level >= 10 else 0.01
    
    if random.random() < boss_chance:
        boss = random.choice(BOSSES)
        return Enemy(
            name=boss["name"],
            hp=boss["hp"],
            power=boss["power"],
            armor=boss["armor"],
            reward=boss["reward"],
            exp=boss["exp"],
            level=boss["level"],
            is_boss=boss.get("is_boss", True)
        )
    
    for (lvl_min, lvl_max), enemies in ENEMIES_BY_LEVEL.items():
        if lvl_min <= player_level <= lvl_max:
            enemy_data = random.choice(enemies)
            hp_var = int(enemy_data["hp"] * random.uniform(0.95, 1.05))
            power_var = int(enemy_data["power"] * random.uniform(0.95, 1.05))
            return Enemy(
                name=enemy_data["name"],
                hp=hp_var,
                power=power_var,
                armor=enemy_data["armor"],
                reward=enemy_data["reward"],
                exp=enemy_data["exp"],
                level=enemy_data["level"],
                is_boss=False
            )
    
    return Enemy("🐀 Крыса-мутант", 85, 12, 5, 45, 6, 1, is_boss=False)


# ===== ПРОФЕССИИ (работы) =====
JOBS_BY_LOCATION = {
    'city': {
        'name': '🏙️ Городские профессии',
        'jobs': [
            {'name': '📦 Грузчик', 'desc': 'Таскать ящики на складе', 'min_earn': 50, 'max_earn': 150, 'exp_reward': 5, 'time': 30, 'requirements': {'level': 1}},
            {'name': '🔧 Помощник кузнеца', 'desc': 'Помогать в кузнице', 'min_earn': 100, 'max_earn': 250, 'exp_reward': 10, 'time': 45, 'requirements': {'level': 3, 'power': 60}},
        ]
    },
    'forest': {
        'name': '🌲 Лесные профессии',
        'jobs': [
            {'name': '🪓 Лесоруб', 'desc': 'Рубить деревья', 'min_earn': 80, 'max_earn': 200, 'exp_reward': 8, 'time': 40, 'requirements': {'level': 2}},
            {'name': '🧺 Травник', 'desc': 'Собирать лечебные травы', 'min_earn': 60, 'max_earn': 180, 'exp_reward': 7, 'time': 35, 'requirements': {'level': 1}},
        ]
    },
    'tavern': {
        'name': '🍺 Таверна',
        'jobs': [
            {'name': '🍻 Бармен', 'desc': 'Наливать эль и слушать истории', 'min_earn': 70, 'max_earn': 180, 'exp_reward': 6, 'time': 35, 'requirements': {'level': 1}},
            {'name': '🥩 Повар', 'desc': 'Готовить еду для посетителей', 'min_earn': 90, 'max_earn': 220, 'exp_reward': 9, 'time': 40, 'requirements': {'level': 2}},
        ]
    }
}