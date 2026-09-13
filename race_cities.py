# race_cities.py - ИСПРАВЛЕННЫЙ (без циклического импорта)
"""
Система городов для разных рас
Каждая раса имеет свой родной город с уникальными магазинами
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Импортируем данные из game_data (теперь это безопасно)
from game_data import RACE_CITIES, CITY_SHOPS, NEUTRAL_CITIES


def get_race_city(race_name: str) -> dict:
    """Возвращает город для расы"""
    return RACE_CITIES.get(race_name)


def get_city_shop(city_id: str) -> dict:
    """Возвращает магазин города"""
    return CITY_SHOPS.get(city_id)


def can_travel_to(from_city: str, to_city: str, player_race: str = None) -> tuple:
    """Проверяет, может ли игрок переместиться между городами"""
    
    # Разрешаем подземелье
    if to_city == "dungeon":
        return True, ""
    
    # Из подземелья можно выйти только в город
    if from_city == "dungeon":
        if to_city == "city":
            return True, ""
        return False, "🏚️ Из подземелья можно выйти только в Авалон!"
    
    # Авалон — центральный хаб
    if to_city == "city" or from_city == "city":
        return True, ""
    
    # Из больницы нельзя никуда, кроме города
    if from_city == "hospital":
        if to_city == "city":
            return True, ""
        return False, "🏥 Ты в больнице! Сначала вылечись."
    
    # В больницу можно только при смерти
    if to_city == "hospital":
        return False, "🏥 В больницу можно попасть только при смерти или ранении."
    
    # Из таверны — только в город
    if from_city == "tavern" and to_city != "city":
        return False, "🍺 Из таверны можно попасть только в Авалон!"
    
    # Если игрок в своём родном городе
    if player_race:
        race_city = RACE_CITIES.get(player_race, {}).get("city_id")
        if from_city == race_city:
            if to_city != "city":
                return False, f"🌍 Из твоего родного города можно попасть только в Авалон!"
    
    return False, "🌍 Этот путь недоступен! Сначала доберись до Авалона."


def get_available_destinations(current_city: str, player_race: str = None) -> list:
    """Возвращает список доступных для перемещения городов"""
    destinations = []
    
    # Авалон доступен всегда
    destinations.append({"id": "city", "name": "🏰 Авалон"})
    
    # Из Авалона можно попасть в родной город расы
    if current_city == "city" and player_race:
        race_city = RACE_CITIES.get(player_race)
        if race_city:
            destinations.append({
                "id": race_city["city_id"],
                "name": race_city["name"]
            })
    
    return destinations


def get_city_travel_text(from_city: str, to_city: str) -> str:
    """Возвращает текст путешествия между городами"""
    travel_texts = {
        ("city", "elf_forest"): "Ты идёшь через цветущие луга и входишь в древний Эльфийский лес...",
        ("city", "demon_gates"): "Ты спускаешься в тёмные земли и чувствуешь жар Врат Бездны...",
        ("city", "human_citadel"): "Ты идёшь по мощёной дороге к величественной цитадели людей...",
        ("city", "beast_woods"): "Ты углубляешься в чащу леса, где обитают зверолюды...",
        ("city", "moon_hollow"): "Лунный свет ведёт тебя в таинственную Лунную лощину...",
        ("city", "bear_mountains"): "Ты поднимаешься в горы, где воздух становится холоднее...",
        ("city", "fox_mist"): "Туман расступается перед тобой, открывая путь в Туманную долину...",
        ("city", "dragon_peak"): "Ты чувствуешь древнюю силу, поднимаясь на Пик Дракона...",
        ("city", "sky_nest"): "Лёгкий ветер поднимает тебя в облака, к Небесному гнезду...",
        ("city", "serpent_temple"): "Тёмные тени ведут тебя к древнему Храму Змея...",
        ("city", "boar_marsh"): "Ты ступаешь на зыбкую почву Кабаньего болота...",
        ("city", "deer_meadow"): "Солнечный свет озаряет цветущие луга Оленьей лужайки..."
    }
    
    key = (from_city, to_city)
    return travel_texts.get(key, "Ты отправляешься в путь...")


def get_city_shop_keyboard(city_id: str):
    """Создаёт клавиатуру для магазина города"""
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