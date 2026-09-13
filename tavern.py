# tavern.py - ИСПРАВЛЕННАЯ ВЕРСИЯ (только изменённые функции)
# Полный файл слишком большой, показываю только добавление декоратора

import random
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Player
from utils import update_message, require_character
from main_screen import show_main_screen
from logger import GameLogger
from config import ALE_PRICE

logger = GameLogger()

# ... (ALE_TYPES, DRUNK_LEVELS, RANDOM_EVENTS, SYNERGIES, SECRET_ACHIEVEMENTS остаются без изменений)

active_sessions = {}
_sleeping_players = {}
player_drinks_history = {}
player_synergies_used = {}
player_achievements = {}


async def leave_tavern(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выйти из таверны на главный экран"""
    uid = str(update.effective_user.id)
    player = Player(uid)
    
    if uid in active_sessions:
        del active_sessions[uid]
    if uid in player_drinks_history:
        del player_drinks_history[uid]
    
    player['location'] = 'city'
    player.save()
    
    await update.message.reply_text("🚪 Ты покинул таверну и вернулся в Авалон.")
    await show_main_screen(update, context)


@require_character
async def sit_at_counter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сесть за стойку"""
    uid = str(update.effective_user.id)
    player = Player(uid)
    
    if player.get('location') != 'tavern':
        await update_message(update, context, "🍺 Сесть за стойку можно только в таверне!")
        return
    
    if is_asleep(uid):
        remaining = get_sleep_remaining(uid)
        minutes = remaining // 60
        seconds = remaining % 60
        await update_message(update, context, f"💤 Ты спишь! Осталось: {minutes}:{seconds:02d}")
        return
    
    active_sessions[uid] = True
    player_drinks_history[uid] = []
    player_synergies_used[uid] = set()
    
    from keyboards import get_tavern_menu_keyboard
    
    await update_message(update, context, 
        "🍺 **ДОБРО ПОЖАЛОВАТЬ В ТАВЕРНУ!** 🍺\n\n"
        "_Бармен улыбается и протирает кружку._\n\n"
        "Выбери эль или закуску:",
        reply_markup=get_tavern_menu_keyboard(), 
        parse_mode='Markdown')


@require_character
async def leave_counter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выйти из-за стойки"""
    uid = str(update.effective_user.id)
    
    if uid in active_sessions:
        del active_sessions[uid]
    if uid in player_drinks_history:
        del player_drinks_history[uid]
    
    await update_message(update, context, 
        "🚪 **Ты встаёшь из-за стойки.**\n\n"
        "_Бармен машет тебе на прощание._",
        parse_mode='Markdown')
    await show_main_screen(update, context)


@require_character
async def show_ale_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню эля"""
    uid = str(update.effective_user.id)
    
    if uid not in active_sessions:
        await update_message(update, context, "❌ Сначала сядь за стойку!")
        return
    
    text = "🍺 **МЕНЮ ЭЛЯ** 🍺\n\n"
    keyboard = []
    
    for ale_id, ale in ALE_TYPES.items():
        text += f"{ale['emoji']} **{ale['name']}** — {ale['price']}💰\n"
        text += f"   _{ale['description']}_\n"
        
        if ale['buffs']:
            buffs = []
            for stat, val in ale['buffs'].items():
                if '%' in stat:
                    buffs.append(f"+{int(val*100)}%")
                else:
                    buffs.append(f"+{val}")
            text += f"   ✨ Эффект: {', '.join(buffs)}\n"
        
        if ale['debuffs']:
            debuffs = []
            for stat, val in ale['debuffs'].items():
                if '%' in stat:
                    debuffs.append(f"{int(val*100)}%")
                else:
                    debuffs.append(f"{val}")
            text += f"   ⚠️ Побочка: {', '.join(debuffs)}\n"
        
        text += "\n"
        keyboard.append([InlineKeyboardButton(f"{ale['emoji']} {ale['name']} — {ale['price']}💰", 
                                             callback_data=f"order_ale_{ale_id}")])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад в меню", callback_data="tavern_menu_back")])
    
    await update_message(update, context, text, 
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode='Markdown')


@require_character
async def order_ale(update: Update, context: ContextTypes.DEFAULT_TYPE, ale_id: str):
    """Заказать конкретный эль"""
    query = update.callback_query
    await query.answer()
    
    uid = str(query.from_user.id)
    player = Player(uid)
    
    if uid not in active_sessions:
        await query.edit_message_text("❌ Сначала сядь за стойку!")
        return
    
    if ale_id not in ALE_TYPES:
        await query.edit_message_text("❌ Такого эля нет в меню!")
        return
    
    ale = ALE_TYPES[ale_id]
    
    if is_asleep(uid):
        remaining = get_sleep_remaining(uid)
        minutes = remaining // 60
        seconds = remaining % 60
        await query.edit_message_text(f"💤 Ты спишь! Осталось: {minutes}:{seconds:02d}")
        return
    
    if player['money'] < ale['price']:
        await query.edit_message_text(f"💸 Не хватает монет! {ale['name']} стоит {ale['price']}💰")
        return
    
    player['money'] -= ale['price']
    
    if uid not in player_drinks_history:
        player_drinks_history[uid] = []
    player_drinks_history[uid].append(ale_id)
    
    total_drinks = player.get('total_drinks', 0) + 1
    player['total_drinks'] = total_drinks
    
    drunk_level = player.get('drunk_level', 0)
    drunk_level = min(drunk_level + 1, max(DRUNK_LEVELS.keys()))
    player['drunk_level'] = drunk_level
    
    apply_ale_effects(player, ale)
    synergy_result = check_synergy(uid, player_drinks_history[uid])
    
    event_result = None
    if random.random() < 0.2:
        event_result = random.choice(RANDOM_EVENTS)
        apply_event_effect(player, event_result)
    
    new_achievements = check_secret_achievements(uid, player, total_drinks, drunk_level)
    
    passed_out = False
    if drunk_level >= 5 and random.random() < 0.3:
        passed_out = True
        await pass_out(uid, context, player)
    
    player.save()
    
    text = f"{ale['emoji']} **Ты заказал {ale['name']}!**\n\n"
    
    if ale['buffs']:
        buff_text = []
        for stat, val in ale['buffs'].items():
            if stat == 'crit':
                buff_text.append(f"+{int(val*100)}% к критическому урону")
            elif stat == 'dodge':
                buff_text.append(f"+{int(val*100)}% к увороту")
            elif stat == 'spell_damage':
                buff_text.append(f"+{val} к урону заклинаний")
            elif stat == 'mana_regen':
                buff_text.append(f"+{val} к регенерации маны")
            else:
                buff_text.append(f"+{val} к {stat}")
        text += f"✨ **Эффект:** {', '.join(buff_text)}\n"
    
    if ale['debuffs']:
        debuff_text = []
        for stat, val in ale['debuffs'].items():
            if stat == 'accuracy':
                debuff_text.append(f"{int(val*100)}% к точности")
            elif stat == 'dodge':
                debuff_text.append(f"{int(val*100)}% к увороту")
            else:
                debuff_text.append(f"{val} к {stat}")
        text += f"⚠️ **Побочка:** {', '.join(debuff_text)}\n"
    
    text += f"\n🍺 Выпито всего: {total_drinks}\n"
    
    drunk_info = DRUNK_LEVELS.get(drunk_level, DRUNK_LEVELS[0])
    text += f"{drunk_info['emoji']} **{drunk_info['name']}** — {drunk_info['description']}\n"
    
    if synergy_result:
        text += f"\n✨ **СИНЕРГИЯ!** {synergy_result['text']}\n"
        for stat, val in synergy_result['effect'].items():
            if stat == 'crit':
                text += f"  └ +{int(val*100)}% к криту\n"
            elif stat == 'dodge':
                text += f"  └ +{int(val*100)}% к увороту\n"
            else:
                text += f"  └ +{val} к {stat}\n"
    
    if event_result:
        text += f"\n🎲 **Случайное событие:** {event_result['text']}\n"
    
    if new_achievements:
        text += f"\n🏆 **НОВЫЕ ДОСТИЖЕНИЯ!** 🏆\n"
        for ach in new_achievements:
            text += f"  └ {ach['name']} +{ach['reward']}💰\n"
    
    text += f"\n💰 Осталось монет: {player['money']}"
    
    if passed_out:
        text += "\n\n💀 **Ты потерял сознание...**\n_Бармен укладывает тебя на лавку._"
    
    from keyboards import get_drink_keyboard
    
    if passed_out:
        await query.edit_message_text(text, parse_mode='Markdown')
        if uid in active_sessions:
            del active_sessions[uid]
        await asyncio.sleep(3)
        await show_main_screen(update, context)
    else:
        await query.edit_message_text(text, parse_mode='Markdown', 
                                     reply_markup=get_drink_keyboard())
    
    logger.work(player['name'], -ale['price'], player['money'], f"выпил {ale['name']}")


# ... (остальные функции apply_ale_effects, check_synergy, apply_event_effect, 
#      check_secret_achievements, order_food, play_dice, show_tavern_achievements,
#      listen_stories, pass_out, wake_up, is_asleep, get_sleep_remaining,
#      reset_daily_drinks остаются без изменений)


@require_character
async def tavern_menu_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться в меню таверны"""
    query = update.callback_query
    await query.answer()
    
    from keyboards import get_tavern_menu_keyboard
    await query.edit_message_text(
        "🍺 **Чего желаешь?**",
        reply_markup=get_tavern_menu_keyboard(),
        parse_mode='Markdown'
    )


async def drink_ale(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /drink - выпить эль (быстрый заказ)"""
    uid = str(update.effective_user.id)
    
    if uid not in active_sessions:
        await update_message(update, context, "❌ Сначала сядь за стойку командой 'Сесть за стойку'!")
        return
    
    await show_ale_menu(update, context)


@require_character
async def tavern_exit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выйти из таверны (кнопка внутри меню)"""
    query = update.callback_query
    await query.answer()
    
    uid = str(query.from_user.id)
    
    if uid in active_sessions:
        del active_sessions[uid]
    if uid in player_drinks_history:
        del player_drinks_history[uid]
    
    await query.edit_message_text("🚪 Ты покинул таверну...")
    await asyncio.sleep(1)
    await show_main_screen(update, context)
    
# ===== ДОБАВИТЬ В КОНЕЦ tavern.py (перед tavern_exit) =====

def apply_ale_effects(player, ale):
    """Применяет эффекты эля к игроку"""
    if ale.get('buffs'):
        for stat, value in ale['buffs'].items():
            current = player.get(stat, 0)
            if stat == 'crit':
                player[stat] = min(0.75, current + value)
            elif stat == 'dodge':
                player[stat] = min(0.50, current + value)
            else:
                player[stat] = current + value
    
    if ale.get('debuffs'):
        for stat, value in ale['debuffs'].items():
            current = player.get(stat, 0)
            if stat == 'crit':
                player[stat] = max(0.05, current - value)
            elif stat == 'dodge':
                player[stat] = max(0.01, current - value)
            else:
                player[stat] = max(0, current - value)


def check_synergy(uid: str, drinks_history: list) -> dict:
    """Проверяет синергию выпитых элей"""
    if len(drinks_history) < 2:
        return None
    
    last_two = drinks_history[-2:]
    
    # Синергия: два разных эля подряд
    if last_two[0] != last_two[1]:
        return {
            'text': 'Разнообразие — ключ к успеху! Ты получил +5 ко всем характеристикам!',
            'effect': {'power': 5, 'crit': 0.03, 'dodge': 0.03}
        }
    
    # Синергия: три одинаковых эля
    if len(drinks_history) >= 3 and drinks_history[-3] == drinks_history[-2] == drinks_history[-1]:
        return {
            'text': 'Три одинаковых эля! Твоё тело привыкло к напитку! +10 HP и +5 маны!',
            'effect': {'hp': 10, 'mana': 5}
        }
    
    return None


def apply_event_effect(player, event):
    """Применяет эффект случайного события"""
    if 'effect' in event:
        for stat, value in event['effect'].items():
            if stat == 'money':
                player['money'] = max(0, player['money'] + value)
            elif stat == 'hp':
                player['hp'] = min(player['max_hp'], player['hp'] + value)
            elif stat == 'mana':
                player['mana'] = min(player['max_mana'], player.get('mana', 50) + value)
            else:
                current = player.get(stat, 0)
                player[stat] = current + value


def check_secret_achievements(uid: str, player, total_drinks: int, drunk_level: int) -> list:
    """Проверяет секретные достижения в таверне"""
    achievements = []
    
    if total_drinks == 10 and not player.get('ach_first_round'):
        player['ach_first_round'] = True
        player['money'] = player.get('money', 0) + 500
        achievements.append({'name': '🍺 Первый раунд', 'reward': 500})
    
    if drunk_level >= 5 and not player.get('ach_drunk_master'):
        player['ach_drunk_master'] = True
        player['money'] = player.get('money', 0) + 1000
        achievements.append({'name': '🥴 Пьяный мастер', 'reward': 1000})
    
    return achievements