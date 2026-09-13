# clan.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
# Добавлена валидация сумм и декоратор require_character

import random
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Player, Database
from keyboards import get_clan_main_keyboard, get_clan_bank_keyboard, get_clan_confirm_keyboard
from utils import update_message, require_character
from main_screen import show_main_screen
from logger import GameLogger

logger = GameLogger()
db = Database()

# Цена создания клана
CLAN_CREATION_PRICE = 5000

# Максимальная сумма для операций с банком
MAX_BANK_AMOUNT = 1_000_000

# Клановые улучшения
CLAN_UPGRADES = {
    'money_bonus': {
        'name': '💰 Налоговая льгота',
        'desc': 'Все участники получают +X% к доходу',
        'levels': [5, 10, 15, 20, 25],
        'prices': [1000, 5000, 20000, 50000, 100000],
        'effect': lambda lvl: lvl * 5
    },
    'work_bonus': {
        'name': '⚒️ Профсоюз',
        'desc': '+X монет к заработку за работу',
        'levels': [10, 20, 30, 50, 100],
        'prices': [500, 2000, 10000, 25000, 50000],
        'effect': lambda lvl: lvl * 10
    },
    'clan_power': {
        'name': '⚔️ Клановая сила',
        'desc': 'Все участники получают +X к силе',
        'levels': [5, 10, 15, 25, 40],
        'prices': [2000, 8000, 30000, 80000, 150000],
        'effect': lambda lvl: lvl * 2
    },
    'clan_armor': {
        'name': '🛡️ Клановая защита',
        'desc': 'Все участники получают +X к броне',
        'levels': [3, 6, 10, 15, 25],
        'prices': [1500, 6000, 25000, 60000, 120000],
        'effect': lambda lvl: lvl
    },
    'crit_bonus': {
        'name': '💥 Клановый критический удар',
        'desc': '+X% к шансу крита',
        'levels': [2, 4, 6, 8, 10],
        'prices': [3000, 12000, 40000, 100000, 200000],
        'effect': lambda lvl: lvl
    },
    'hunt_reward': {
        'name': '🎯 Клановая охота',
        'desc': '+X% к награде за охоту',
        'levels': [5, 10, 15, 20, 30],
        'prices': [1000, 5000, 20000, 50000, 120000],
        'effect': lambda lvl: lvl * 2
    },
    'drop_bonus': {
        'name': '🎁 Клановый дроп',
        'desc': '+X% к шансу выпадения предметов',
        'levels': [2, 4, 6, 8, 10],
        'prices': [2000, 8000, 30000, 80000, 150000],
        'effect': lambda lvl: lvl
    },
    'member_limit': {
        'name': '👥 Расширение гильдии',
        'desc': '+X мест для участников',
        'levels': [5, 10, 15, 20, 30],
        'prices': [5000, 20000, 50000, 100000, 200000],
        'effect': lambda lvl: lvl * 2
    }
}


class ClanSystem:
    def __init__(self):
        data = db.get_all()
        if '_clans' not in data:
            data['_clans'] = {}
            db.save()
        self.clans = data['_clans']
    
    def save(self):
        data = db.get_all()
        data['_clans'] = self.clans
        db.save()
    
    def get_clan_by_member(self, user_id):
        for clan_id, clan in self.clans.items():
            if str(user_id) in clan.get('members', {}):
                return clan_id, clan
        return None, None
    
    def get_clan(self, clan_id):
        return self.clans.get(clan_id)
    
    def get_clan_by_name(self, clan_name):
        for clan_id, clan in self.clans.items():
            if clan['name'].lower() == clan_name.lower():
                return clan_id, clan
        return None, None
    
    def create_clan(self, clan_name, leader_id, leader_name):
        for cid, clan in self.clans.items():
            if clan['name'].lower() == clan_name.lower():
                return False, "Клан с таким именем уже существует", None
        
        for cid, clan in self.clans.items():
            if str(leader_id) in clan['members']:
                return False, "Ты уже состоишь в клане", None
        
        clan_id = f"clan_{len(self.clans) + 1}_{random.randint(1000, 9999)}"
        
        self.clans[clan_id] = {
            'name': clan_name,
            'tag': '',
            'leader': str(leader_id),
            'co_leaders': [],
            'members': {
                str(leader_id): {
                    'name': leader_name,
                    'role': 'leader',
                    'joined': datetime.now().isoformat(),
                    'donations': 0,
                    'kills': 0
                }
            },
            'level': 1,
            'exp': 0,
            'bank': {'money': 0},
            'upgrades': {},
            'wins': 0,
            'losses': 0,
            'created': datetime.now().isoformat(),
            'description': '',
            'announcement': ''
        }
        
        self.save()
        return True, f"✅ Клан '{clan_name}' создан!", clan_id
    
    def leave_clan(self, user_id):
        clan_id, clan = self.get_clan_by_member(user_id)
        if not clan:
            return False, "Ты не в клане"
        
        if clan['members'][str(user_id)]['role'] == 'leader':
            return False, "Лидер не может покинуть клан. Передай лидерство или распусти клан"
        
        del clan['members'][str(user_id)]
        
        if len(clan['members']) == 0:
            del self.clans[clan_id]
        
        self.save()
        return True, "✅ Ты покинул клан"
    
    def disband_clan(self, leader_id, clan_id):
        clan = self.clans.get(clan_id)
        if not clan:
            return False, "Клан не найден"
        
        if clan['leader'] != str(leader_id):
            return False, "Только лидер может распустить клан"
        
        del self.clans[clan_id]
        self.save()
        return True, "✅ Клан распущен"
    
    def get_upgrade_level(self, clan_id, upgrade_id):
        clan = self.clans.get(clan_id)
        if not clan:
            return 0
        return clan.get('upgrades', {}).get(upgrade_id, 0)
    
    def get_upgrade_effect(self, clan_id, upgrade_id):
        level = self.get_upgrade_level(clan_id, upgrade_id)
        if level == 0:
            return 0
        upgrade = CLAN_UPGRADES.get(upgrade_id)
        if upgrade:
            return upgrade['effect'](level)
        return 0
    
    def get_all_clan_bonuses(self, clan_id):
        bonuses = {}
        for upgrade_id in CLAN_UPGRADES:
            effect = self.get_upgrade_effect(clan_id, upgrade_id)
            if effect:
                bonuses[upgrade_id] = effect
        return bonuses
    
    def upgrade_clan(self, clan_id, upgrade_id, leader_id):
        clan = self.clans.get(clan_id)
        if not clan:
            return False, "Клан не найден"
        
        if clan['leader'] != str(leader_id):
            return False, "Только лидер может улучшать клан"
        
        level = self.get_upgrade_level(clan_id, upgrade_id)
        upgrade = CLAN_UPGRADES.get(upgrade_id)
        
        if not upgrade:
            return False, "Улучшение не найдено"
        
        if level >= len(upgrade['levels']):
            return False, "Максимальный уровень достигнут"
        
        price = upgrade['prices'][level]
        bank = clan.get('bank', {})
        
        if bank.get('money', 0) < price:
            return False, f"В банке клана недостаточно монет! Нужно: {price}"
        
        bank['money'] = bank.get('money', 0) - price
        
        if 'upgrades' not in clan:
            clan['upgrades'] = {}
        clan['upgrades'][upgrade_id] = level + 1
        clan['bank'] = bank
        
        self.save()
        return True, f"✅ {upgrade['name']} улучшен до {level + 1} уровня!"
    
    def donate_to_bank(self, user_id, clan_id, amount):
        clan = self.clans.get(clan_id)
        if not clan:
            return False, "Клан не найден"
        
        if str(user_id) not in clan['members']:
            return False, "Ты не в этом клане"
        
        player = Player(user_id)
        if player['money'] < amount:
            return False, f"Не хватает {amount} монет"
        
        player['money'] -= amount
        if 'bank' not in clan:
            clan['bank'] = {'money': 0}
        clan['bank']['money'] = clan['bank'].get('money', 0) + amount
        clan['members'][str(user_id)]['donations'] = clan['members'][str(user_id)].get('donations', 0) + amount
        
        player.save()
        self.save()
        
        return True, f"✅ Пожертвовано {amount} монет в банк клана!"
    
    def withdraw_from_bank(self, user_id, clan_id, amount):
        clan = self.clans.get(clan_id)
        if not clan:
            return False, "Клан не найден"
        
        role = clan['members'].get(str(user_id), {}).get('role')
        if role not in ['leader', 'co_leader']:
            return False, "Только лидер и со-лидер могут брать из банка"
        
        if clan['bank'].get('money', 0) < amount:
            return False, f"В банке недостаточно монет"
        
        clan['bank']['money'] -= amount
        if clan['bank']['money'] <= 0:
            clan['bank']['money'] = 0
        
        player = Player(user_id)
        player['money'] += amount
        player.save()
        self.save()
        
        return True, f"✅ Взято {amount} монет из банка!"
    
    def clan_info(self, clan_id):
        clan = self.clans.get(clan_id)
        if not clan:
            return None
        
        members_list = []
        for uid, data in clan['members'].items():
            role_emoji = "👑" if data['role'] == 'leader' else "⭐" if data['role'] == 'co_leader' else "👤"
            members_list.append(f"{role_emoji} {data['name']} (💀{data.get('kills',0)})")
        
        return {
            'name': clan['name'],
            'tag': clan.get('tag', ''),
            'level': clan['level'],
            'exp': clan['exp'],
            'exp_needed': clan['level'] * 1000,
            'members': members_list,
            'count': len(members_list),
            'leader': clan['members'][clan['leader']]['name'],
            'description': clan.get('description', ''),
            'wins': clan.get('wins', 0),
            'losses': clan.get('losses', 0),
            'bank': clan.get('bank', {}),
            'announcement': clan.get('announcement', ''),
            'created': clan.get('created', '')
        }
    
    def clan_list(self):
        clan_list = []
        for clan_id, clan in self.clans.items():
            clan_list.append({
                'id': clan_id,
                'name': clan['name'],
                'tag': clan.get('tag', ''),
                'level': clan['level'],
                'members': len(clan['members']),
                'wins': clan.get('wins', 0),
                'losses': clan.get('losses', 0)
            })
        return sorted(clan_list, key=lambda x: (-x['level'], -x['wins'], -x['members']))


clan_system = ClanSystem()


async def clan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню кланов"""
    uid = str(update.effective_user.id)
    player = Player(uid)
    
    if not player.get('race'):
        await update_message(update, context, "❌ Сначала создай персонажа через /start")
        return
    
    clan_id, clan = clan_system.get_clan_by_member(uid)
    
    if clan_id:
        await show_clan_menu(update, context, clan_id)
    else:
        text = "🏰 **КЛАНЫ АВАЛОНА** 🏰\n\nТы ещё не состоишь в клане.\nСоздай свой или вступи в существующий!"
        await update_message(update, context, text, reply_markup=get_clan_main_keyboard(has_clan=False), parse_mode='Markdown')


async def show_clan_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, clan_id):
    """Показать меню клана"""
    uid = str(update.effective_user.id)
    info = clan_system.clan_info(clan_id)
    clan = clan_system.get_clan(clan_id)
    
    if not info:
        await update_message(update, context, "❌ Клан не найден")
        return
    
    progress = int((info['exp'] / info['exp_needed']) * 10) if info['exp_needed'] > 0 else 0
    exp_bar = "🟩" * progress + "⬜" * (10 - progress)
    
    bonuses = clan_system.get_all_clan_bonuses(clan_id)
    bonus_text = ""
    if bonuses:
        bonus_text = "\n✨ **БОНУСЫ КЛАНА:**\n"
        for bonus_id, value in bonuses.items():
            upgrade = CLAN_UPGRADES.get(bonus_id, {})
            bonus_text += f"└ {upgrade.get('name', bonus_id)}: +{value}\n"
    
    text = f"🏰 **{info['name']}** (ур.{info['level']})\n"
    text += f"{exp_bar} {info['exp']}/{info['exp_needed']} опыта\n\n"
    text += f"👥 Участников: {info['count']}\n"
    text += f"👑 Лидер: {info['leader']}\n"
    text += f"⚔️ Побед: {info['wins']} | Поражений: {info['losses']}\n"
    text += f"💰 В банке: {info['bank'].get('money', 0)} монет{bonus_text}\n\n"
    
    if info['announcement']:
        text += f"📢 **Объявление:** {info['announcement']}\n\n"
    
    text += "**Участники:**\n" + "\n".join(info['members'][:5])
    if info['count'] > 5:
        text += f"\n...и ещё {info['count'] - 5}"
    
    await update_message(update, context, text, reply_markup=get_clan_main_keyboard(has_clan=True), parse_mode='Markdown')


async def clan_create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать создание клана"""
    uid = str(update.effective_user.id)
    player = Player(uid)
    
    clan_id, _ = clan_system.get_clan_by_member(uid)
    if clan_id:
        await update_message(update, context, "❌ Ты уже в клане!")
        return
    
    if player['money'] < CLAN_CREATION_PRICE:
        await update_message(update, context, f"❌ Недостаточно монет! Для создания клана нужно {CLAN_CREATION_PRICE}💰")
        return
    
    context.user_data['creating_clan'] = True
    await update_message(update, context, 
        "🏰 **СОЗДАНИЕ КЛАНА**\n\n"
        "Отправь название клана (от 3 до 30 символов):\n"
        "_(или отправь ❌ Отмена)_",
        parse_mode='Markdown')


async def clan_create_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Обработка ввода названия клана"""
    if not context.user_data.get('creating_clan'):
        return False
    
    uid = str(update.effective_user.id)
    player = Player(uid)
    clan_name = update.message.text.strip()
    
    if clan_name.lower() in ['отмена', 'cancel', '❌']:
        context.user_data['creating_clan'] = False
        await update.message.reply_text("❌ Создание клана отменено")
        await clan_command(update, context)
        return True
    
    if len(clan_name) < 3:
        await update.message.reply_text("❌ Название слишком короткое! Минимум 3 символа. Попробуй ещё раз:")
        return True
    
    if len(clan_name) > 30:
        await update.message.reply_text("❌ Название слишком длинное! Максимум 30 символов. Попробуй ещё раз:")
        return True
    
    existing_id, existing = clan_system.get_clan_by_name(clan_name)
    if existing:
        await update.message.reply_text(f"❌ Клан '{clan_name}' уже существует! Придумай другое название:")
        return True
    
    context.user_data['clan_name'] = clan_name
    context.user_data['creating_clan'] = False
    
    await update.message.reply_text(
        f"🏰 **СОЗДАНИЕ КЛАНА**\n\n"
        f"Название: **{clan_name}**\n"
        f"Стоимость: {CLAN_CREATION_PRICE}💰\n"
        f"Твой баланс: {player['money']}💰\n\n"
        f"Подтверждаешь создание?",
        parse_mode='Markdown',
        reply_markup=get_clan_confirm_keyboard()
    )
    return True


@require_character
async def clan_create_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение создания клана"""
    query = update.callback_query
    await query.answer()
  
    if query.data == "clan_confirm_no":
        context.user_data.pop('clan_name', None)
        await query.edit_message_text("❌ Создание клана отменено")
        return
    
    uid = str(query.from_user.id)
    player = Player(uid)
    user_name = query.from_user.first_name
    clan_name = context.user_data.get('clan_name', '')
    
    if not clan_name:
        await query.edit_message_text("❌ Название клана не найдено. Начни заново.")
        await clan_command(update, context)
        return
    
    if player['money'] < CLAN_CREATION_PRICE:
        await query.edit_message_text(f"❌ Недостаточно монет! Нужно {CLAN_CREATION_PRICE}💰")
        return
    
    player['money'] -= CLAN_CREATION_PRICE
    player.save()
    
    success, msg, clan_id = clan_system.create_clan(clan_name, uid, user_name)
    
    if success:
        logger.clan_create(user_name, clan_name, CLAN_CREATION_PRICE)
        await query.edit_message_text(f"✅ {msg}\n💰 Создание клана: -{CLAN_CREATION_PRICE} монет")
        await show_clan_menu(update, context, clan_id)
    else:
        player['money'] += CLAN_CREATION_PRICE
        player.save()
        await query.edit_message_text(msg)
    
    context.user_data.pop('clan_name', None)


async def clan_leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Покинуть клан"""
    uid = str(update.effective_user.id)
    player = Player(uid)
    
    success, msg = clan_system.leave_clan(uid)
    
    if success:
        logger.clan_leave(player['name'], "клан")
    
    await update_message(update, context, msg, reply_markup=get_clan_main_keyboard(has_clan=False))


async def clan_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список кланов"""
    clans = clan_system.clan_list()
    
    if not clans:
        await update_message(update, context, "🏰 Пока нет созданных кланов")
        return
    
    text = "🏰 **СПИСОК КЛАНОВ** 🏰\n\n"
    for i, clan in enumerate(clans[:10], 1):
        text += f"{i}. **{clan['name']}** | Ур.{clan['level']} | {clan['members']} уч. | ⚔️ {clan['wins']}/{clan['losses']}\n"
    
    await update_message(update, context, text, parse_mode='Markdown', reply_markup=get_clan_main_keyboard(has_clan=False))


async def clan_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Топ кланов"""
    clans = clan_system.clan_list()
    
    if not clans:
        await update_message(update, context, "🏰 Пока нет созданных кланов")
        return
    
    text = "🏆 **ТОП КЛАНОВ АВАЛОНА** 🏆\n\n"
    medals = ["🥇", "🥈", "🥉"]
    
    for i, clan in enumerate(clans[:10], 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        text += f"{medal} **{clan['name']}**\n"
        text += f"   Ур.{clan['level']} | {clan['members']} уч. | ⚔️ {clan['wins']}/{clan['losses']}\n\n"
    
    await update_message(update, context, text, parse_mode='Markdown', reply_markup=get_clan_main_keyboard(has_clan=False))


async def clan_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Поиск клана по названию"""
    uid = str(update.effective_user.id)
    player = Player(uid)
    
    clan_id, _ = clan_system.get_clan_by_member(uid)
    if clan_id:
        await update_message(update, context, "❌ Ты уже в клане! Сначала покинь текущий клан.")
        return
    
    context.user_data['clan_search_mode'] = True
    await update_message(update, context, 
        "🔍 **ПОИСК КЛАНА**\n\n"
        "Введи название клана (или часть названия) для поиска:\n"
        "_(или отправь ❌ Отмена)_",
        parse_mode='Markdown')


async def clan_search_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Обработка ввода названия клана для поиска"""
    if not context.user_data.get('clan_search_mode'):
        return False
    
    uid = str(update.effective_user.id)
    player = Player(uid)
    search_text = update.message.text.strip()
    
    if search_text.lower() in ['отмена', 'cancel', '❌']:
        context.user_data['clan_search_mode'] = False
        await clan_command(update, context)
        return True
    
    clans = clan_system.clan_list()
    found_clans = []
    
    for clan in clans:
        if search_text.lower() in clan['name'].lower():
            found_clans.append(clan)
    
    if not found_clans:
        await update.message.reply_text(
            f"❌ Кланы с названием содержащим '{search_text}' не найдены!\n\n"
            f"Попробуй другой запрос или создай свой клан."
        )
        context.user_data['clan_search_mode'] = False
        await clan_command(update, context)
        return True
    
    text = f"🔍 **РЕЗУЛЬТАТЫ ПОИСКА** (по запросу '{search_text}')\n\n"
    
    keyboard = []
    for i, clan in enumerate(found_clans[:10], 1):
        text += f"{i}. **{clan['name']}** | Ур.{clan['level']} | {clan['members']} уч. | ⚔️ {clan['wins']}/{clan['losses']}\n"
        keyboard.append([InlineKeyboardButton(
            f"📋 {clan['name']}", 
            callback_data=f"clan_info_{clan['id']}"
        )])
    
    if len(found_clans) > 10:
        text += f"\n...и ещё {len(found_clans) - 10} кланов"
    
    text += "\n\nНажми на клан, чтобы посмотреть детали и вступить."
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="clan_back")])
    
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    
    context.user_data['clan_search_mode'] = False
    return True


@require_character
async def clan_info_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать информацию о клане и дать возможность вступить"""
    query = update.callback_query
    await query.answer()
    
    clan_id = query.data.replace("clan_info_", "")
    clan = clan_system.get_clan(clan_id)
    
    if not clan:
        await query.edit_message_text("❌ Клан не найден!")
        return
    
    uid = str(query.from_user.id)
    player = Player(uid)
    
    existing_clan_id, _ = clan_system.get_clan_by_member(uid)
    if existing_clan_id:
        await query.answer("❌ Ты уже в клане!", show_alert=True)
        return
    
    info = clan_system.clan_info(clan_id)
    
    text = f"🏰 **{info['name']}**\n"
    text += f"👑 Лидер: {info['leader']}\n"
    text += f"⭐ Уровень: {info['level']}\n"
    text += f"👥 Участников: {info['count']}\n"
    text += f"⚔️ Побед/Поражений: {info['wins']}/{info['losses']}\n"
    text += f"💰 В банке: {info['bank'].get('money', 0)} монет\n\n"
    
    if info['description']:
        text += f"📜 **Описание:** {info['description']}\n\n"
    
    if info['members']:
        text += "**Участники:**\n"
        for member in info['members'][:5]:
            text += f"  {member}\n"
        if info['count'] > 5:
            text += f"  ...и ещё {info['count'] - 5}\n"
    
    keyboard = [
        [InlineKeyboardButton("📥 Вступить в клан", callback_data=f"clan_join_{clan_id}")],
        [InlineKeyboardButton("🔙 Назад к поиску", callback_data="clan_search_back")]
    ]
    
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))


@require_character
async def clan_join_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик вступления в клан"""
    query = update.callback_query
    await query.answer()
    
    uid = str(query.from_user.id)
    player = Player(uid)
    clan_id = query.data.replace("clan_join_", "")
    
    clan = clan_system.get_clan(clan_id)
    if not clan:
        await query.edit_message_text("❌ Клан не найден!")
        return
    
    existing_clan_id, _ = clan_system.get_clan_by_member(uid)
    if existing_clan_id:
        await query.answer("❌ Ты уже в клане! Сначала покинь текущий клан.", show_alert=True)
        return
    
    user_name = query.from_user.first_name
    
    clan['members'][uid] = {
        'name': user_name,
        'role': 'member',
        'joined': datetime.now().isoformat(),
        'donations': 0,
        'kills': 0
    }
    clan_system.save()
    
    logger.clan_join(user_name, clan['name'])
    
    await query.edit_message_text(
        f"✅ **Ты вступил в клан {clan['name']}!**\n\n"
        f"Добро пожаловать, {user_name}!\n"
        f"Теперь ты можешь жертвовать в банк и получать клановые бонусы.",
        parse_mode='Markdown'
    )
    
    await asyncio.sleep(2)
    await show_clan_menu(update, context, clan_id)


async def clan_search_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться к поиску кланов"""
    query = update.callback_query
    await query.answer()
    
    clans = clan_system.clan_list()
    
    if not clans:
        await query.edit_message_text("🏰 Пока нет созданных кланов")
        await clan_command(update, context)
        return
    
    text = "🔍 **СПИСОК ВСЕХ КЛАНОВ** 🔍\n\n"
    
    keyboard = []
    for i, clan in enumerate(clans[:10], 1):
        text += f"{i}. **{clan['name']}** | Ур.{clan['level']} | {clan['members']} уч. | ⚔️ {clan['wins']}/{clan['losses']}\n"
        keyboard.append([InlineKeyboardButton(
            f"📋 {clan['name']}", 
            callback_data=f"clan_info_{clan['id']}"
        )])
    
    if len(clans) > 10:
        text += f"\n...и ещё {len(clans) - 10} кланов"
    
    text += "\n\nНажми на клан, чтобы посмотреть детали и вступить."
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="clan_back")])
    
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))


async def clan_bank_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню банка клана"""
    uid = str(update.effective_user.id)
    clan_id, clan = clan_system.get_clan_by_member(uid)
    
    if not clan_id:
        await update_message(update, context, "❌ Ты не в клане!")
        return
    
    text = f"🏦 **БАНК КЛАНА**\n\n"
    text += f"💰 В банке: {clan.get('bank', {}).get('money', 0)} монет\n"
    text += f"📊 Твои пожертвования: {clan['members'][uid].get('donations', 0)}\n\n"
    text += "Выбери действие:"
    
    await update_message(update, context, text, reply_markup=get_clan_bank_keyboard(), parse_mode='Markdown')


async def clan_bank_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Положить монеты в банк"""
    uid = str(update.effective_user.id)
    player = Player(uid)
    clan_id, clan = clan_system.get_clan_by_member(uid)
    
    if not clan_id:
        await update_message(update, context, "❌ Ты не в клане!")
        return
    
    context.user_data['bank_action'] = 'deposit'
    await update_message(update, context, 
        "📥 **Введи сумму для пожертвования:**\n\n"
        f"Максимум: {MAX_BANK_AMOUNT:,}💰\n"
        "Пример: `1000`\n\n"
        "_(или отправь ❌ Отмена)_",
        parse_mode='Markdown')


async def clan_bank_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Взять монеты из банка"""
    uid = str(update.effective_user.id)
    player = Player(uid)
    clan_id, clan = clan_system.get_clan_by_member(uid)
    
    if not clan_id:
        await update_message(update, context, "❌ Ты не в клане!")
        return
    
    role = clan['members'][uid].get('role')
    if role not in ['leader', 'co_leader']:
        await update_message(update, context, "❌ Только лидер и со-лидер могут брать из банка!")
        return
    
    context.user_data['bank_action'] = 'withdraw'
    await update_message(update, context, 
        "📤 **Введи сумму для снятия:**\n\n"
        f"Максимум: {MAX_BANK_AMOUNT:,}💰\n"
        "Пример: `500`\n\n"
        "_(или отправь ❌ Отмена)_",
        parse_mode='Markdown')


async def clan_bank_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка операций с банком (с валидацией суммы)"""
    if 'bank_action' not in context.user_data:
        return False
    
    uid = str(update.effective_user.id)
    player = Player(uid)
    clan_id, clan = clan_system.get_clan_by_member(uid)
    action = context.user_data['bank_action']
    text = update.message.text.strip()
    
    if text.lower() in ['отмена', 'cancel', '❌']:
        context.user_data.pop('bank_action', None)
        await clan_bank_menu(update, context)
        return True
    
    try:
        amount = int(text)
        if amount <= 0:
            await update.message.reply_text("❌ Сумма должна быть больше 0!")
            return True
        
        # ВАЖНО: проверка максимальной суммы
        if amount > MAX_BANK_AMOUNT:
            await update.message.reply_text(f"❌ Сумма не может превышать {MAX_BANK_AMOUNT:,}💰!")
            return True
            
    except ValueError:
        await update.message.reply_text("❌ Введи число!")
        return True
    
    if action == 'deposit':
        if player['money'] < amount:
            await update.message.reply_text(f"❌ Недостаточно монет! У тебя {player['money']}💰")
            return True
        
        success, msg = clan_system.donate_to_bank(uid, clan_id, amount)
        await update.message.reply_text(msg)
        
    elif action == 'withdraw':
        success, msg = clan_system.withdraw_from_bank(uid, clan_id, amount)
        await update.message.reply_text(msg)
    
    context.user_data.pop('bank_action', None)
    await clan_bank_menu(update, context)
    return True


@require_character
async def clan_upgrades_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню улучшений клана"""
    uid = str(update.effective_user.id)
    clan_id, clan = clan_system.get_clan_by_member(uid)
    
    if not clan_id:
        await update_message(update, context, "❌ Ты не в клане!")
        return
    
    if clan['leader'] != uid:
        await update_message(update, context, "❌ Только лидер может улучшать клан!")
        return
    
    text = f"🏰 **УЛУЧШЕНИЯ КЛАНА {clan['name']}** 🏰\n\n"
    text += f"💰 В банке: {clan.get('bank', {}).get('money', 0)} монет\n\n"
    
    keyboard = []
    for upgrade_id, upgrade in CLAN_UPGRADES.items():
        level = clan_system.get_upgrade_level(clan_id, upgrade_id)
        max_level = len(upgrade['levels'])
        effect = clan_system.get_upgrade_effect(clan_id, upgrade_id)
        
        status = f"Ур.{level}/{max_level}"
        if effect:
            if '%' in upgrade['desc']:
                status += f" | +{effect}%"
            else:
                status += f" | +{effect}"
        
        if level < max_level:
            price = upgrade['prices'][level]
            status += f" | 🔽 {price}💰"
            keyboard.append([InlineKeyboardButton(
                f"⬆️ {upgrade['name']} ({price}💰)",
                callback_data=f"clan_upgrade_{upgrade_id}"
            )])
        
        text += f"**{upgrade['name']}**\n"
        text += f"└ {upgrade['desc']}\n"
        text += f"└ {status}\n\n"
    
    keyboard.append([InlineKeyboardButton("◀️ Назад в клан", callback_data="clan_back")])
    
    await update_message(update, context, text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')


@require_character
async def clan_upgrade_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик улучшения клана"""
    query = update.callback_query
    await query.answer()
    
    upgrade_id = query.data.replace('clan_upgrade_', '')
    uid = str(query.from_user.id)
    clan_id, clan = clan_system.get_clan_by_member(uid)
    
    if not clan_id or clan['leader'] != uid:
        await query.edit_message_text("❌ Только лидер может улучшать клан!")
        return
    
    success, msg = clan_system.upgrade_clan(clan_id, upgrade_id, uid)
    
    if success:
        logger.clan_bank(uid, "улучшил", upgrade_id, 1)
    
    await query.edit_message_text(msg)
    await clan_upgrades_menu(update, context)


async def clan_back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться в меню клана"""
    query = update.callback_query
    await query.answer()
    
    uid = str(query.from_user.id)
    clan_id, _ = clan_system.get_clan_by_member(uid)
    
    if clan_id:
        await show_clan_menu(update, context, clan_id)
    else:
        await clan_command(update, context)


async def clan_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых кнопок кланов"""
    text = update.message.text
    
    if text == "🏰 Создать клан":
        await clan_create(update, context)
    elif text == "📋 Список кланов":
        await clan_list(update, context)
    elif text == "🏆 Топ кланов":
        await clan_top(update, context)
    elif text == "🔍 Поиск клана":
        await clan_search(update, context)
    elif text == "🏰 Мой клан":
        uid = str(update.effective_user.id)
        clan_id, _ = clan_system.get_clan_by_member(uid)
        if clan_id:
            await show_clan_menu(update, context, clan_id)
        else:
            await update_message(update, context, "❌ Ты не в клане")
    elif text == "🏦 Банк клана":
        await clan_bank_menu(update, context)
    elif text == "📤 Покинуть клан":
        await clan_leave(update, context)
    elif text == "📥 Положить":
        await clan_bank_deposit(update, context)
    elif text == "📤 Взять":
        await clan_bank_withdraw(update, context)
    elif text == "📊 Статистика банка":
        await clan_bank_menu(update, context)
    elif text == "⚙️ Управление кланом":
        await clan_upgrades_menu(update, context)
    elif text == "🔙 Назад к клану":
        uid = str(update.effective_user.id)
        clan_id, _ = clan_system.get_clan_by_member(uid)
        if clan_id:
            await show_clan_menu(update, context, clan_id)
        else:
            await clan_command(update, context)
    elif text == "🔙 На главную":
        await show_main_screen(update, context)