# game_data.py - ПОЛНАЯ ВЕРСИЯ
import random
from rank_system import RankSystem

# ===== РАСЫ =====
RACES = {
    '🧝 Эльф': {'mult': 1.1, 'bonus': 5, 'dodge': 0.05},
    '👹 Демон': {'mult': 1.0, 'bonus': 15, 'power': 5},
    '🧙 Человек': {'mult': 1.15, 'bonus': 0, 'luck': 0.02},
}

BEAST_FOLK = {
    '🐺 Волколюд': {'mult': 1.05, 'bonus': 10, 'crit': 0.05, 'desc': '🐺 Сила стаи течёт в твоих жилах.'},
    '🐱 Кошколюд': {'mult': 1.08, 'bonus': 7, 'dodge': 0.08, 'crit': 0.02, 'desc': '🐱 Кошачья грация делает тебя неуловимым.'},
    '🐻 Медведолюд': {'mult': 1.0, 'bonus': 15, 'armor': 10, 'hp_bonus': 50, 'desc': '🐻 Мощь медведя в твоих руках.'},
    '🦊 Лисолюд': {'mult': 1.1, 'bonus': 5, 'luck': 0.07, 'dodge': 0.03, 'desc': '🦊 Хитрость лисы помогает находить редкую добычу.'},
    '🐉 Драконолюд': {'mult': 0.95, 'bonus': 20, 'power': 10, 'hp_bonus': 100, 'desc': '🐉 Драконья кровь делает тебя невероятно сильным.'},
    '🐦 Птицелюд': {'mult': 1.15, 'bonus': 3, 'dodge': 0.10, 'desc': '🐦 Лёгкий как пёрышко, быстрый как ветер.'},
    '🐍 Змеелюд': {'mult': 1.0, 'bonus': 12, 'crit': 0.07, 'desc': '🐍 Холодная кровь и смертельный яд.'},
    '🐗 Кабанолюд': {'mult': 1.02, 'bonus': 12, 'armor': 8, 'power': 5, 'desc': '🐗 Ты несёшься напролом, не зная страха.'},
    '🦌 Оленелюд': {'mult': 1.12, 'bonus': 4, 'dodge': 0.05, 'desc': '🦌 Благородный и быстрый.'}
}

ALL_RACES = {**RACES, **BEAST_FOLK}
GENDERS = ['♂️ Мужской', '♀️ Женский']

# ===== ГОРОДА ДЛЯ РАЗНЫХ РАС =====
RACE_CITIES = {
    "🧝 Эльф": {
        "city_id": "elf_forest",
        "name": "🌳 Эльфийский лес",
        "emoji": "🌳",
        "desc": "Древний лес, где эльфы живут в гармонии с природой.",
        "image": "images/locations/elf_forest.jpg",
        "traits": ["nature_magic", "archery", "agility"],
        "specialization": "🏹 Лучное дело и магия природы",
        "shop_specialization": "bows_nature"
    },
    "👹 Демон": {
        "city_id": "demon_gates",
        "name": "🔥 Врата Бездны",
        "emoji": "🔥",
        "desc": "Мрачные земли, где демоны куют оружие в лаве.",
        "image": "images/locations/demon_gates.jpg",
        "traits": ["fire_magic", "strength", "darkness"],
        "specialization": "⚔️ Тяжёлое оружие и демоническая магия",
        "shop_specialization": "weapons_dark"
    },
    "🧙 Человек": {
        "city_id": "human_citadel",
        "name": "🏰 Человеческая цитадель",
        "emoji": "🏰",
        "desc": "Величественная крепость людей. Центр торговли и ремёсел.",
        "image": "images/locations/human_citadel.jpg",
        "traits": ["versatility", "trade", "crafting"],
        "specialization": "🔨 Ремёсла и торговля",
        "shop_specialization": "crafting_trade"
    },
    "🐺 Волколюд": {
        "city_id": "beast_woods",
        "name": "🌲 Лесная чаща",
        "emoji": "🌲",
        "desc": "Густой лес, где зверолюды живут в единстве с природой.",
        "image": "images/locations/beast_woods.jpg",
        "traits": ["hunting", "tracking", "survival"],
        "specialization": "🏹 Охота и сбор ресурсов",
        "shop_specialization": "hunting_gathering"
    },
    "🐱 Кошколюд": {
        "city_id": "moon_hollow",
        "name": "🌙 Лунная лощина",
        "emoji": "🌙",
        "desc": "Таинственное место, где кошколюды практикуют скрытность и ловкость.",
        "image": "images/locations/moon_hollow.jpg",
        "traits": ["stealth", "agility", "luck"],
        "specialization": "🗡️ Лёгкое оружие и скрытность",
        "shop_specialization": "light_weapons"
    },
    "🐻 Медведолюд": {
        "city_id": "bear_mountains",
        "name": "⛰️ Медвежьи горы",
        "emoji": "⛰️",
        "desc": "Суровые горы, где медведолюды добывают редкие руды.",
        "image": "images/locations/bear_mountains.jpg",
        "traits": ["strength", "mining", "endurance"],
        "specialization": "⛏️ Добыча ресурсов и тяжёлая броня",
        "shop_specialization": "mining_armor"
    },
    "🦊 Лисолюд": {
        "city_id": "fox_mist",
        "name": "🌫️ Туманная долина",
        "emoji": "🌫️",
        "desc": "Таинственная долина, окутанная туманом.",
        "image": "images/locations/fox_mist.jpg",
        "traits": ["cunning", "luck", "illusion"],
        "specialization": "🔮 Магия иллюзий и удача",
        "shop_specialization": "magic_luck"
    },
    "🐉 Драконолюд": {
        "city_id": "dragon_peak",
        "name": "🏔️ Пик Дракона",
        "emoji": "🏔️",
        "desc": "Высочайшая гора, где драконолюды поклоняются древним драконам.",
        "image": "images/locations/dragon_peak.jpg",
        "traits": ["fire_magic", "strength", "pride"],
        "specialization": "🐉 Драконья магия и сила",
        "shop_specialization": "dragon_magic"
    },
    "🐦 Птицелюд": {
        "city_id": "sky_nest",
        "name": "☁️ Небесное гнездо",
        "emoji": "☁️",
        "desc": "Город в облаках, где птицелюды строят свои гнёзда.",
        "image": "images/locations/sky_nest.jpg",
        "traits": ["speed", "wind_magic", "perception"],
        "specialization": "💨 Скорость и ветряная магия",
        "shop_specialization": "speed_wind"
    },
    "🐍 Змеелюд": {
        "city_id": "serpent_temple",
        "name": "🐍 Храм Змея",
        "emoji": "🐍",
        "desc": "Древний храм, где змеелюды практикуют яды и тёмную магию.",
        "image": "images/locations/serpent_temple.jpg",
        "traits": ["poison", "dark_magic", "deception"],
        "specialization": "☠️ Яды и тёмная магия",
        "shop_specialization": "poison_dark"
    },
    "🐗 Кабанолюд": {
        "city_id": "boar_marsh",
        "name": "🏞️ Кабанье болото",
        "emoji": "🏞️",
        "desc": "Топкие болота, где кабанолюды добывают редкие травы.",
        "image": "images/locations/boar_marsh.jpg",
        "traits": ["endurance", "herbalism", "strength"],
        "specialization": "🌿 Травничество и выносливость",
        "shop_specialization": "herbalism"
    },
    "🦌 Оленелюд": {
        "city_id": "deer_meadow",
        "name": "🌾 Оленья лужайка",
        "emoji": "🌾",
        "desc": "Цветущие луга, где оленелюды пасут стада и собирают урожай.",
        "image": "images/locations/deer_meadow.jpg",
        "traits": ["speed", "nature_magic", "herbalism"],
        "specialization": "🌿 Природная магия и сбор",
        "shop_specialization": "nature_herbs"
    }
}

# ===== МАГАЗИНЫ ГОРОДОВ =====
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

# ===== НЕЙТРАЛЬНЫЕ ГОРОДА =====
NEUTRAL_CITIES = {
    "avalon": {
        "name": "🏰 Авалон",
        "emoji": "🏰",
        "desc": "Великий центральный город, куда стекаются все расы.",
        "image": "images/locations/Avalon.jpeg",
        "is_hub": True
    },
    "hospital": {
        "name": "🏥 Госпиталь Святого Клинка",
        "emoji": "🏥",
        "desc": "Место лечения раненых героев.",
        "image": "images/locations/hospital.jpg"
    }
}

# ===== ЛОКАЦИИ =====
LOCATIONS = {
    'city': {
        'name': '🏰 Авалон',
        'desc': 'Величественный город, центр магии и приключений.',
        'image': 'images/locations/Avalon.jpg',
        'can_hunt': False,
        'can_work': True
    },
    'forest': {
        'name': '🌲 Дремучий лес',
        'desc': 'Таинственный лес, полный опасных тварей.',
        'image': 'images/locations/forest.jpg',
        'can_hunt': True,
        'can_work': True
    },
    'tavern': {
        'name': '🍺 Таверна',
        'desc': 'Уютное место с тёплым очагом и вкусным элем.',
        'image': 'images/locations/Tavern.jpeg',
        'can_hunt': False,
        'can_work': True
    },
    'dungeon': {
        'name': '🏚️ Глубинная Бездна',
        'desc': 'Тёмные подземелья, полные чудовищ и сокровищ.',
        'image': 'images/locations/dungeon.jpeg',
        'can_hunt': False,
        'can_work': False,
        'is_dungeon': True
    },
    'hospital': {
        'name': '🏥 Госпиталь Святого Клинка',
        'desc': 'Святое место, где лечат раненых героев.',
        'image': 'images/locations/hospital.jpeg',
        'can_hunt': False,
        'can_work': False,
        'is_hospital': True
    }
}

# Добавляем города рас в LOCATIONS
for race_name, city_data in RACE_CITIES.items():
    LOCATIONS[city_data["city_id"]] = {
        'name': city_data["name"],
        'desc': city_data["desc"],
        'image': city_data["image"],
        'can_hunt': True,
        'can_work': True,
        'is_race_city': True,
        'race': race_name
    }

# ===== РЕСУРСЫ =====
RESOURCES = {
    "iron_ore": {"name": "🪨 Железная руда", "type": "ore", "value": 15},
    "coal": {"name": "🪨 Уголь", "type": "ore", "value": 8},
    "iron_shard": {"name": "⚙️ Железный осколок", "type": "shard", "value": 20},
    "iron_ingot": {"name": "🏭 Железный слиток", "type": "ingot", "value": 60},
    "steel_ingot": {"name": "🏭 Стальной слиток", "type": "ingot", "value": 100},
    "mithril_ore": {"name": "✨ Мифриловая руда", "type": "ore", "value": 100},
    "mithril_shard": {"name": "✨ Мифриловый осколок", "type": "shard", "value": 50},
    "mithril_ingot": {"name": "✨ Мифриловый слиток", "type": "ingot", "value": 300},
    "leather": {"name": "🧵 Кожа", "type": "material", "value": 10},
    "cloth": {"name": "🧶 Ткань", "type": "material", "value": 8},
    "wood": {"name": "🪵 Древесина", "type": "material", "value": 5},
    "herb": {"name": "🌿 Лечебная трава", "type": "material", "value": 10},
    "berry": {"name": "🍓 Ягоды", "type": "material", "value": 3},
    "mushroom": {"name": "🍄 Гриб", "type": "material", "value": 8},
    "elf_herb": {"name": "✨ Эльфийская трава", "type": "material", "value": 20},
    "magic_dust": {"name": "✨ Магическая пыльца", "type": "magic", "value": 30},
    "small_magic_stone": {"name": "💎 Малый магический камень", "type": "magic", "value": 50},
    "medium_magic_stone": {"name": "💎 Средний магический камень", "type": "magic", "value": 150},
    "large_magic_stone": {"name": "💎 Большой магический камень", "type": "magic", "value": 500},
    "dragon_scale": {"name": "🐉 Чешуя дракона", "type": "material", "value": 200},
    "dragon_heart": {"name": "❤️ Сердце дракона", "type": "material", "value": 1000, "boss_only": True},
    "dragon_bone": {"name": "🦴 Кость дракона", "type": "material", "value": 300, "boss_only": True},
    "demon_essence": {"name": "👿 Эссенция демона", "type": "magic", "value": 800, "boss_only": True},
    "lich_philactery": {"name": "💀 Филактерия лича", "type": "material", "value": 600, "boss_only": True},
    "shadow_core": {"name": "🌑 Теневой кристалл", "type": "magic", "value": 400, "boss_only": True},
    "ancient_wood": {"name": "🌳 Древняя древесина", "type": "material", "value": 150},
    "phoenix_feather": {"name": "🔥 Перо феникса", "type": "material", "value": 1000, "boss_only": True},
    "titan_steel": {"name": "🏛️ Титановая сталь", "type": "ingot", "value": 1500, "boss_only": True},
    "scrap_metal": {"name": "🔩 Металлолом", "type": "material", "value": 8},
}

# ===== РЕЦЕПТЫ ПЛАВКИ =====
SMELTING_RECIPES = {
    "iron_shard": {
        "name": "⚙️ Железный осколок",
        "materials": {"iron_ore": 1, "coal": 1},
        "result": "iron_shard",
        "result_count": 1,
        "time": 30
    },
    "mithril_shard": {
        "name": "✨ Мифриловый осколок",
        "materials": {"mithril_ore": 1, "coal": 2, "small_magic_stone": 1},
        "result": "mithril_shard",
        "result_count": 1,
        "time": 60
    }
}

# ===== РЕЦЕПТЫ КРАФТА СЛИТКОВ =====
CRAFT_RECIPES = {
    "iron_ingot": {
        "name": "🏭 Железный слиток",
        "materials": {"iron_shard": 3},
        "result": "iron_ingot",
        "result_count": 1,
        "time": 10
    },
    "steel_ingot": {
        "name": "🏭 Стальной слиток",
        "materials": {"iron_ingot": 2, "coal": 2},
        "result": "steel_ingot",
        "result_count": 1,
        "time": 20
    },
    "mithril_ingot": {
        "name": "✨ Мифриловый слиток",
        "materials": {"mithril_shard": 3, "small_magic_stone": 1},
        "result": "mithril_ingot",
        "result_count": 1,
        "time": 30
    }
}

# ===== РЕЦЕПТЫ ЭКИПИРОВКИ =====
EQUIPMENT_RECIPES = {}

# Железный сет
IRON_SET = {
    "iron_sword": {
        "name": "⚔️ Железный меч",
        "type": "weapon",
        "materials": {"iron_ingot": 2, "leather": 1},
        "result_count": 1,
        "time": 20,
        "stats": {"power": 8},
        "rank": "F"
    },
    "iron_chestplate": {
        "name": "🛡️ Железный нагрудник",
        "type": "armor",
        "materials": {"iron_ingot": 5, "leather": 2},
        "result_count": 1,
        "time": 40,
        "stats": {"armor": 15, "hp": 50},
        "rank": "F"
    },
    "iron_helmet": {
        "name": "⛑️ Железный шлем",
        "type": "helmet",
        "materials": {"iron_ingot": 3, "leather": 1},
        "result_count": 1,
        "time": 25,
        "stats": {"armor": 8, "hp": 20},
        "rank": "F"
    },
    "iron_boots": {
        "name": "👢 Железные сапоги",
        "type": "boots",
        "materials": {"iron_ingot": 3, "leather": 2},
        "result_count": 1,
        "time": 25,
        "stats": {"armor": 6, "dodge": 0.02},
        "rank": "F"
    },
    "iron_shield": {
        "name": "🛡️ Железный щит",
        "type": "shield",
        "materials": {"iron_ingot": 4, "leather": 1},
        "result_count": 1,
        "time": 30,
        "stats": {"armor": 12, "block": 0.05},
        "rank": "F"
    }
}

# Стальной сет
STEEL_SET = {
    "steel_sword": {
        "name": "⚔️ Стальной меч",
        "type": "weapon",
        "materials": {"steel_ingot": 2, "leather": 2},
        "result_count": 1,
        "time": 30,
        "stats": {"power": 15, "crit": 0.05},
        "rank": "D"
    },
    "steel_chestplate": {
        "name": "🛡️ Стальной нагрудник",
        "type": "armor",
        "materials": {"steel_ingot": 4, "leather": 3},
        "result_count": 1,
        "time": 50,
        "stats": {"armor": 25, "hp": 80},
        "rank": "D"
    },
    "steel_helmet": {
        "name": "⛑️ Стальной шлем",
        "type": "helmet",
        "materials": {"steel_ingot": 2, "leather": 2},
        "result_count": 1,
        "time": 30,
        "stats": {"armor": 12, "hp": 35},
        "rank": "D"
    },
    "steel_boots": {
        "name": "👢 Стальные сапоги",
        "type": "boots",
        "materials": {"steel_ingot": 2, "leather": 3},
        "result_count": 1,
        "time": 30,
        "stats": {"armor": 10, "dodge": 0.03},
        "rank": "D"
    },
    "steel_shield": {
        "name": "🛡️ Стальной щит",
        "type": "shield",
        "materials": {"steel_ingot": 3, "leather": 2},
        "result_count": 1,
        "time": 40,
        "stats": {"armor": 20, "block": 0.08},
        "rank": "D"
    }
}

# Мифриловый сет
MITHRIL_SET = {
    "mithril_sword": {
        "name": "⚔️ Мифриловый меч",
        "type": "weapon",
        "materials": {"mithril_ingot": 2, "leather": 2, "small_magic_stone": 2},
        "result_count": 1,
        "time": 45,
        "stats": {"power": 25, "crit": 0.08, "spell_damage": 10},
        "rank": "B"
    },
    "mithril_chestplate": {
        "name": "🛡️ Мифриловая броня",
        "type": "armor",
        "materials": {"mithril_ingot": 5, "leather": 3, "small_magic_stone": 3},
        "result_count": 1,
        "time": 70,
        "stats": {"armor": 40, "hp": 150, "mana": 50},
        "rank": "B"
    },
    "mithril_helmet": {
        "name": "⛑️ Мифриловый шлем",
        "type": "helmet",
        "materials": {"mithril_ingot": 3, "leather": 2, "small_magic_stone": 2},
        "result_count": 1,
        "time": 45,
        "stats": {"armor": 18, "hp": 60, "mana": 30},
        "rank": "B"
    },
    "mithril_boots": {
        "name": "👢 Мифриловые сапоги",
        "type": "boots",
        "materials": {"mithril_ingot": 3, "leather": 3, "small_magic_stone": 1},
        "result_count": 1,
        "time": 45,
        "stats": {"armor": 15, "dodge": 0.08},
        "rank": "B"
    }
}

# Драконий сет
DRAGON_SET = {
    "dragon_sword": {
        "name": "⚔️ Драконий клинок",
        "type": "weapon",
        "materials": {"dragon_scale": 5, "mithril_ingot": 2, "medium_magic_stone": 3},
        "result_count": 1,
        "time": 60,
        "stats": {"power": 40, "crit": 0.12, "fire_damage": 20},
        "rank": "A"
    },
    "dragon_chestplate": {
        "name": "🛡️ Драконья броня",
        "type": "armor",
        "materials": {"dragon_scale": 8, "mithril_ingot": 4, "medium_magic_stone": 5},
        "result_count": 1,
        "time": 90,
        "stats": {"armor": 60, "hp": 250, "fire_resist": 0.5},
        "rank": "A"
    },
    "dragon_helmet": {
        "name": "⛑️ Драконий шлем",
        "type": "helmet",
        "materials": {"dragon_scale": 4, "mithril_ingot": 2, "medium_magic_stone": 3},
        "result_count": 1,
        "time": 60,
        "stats": {"armor": 25, "hp": 100, "fire_resist": 0.3},
        "rank": "A"
    },
    "dragon_boots": {
        "name": "👢 Драконьи сапоги",
        "type": "boots",
        "materials": {"dragon_scale": 4, "mithril_ingot": 2, "medium_magic_stone": 2},
        "result_count": 1,
        "time": 60,
        "stats": {"armor": 20, "dodge": 0.10},
        "rank": "A"
    }
}

# Аксессуары
ACCESSORIES = {
    "ring_of_power": {
        "name": "💍 Кольцо силы",
        "type": "accessory",
        "materials": {"mithril_ingot": 1, "small_magic_stone": 1},
        "result_count": 1,
        "time": 20,
        "stats": {"power": 5, "crit": 0.03},
        "rank": "D"
    },
    "ring_of_health": {
        "name": "💍 Кольцо здоровья",
        "type": "accessory",
        "materials": {"mithril_ingot": 1, "ancient_wood": 3},
        "result_count": 1,
        "time": 20,
        "stats": {"hp": 50},
        "rank": "D"
    },
    "amulet_of_magic": {
        "name": "🔮 Амулет магии",
        "type": "accessory",
        "materials": {"small_magic_stone": 3, "cloth": 2},
        "result_count": 1,
        "time": 25,
        "stats": {"mana": 50, "spell_damage": 8},
        "rank": "D"
    }
}

# Собираем все рецепты
EQUIPMENT_RECIPES.update(IRON_SET)
EQUIPMENT_RECIPES.update(STEEL_SET)
EQUIPMENT_RECIPES.update(MITHRIL_SET)
EQUIPMENT_RECIPES.update(DRAGON_SET)
EQUIPMENT_RECIPES.update(ACCESSORIES)

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
        return RankSystem.format_monster_rank(self.level)


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


def get_drop(enemy_name, player_level, player_name=None):
    """Получить список предметов, которые выпали с врага"""
    drops = []
    
    # Базовый дроп
    if "крыса" in enemy_name.lower():
        drops.append({"name": "🧵 Кожа", "type": "material", "rarity": "common", "stats": {"value": 15}})
    elif "волк" in enemy_name.lower():
        drops.append({"name": "🧵 Волчья шкура", "type": "material", "rarity": "common", "stats": {"value": 20}})
    elif "дракон" in enemy_name.lower():
        drops.append({"name": "🐉 Чешуя дракона", "type": "material", "rarity": "epic", "stats": {"value": 200}})
        if random.random() < 0.3:
            drops.append({"name": "💎 Малый магический камень", "type": "magic", "rarity": "uncommon", "stats": {"value": 50}})
    elif "босс" in enemy_name.lower() or "Ктулху" in enemy_name or "Феникс" in enemy_name:
        drops.append({"name": "💎 Большой магический камень", "type": "magic", "rarity": "epic", "stats": {"value": 500}})
        if random.random() < 0.2:
            drops.append({"name": "📜 Свиток улучшения", "type": "artifact", "rarity": "legendary", "stats": {"upgrade": 1}})
    
    return drops


# ===== ПРОФЕССИИ (работы) =====
JOBS_BY_LOCATION = {
    'city': {
        'name': '🏙️ Городские профессии',
        'jobs': [
            {'name': '📦 Грузчик', 'desc': 'Таскать ящики на складе', 'min_earn': 50, 'max_earn': 150, 'exp_reward': 5, 'time': 30, 'requirements': {'level': 1}},
            {'name': '🔧 Помощник кузнеца', 'desc': 'Помогать в кузнице', 'min_earn': 100, 'max_earn': 250, 'exp_reward': 10, 'time': 45, 'requirements': {'level': 3, 'power': 60}},
            {'name': '📜 Писарь', 'desc': 'Переписывать свитки', 'min_earn': 80, 'max_earn': 200, 'exp_reward': 8, 'time': 35, 'requirements': {'level': 2}},
        ]
    },
    'forest': {
        'name': '🌲 Лесные профессии',
        'jobs': [
            {'name': '🪓 Лесоруб', 'desc': 'Рубить деревья', 'min_earn': 80, 'max_earn': 200, 'exp_reward': 8, 'time': 40, 'requirements': {'level': 2}},
            {'name': '🧺 Травник', 'desc': 'Собирать лечебные травы', 'min_earn': 60, 'max_earn': 180, 'exp_reward': 7, 'time': 35, 'requirements': {'level': 1}},
            {'name': '🏹 Охотник', 'desc': 'Охотиться на дичь', 'min_earn': 90, 'max_earn': 220, 'exp_reward': 9, 'time': 40, 'requirements': {'level': 2, 'power': 50}},
        ]
    },
    'tavern': {
        'name': '🍺 Таверна',
        'jobs': [
            {'name': '🍻 Бармен', 'desc': 'Наливать эль и слушать истории', 'min_earn': 70, 'max_earn': 180, 'exp_reward': 6, 'time': 35, 'requirements': {'level': 1}},
            {'name': '🥩 Повар', 'desc': 'Готовить еду для посетителей', 'min_earn': 90, 'max_earn': 220, 'exp_reward': 9, 'time': 40, 'requirements': {'level': 2}},
            {'name': '🎤 Бард', 'desc': 'Петь песни и развлекать гостей', 'min_earn': 100, 'max_earn': 250, 'exp_reward': 10, 'time': 45, 'requirements': {'level': 3, 'charisma': 10}},
        ]
    }
}

# Добавляем работы для расовых городов
for race_name, city_data in RACE_CITIES.items():
    city_id = city_data["city_id"]
    if city_id not in JOBS_BY_LOCATION:
        JOBS_BY_LOCATION[city_id] = {
            'name': f'🏙️ Профессии {city_data["name"]}',
            'jobs': [
                {'name': '🔨 Ремесленник', 'desc': 'Создавать местные товары', 'min_earn': 80, 'max_earn': 200, 'exp_reward': 8, 'time': 40, 'requirements': {'level': 2}},
                {'name': '🎯 Охотник', 'desc': 'Охотиться на местных зверей', 'min_earn': 100, 'max_earn': 250, 'exp_reward': 10, 'time': 45, 'requirements': {'level': 3, 'power': 60}},
            ]
        }