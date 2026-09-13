# quests.py - ИСПРАВЛЕННАЯ ПОЛНАЯ ВЕРСИЯ
from datetime import datetime
from typing import Dict, List, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Player
from logger import GameLogger
from utils import require_character, update_message

logger = GameLogger()

# Данные ежедневных квестов
DAILY_QUESTS_DATA = {
    "hunt_3": {"name": "👾 Охотник", "type": "hunt", "target": 3, "reward_money": 500, "reward_exp": 50},
    "work_3": {"name": "💼 Трудяга", "type": "work", "target": 3, "reward_money": 600, "reward_exp": 75},
    "craft_2": {"name": "🔨 Кузнец", "type": "craft", "target": 2, "reward_money": 400, "reward_exp": 60},
    "gather_5": {"name": "🌿 Собиратель", "type": "gather", "target": 5, "reward_money": 300, "reward_exp": 40},
    "duel_1": {"name": "⚔️ Дуэлянт", "type": "duel", "target": 1, "reward_money": 800, "reward_exp": 100},
}


class QuestSystem:
    """Единая система квестов (ежедневные + карты судьбы)"""
    
    def __init__(self):
        self.daily_quests = self._init_daily_quests()
        self.destiny_quests = {}  # {uid: quest}
    
    def _init_daily_quests(self) -> List[Dict]:
        return [
            {"id": "hunt_3", "name": "👾 Охотник", "type": "hunt", "target": 3, "reward_money": 500, "reward_exp": 50, "progress": 0},
            {"id": "work_3", "name": "💼 Трудяга", "type": "work", "target": 3, "reward_money": 600, "reward_exp": 75, "progress": 0},
            {"id": "craft_2", "name": "🔨 Кузнец", "type": "craft", "target": 2, "reward_money": 400, "reward_exp": 60, "progress": 0},
            {"id": "gather_5", "name": "🌿 Собиратель", "type": "gather", "target": 5, "reward_money": 300, "reward_exp": 40, "progress": 0},
            {"id": "duel_1", "name": "⚔️ Дуэлянт", "type": "duel", "target": 1, "reward_money": 800, "reward_exp": 100, "progress": 0},
        ]
    
    def update_progress(self, uid: str, action_type: str, value: int = 1):
        """Обновляет прогресс квестов"""
        player = Player(uid)
        
        # Получаем или создаём данные прогресса
        quests_progress = player.get('daily_quests_progress', {})
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Сбрасываем прогресс если новый день
        if quests_progress.get('date') != today:
            quests_progress = {'date': today}
            for q in self.daily_quests:
                quests_progress[q['id']] = 0
        
        # Обновляем прогресс для каждого квеста
        for q in self.daily_quests:
            if q['type'] == action_type:
                current = quests_progress.get(q['id'], 0)
                if current < q['target']:
                    quests_progress[q['id']] = min(q['target'], current + value)
        
        player['daily_quests_progress'] = quests_progress
        player.save()
        
        # Проверяем завершённые квесты
        self._check_completed_quests(uid, player, quests_progress)
    
    def _check_completed_quests(self, uid: str, player: Player, progress: dict):
        """Проверяет и выдаёт награды за завершённые квесты"""
        completed = player.get('daily_quests_completed', [])
        new_completed = []
        
        for q in self.daily_quests:
            if q['id'] not in completed and progress.get(q['id'], 0) >= q['target']:
                # Выдаём награду
                player['money'] += q['reward_money']
                player['exp'] += q['reward_exp']
                new_completed.append(q['id'])
                
                logger.system(f"Игрок {player['name']} завершил квест {q['name']}", 
                             f"+{q['reward_money']}💰 +{q['reward_exp']}📚")
        
        if new_completed:
            completed.extend(new_completed)
            player['daily_quests_completed'] = completed
            player.save()
    
    def get_daily_quests_status(self, uid: str) -> List[Dict]:
        """Возвращает статус всех ежедневных квестов"""
        player = Player(uid)
        progress = player.get('daily_quests_progress', {})
        completed = player.get('daily_quests_completed', [])
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Сброс если новый день
        if progress.get('date') != today:
            progress = {'date': today}
            completed = []
            for q in self.daily_quests:
                progress[q['id']] = 0
            player['daily_quests_progress'] = progress
            player['daily_quests_completed'] = completed
            player.save()
        
        result = []
        for q in self.daily_quests:
            current = progress.get(q['id'], 0)
            is_completed = q['id'] in completed
            result.append({
                **q,
                'progress': current,
                'completed': is_completed,
                'remaining': max(0, q['target'] - current)
            })
        
        return result
    
    def get_active_destiny_quest(self, uid: str):
        """Получает активный квест судьбы"""
        return self.destiny_quests.get(uid)
    
    def set_destiny_quest(self, uid: str, quest: Dict):
        """Устанавливает квест судьбы"""
        self.destiny_quests[uid] = quest
    
    def clear_destiny_quest(self, uid: str):
        """Очищает квест судьбы"""
        if uid in self.destiny_quests:
            del self.destiny_quests[uid]
    
    @require_character
    async def show_quests(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает все активные квесты"""
        uid = str(update.effective_user.id)
        player = Player(uid)
        
        # Ежедневные квесты
        daily_status = self.get_daily_quests_status(uid)
        
        text = "📋 **АКТИВНЫЕ КВЕСТЫ** 📋\n\n"
        text += "**📅 Ежедневные квесты:**\n"
        
        for q in daily_status:
            if q['completed']:
                status = "✅ ЗАВЕРШЁН"
            else:
                status = f"🎯 {q['progress']}/{q['target']}"
            
            text += f"\n{q['name']}\n"
            text += f"└ {status}\n"
            text += f"└ Награда: {q['reward_money']}💰 +{q['reward_exp']}📚\n"
        
        # Квест судьбы
        destiny_quest = self.get_active_destiny_quest(uid)
        if destiny_quest:
            text += f"\n**✨ Задание судьбы:**\n"
            text += f"└ {destiny_quest.get('name', 'Неизвестно')}\n"
            text += f"└ {destiny_quest.get('description', '')}\n"
            if not destiny_quest.get('completed', False):
                text += f"└ Статус: в процессе\n"
            else:
                text += f"└ ✅ Завершено! Награда уже выдана.\n"
        else:
            text += f"\n**✨ Задание судьбы:**\n"
            text += f"└ Нет активного задания\n"
            text += f"└ Используй `/destiny` чтобы получить задание\n"
        
        text += f"\n🕐 Ежедневные квесты сбрасываются в 4:00 по UTC"
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 На главную", callback_data="main_screen")
        ]])
        
        await update_message(update, context, text, parse_mode='Markdown', reply_markup=keyboard)
    
    def reset_daily_quests(self):
        """Сбрасывает все ежедневные квесты (вызывается по расписанию)"""
        data = Database().get_all()
        for uid, p in data.items():
            if isinstance(p, dict) and p.get('race'):
                # Очищаем прогресс
                if 'daily_quests_progress' in p:
                    del p['daily_quests_progress']
                if 'daily_quests_completed' in p:
                    del p['daily_quests_completed']
        Database().save()
        logger.system("Ежедневные квесты", "Сброшены для всех игроков")


# Глобальный экземпляр
quest_system = QuestSystem()