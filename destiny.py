# destiny.py
import random
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Player
from utils import update_message
from logger import GameLogger

logger = GameLogger()


class Quest:
    """Класс задания от карты судьбы"""
    def __init__(self, name, description, check_func, reward_func, failure_func=None):
        self.name = name
        self.description = description
        self.check_func = check_func
        self.reward_func = reward_func
        self.failure_func = failure_func
        self.completed = False

    async def check_and_reward(self, uid, context, **kwargs):
        if self.completed:
            return False
        
        result = await self.check_func(uid, **kwargs) if callable(self.check_func) else self.check_func(uid, **kwargs)
        if result:
            await self.reward_func(uid, context)
            self.completed = True
            
            if hasattr(DestinySystem, "active_quests") and uid in DestinySystem.active_quests:
                del DestinySystem.active_quests[uid]
            return True
        return False


class DestinySystem:
    IMAGES_DIR = "images/destiny"
    
    # Карты и соответствующие им задания
    CARDS = {
        "Sword": {
            "name": "🗡️ Меч",
            "description": "Карта воина",
            "quest_name": "Рыцарский долг",
            "quest_desc": "Убей 3 монстров в одиночной охоте.",
            "check_func": lambda uid, kills=None: kills >= 3,
            "reward_func": "hunt_bonus",
            "bonus": 1.2
        },
        "Star": {
            "name": "⭐ Звезда",
            "description": "Карта мастера",
            "quest_name": "Звёздный кузнец",
            "quest_desc": "Создай 2 предмета в крафте.",
            "check_func": lambda uid, crafts_done=None: crafts_done >= 2,
            "reward_func": "craft_bonus",
            "bonus": 1.3
        },
        "Shadow": {
            "name": "🌑 Тень",
            "description": "Карта интригана",
            "quest_name": "Теневой торгаш",
            "quest_desc": "Выиграй дуэль с любой ставкой.",
            "check_func": lambda uid, duel_won=False: duel_won,
            "reward_func": "duel_bonus",
            "bonus": 1.2
        },
        "Treasure": {
            "name": "💰 Сокровище",
            "description": "Карта купца",
            "quest_name": "Жадный купец",
            "quest_desc": "Заработай 500 монет за день.",
            "check_func": lambda uid, money_earned=0: money_earned >= 500,
            "reward_func": "money_bonus",
            "bonus": 1.2
        },
        "Nature": {
            "name": "🌿 Природа",
            "description": "Карта собирателя",
            "quest_name": "Хранитель леса",
            "quest_desc": "Собери 5 любых ресурсов.",
            "check_func": lambda uid, resources_gained=0: resources_gained >= 5,
            "reward_func": "resource_bonus",
            "bonus": 2
        }
    }
    
    @staticmethod
    def get_daily_cards():
        """Возвращает 3 случайные карты на день"""
        all_cards = list(DestinySystem.CARDS.keys())
        if len(all_cards) < 3:
            return []
        
        selected = random.sample(all_cards, 3)
        cards = []
        
        for card_id in selected:
            card_data = DestinySystem.CARDS[card_id]
            cards.append({
                "id": card_id,
                "name": card_data["name"],
                "description": card_data["description"],
                "image_file": f"{card_id}.jpg"
            })
        
        return cards
    
    @staticmethod
    async def send_card(update: Update, context: ContextTypes.DEFAULT_TYPE, card, index, caption=None):
        """Отправляет картинку карты с кнопкой выбора"""
        file_path = os.path.join(DestinySystem.IMAGES_DIR, card["image_file"])
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Выбрать", callback_data=f"destiny_{index}")
        ]])
        
        final_caption = caption or f"🔮 {card['name']} — {card['description']}"
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'rb') as photo:
                    sent = await update.message.reply_photo(
                        photo=photo,
                        caption=final_caption,
                        reply_markup=keyboard
                    )
                    return sent
            except Exception as e:
                print(f"Ошибка отправки картинки: {e}")
        
        sent = await update.message.reply_text(
            f"🔮 **{card['name']}**\n{card['description']}\n\n{final_caption}",
            parse_mode='Markdown',
            reply_markup=keyboard
        )
        return sent
    
    @staticmethod
    def apply_card(uid, card):
        """Применяет эффект карты — выдаёт задание"""
        player = Player(uid)
        card_data = DestinySystem.CARDS.get(card["id"])
        
        if not card_data:
            return f"✨ Ты выбрал карту **{card['name']}**!\nНичего не произошло..."
        
        # Создаём квест
        quest = Quest(
            name=card_data["quest_name"],
            description=card_data["quest_desc"],
            check_func=card_data["check_func"],
            reward_func=lambda uid, ctx: DestinySystem._reward_bonus(
                uid, ctx, card_data["reward_func"], card_data["bonus"]
            )
        )
        
        # Сохраняем активный квест
        if not hasattr(DestinySystem, "active_quests"):
            DestinySystem.active_quests = {}
        DestinySystem.active_quests[uid] = quest
        
        # Сохраняем дату выбора
        player['destiny_last_choice'] = datetime.now().isoformat()
        player.save()
        
        return (f"✨ Ты выбрал карту **{card['name']}**!\n\n"
                f"📜 **Новое задание:** {quest.name}\n"
                f"_{quest.description}_\n\n"
                f"Выполни его до конца дня и получи награду!")
    
    @staticmethod
    async def _reward_bonus(uid, context, bonus_type, bonus):
        """Выдаёт временный бонус за выполнение квеста"""
        duration = 86400  # 24 часа
        
        if not hasattr(DestinySystem, "active_effects"):
            DestinySystem.active_effects = {}
        
        effect = {
            "type": bonus_type,
            "bonus": bonus,
            "expires": datetime.now() + timedelta(seconds=duration)
        }
        
        DestinySystem.active_effects[uid] = effect
        
        bonus_text = {
            "hunt_bonus": f"+{int((bonus-1)*100)}% к награде за охоту",
            "craft_bonus": f"x{bonus} к результату крафта",
            "duel_bonus": f"+{int((bonus-1)*100)}% к выигрышу в дуэлях",
            "money_bonus": f"+{int((bonus-1)*100)}% к заработку",
            "resource_bonus": f"x{bonus} к добыче ресурсов"
        }.get(bonus_type, f"x{bonus}")
        
        await context.bot.send_message(
            chat_id=int(uid),
            text=f"🎉 **Задание выполнено!**\n\n"
                 f"Ты получаешь бонус на 24 часа:\n"
                 f"✨ {bonus_text}",
            parse_mode='Markdown'
        )
    
    @staticmethod
    def get_active_effect(uid):
        """Получить активный эффект для игрока"""
        if hasattr(DestinySystem, "active_effects") and uid in DestinySystem.active_effects:
            effect = DestinySystem.active_effects[uid]
            if datetime.now() < effect["expires"]:
                return effect
            else:
                del DestinySystem.active_effects[uid]
        return None
    
    @staticmethod
    def get_active_quest(uid):
        """Получить активный квест для игрока"""
        if hasattr(DestinySystem, "active_quests") and uid in DestinySystem.active_quests:
            return DestinySystem.active_quests[uid]
        return None
    
    @staticmethod
    def can_choose_card(uid):
        """Проверяет, может ли игрок выбрать карту сегодня"""
        player = Player(uid)
        last_choice = player.get('destiny_last_choice')
        
        if not last_choice:
            return True
        
        try:
            last_date = datetime.fromisoformat(last_choice).date()
            today = datetime.now().date()
            return last_date != today
        except:
            return True