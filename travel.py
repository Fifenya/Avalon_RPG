# travel.py v2 — перемещения: основные локации + города рас
import asyncio
import random
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from database import Player
from main_screen import show_main_screen
from cities_data import CITIES, CONNECTIONS, TRAVEL_TIME_CITY

TRAVEL_TIME = {'city': 10, 'forest': 15, 'tavern': 5, 'dungeon': 20, 'hospital': 10}
TRAVEL_TIME.update(TRAVEL_TIME_CITY)

LOCATION_BUTTONS = {
    'city': '🏰 Авалон',
    'forest': '🌲 Дремучий лес',
    'tavern': '🍺 Таверна',
    'dungeon': '🏚️ Подземелье',
    'hospital': '🏥 Госпиталь',
}

MOB_FACTS = [
    "🐀 Крыса-мутант — первый моб новичков: всего 85 HP и 12 силы.",
    "🐺 Голодный волк вдвое сильнее крысы — не ходи в лес без меча!",
    "🦇 Летучие мыши и пещерные пауки кишат на 1-м этаже подземелья.",
    "👑 Король пауков (500 HP) стережёт выход со 1-го этажа рейда.",
    "🔥 Огненный элементаль не горит в огне — зато уязвим к стали.",
    "🧟 Пылающий зомби горит, но не сгорает: 200 HP и 15 брони.",
    "🌑 Теневой призрак почти без брони (5), но бьёт на 40 силы.",
    "🐉 Древний дракон (3000 HP, 100 брони) охраняет 4-й этаж.",
    "👾 Архидемон — финальный босс Бездны: 8000 HP и 350 силы!",
    "💀 Король Личей не расстаётся с филактерией — редкий трофей.",
    "🌑 Властелин Теней наносит 140 урона за удар — бери зелья!",
    "🏛️ Титан — самый жирный босс игры: 8000 HP и 120 брони.",
    "🔥 Феникс возрождается из пепла... но только не в бою с тобой.",
    "👾 Ктулху (3000 HP) приходит лишь к самым опытным охотникам.",
]

def loc_name(loc_id):
    if loc_id in CITIES:
        return CITIES[loc_id]['name']
    return LOCATION_BUTTONS.get(loc_id, loc_id)

def get_destinations(current):
    """Куда можно пойти из текущей локации (с учётом связности городов)"""
    if current in CITIES:
        return [(i, loc_name(i)) for i in CONNECTIONS.get(current, [])]
    out = [(lid, btn) for lid, btn in LOCATION_BUTTONS.items() if lid != current]
    out += [(cid, CITIES[cid]['name']) for cid in CONNECTIONS.get(current, [])]
    return out

def _rows(dests):
    rows, row = [], []
    for _, label in dests:
        row.append(label)
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append(["🔙 На главную"])
    return rows

def _travel_text(dest_name, remaining, facts):
    return (f"🚶 **В ПУТИ: {dest_name}**\n"
            f"⏳ До места назначения осталось: {remaining} сек\n\n"
            f"💡 **Факты о мобах:**\n" + "\n".join(f"• {x}" for x in facts))

async def show_locations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player = Player(str(update.effective_user.id))
    current = player.get('location', 'city')
    dests = get_destinations(current)
    if not dests:
        await update.message.reply_text("❌ Отсюда некуда идти.")
        return
    context.user_data['travel_mode'] = True
    await update.message.reply_text(
        f"🗺️ **ВЫБОР ЛОКАЦИИ** 🗺️\n\nТы сейчас: {loc_name(current)}\nКуда отправимся?",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(_rows(dests), resize_keyboard=True))

async def travel_by_button(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> bool:
    if context.user_data.get('traveling'):
        return True  # уже в пути — игнорируем спам
    if text == "🔙 На главную":
        context.user_data['travel_mode'] = False
        await show_main_screen(update, context)
        return True
    player = Player(str(update.effective_user.id))
    current = player.get('location', 'city')
    for loc_id, label in get_destinations(current):
        if text == label:
            context.user_data['travel_mode'] = False
            await travel_to(update, context, loc_id)
            return True
    return False

async def travel_to(update: Update, context: ContextTypes.DEFAULT_TYPE, dest: str):
    print(f"🚶 [travel] travel_to: dest={dest}")
    player = Player(str(update.effective_user.id))
    if player.get('location') == dest:
        await show_main_screen(update, context)
        return
    total = TRAVEL_TIME.get(dest, 15)
    dest_name = loc_name(dest)
    facts = random.sample(MOB_FACTS, k=3)
    context.user_data['traveling'] = True
    msg = await update.message.reply_text(
        _travel_text(dest_name, total, facts), parse_mode='Markdown')
    for remaining in range(total - 1, 0, -1):
        await asyncio.sleep(1)
        try:
            await msg.edit_text(_travel_text(dest_name, remaining, facts),
                                parse_mode='Markdown')
        except Exception as e:
            import traceback
            print(f"❌ [travel] ошибка отправки темы: {e}")
            traceback.print_exc()
    player['location'] = dest
    player.save()
    context.user_data['traveling'] = False
    try:
        await msg.delete()
    except Exception:
        pass
    # 🎵 саундтрек города (если тема задана в city_themes.py)
    print(f"🎵 [travel] проверяю тему для {dest}")
    if dest in CITIES:
        try:
            from city_themes import play_theme_for_city
            await play_theme_for_city(update, context, dest)
        except Exception:
            pass
    await show_main_screen(update, context)
