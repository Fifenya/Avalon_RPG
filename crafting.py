# crafting.py
import random
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from database import Player
from game_data import SMELTING_RECIPES, CRAFT_RECIPES, EQUIPMENT_RECIPES, RESOURCES
from keyboards import get_crafting_keyboard
from utils import update_message
from main_screen import show_main_screen
from logger import GameLogger
from session_manager import session_manager

logger = GameLogger()
session_manager.save()

# Активные процессы крафта/плавки
active_crafts = {}


async def check_active_craft(uid: str, update: Update, context: ContextTypes.DEFAULT_TYPE, action_name: str = "крафт") -> bool:
    """Проверяет, не занят ли игрок крафтом/плавкой. Возвращает True если занят."""
    if uid in active_crafts:
        await update_message(update, context, f"⏳ Уже идёт {action_name}! Дождись завершения.")
        return True
    return False


async def start_craft_timer(uid: str, duration: int, context: ContextTypes.DEFAULT_TYPE, item_name: str):
    """Запускает таймер для крафта"""
    await asyncio.sleep(duration)
    if uid in active_crafts:
        del active_crafts[uid]
        player = Player(uid)
        await context.bot.send_message(
            chat_id=int(uid),
            text=f"✅ **{item_name}** готов! Ты можешь начать новый крафт.",
            parse_mode='Markdown'
        )


async def crafting_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню крафта"""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
    
    text = "🔨 **МАСТЕРСКАЯ** 🔨\n\nВыбери категорию:"
    
    await update_message(update, context, text, reply_markup=get_crafting_keyboard(), parse_mode='Markdown')


async def crafting_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых кнопок крафта и callback-запросов"""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        text = query.data
        if text.startswith("craft_"):
            text = text.replace("craft_", "")
    else:
        text = update.message.text
    
    if text == "🔨 Крафт" or text == "🔙 На главную":
        await show_main_screen(update, context)
    
    elif text == "🔥 Плавка":
        await smelting_menu(update, context)
    
    elif text == "🔨 Крафт слитков":
        await craft_ingots_menu(update, context)
    
    elif text.startswith("⚔️ ") or text.startswith("🛡️ ") or text.startswith("🔮 ") or \
         text.startswith("💍 ") or text.startswith("🏹 ") or text.startswith("🧪 "):
        await craft_item(update, context, text)


async def smelting_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню плавки"""
    uid = str(update.effective_user.id)
    player = Player(uid)
    
    if await check_active_craft(uid, update, context, "плавка"):
        return
    
    text = "🔥 **ПЛАВКА** 🔥\n\n"
    text += "Руда + уголь = осколки\n\n"
    
    for recipe_id, recipe in SMELTING_RECIPES.items():
        mats = []
        for mat_id, count in recipe['materials'].items():
            mat_name = RESOURCES.get(mat_id, {}).get('name', mat_id)
            mats.append(f"{mat_name} x{count}")
        
        time_min = recipe['time'] // 60
        time_sec = recipe['time'] % 60
        time_str = f"{time_min}м {time_sec}с" if time_min else f"{time_sec}с"
        
        text += f"• **{recipe['name']}**: {' + '.join(mats)} → ⏱️ {time_str}\n"
    
    text += "\n📝 Введи название рецепта для плавки (например: Железный осколок)"
    
    context.user_data['crafting_mode'] = 'smelting'
    
    await update_message(update, context, text, parse_mode='Markdown')


async def craft_ingots_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню крафта слитков"""
    uid = str(update.effective_user.id)
    player = Player(uid)
    
    if await check_active_craft(uid, update, context, "крафт"):
        return
    
    text = "🔨 **КРАФТ СЛИТКОВ** 🔨\n\n"
    text += "3 осколка = 1 слиток\n\n"
    
    for recipe_id, recipe in CRAFT_RECIPES.items():
        mats = []
        for mat_id, count in recipe['materials'].items():
            mat_name = RESOURCES.get(mat_id, {}).get('name', mat_id)
            mats.append(f"{mat_name} x{count}")
        
        text += f"• **{recipe['name']}**: {' + '.join(mats)}\n"
    
    text += "\n📝 Введи название рецепта для крафта (например: Железный слиток)"
    
    context.user_data['crafting_mode'] = 'ingots'
    
    await update_message(update, context, text, parse_mode='Markdown')


async def process_craft_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Обработка ввода названия рецепта для крафта/плавки"""
    if 'crafting_mode' not in context.user_data:
        return False
    
    uid = str(update.effective_user.id)
    player = Player(uid)
    text = update.message.text.strip()
    mode = context.user_data['crafting_mode']
    
    if uid in active_crafts:
        await update.message.reply_text("⏳ Уже идёт крафт/плавка! Дождись завершения.")
        del context.user_data['crafting_mode']
        return True
    
    if mode == 'smelting':
        selected_recipe = None
        for rid, rec in SMELTING_RECIPES.items():
            if rec['name'].lower() == text.lower():
                selected_recipe = rec
                break
        
        if not selected_recipe:
            await update.message.reply_text("❌ Рецепт не найден! Попробуй ещё раз или /cancel")
            return True
        
        resources = player.get('resources', {})
        missing = []
        for mat_id, needed in selected_recipe['materials'].items():
            if resources.get(mat_id, 0) < needed:
                missing.append(f"{RESOURCES.get(mat_id, {}).get('name', mat_id)} x{needed}")
        
        if missing:
            await update.message.reply_text(f"❌ Не хватает:\n" + "\n".join(missing))
            del context.user_data['crafting_mode']
            return True
        
        for mat_id, needed in selected_recipe['materials'].items():
            resources[mat_id] -= needed
            if resources[mat_id] <= 0:
                del resources[mat_id]
        
        result_id = selected_recipe['result']
        result_count = selected_recipe.get('result_count', 1)
        resources[result_id] = resources.get(result_id, 0) + result_count
        
        player.save()
        
        time_min = selected_recipe['time'] // 60
        time_sec = selected_recipe['time'] % 60
        time_str = f"{time_min}м {time_sec}с" if time_min else f"{time_sec}с"
        
        await update.message.reply_text(
            f"✅ Ты создал **{selected_recipe['name']}** x{result_count}!\n⏱️ Время: {time_str}",
            parse_mode='Markdown'
        )
        
        logger.craft_complete(player['name'], selected_recipe['name'], result_count)
        
        del context.user_data['crafting_mode']
        await crafting_menu(update, context)
        return True
    
    elif mode == 'ingots':
        selected_recipe = None
        for rid, rec in CRAFT_RECIPES.items():
            if rec['name'].lower() == text.lower():
                selected_recipe = rec
                break
        
        if not selected_recipe:
            await update.message.reply_text("❌ Рецепт не найден! Попробуй ещё раз или /cancel")
            return True
        
        resources = player.get('resources', {})
        missing = []
        for mat_id, needed in selected_recipe['materials'].items():
            if resources.get(mat_id, 0) < needed:
                missing.append(f"{RESOURCES.get(mat_id, {}).get('name', mat_id)} x{needed}")
        
        if missing:
            await update.message.reply_text(f"❌ Не хватает:\n" + "\n".join(missing))
            del context.user_data['crafting_mode']
            return True
        
        for mat_id, needed in selected_recipe['materials'].items():
            resources[mat_id] -= needed
            if resources[mat_id] <= 0:
                del resources[mat_id]
        
        result_id = selected_recipe['result']
        result_count = selected_recipe.get('result_count', 1)
        resources[result_id] = resources.get(result_id, 0) + result_count
        
        player.save()
        
        await update.message.reply_text(f"✅ Ты создал **{selected_recipe['name']}** x{result_count}!", parse_mode='Markdown')
        
        logger.craft_complete(player['name'], selected_recipe['name'], result_count)
        
        del context.user_data['crafting_mode']
        await crafting_menu(update, context)
        return True
    
    return False


async def craft_item(update: Update, context: ContextTypes.DEFAULT_TYPE, item_name: str):
    """Крафт предмета из меню (оружие, броня и т.д.)"""
    uid = str(update.effective_user.id)
    player = Player(uid)
    
    if await check_active_craft(uid, update, context, "крафт"):
        return
    
    emoji_list = ["⚔️ ", "🛡️ ", "🔮 ", "💍 ", "🏹 ", "🧪 ", "⛑️ ", "👢 "]
    for emoji in emoji_list:
        if item_name.startswith(emoji):
            item_name = item_name.replace(emoji, "")
            break
    
    selected_recipe = None
    for recipe_id, recipe in EQUIPMENT_RECIPES.items():
        if recipe['name'].lower() == item_name.lower():
            selected_recipe = recipe
            break
    
    if not selected_recipe:
        await update_message(update, context, f"❌ Рецепт **{item_name}** не найден!", parse_mode='Markdown')
        return
    
    resources = player.get('resources', {})
    missing = []
    for mat_id, needed in selected_recipe['materials'].items():
        current = resources.get(mat_id, 0)
        if current < needed:
            mat_name = RESOURCES.get(mat_id, {}).get('name', mat_id)
            missing.append(f"{mat_name} x{needed} (есть {current})")
    
    if missing:
        await update_message(update, context, f"❌ **Не хватает ресурсов для {selected_recipe['name']}**\n\n" + "\n".join(missing), parse_mode='Markdown')
        return
    
    for mat_id, needed in selected_recipe['materials'].items():
        resources[mat_id] -= needed
        if resources[mat_id] <= 0:
            del resources[mat_id]
    
    result_count = selected_recipe.get('result_count', 1)
    
    if 'inventory' not in player.data:
        player['inventory'] = {'items': [], 'equipped': {}}
    
    new_item = {
        'id': selected_recipe.get('result', selected_recipe.get('name')),
        'name': selected_recipe['name'],
        'type': selected_recipe.get('type', 'item'),
        'rarity': selected_recipe.get('rarity', 'common'),
        'stats': selected_recipe.get('stats', {})
    }
    
    for _ in range(result_count):
        player['inventory']['items'].append(new_item.copy())
    
    player.save()
    
    stats_text = ""
    if selected_recipe.get('stats'):
        stats_parts = []
        stat_icons = {
            'power': '⚔️', 'armor': '🛡️', 'hp': '❤️', 'mana': '💙',
            'spell_damage': '✨', 'crit': '💥', 'dodge': '💨', 'block': '🛡️'
        }
        for stat, value in selected_recipe['stats'].items():
            icon = stat_icons.get(stat, '📊')
            if stat in ['crit', 'dodge', 'block']:
                stats_parts.append(f"{icon} +{value*100:.0f}%")
            else:
                stats_parts.append(f"{icon} +{value}")
        stats_text = f"\n📊 **Характеристики:** {' '.join(stats_parts)}"
    
    type_emoji = {
        'weapon': '⚔️', 'armor': '🛡️', 'helmet': '⛑️', 'boots': '👢',
        'shield': '🛡️', 'staff': '🔮', 'bow': '🏹', 'potion': '🧪', 'accessory': '💍'
    }.get(selected_recipe.get('type'), '📦')
    
    await update_message(update, context,
        f"✅ **КРАФТ УСПЕШЕН!**\n\n"
        f"{type_emoji} **{selected_recipe['name']}** x{result_count}\n"
        f"{stats_text}\n\n"
        f"💡 Найти предмет можно в **Экипировке**",
        parse_mode='Markdown'
    )
    
    logger.craft_complete(player['name'], selected_recipe['name'], result_count)