# equipment.py
import random
from telegram import Update
from telegram.ext import ContextTypes
from database import Player
from rank_system import RankSystem, ITEM_RANKS
from keyboards import get_equipment_keyboard
from utils import update_message, is_resource_item, get_player_address
from main_screen import show_main_screen
from logger import GameLogger

logger = GameLogger()

# Состояния для надевания/снятия/улучшения
awaiting_equip = {}
awaiting_unequip = {}
awaiting_upgrade = {}


def format_equipment_screen(player) -> tuple:
    """Форматирует экран экипировки с рангами предметов"""
    inventory = player.get('inventory', {'items': [], 'equipped': {}})
    equipped = inventory.get('equipped', {})
    items = inventory.get('items', [])
    
    # Слоты в порядке приоритета
    slot_order = ['weapon', 'shield', 'armor', 'helmet', 'boots', 'accessory']
    slot_names = {
        'weapon': '⚔️ Оружие',
        'shield': '🛡️ Щит',
        'armor': '👕 Броня',
        'helmet': '⛑️ Шлем',
        'boots': '👢 Обувь',
        'accessory': '💍 Аксессуар'
    }
    slot_icons = {
        'weapon': '⚔️',
        'shield': '🛡️',
        'armor': '👕',
        'helmet': '⛑️',
        'boots': '👢',
        'accessory': '💍'
    }
    
    text = "⚔️ **ЭКИПИРОВКА** ⚔️\n\n"
    text += "🟢 **НАДЕТО:**\n"
    
    for slot in slot_order:
        if slot in equipped:
            item = equipped[slot]
            item_name = item.get('name', 'Предмет')
            item_rank = item.get('rank', 'G')
            rank_display = RankSystem.format_item_rank(item_rank)
            
            # Собираем статы предмета
            stats_text = []
            if 'stats' in item:
                for stat, value in item['stats'].items():
                    if stat == 'power':
                        stats_text.append(f"⚔️ +{value}")
                    elif stat == 'armor':
                        stats_text.append(f"🛡️ +{value}")
                    elif stat == 'hp':
                        stats_text.append(f"❤️ +{value}")
                    elif stat == 'mana':
                        stats_text.append(f"💙 +{value}")
                    elif stat == 'crit':
                        stats_text.append(f"💥 +{int(value*100)}%")
                    elif stat == 'dodge':
                        stats_text.append(f"💨 +{int(value*100)}%")
            
            stats_str = f" ({', '.join(stats_text)})" if stats_text else ""
            text += f"└ {slot_icons.get(slot, '📦')} {rank_display} **{item_name}**{stats_str}\n"
        else:
            text += f"└ {slot_icons.get(slot, '📦')} ❌ пусто\n"
    
    # Фильтруем предметы (не ресурсы)
    available_items = []
    for i, item in enumerate(items, 1):
        if not is_resource_item(item):
            available_items.append((i, item))
    
    text += f"\n📦 **В ИНВЕНТАРЕ** (доступно для экипировки):\n"
    
    if available_items:
        for num, item in available_items[:15]:
            item_name = item.get('name', 'Предмет')
            item_rank = item.get('rank', 'G')
            rank_display = RankSystem.format_item_rank(item_rank)
            
            stats_text = []
            if 'stats' in item:
                for stat, value in item['stats'].items():
                    if stat == 'power':
                        stats_text.append(f"⚔️ +{value}")
                    elif stat == 'armor':
                        stats_text.append(f"🛡️ +{value}")
                    elif stat == 'hp':
                        stats_text.append(f"❤️ +{value}")
                    elif stat == 'mana':
                        stats_text.append(f"💙 +{value}")
            
            stats_str = f" ({', '.join(stats_text)})" if stats_text else ""
            text += f"{num}. {rank_display} {item_name}{stats_str}\n"
        
        if len(available_items) > 15:
            text += f"\n...и ещё {len(available_items) - 15} предметов\n"
    else:
        text += "Нет предметов для экипировки\n"
    
    text += f"\n📊 Всего предметов: {len(items)} | Экипировано: {len(equipped)}"
    text += f"\n💡 Улучшить предмет можно командой `/upgrade_rank <номер>`"
    
    return text, available_items


async def show_equipment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать экран экипировки"""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        user = query.from_user
    else:
        user = update.effective_user
    
    uid = str(user.id)
    player = Player(uid)
    
    if not player.get('race'):
        await update_message(update, context, "❌ Сначала создай персонажа через /start")
        return
    
    if 'inventory' not in player.data:
        player['inventory'] = {'items': [], 'equipped': {}}
        player.save()
    
    text, available_items = format_equipment_screen(player)
    
    # Сохраняем список предметов в контекст
    context.user_data['equipment_items'] = available_items
    
    await update_message(update, context, text, reply_markup=get_equipment_keyboard(), parse_mode='Markdown')


async def equip_wear_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать процесс надевания предмета"""
    query = update.callback_query
    await query.answer()
    
    uid = str(query.from_user.id)
    player = Player(uid)
    
    if 'inventory' not in player.data:
        player['inventory'] = {'items': [], 'equipped': {}}
        player.save()
    
    _, available_items = format_equipment_screen(player)
    
    if not available_items:
        await update_message(update, context, "❌ В инвентаре нет предметов для экипировки!\n\n[🔙 Назад]", 
                            reply_markup=get_equipment_keyboard())
        return
    
    awaiting_equip[uid] = True
    context.user_data['awaiting_equip'] = True
    
    await update_message(update, context, 
        "🔄 **Введи номер предмета для экипировки:**\n\n"
        "Например: `1`\n\n"
        "_(или отправь ❌ Отмена)_",
        reply_markup=None,
        parse_mode='Markdown')


async def equip_wear_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Обработка ввода номера предмета для надевания"""
    if not context.user_data.get('awaiting_equip'):
        return False
    
    uid = str(update.effective_user.id)
    player = Player(uid)
    text = update.message.text.strip()
    
    if text.lower() in ['отмена', 'cancel', '❌']:
        context.user_data['awaiting_equip'] = False
        await show_equipment(update, context)
        return True
    
    try:
        item_num = int(text) - 1
    except ValueError:
        await update.message.reply_text("❌ Введи число (номер предмета) или ❌ Отмена")
        return True
    
    _, available_items = format_equipment_screen(player)
    
    if item_num < 0 or item_num >= len(available_items):
        await update.message.reply_text(f"❌ Неправильный номер! Доступны: 1-{len(available_items)}")
        return True
    
    original_num, item = available_items[item_num]
    
    # Определяем слот для предмета
    slot_map = {
        'weapon': 'weapon',
        'shield': 'shield',
        'armor': 'armor',
        'helmet': 'helmet',
        'boots': 'boots',
        'accessory': 'accessory',
        'artifact': 'accessory'
    }
    
    item_type = item.get('type', 'weapon')
    slot = slot_map.get(item_type, 'accessory')
    
    slot_names = {
        'weapon': 'оружие',
        'shield': 'щит',
        'armor': 'броню',
        'helmet': 'шлем',
        'boots': 'обувь',
        'accessory': 'аксессуар'
    }
    
    # Находим предмет в инвентаре
    inventory_items = player['inventory']['items']
    actual_index = -1
    actual_item = None
    
    filtered_count = 0
    for i, inv_item in enumerate(inventory_items):
        if not is_resource_item(inv_item):
            if filtered_count == original_num - 1:
                actual_index = i
                actual_item = inv_item
                break
            filtered_count += 1
    
    if actual_index == -1:
        await update.message.reply_text("❌ Предмет не найден!")
        context.user_data['awaiting_equip'] = False
        await show_equipment(update, context)
        return True
    
    # Если в слоте уже есть предмет, снимаем его
    if slot in player['inventory']['equipped']:
        old_item = player['inventory']['equipped'][slot]
        player['inventory']['items'].append(old_item)
    
    # Надеваем новый предмет
    player['inventory']['equipped'][slot] = actual_item
    player['inventory']['items'].pop(actual_index)
    
    # Пересчитываем статы игрока от экипировки
    update_player_stats_from_equipment(player)
    
    player.save()
    
    logger.equip(player['name'], actual_item.get('name', 'Предмет'), slot)
    
    context.user_data['awaiting_equip'] = False
    
    address = get_player_address(player)
    await update.message.reply_text(
        f"✅ Теперь **{actual_item.get('name', 'Предмет')}** красуется в слоте **{slot_names.get(slot, slot)}**, {address}!",
        parse_mode='Markdown'
    )
    
    await show_equipment(update, context)
    return True


async def equip_remove_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать процесс снятия предмета"""
    query = update.callback_query
    await query.answer()
    
    uid = str(query.from_user.id)
    player = Player(uid)
    
    equipped = player.get('inventory', {}).get('equipped', {})
    
    if not equipped:
        await update_message(update, context, "❌ У тебя ничего не экипировано!\n\n[🔙 Назад]", 
                            reply_markup=get_equipment_keyboard())
        return
    
    slot_names = {
        'weapon': '⚔️ оружие',
        'shield': '🛡️ щит',
        'armor': '👕 броню',
        'helmet': '⛑️ шлем',
        'boots': '👢 обувь',
        'accessory': '💍 аксессуар'
    }
    
    slots_list = "\n".join([f"• {slot_names.get(s, s)}" for s in equipped.keys()])
    
    awaiting_unequip[uid] = True
    context.user_data['awaiting_unequip'] = True
    
    await update_message(update, context, 
        f"❌ **Введи название слота для снятия:**\n\n"
        f"Доступные слоты:\n{slots_list}\n\n"
        f"Пример: `weapon` или `оружие`\n\n"
        f"_(или отправь ❌ Отмена)_",
        reply_markup=None,
        parse_mode='Markdown')


async def equip_remove_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Обработка ввода слота для снятия"""
    if not context.user_data.get('awaiting_unequip'):
        return False
    
    uid = str(update.effective_user.id)
    player = Player(uid)
    text = update.message.text.strip().lower()
    
    if text in ['отмена', 'cancel', '❌']:
        context.user_data['awaiting_unequip'] = False
        await show_equipment(update, context)
        return True
    
    slot_map = {
        'weapon': 'weapon', 'оружие': 'weapon', 'меч': 'weapon',
        'shield': 'shield', 'щит': 'shield',
        'armor': 'armor', 'броня': 'armor', 'броню': 'armor',
        'helmet': 'helmet', 'шлем': 'helmet',
        'boots': 'boots', 'обувь': 'boots', 'сапоги': 'boots',
        'accessory': 'accessory', 'аксессуар': 'accessory', 'кольцо': 'accessory'
    }
    
    slot = slot_map.get(text)
    
    if not slot:
        await update.message.reply_text(
            "❌ Неправильный слот!\n\n"
            "Доступные слоты: weapon, shield, armor, helmet, boots, accessory\n"
            "Или напиши: оружие, щит, броня, шлем, обувь, аксессуар\n\n"
            "Попробуй ещё раз или отправь ❌ Отмена"
        )
        return True
    
    if slot not in player['inventory']['equipped']:
        await update.message.reply_text(f"❌ В слоте {slot} ничего нет!")
        context.user_data['awaiting_unequip'] = False
        await show_equipment(update, context)
        return True
    
    # Снимаем предмет
    item = player['inventory']['equipped'][slot]
    player['inventory']['items'].append(item)
    del player['inventory']['equipped'][slot]
    
    # Пересчитываем статы
    update_player_stats_from_equipment(player)
    
    player.save()
    
    logger.unequip(player['name'], item.get('name', 'Предмет'), slot)
    
    context.user_data['awaiting_unequip'] = False
    
    address = get_player_address(player)
    await update.message.reply_text(
        f"✅ Ты снял **{item.get('name', 'Предмет')}**, {address}!",
        parse_mode='Markdown'
    )
    
    await show_equipment(update, context)
    return True


async def upgrade_item_rank_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Улучшить ранг предмета"""
    uid = str(update.effective_user.id)
    player = Player(uid)
    
    if not player.get('race'):
        await update_message(update, context, "❌ Сначала создай персонажа через /start")
        return
    
    if 'inventory' not in player.data:
        player['inventory'] = {'items': [], 'equipped': {}}
        player.save()
    
    if not context.args:
        await update_message(update, context, 
            "📝 **УЛУЧШЕНИЕ РАНГА ПРЕДМЕТА**\n\n"
            "Использование: `/upgrade_rank <номер>`\n\n"
            "💡 Шанс улучшения зависит от текущего ранга:\n"
            "• G→F: 90% | F→E: 80% | E→D: 70%\n"
            "• D→C: 60% | C→B: 50% | B→A: 40%\n"
            "• A→S: 30% | S→S+: 20% | S+→SS: 15%\n"
            "• SS→SS+: 10% | SS+→SSR: 8% | SSR→SSR+: 5%\n\n"
            "💰 Цена: 1000 монет\n"
            "⚠️ При провале предмет не ломается, но монеты сгорают!")
        return
    
    try:
        item_num = int(context.args[0]) - 1
        
        inventory = player['inventory']['items']
        if item_num < 0 or item_num >= len(inventory):
            await update_message(update, context, "❌ Неправильный номер предмета!")
            return
        
        item = inventory[item_num]
        
        # Проверяем, не ресурс ли это
        if is_resource_item(item):
            await update_message(update, context, "❌ Нельзя улучшить ресурс!")
            return
        
        current_rank = item.get('rank', 'G')
        rank_order = ["G", "F", "E", "D", "C", "B", "A", "S", "S+", "SS", "SS+", "SSR", "SSR+"]
        
        if current_rank not in rank_order:
            current_rank = "G"
        
        if rank_order.index(current_rank) + 1 >= len(rank_order):
            await update_message(update, context, f"❌ {RankSystem.format_item_rank(current_rank)} — максимальный ранг!")
            return
        
        if player['money'] < 1000:
            await update_message(update, context, f"💸 Нужно 1000 монет! У тебя {player['money']}")
            return
        
        player['money'] -= 1000
        
        success, new_rank, chance = RankSystem.upgrade_item_rank(current_rank)
        
        if success:
            item['rank'] = new_rank
            # Обновляем статы предмета с учётом нового ранга
            update_item_stats_by_rank(item, new_rank)
            player.save()
            await update_message(update, context,
                f"✅ **УЛУЧШЕНИЕ УСПЕШНО!**\n\n"
                f"📦 {item.get('name', 'Предмет')}\n"
                f"{RankSystem.format_item_rank(current_rank)} → {RankSystem.format_item_rank(new_rank)}\n"
                f"🎲 Шанс: {chance}%\n"
                f"💰 Осталось монет: {player['money']}",
                parse_mode='Markdown')
        else:
            player.save()
            await update_message(update, context,
                f"❌ **УЛУЧШЕНИЕ НЕ УДАЛОСЬ!**\n\n"
                f"📦 {item.get('name', 'Предмет')}\n"
                f"{RankSystem.format_item_rank(current_rank)} остаётся\n"
                f"🎲 Шанс был: {chance}%\n"
                f"💰 Потеряно: 1000 монет\n\n"
                f"💡 Попробуй ещё раз!",
                parse_mode='Markdown')
    
    except ValueError:
        await update_message(update, context, "❌ Номер должен быть числом!")


def update_player_stats_from_equipment(player):
    """Пересчитывает боевые статы игрока от экипировки"""
    equipped = player.get('inventory', {}).get('equipped', {})
    
    # Базовые статы
    base_power = player.get('base_power', 50)
    base_crit = 0.1
    base_dodge = 0.05
    base_block = 0.05
    
    power_bonus = 0
    crit_bonus = 0
    dodge_bonus = 0
    block_bonus = 0
    
    for slot, item in equipped.items():
        if 'stats' in item:
            for stat, value in item['stats'].items():
                if stat == 'power':
                    power_bonus += value
                elif stat == 'crit':
                    crit_bonus += value
                elif stat == 'dodge':
                    dodge_bonus += value
                elif stat == 'block':
                    block_bonus += value
    
    player['power'] = base_power + power_bonus
    player['crit_chance'] = min(0.75, base_crit + crit_bonus)
    player['dodge_chance'] = min(0.5, base_dodge + dodge_bonus)
    player['block_chance'] = min(0.5, base_block + block_bonus)


def update_item_stats_by_rank(item, new_rank):
    """Обновляет статы предмета при повышении ранга"""
    rank_multiplier = ITEM_RANKS.get(new_rank, ITEM_RANKS["G"])["multiplier"]
    
    if 'stats' in item:
        for stat, value in item['stats'].items():
            if stat in ['power', 'armor', 'hp', 'mana', 'spell_damage']:
                new_value = int(value * rank_multiplier)
                item['stats'][stat] = max(1, new_value)