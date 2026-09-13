# cities_data.py — города рас и их связность
from game_data import LOCATIONS

# Личные города зверолюдей (id -> (название, раса))
BEAST_CITIES = {
    'city_volk':  ('🐺 Волкоград',    '🐺 Волколюд'),
    'city_kosh':  ('🐱 Мурр-Ашар',    '🐱 Кошколюд'),
    'city_medv':  ('🐻 Медвежий Лог', '🐻 Медведолюд'),
    'city_lis':   ('🦊 Лисья Падь',   '🦊 Лисолюд'),
    'city_drak':  ('🐉 Драконий Пик', '🐉 Драконолюд'),
    'city_ptic':  ('🐦 Небоград',     '🐦 Птицелюд'),
    'city_zmey':  ('🐍 Змеиный Дол',  '🐍 Змеелюд'),
    'city_kaban': ('🐗 Кабанск',      '🐗 Кабанолюд'),
    'city_olen':  ('🦌 Оленья Роща',  '🦌 Оленелюд'),
}

CITIES = {
    'elf_city':   {'name': '🌿 Сильварис', 'desc': 'Город эльфов среди тысячелетних дубов.', 'race': '🧝 Эльф'},
    'demon_city': {'name': '🔥 Инфернус',  'desc': 'Город демонов среди вечного пламени.', 'race': '👹 Демон'},
    'dorton':     {'name': '🐾 Дортон',    'desc': 'Нейтральный город зверолюдей. Перекрёсток всех звериных троп.', 'race': None},
}
for cid, (name, race) in BEAST_CITIES.items():
    CITIES[cid] = {'name': name, 'desc': f'Город расы {race}.', 'race': race}

BEAST_IDS = list(BEAST_CITIES.keys())

# Связность: города зверолюдей ДОСТУПНЫ ТОЛЬКО из Дортона и друг с другом не связаны
CONNECTIONS = {
    'city':     ['elf_city', 'demon_city', 'dorton'],  # врата из Авалона
    'forest':   [], 'tavern': [], 'dungeon': [], 'hospital': [],
    'elf_city':   ['city'],
    'demon_city': ['city'],
    'dorton':     ['city'] + BEAST_IDS,
}
for cid in BEAST_IDS:
    CONNECTIONS[cid] = ['dorton']  # только обратно в Дортон!

# Время в пути (сек)
TRAVEL_TIME_CITY = {'elf_city': 25, 'demon_city': 25, 'dorton': 30}
for cid in BEAST_IDS:
    TRAVEL_TIME_CITY[cid] = 20

# Регистрируем города в глобальном LOCATIONS, чтобы главный экран их знал
for cid, data in CITIES.items():
    LOCATIONS[cid] = {
        'name': data['name'],
        'desc': data['desc'],
        'image': f'images/locations/{cid}.jpg',
        'can_hunt': False,
        'can_work': False,
    }
