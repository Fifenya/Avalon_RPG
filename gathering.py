# gathering.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
import random
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Player
from utils import update_message, require_character
from logger import GameLogger

logger = GameLogger()

GATHERING_RESOURCES = {
    "forest": {
        "name": "🌲 Лес",
        "resources": [
            {"id": "wood", "name": "🪵 Древесина", "min": 1, "max": 3, "chance": 0.7, "value": 5},
            {"id": "herb", "name": "🌿 Лечебная трава", "min": 1, "max": 2, "chance": 0.5, "value": 10},
            {"id": "berry", "name": "🍓 Ягоды", "min": 1, "max": 4, "chance": 0.6, "value": 3},
            {"id": "mushroom", "name": "🍄 Гриб", "min": 1, "max": 2, "chance": 0.4, "value": 8},
        ]
    },
    "city": {
        "name": "🏰 Авалон",
        "resources": [
            {"id": "cloth", "name": "🧵 Ткань", "min": 1, "max": 2, "chance": 0.4, "value": 12},
            {"id": "scrap_metal", "name": "🔩 Металлолом", "min": 1, "max": 2, "chance": 0.3, "value": 8},
        ]
    },
    "elf_forest": {
        "name": "🌳 Эльфийский лес",
        "resources": [
            {"id": "elf_herb", "name": "✨ Эльфийская трава", "min": 1, "max": 2, "chance": 0.6, "value": 20},
            {"id": "wood", "name": "🪵 Древесина", "min": 1, "max": 3, "chance": 0.5, "value": 5},
            {"id": "magic_dust", "name": "✨ Магическая пыльца", "min": 1, "max": 1, "chance": 0.3, "value": 30},
        ]
    },
    "beast_woods": {
        "name": "🌲 Лесная чаща",
        "resources": [
            {"id": "herb", "name": "🌿 Лечебная трава", "min": 1, "max": 3, "chance": 0.7, "value": 10},
            {"id": "leather", "name": "🧵 Кожа", "min": 1, "max": 1, "chance": 0.4, "value": 15},
            {"id": "mushroom", "name": "🍄 Гриб", "min": 1, "max": 3, "chance": 0.5, "value": 8},
        ]
    }
}

ALCHEMY_RECIPES = {
    "small_hp_potion": {
        "name": "❤️ Малое зелье здоровья",
        "materials": {"herb": 2, "berry": 3},
        "result": {"hp": 30},
        "time": 10,
        "value": 40
    },
    "medium_hp_potion": {
        "name": "❤️ Среднее зелье здоровья",
        "materials": {"herb": 4, "elf_herb": 1, "berry": 5},
        "result": {"hp": 70},
        "time": 20,
        "value": 100
    },
    "small_mana_potion": {
        "name": "💙 Малое зелье маны",
        "materials": {"herb": 2, "magic_dust": 1},
        "result": {"mana": 30},
        "time": 10,
        "value": 40
    },
    "medium_mana_potion": {
        "name": "💙 Среднее зелье маны",
        "materials": {"herb": 4, "elf_herb": 1, "magic_dust": 2},
        "result": {"mana": 70},
        "time": 20,
        "value": 100
    }
}

active_gathering = {}


@require_character
async def gathering_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню сбора ресурсов"""
    uid = str(update.effective_user.id)
    player = Player(uid)
    
    current_loc = player.get('location', 'city')
    gathering_data = GATHERING_RESOURCES.get(current_loc)
    
    if not gathering_data:
        await update_message(update, context, "❌ В этой локации нельзя собирать ресурсы!")
        return
    
    text = f"🌿 **СБОР РЕСУРСОВ** 🌿\n\n"
    text += f"📍 {gathering_data['name']}\n\n"
    text += "**Что можно найти:**\n"
    
    for res in gathering_data["resources"]:
        text += f"• {res['name']} — {res['min']}-{res['max']} шт. (шанс {int(res['chance']*100)}%)\n"
    
    text += "\n⏱️ Сбор занимает **30 секунд**"
    text += "\n\n🔮 **ИЛИ** выбери Алхимию для создания зелий из трав!"
    
    keyboard = [
        [InlineKeyboardButton("🌿 Начать сбор", callback_data="gathering_start")],
        [InlineKeyboardButton("🧪 Алхимия", callback_data="gathering_alchemy")],
        [InlineKeyboardButton("🔙 На главную", callback_data="main_screen")]
    ]
    
    await update_message(update, context, text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')


@require_character
async def start_gathering(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать сбор ресурсов"""
    query = update.callback_query
    await query.answer()
    
    uid = str(query.from_user.id)
    player = Player(uid)
    current_loc = player.get('location', 'city')
    gathering_data = GATHERING_RESOURCES.get(current_loc)
    
    if not gathering_data:
        await query.edit_message_text("❌ В этой локации нельзя собирать ресурсы!")
        return
    
    if uid in active_gathering:
        await query.edit_message_text("⏳ Ты уже собираешь ресурсы! Дождись завершения.")
        return
    
    active_gathering[uid] = {
        "finish_time": datetime.now() + timedelta(seconds=30),
        "location": current_loc
    }
    
    keyboard = [[InlineKeyboardButton("❌ Отменить сбор", callback_data="gathering_cancel")]]
    
    await query.edit_message_text(
        "🌿 **Ты начал собирать ресурсы...**\n\n"
        "🔍 Осматриваешь окрестности в поисках полезных трав и материалов.\n"
        "⏱️ Это займёт **30 секунд**.\n\n"
        "_Не отвлекайся, чтобы ничего не упустить!_",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    asyncio.create_task(finish_gathering(uid, context, gathering_data))


async def finish_gathering(uid: str, context: ContextTypes.DEFAULT_TYPE, gathering_data: dict):
    """Завершение сбора ресурсов"""
    await asyncio.sleep(30)
    
    if uid not in active_gathering:
        return
    
    player = Player(uid)
    collected = []
    
    for res in gathering_data["resources"]:
        if random.random() < res["chance"]:
            amount = random.randint(res["min"], res["max"])
            collected.append({"res": res, "amount": amount})
    
    if 'resources' not in player.data:
        player['resources'] = {}
    
    reward_text = ""
    for item in collected:
        res_id = item["res"]["id"]
        amount = item["amount"]
        player['resources'][res_id] = player['resources'].get(res_id, 0) + amount
        reward_text += f"• {item['res']['name']} x{amount}\n"
    
    player.save()
    del active_gathering[uid]
    
    if collected:
        text = f"✅ **Сбор завершён!**\n\nТы нашёл:\n{reward_text}"
    else:
        text = "🍃 **Сбор завершён, но ты ничего не нашёл...**\n\nПовезёт в следующий раз!"
    
    keyboard = [[InlineKeyboardButton("🌿 Собрать снова", callback_data="gathering_start")],
                [InlineKeyboardButton("🔙 На главную", callback_data="main_screen")]]
    
    try:
        await context.bot.send_message(
            chat_id=int(uid),
            text=text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        logger.work(player.get('name', 'Игрок'), 0, player.get('money', 0), f"собрал {len(collected)} ресурсов")
    except Exception as e:
        print(f"Ошибка завершения сбора: {e}")


@require_character
async def cancel_gathering(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменить сбор"""
    query = update.callback_query
    await query.answer()
    
    uid = str(query.from_user.id)
    
    if uid in active_gathering:
        del active_gathering[uid]
        await query.edit_message_text("❌ Сбор ресурсов отменён.")
    else:
        await query.edit_message_text("❌ Ты не собираешь ресурсы.")


@require_character
async def alchemy_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню алхимии"""
    query = update.callback_query
    await query.answer()
    
    uid = str(query.from_user.id)
    player = Player(uid)
    
    if uid in active_gathering:
        await query.edit_message_text("⏳ Ты занят сбором ресурсов! Дождись завершения.")
        return
    
    text = "🧪 **АЛХИМИЯ** 🧪\n\n"
    text += "Создавай зелья из собранных трав!\n\n"
    
    keyboard = []
    
    for recipe_id, recipe in ALCHEMY_RECIPES.items():
        resources = player.get('resources', {})
        missing = []
        for mat, needed in recipe["materials"].items():
            if resources.get(mat, 0) < needed:
                missing.append(f"{mat} x{needed}")
        
        status = "❌" if missing else "✅"
        text += f"{status} **{recipe['name']}**\n"
        text += f"   Материалы: "
        mats_text = []
        for mat, needed in recipe["materials"].items():
            mats_text.append(f"{mat} x{needed}")
        text += " + ".join(mats_text)
        if missing:
            text += f" (не хватает: {', '.join(missing)})"
        text += f"\n   ⏱️ {recipe['time']} сек\n\n"
        
        if not missing:
            keyboard.append([InlineKeyboardButton(
                f"⚗️ Создать {recipe['name']}",
                callback_data=f"alchemy_craft_{recipe_id}"
            )])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад к сбору", callback_data="gathering_back")])
    
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))


@require_character
async def craft_potion(update: Update, context: ContextTypes.DEFAULT_TYPE, recipe_id: str):
    """Создать зелье"""
    query = update.callback_query
    await query.answer()
    
    uid = str(query.from_user.id)
    player = Player(uid)
    recipe = ALCHEMY_RECIPES.get(recipe_id)
    
    if not recipe:
        await query.edit_message_text("❌ Рецепт не найден!")
        return
    
    if uid in active_gathering:
        await query.edit_message_text("⏳ Ты занят! Дождись завершения.")
        return
    
    resources = player.get('resources', {})
    missing = []
    for mat, needed in recipe["materials"].items():
        if resources.get(mat, 0) < needed:
            missing.append(mat)
    
    if missing:
        await query.edit_message_text(f"❌ Не хватает материалов: {', '.join(missing)}")
        return
    
    for mat, needed in recipe["materials"].items():
        resources[mat] -= needed
        if resources[mat] <= 0:
            del resources[mat]
    
    if 'inventory' not in player.data:
        player['inventory'] = {'items': [], 'equipped': {}}
    
    potion = {
        'id': recipe_id,
        'name': recipe['name'],
        'type': 'potion',
        'rarity': 'common',
        'stats': recipe['result'].copy(),
        'value': recipe['value']
    }
    
    player['inventory']['items'].append(potion)
    player['crafts_done'] = player.get('crafts_done', 0) + 1
    player.save()
    
    from achievements import AchievementsSystem
    ach = AchievementsSystem()
    ach.check_achievements(uid)
    
    await query.edit_message_text(
        f"✅ **Ты создал {recipe['name']}!**\n\n"
        f"🧪 Зелье добавлено в инвентарь.\n"
        f"Его можно использовать в бою для восстановления.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 В алхимию", callback_data="gathering_alchemy")
        ]])
    )


@require_character
async def gathering_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопок сбора ресурсов"""
    query = update.callback_query
    data = query.data
    
    if data == "gathering_start":
        await start_gathering(update, context)
    elif data == "gathering_cancel":
        await cancel_gathering(update, context)
    elif data == "gathering_alchemy":
        await alchemy_menu(update, context)
    elif data == "gathering_back":
        await gathering_menu(update, context)
    elif data.startswith("alchemy_craft_"):
        recipe_id = data.replace("alchemy_craft_", "")
        await craft_potion(update, context, recipe_id)