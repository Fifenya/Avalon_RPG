# shop.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
# Добавлен декоратор require_character и проверка существования предметов

import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Player
from game_data import RESOURCES, EQUIPMENT_RECIPES
from keyboards import get_shop_keyboard, get_shop_items_keyboard
from utils import update_message, require_character
from main_screen import show_main_screen
from logger import GameLogger

logger = GameLogger()

# Товары в магазине
SHOP_ITEMS = {
    "consumables": [
        {"name": "❤️ Малое зелье здоровья", "price": 50, "type": "potion", "stats": {"hp": 30}},
        {"name": "💙 Малое зелье маны", "price": 40, "type": "potion", "stats": {"mana": 30}},
        {"name": "❤️ Среднее зелье здоровья", "price": 120, "type": "potion", "stats": {"hp": 75}},
        {"name": "💙 Среднее зелье маны", "price": 100, "type": "potion", "stats": {"mana": 75}},
    ],
    "weapons": [
        {"name": "🗡️ Ржавый меч", "price": 300, "type": "weapon", "stats": {"power": 3}},
        {"name": "⚔️ Железный меч", "price": 500, "type": "weapon", "stats": {"power": 8}},
        {"name": "🪓 Железный топор", "price": 600, "type": "weapon", "stats": {"power": 10}},
    ],
    "armor": [
        {"name": "👘 Рваный балахон", "price": 200, "type": "armor", "stats": {"armor": 1, "mana": 3}},
        {"name": "🛡️ Железный нагрудник", "price": 800, "type": "armor", "stats": {"armor": 15, "hp": 50}},
        {"name": "⛑️ Железный шлем", "price": 400, "type": "helmet", "stats": {"armor": 8, "hp": 20}},
    ],
    "magic": [
        {"name": "🪄 Слабый посох (искра)", "price": 300, "type": "weapon", "stats": {"power": 6, "spell_damage": 3}},
        {"name": "🔮 Железный посох", "price": 600, "type": "weapon", "stats": {"power": 10, "spell_damage": 15}},
    ],
    "resources": [],
    "special": []
}

# Товары дня (обновляются при старте)
featured_items = []


def generate_featured_items():
    """Генерирует товары дня"""
    global featured_items
    all_items = []
    for category in SHOP_ITEMS.values():
        all_items.extend(category)
    
    random.shuffle(all_items)
    featured_items = []
    for item in all_items[:3]:
        original_price = item['price']
        discount_price = int(original_price * 0.8)
        featured_items.append({
            **item,
            "original_price": original_price,
            "discount_price": discount_price,
            "discount": 20
        })


# Генерируем товары дня при загрузке
generate_featured_items()


async def shop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    player = Player(uid)
    money = player['money']
    
    crazy_text = (
        f"🏪🧙🍺👑🐉📜🎲\n"
        f"**ЛАВКА 'КРИВОЙ СТАРОСТА'**\n"
        f"🎭 Показания очевидцев:\n"
        f"   👑 Король: {money}\n"
        f"   🍺 Бард: {money}\n"
        f"   🧙 Маг: {money} (магией)\n"
        f"   🐉 Дракон: {money} (чешуёй)\n"
        f"   📜 Летописец: {money} (чернилами)\n"
        f"   🎲 Гоблин: {money} (в кости)\n"
        f"   🛡️ Стражник: {money} (проверил)\n"
        f"💩 **Итог: {money} монет**\n\n"
        f"🛒 **Чего изволите?**"
    )
    
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(crazy_text, parse_mode='Markdown', reply_markup=get_shop_keyboard())
    else:
        await update.message.reply_text(crazy_text, parse_mode='Markdown', reply_markup=get_shop_keyboard())


@require_character
async def shop_category(update: Update, context: ContextTypes.DEFAULT_TYPE, category_id: str):
    """Показать предметы категории"""
    query = update.callback_query
    await query.answer()
    
    uid = str(query.from_user.id)
    player = Player(uid)
    
    if category_id not in SHOP_ITEMS:
        await shop_command(update, context)
        return
    
    items = SHOP_ITEMS[category_id]
    
    if not items:
        text = f"📦 В этой категории пока нет товаров\n\n◀️ Назад"
        await query.edit_message_text(text, reply_markup=get_shop_keyboard())
        return
    
    context.user_data['shop_category'] = category_id
    context.user_data['shop_items'] = items
    
    cat_names = {
        "consumables": "🧪 Расходники",
        "weapons": "⚔️ Оружие",
        "armor": "🛡️ Броня",
        "magic": "🔮 Магия",
        "resources": "📦 Ресурсы",
        "special": "✨ Особое"
    }
    cat_name = cat_names.get(category_id, category_id)
    
    keyboard = []
    for i, item in enumerate(items):
        keyboard.append([InlineKeyboardButton(
            f"{item['name']} — {item['price']}💰", 
            callback_data=f"shop_buy_{category_id}_{i}"
        )])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="shop_back")])
    
    await query.edit_message_text(
        f"{cat_name}\n💰 Твой баланс: {player['money']} монет\n\nВыбери предмет:", 
        reply_markup=InlineKeyboardMarkup(keyboard), 
        parse_mode='Markdown'
    )


@require_character
async def shop_buy(update: Update, context: ContextTypes.DEFAULT_TYPE, category_id: str, item_index: int):
    """Купить предмет с проверкой"""
    query = update.callback_query
    await query.answer()
    
    uid = str(query.from_user.id)
    player = Player(uid)
    
    # Проверяем, не товар ли дня
    if category_id == "featured":
        items = featured_items
    elif category_id in SHOP_ITEMS:
        items = SHOP_ITEMS[category_id]
    else:
        await shop_command(update, context)
        return
    
    # Проверка существования предмета
    if item_index < 0 or item_index >= len(items):
        await shop_command(update, context)
        return
    
    item = items[item_index].copy()
    
    # Если это товар дня, используем скидочную цену
    if category_id == "featured":
        item['price'] = item['discount_price']
    
    # Проверяем, хватает ли денег
    if player['money'] < item['price']:
        await query.answer(f"💸 Не хватает монет! Нужно: {item['price']}💰", show_alert=True)
        return
    
    # Списываем деньги
    player['money'] -= item['price']
    
    # Добавляем предмет в инвентарь
    if 'inventory' not in player.data:
        player['inventory'] = {'items': [], 'equipped': {}}
    
    # Проверяем лимит инвентаря
    from inventory import can_add_item
    if not can_add_item(player, item):
        player['money'] += item['price']  # Возвращаем деньги
        await query.edit_message_text(
            f"❌ **НЕВОЗМОЖНО КУПИТЬ!**\n\n"
            f"Твой инвентарь переполнен!\n"
            f"Продай или выброси лишние предметы.\n\n"
            f"💰 Монеты возвращены.",
            parse_mode='Markdown'
        )
        return
    
    # Создаём предмет для инвентаря
    new_item = {
        'id': item['name'].lower().replace(' ', '_').replace('️', ''),
        'name': item['name'],
        'type': item['type'],
        'rarity': 'common',
        'stats': item.get('stats', {})
    }
    
    player['inventory']['items'].append(new_item)
    player.save()
    
    logger.buy(player['name'], item['name'], item['price'], player['money'])
    
    item_type_emoji = {
        'weapon': '⚔️',
        'armor': '🛡️',
        'helmet': '⛑️',
        'boots': '👢',
        'shield': '🛡️',
        'potion': '🧪',
        'accessory': '💍'
    }.get(item['type'], '📦')
    
    result_text = (
        f"✅ **ПОКУПКА УСПЕШНА!**\n\n"
        f"{item_type_emoji} **{item['name']}** добавлен в инвентарь!\n"
        f"💰 Осталось монет: {player['money']}\n\n"
        f"📦 Чтобы использовать зелье, найди его в **Инвентаре**\n"
        f"⚔️ Чтобы надеть предмет, открой **Экипировку**\n\n"
        f"◀️ Нажми кнопку ниже, чтобы вернуться в магазин"
    )
    
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("◀️ Вернуться в магазин", callback_data="shop_back")
    ]])
    
    await query.edit_message_text(
        text=result_text,
        parse_mode='Markdown',
        reply_markup=keyboard
    )


@require_character
async def shop_featured(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать товары дня"""
    query = update.callback_query
    await query.answer()
    
    uid = str(query.from_user.id)
    player = Player(uid)
    
    if not featured_items:
        await query.edit_message_text("🌟 Сегодня нет товаров дня\n\n◀️ Назад", reply_markup=get_shop_keyboard())
        return
    
    text = "🌟 **ТОВАРЫ ДНЯ** 🌟\n\n"
    for i, item in enumerate(featured_items):
        text += f"{i+1}. {item['name']}\n"
        text += f"   ~~{item['original_price']}💰~~ → **{item['discount_price']}💰** (-{item['discount']}%)\n\n"
    
    text += f"💰 Твой баланс: {player['money']} монет\n\n"
    text += "Нажми на предмет, чтобы купить"
    
    keyboard = []
    for i, item in enumerate(featured_items):
        keyboard.append([InlineKeyboardButton(
            f"{item['name']} — {item['discount_price']}💰", 
            callback_data=f"shop_buy_featured_{i}"
        )])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="shop_back")])
    
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))


@require_character
async def shop_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback-запросов магазина"""
    query = update.callback_query
    data = query.data
    
    print(f"🔍 Shop callback: {data}")
    
    if data == "shop_back":
        await shop_command(update, context)
    
    elif data.startswith("shop_cat_"):
        category_id = data.replace("shop_cat_", "")
        await shop_category(update, context, category_id)
    
    elif data.startswith("shop_buy_"):
        parts = data.split("_")
        if len(parts) >= 4:
            category_id = parts[2]
            try:
                item_index = int(parts[3])
                await shop_buy(update, context, category_id, item_index)
            except ValueError:
                print(f"Ошибка парсинга индекса: {data}")
        else:
            print(f"Ошибка парсинга: {data}")
    
    elif data == "shop_featured":
        await shop_featured(update, context)