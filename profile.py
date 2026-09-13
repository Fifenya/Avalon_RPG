# profile.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
from telegram import Update
from telegram.ext import ContextTypes
from database import Player
from keyboards import get_profile_keyboard
from utils import update_message, format_hp_bar, get_race_emoji, get_class_emoji
from rank_system import RankSystem
from logger import GameLogger

logger = GameLogger()


def format_profile_text(player) -> str:
    """Форматирует полный профиль игрока"""
    
    # Исправляем расу, если нужно (метод возвращает bool, не нужно присваивать)
    player.fix_race()
    
    current_mana, max_mana, mana_regen = player.get_mana_info()
    
    kills = player.get('kills', 0)
    wins = player.get('wins', 0)
    losses = player.get('losses', 0)
    duel_ratio = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
    
    equipped = player.get('inventory', {}).get('equipped', {})
    weapon = equipped.get('weapon', {}).get('name', '🗡️ Нет')
    armor = equipped.get('armor', {}).get('name', '🛡️ Нет')
    helmet = equipped.get('helmet', {}).get('name', '⛑️ Нет')
    boots = equipped.get('boots', {}).get('name', '👢 Нет')
    accessory = equipped.get('accessory', {}).get('name', '💍 Нет')
    
    hp_bar = format_hp_bar(player['hp'], player['max_hp'])
    
    # Эмодзи
    class_emoji = get_class_emoji(player.get('class'))
    race_emoji = get_race_emoji(player.get('race', ''))
    
    # Формируем префикс
    if class_emoji and race_emoji and race_emoji != '👤':
        emoji_prefix = f"{class_emoji}{race_emoji}"
    elif class_emoji:
        emoji_prefix = class_emoji
    elif race_emoji and race_emoji != '👤':
        emoji_prefix = race_emoji
    else:
        emoji_prefix = ''
    
    rank_text = RankSystem.format_player_rank(player['power'])
    
    text = f"📜 **ПРОФИЛЬ** 📜\n\n"
    
    if emoji_prefix:
        text += f"{emoji_prefix} **{player['name']}**\n"
    else:
        text += f"**{player['name']}**\n"
    
    text += f"{rank_text}\n"
    
    race_name = player.get('race', 'Странник')
    gender = player.get('gender', '???')
    text += f"*{race_name}* • {gender}\n\n"
    
    text += f"❤️ {hp_bar} {player['hp']}/{player['max_hp']}\n"
    text += f"💙 {current_mana}/{max_mana} (+{mana_regen}/мин)\n"
    text += f"⚔️ {player['power']}  💰 {player['money']}\n"
    text += f"⭐ Ур.{player['level']}  📚 {player['exp']}\n\n"
    
    text += f"**🛡️ ЭКИПИРОВКА**\n"
    text += f"└ ⚔️ Оружие: {weapon}\n"
    text += f"└ 🛡️ Броня: {armor}\n"
    text += f"└ ⛑️ Шлем: {helmet}\n"
    text += f"└ 👢 Обувь: {boots}\n"
    text += f"└ 💍 Аксессуар: {accessory}\n\n"
    
    text += f"**⚔️ СТАТИСТИКА**\n"
    text += f"└ 💀 Убийств: {kills}\n"
    text += f"└ 🎯 Дуэли: {wins}/{losses} ({duel_ratio:.1f}%)\n\n"
    
    text += f"**🎯 БОНУСЫ**\n"
    text += f"└ 💥 Крит: {player.get('crit_chance', 0.1)*100:.0f}%\n"
    text += f"└ 💨 Уворот: {player.get('dodge_chance', 0.05)*100:.0f}%\n"
    text += f"└ 🛡️ Блок: {player.get('block_chance', 0.05)*100:.0f}%"
    
    text += f"\n\n📊 **ДЕТАЛЬНАЯ СТАТИСТИКА**\n"
    text += f"└ 💥 Всего критических ударов: {player.get('total_crits', 0)}\n"
    text += f"└ ⚔️ Максимальный урон за удар: {player.get('max_damage', 0)}\n"
    text += f"└ 💚 Максимальный крит: {player.get('max_crit', 0)}\n"
    text += f"└ 🛡️ Всего заблокировано урона: {player.get('total_blocked', 0)}\n"
    text += f"└ 💨 Всего увернулся: {player.get('total_dodges', 0)}\n"
    text += f"└ 💙 Всего восстановлено маны: {player.get('total_mana_regen', 0)}\n"
    text += f"└ ❤️ Всего восстановлено HP: {player.get('total_hp_regen', 0)}\n"
    text += f"└ 🏆 За всё время заработано: {player.get('total_earned', 0)}💰\n"
    text += f"└ 💸 За всё время потрачено: {player.get('total_spent', 0)}💰\n"
    
    achievements = player.get('achievements', {})
    if achievements:
        text += f"\n\n**🏆 ДОСТИЖЕНИЯ**\n"
        for ach_id, ach_data in list(achievements.items())[:3]:
            text += f"└ {ach_data.get('name', ach_id)}\n"
        if len(achievements) > 3:
            text += f"└ ...и ещё {len(achievements) - 3}\n"
    
    return text


async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать полный профиль"""
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
    
    text = format_profile_text(player)
    
    await update_message(update, context, text, reply_markup=get_profile_keyboard(), parse_mode='Markdown')
    
    logger.profile(player['name'], player['money'], player['power'], 
                   player['level'], player.get('mana', 50), player.get('location', 'city'))