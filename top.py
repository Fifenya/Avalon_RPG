# top.py
from telegram import Update
from telegram.ext import ContextTypes
from database import Database
from keyboards import get_top_keyboard
from utils import update_message
from main_screen import show_main_screen

db = Database()
top_blacklist = []  # ID игроков, исключённых из топов


def get_all_players():
    """Получить всех игроков с персонажами"""
    data = db.get_all()
    players = []
    for uid, p in data.items():
        if uid.startswith('_') or not isinstance(p, dict):
            continue
        if p.get('race') and uid not in top_blacklist:
            players.append((uid, p))
    return players


async def top_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню топов"""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
    else:
        # Если вызвано из текстовой кнопки
        pass
    
    text = "🏆 **ТОПЫ АВАЛОНА** 🏆\n\nВыбери категорию:"
    
    await update_message(update, context, text, reply_markup=get_top_keyboard(), parse_mode='Markdown')


async def top_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Топ богачей"""
    players = get_all_players()
    
    rich_players = []
    for uid, p in players:
        rich_players.append((p.get('name', 'NoName'), p.get('money', 0), p.get('level', 1)))
    
    top_list = sorted(rich_players, key=lambda x: x[1], reverse=True)[:10]
    
    if not top_list:
        await update_message(update, context, "📊 Пока нет игроков в топе", reply_markup=get_top_keyboard())
        return
    
    text = "💰 **ТОП БОГАЧЕЙ** 💰\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    for i, (name, money, level) in enumerate(top_list):
        medal = medals[i] if i < 3 else f"{i+1}."
        text += f"{medal} {name} — 💰 {money} (ур.{level})\n"
    
    await update_message(update, context, text, reply_markup=get_top_keyboard(), parse_mode='Markdown')


async def top_power(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Топ сильнейших"""
    players = get_all_players()
    
    strong_players = []
    for uid, p in players:
        strong_players.append((p.get('name', 'NoName'), p.get('power', 50), p.get('level', 1)))
    
    top_list = sorted(strong_players, key=lambda x: x[1], reverse=True)[:10]
    
    text = "⚔️ **ТОП СИЛАЧЕЙ** ⚔️\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    for i, (name, power, level) in enumerate(top_list):
        medal = medals[i] if i < 3 else f"{i+1}."
        text += f"{medal} {name} — ⚔️ {power} (ур.{level})\n"
    
    await update_message(update, context, text, reply_markup=get_top_keyboard(), parse_mode='Markdown')


async def top_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Топ по уровню"""
    players = get_all_players()
    
    level_players = []
    for uid, p in players:
        level_players.append((p.get('name', 'NoName'), p.get('level', 1), p.get('exp', 0), p.get('power', 50)))
    
    top_list = sorted(level_players, key=lambda x: (x[1], x[2]), reverse=True)[:10]
    
    text = "⭐ **ТОП ПО УРОВНЮ** ⭐\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    for i, (name, level, exp, power) in enumerate(top_list):
        medal = medals[i] if i < 3 else f"{i+1}."
        text += f"{medal} {name} — ⭐ ур.{level} (⚔️ {power})\n"
    
    await update_message(update, context, text, reply_markup=get_top_keyboard(), parse_mode='Markdown')


async def top_hunter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Топ охотников"""
    players = get_all_players()
    
    hunter_players = []
    for uid, p in players:
        kills = p.get('kills', 0)
        if kills > 0:
            hunter_players.append((p.get('name', 'NoName'), kills, p.get('level', 1)))
    
    top_list = sorted(hunter_players, key=lambda x: x[1], reverse=True)[:10]
    
    if not top_list:
        await update_message(update, context, "👾 Пока никто не убивал монстров...", reply_markup=get_top_keyboard())
        return
    
    text = "👾 **ТОП ОХОТНИКОВ** 👾\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    for i, (name, kills, level) in enumerate(top_list):
        medal = medals[i] if i < 3 else f"{i+1}."
        text += f"{medal} {name} — 💀 {kills} убийств (ур.{level})\n"
    
    await update_message(update, context, text, reply_markup=get_top_keyboard(), parse_mode='Markdown')