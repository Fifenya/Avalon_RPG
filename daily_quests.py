# daily_quests.py
from datetime import datetime
from typing import Dict, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Player
from logger import GameLogger

logger = GameLogger()

DAILY_QUESTS = [
    {"id": "hunt_3", "name": "👾 Охотник", "description": "Убей 3 монстров", "type": "hunt", "target": 3, "reward_money": 500, "reward_exp": 50},
    {"id": "hunt_5", "name": "🏆 Истребитель", "description": "Убей 5 монстров", "type": "hunt", "target": 5, "reward_money": 1000, "reward_exp": 100},
    {"id": "work_3", "name": "💼 Трудяга", "description": "Поработай 3 раза", "type": "work", "target": 3, "reward_money": 600, "reward_exp": 75},
    {"id": "duel_win_1", "name": "⚔️ Дуэлянт", "description": "Выиграй 1 дуэль", "type": "duel_win", "target": 1, "reward_money": 800, "reward_exp": 100},
    {"id": "craft_2", "name": "🔨 Кузнец", "description": "Скрафти 2 предмета", "type": "craft", "target": 2, "reward_money": 400, "reward_exp": 60},
    {"id": "smelt_2", "name": "🔥 Плавильщик", "description": "Расплавь 2 предмета", "type": "smelt", "target": 2, "reward_money": 400, "reward_exp": 60},
    {"id": "visit_tavern", "name": "🍺 Завсегдатай", "description": "Посети таверну", "type": "visit", "target": 1, "target_location": "tavern", "reward_money": 200, "reward_exp": 30},
    {"id": "casino_win", "name": "🎲 Счастливчик", "description": "Выиграй в казино", "type": "casino_win", "target": 1, "reward_money": 300, "reward_exp": 40},
    {"id": "clan_donate", "name": "💰 Щедрый", "description": "Пожертвуй 1000 монет в банк", "type": "clan_donate", "target": 1000, "reward_money": 500, "reward_exp": 80},
    {"id": "level_up", "name": "⭐ Рост силы", "description": "Повысь уровень", "type": "level_up", "target": 1, "reward_money": 1000, "reward_exp": 200}
]


class DailyQuestSystem:
    def __init__(self):
        self.quests_data = {}
    
    def _get_today_key(self) -> str:
        return datetime.now().strftime("%Y-%m-%d")
    
    def get_daily_quests(self, uid: str) -> List[Dict]:
        import random
        
        if uid not in self.quests_data:
            self.quests_data[uid] = {"date": "", "quests": [], "progress": {}, "completed": {}}
        
        today = self._get_today_key()
        
        if self.quests_data[uid]["date"] != today:
            selected = random.sample(DAILY_QUESTS, min(3, len(DAILY_QUESTS)))
            self.quests_data[uid] = {
                "date": today,
                "quests": selected,
                "progress": {q["id"]: 0 for q in selected},
                "completed": {q["id"]: False for q in selected}
            }
        
        result = []
        for quest in self.quests_data[uid]["quests"]:
            quest_copy = quest.copy()
            quest_copy["progress"] = self.quests_data[uid]["progress"].get(quest["id"], 0)
            quest_copy["completed"] = self.quests_data[uid]["completed"].get(quest["id"], False)
            result.append(quest_copy)
        
        return result
    
    def update_progress(self, uid: str, action_type: str, value: int = 1, location: str = None, amount: int = None) -> List[Dict]:
        completed = []
        
        if uid not in self.quests_data:
            return completed
        
        today = self._get_today_key()
        if self.quests_data[uid]["date"] != today:
            return completed
        
        for quest in self.quests_data[uid]["quests"]:
            quest_id = quest["id"]
            
            if self.quests_data[uid]["completed"].get(quest_id, False):
                continue
            
            if quest["type"] == action_type:
                increment = 0
                if action_type == "clan_donate" and amount:
                    increment = amount
                elif action_type == "visit" and location and quest.get("target_location") == location:
                    increment = 1
                elif action_type == "duel_win" and value:
                    increment = value
                else:
                    increment = value
                
                if increment > 0:
                    new_progress = self.quests_data[uid]["progress"].get(quest_id, 0) + increment
                    self.quests_data[uid]["progress"][quest_id] = new_progress
                    
                    if new_progress >= quest["target"]:
                        self.quests_data[uid]["completed"][quest_id] = True
                        completed.append(quest)
        
        return completed
    
    async def claim_reward(self, update: Update, context: ContextTypes.DEFAULT_TYPE, uid: str, quest_id: str) -> bool:
        from utils import update_message
        
        if uid not in self.quests_data:
            return False
        
        quests_data = self.quests_data[uid]
        
        quest = None
        for q in quests_data["quests"]:
            if q["id"] == quest_id:
                quest = q
                break
        
        if not quest:
            return False
        
        if not quests_data["completed"].get(quest_id, False):
            await update_message(update, context, f"❌ Квест '{quest['name']}' ещё не выполнен!")
            return False
        
        if quests_data.get(f"{quest_id}_claimed", False):
            await update_message(update, context, f"❌ Награда за '{quest['name']}' уже получена!")
            return False
        
        player = Player(uid)
        player["money"] = player.get("money", 0) + quest["reward_money"]
        player["exp"] = player.get("exp", 0) + quest["reward_exp"]
        
        quests_data[f"{quest_id}_claimed"] = True
        player.save()
        
        await update_message(update, context,
            f"✅ **Квест выполнен!**\n\n"
            f"📜 {quest['name']}\n"
            f"💰 +{quest['reward_money']} монет\n"
            f"📚 +{quest['reward_exp']} опыта\n\n"
            f"Продолжай в том же духе! 🎉",
            parse_mode='Markdown')
        
        return True
    
    def get_progress_text(self, uid: str) -> str:
        quests = self.get_daily_quests(uid)
        
        if not quests:
            return "📋 На сегодня нет активных квестов"
        
        text = "📋 **ЕЖЕДНЕВНЫЕ КВЕСТЫ** 📋\n\n"
        
        for quest in quests:
            status_emoji = "✅" if quest["completed"] else "🔄"
            progress_bar = self._get_progress_bar(quest["progress"], quest["target"])
            text += f"{status_emoji} **{quest['name']}**\n"
            text += f"   {quest['description']}\n"
            text += f"   {progress_bar} {quest['progress']}/{quest['target']}\n\n"
        
        return text
    
    def _get_progress_bar(self, current: int, target: int, length: int = 10) -> str:
        if target == 0:
            return "🟩" * length
        filled = int((current / target) * length)
        filled = min(length, max(0, filled))
        return "🟩" * filled + "⬜" * (length - filled)


daily_quests = DailyQuestSystem()