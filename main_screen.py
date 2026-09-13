# main_screen.py - ДОБАВЛЕН ПРОПУЩЕННЫЙ ИМПОРТ
import os
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from database import Player, Database
from keyboards import get_main_keyboard, get_races_inline, get_genders_inline, get_class_keyboard  # ДОБАВЛЕН get_main_keyboard
from game_data import LOCATIONS
from rank_system import RankSystem
from utils import update_message, format_hp_bar, get_race_emoji, get_class_emoji
from logger import GameLogger

logger = GameLogger()
db = Database()


def get_players_at_location(location_key: str) -> int:
    """Подсчитывает количество игроков на указанной локации"""
    data = db.get_all()
    count = 0
    for uid, p in data.items():
        if uid.startswith('_') or not isinstance(p, dict):
            continue
        if p.get('race') and p.get('location') == location_key:
            count += 1
    return count


def format_main_screen_text(player, location_id: str) -> str:
    """Форматирует текст главного экрана"""
    
    # Исправляем расу, если нужно
    player.fix_race()
    
    loc_data = LOCATIONS.get(location_id, LOCATIONS.get('city', {'name': '🏰 Авалон', 'desc': 'Главный город'}))
    current_mana, max_mana, mana_regen = player.get_mana_info()
    players_count = get_players_at_location(location_id)
    
    hp_bar = format_hp_bar(player['hp'], player['max_hp'])
    
    # Получаем эмодзи класса
    class_emoji = get_class_emoji(player.get('class'))
    
    # Получаем эмодзи расы
    race_name = player.get('race', '')
    race_emoji = get_race_emoji(race_name)
    
    # Формируем префикс с эмодзи: сначала класс, потом раса
    if class_emoji and race_emoji and race_emoji != '👤':
        emoji_prefix = f"{class_emoji}{race_emoji}"
    elif class_emoji:
        emoji_prefix = class_emoji
    elif race_emoji and race_emoji != '👤':
        emoji_prefix = race_emoji
    else:
        emoji_prefix = ''
    
    # Ранг
    rank_text = RankSystem.format_player_rank(player['power'])
    
    # Имя
    player_name = player.get('name', 'Безымянный')
    
    # Собираем текст
    text = f"**{loc_data['name']}**\n"
    text += f"_{loc_data['desc']}_\n\n"
    
    if emoji_prefix:
        text += f"{emoji_prefix} **{player_name}**\n"
    else:
        text += f"**{player_name}**\n"
    
    text += f"{rank_text}\n"
    text += f"❤️ {hp_bar} {player['hp']}/{player['max_hp']}\n"
    text += f"💙 {current_mana}/{max_mana} (+{player.get('mana_regen', 1)}/мин)\n"
    text += f"⚔️ {player['power']} 💰 {player['money']}\n"
    text += f"⭐ Ур.{player['level']} 📚 {player['exp']}\n\n"
    
    text += f"👥 Авантюристов здесь: {players_count}\n"
    
    if location_id == 'dungeon':
        floor = player.get('dungeon_floor', 1)
        progress = player.get('dungeon_progress', 0)
        text += f"\n📍 Этаж подземелья: {floor}/5"
        if progress > 0:
            text += f" | 🎯 Прогресс: {progress}/?"
    
    return text


async def send_location_image(context, chat_id, location_id: str, caption: str = None):
    """Отправляет картинку локации"""
    loc_data = LOCATIONS.get(location_id, LOCATIONS.get('city', {}))
    image_path = loc_data.get('image', '')
    
    if os.path.exists(image_path):
        try:
            with open(image_path, 'rb') as photo:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=caption,
                    parse_mode='Markdown'
                )
            return True
        except Exception as e:
            print(f"Ошибка отправки картинки {image_path}: {e}")
    return False


async def show_main_screen(update: Update, context: ContextTypes.DEFAULT_TYPE, location_id: str = None):
    """Показать главный экран (основное меню)"""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        user = query.from_user
        message = query.message
    else:
        user = update.effective_user
        message = update.message
    
    uid = str(user.id)
    player = Player(uid)
    
    if not player.get('race'):
        await update_message(update, context, "❌ Сначала создай персонажа через /start")
        return
    
    # ===== НОВАЯ ПРОВЕРКА: целостность персонажа =====
    is_complete, missing = player.is_complete()
    
    if not is_complete:
        # Если не хватает каких-то данных — отправляем на до创建ние
        await fix_character_handler(update, context, player, missing)
        return
    
    from hospital import hospital
    if await hospital.handle_location_check(update, context, uid, player):
        return
    
    if location_id is None:
        location_id = player.get('location', 'city')
    
    if player.get('location') != location_id:
        player['location'] = location_id
        player.save()
    
    text = format_main_screen_text(player, location_id)
    
    loc_data = LOCATIONS.get(location_id, LOCATIONS.get('city', {}))
    image_path = loc_data.get('image', '')
    reply_markup = get_main_keyboard(location_id)
    
    if os.path.exists(image_path):
        try:
            if update.callback_query:
                await message.edit_text(text, parse_mode='Markdown', reply_markup=reply_markup)
                with open(image_path, 'rb') as photo:
                    await context.bot.send_photo(
                        chat_id=int(uid),
                        photo=photo,
                        caption=f"📍 **{loc_data.get('name', 'Локация')}**",
                        parse_mode='Markdown'
                    )
            else:
                await message.reply_photo(
                    photo=open(image_path, 'rb'),
                    caption=text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            return
        except Exception as e:
            print(f"Ошибка отправки картинки локации: {e}")
    
    await update_message(update, context, text, reply_markup=reply_markup, parse_mode='Markdown')


async def change_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик смены локации"""
    query = update.callback_query
    await query.answer()
    
    to_location = query.data.replace("loc_", "")
    
    if to_location not in LOCATIONS:
        await query.edit_message_text("❌ Неизвестная локация!")
        return
    
    uid = str(query.from_user.id)
    player = Player(uid)
    
    from hospital import hospital
    if hospital.is_in_hospital(uid):
        await query.answer("🏥 Ты в больнице! Сначала вылечись.", show_alert=True)
        return
    
    if player.is_dead():
        await query.answer("💀 Ты мёртв! Воскресни в таверне.", show_alert=True)
        return
    
    old_location = player.get('location', 'city')
    
    from race_cities import can_travel_to, get_city_travel_text
    can_move, reason = can_travel_to(old_location, to_location, player.get('race'))
    if not can_move:
        await query.answer(reason, show_alert=True)
        return
    
    player['location'] = to_location
    player.save()
    
    travel_text = get_city_travel_text(old_location, to_location)
    
    await query.edit_message_text(f"🚶‍♂️ {travel_text}\n\n_Загрузка..._", parse_mode='Markdown')
    
    await asyncio.sleep(1.5)
    
    await show_main_screen(update, context, to_location)


async def fix_character_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, player, missing_fields: list):
    """Предлагает игроку выбрать недостающие данные"""
    
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        user = query.from_user
        message_func = query.edit_message_text
    else:
        user = update.effective_user
        message_func = update.message.reply_text
    
    uid = str(user.id)
    
    # Определяем, какое поле нужно заполнить первым
    if 'race' in missing_fields:
        text = "🧙 **ВОССТАНОВЛЕНИЕ ПЕРСОНАЖА** 🧙\n\n"
        text += "Твои данные повреждены или отсутствуют.\n"
        text += "Давай восстановим твоего героя!\n\n"
        text += "**Шаг 1:** Выбери свою расу:"
        
        await message_func(text, parse_mode='Markdown', reply_markup=get_races_inline())
        context.user_data['fixing_character'] = True
        context.user_data['fix_step'] = 'race'
        
    elif 'gender' in missing_fields:
        text = "🧙 **ВОССТАНОВЛЕНИЕ ПЕРСОНАЖА** 🧙\n\n"
        text += f"Твоя раса: {player.get('race')}\n\n"
        text += "**Шаг 2:** Выбери свой пол:"
        
        await message_func(text, parse_mode='Markdown', reply_markup=get_genders_inline())
        context.user_data['fixing_character'] = True
        context.user_data['fix_step'] = 'gender'
        
    elif 'class' in missing_fields:
        text = "🧙 **ВОССТАНОВЛЕНИЕ ПЕРСОНАЖА** 🧙\n\n"
        text += f"Твоя раса: {player.get('race')}\n"
        text += f"Твой пол: {player.get('gender', 'не выбран')}\n\n"
        text += "**Шаг 3:** Выбери свой класс:"
        
        await message_func(text, parse_mode='Markdown', reply_markup=get_class_keyboard())
        context.user_data['fixing_character'] = True
        context.user_data['fix_step'] = 'class'