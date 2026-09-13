# race_shop.py
"""
Магазины расовых городов
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Player
from utils import update_message
from race_cities import CITY_SHOPS, get_city_shop, RACE_CITIES
from logger import GameLogger

logger = GameLogger()


async def race_shop_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать магазин расового города"""
    query = update.callback_query
    await query.answer()
    
    uid = str(query.from_user.id)
    player = Player(uid)
    
    current_location = player.get('location', 'city')
    
    # Проверяем, в расовом ли городе игрок
    race_city = None
    for race, city_data in RACE_CITIES.items():
        if city_data["city_id"] == current_location:
            race_city = city_data
            break
    
    if not race_city:
        await query.edit_message_text("❌ Ты не в расовом городе!")
        return
    
    shop = CITY_SHOPS.get(current_location)
    if not shop:
        await query.edit_message_text("❌ В этом городе нет магазина!")
        return
    
    text = f"🏪 **{shop['name']}**\n"
    text += f"✨ Специализация: {shop['specialty']}\n"
    text += f"📍 {race_city['name']}\n\n"
    text += "**Доступные товары:**\n\n"
    
    for i, item in enumerate(shop["items"]):
        text += f"{i+1}. {item['name']}\n"
        text += f"   💰 {item['price']} монет\n"
        if "stats" in item:
            stats_text = []
            for stat, val in item["stats"].items():
                if stat == "power":
                    stats_text.append(f"⚔️ +{val}")
                elif stat == "armor":
                    stats_text.append(f"🛡️ +{val}")
                elif stat == "crit":
                    stats_text.append(f"💥 +{int(val*100)}%")
                elif stat == "dodge":
                    stats_text.append(f"💨 +{int(val*100)}%")
                elif stat == "luck":
                    stats_text.append(f"🍀 +{int(val*100)}%")
                else:
                    stats_text.append(f"✨ +{val}")
            if stats_text:
                text += f"   {' '.join(stats_text)}\n"
        text += "\n"
    
    keyboard = []
    for i, item in enumerate(shop["items"]):
        keyboard.append([InlineKeyboardButton(
            f"🛒 Купить {item['name']} ({item['price']}💰)",
            callback_data=f"race_shop_buy_{current_location}_{i}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 На главную", callback_data="main_screen")])
    
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))


async def race_shop_buy(update: Update, context: ContextTypes.DEFAULT_TYPE, city_id: str, item_index: int):
    """Купить предмет в расовом магазине"""
    query = update.callback_query
    await query.answer()
    
    uid = str(query.from_user.id)
    player = Player(uid)
    
    shop = CITY_SHOPS.get(city_id)
    if not shop or item_index >= len(shop["items"]):
        await query.edit_message_text("❌ Товар не найден!")
        return
    
    item = shop["items"][item_index].copy()
    
    if player["money"] < item["price"]:
        await query.answer(f"💸 Не хватает монет! Нужно {item['price']}💰", show_alert=True)
        return
    
    player["money"] -= item["price"]
    
    if 'inventory' not in player.data:
        player['inventory'] = {'items': [], 'equipped': {}}
    
    new_item = {
        'id': item['name'].lower().replace(' ', '_'),
        'name': item['name'],
        'type': item['type'],
        'rarity': 'uncommon',
        'stats': item.get('stats', {})
    }
    
    player['inventory']['items'].append(new_item)
    player.save()
    
    logger.buy(player['name'], item['name'], item['price'], player['money'])
    
    # Получаем название города
    city_name = "городе"
    for race, city_data in RACE_CITIES.items():
        if city_data["city_id"] == city_id:
            city_name = city_data["name"]
            break
    
    await query.edit_message_text(
        f"✅ Ты купил **{item['name']}** в {city_name}!\n"
        f"💰 Осталось монет: {player['money']}\n\n"
        f"◀️ Нажми, чтобы вернуться в магазин",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("◀️ Назад в магазин", callback_data=f"race_shop_back_{city_id}")
        ]])
    )


async def race_shop_back(update: Update, context: ContextTypes.DEFAULT_TYPE, city_id: str):
    """Вернуться в магазин"""
    query = update.callback_query
    await query.answer()
    
    # Восстанавливаем меню магазина
    shop = CITY_SHOPS.get(city_id)
    if not shop:
        await query.edit_message_text("❌ Магазин не найден!")
        return
    
    text = f"🏪 **{shop['name']}**\n"
    text += f"✨ Специализация: {shop['specialty']}\n\n"
    text += "**Доступные товары:**\n\n"
    
    for i, item in enumerate(shop["items"]):
        text += f"{i+1}. {item['name']}\n"
        text += f"   💰 {item['price']} монет\n\n"
    
    keyboard = []
    for i, item in enumerate(shop["items"]):
        keyboard.append([InlineKeyboardButton(
            f"🛒 Купить {item['name']} ({item['price']}💰)",
            callback_data=f"race_shop_buy_{city_id}_{i}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 На главную", callback_data="main_screen")])
    
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))