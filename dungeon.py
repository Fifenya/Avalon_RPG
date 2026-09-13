# dungeon.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
import random
import asyncio
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Player
from game_data import Enemy, get_drop
from rank_system import RankSystem
from battle import BattleManager, active_battles
from utils import update_message, require_character
from main_screen import show_main_screen
from logger import GameLogger
from config import DEATH_REGEN_DELAY

logger = GameLogger()

# Данные подземелья по этажам
DUNGEON_FLOORS = {
    1: {
        "name": "🕷️ Этаж пауков",
        "desc": "Тёмные тоннели, покрытые паутиной. В воздухе пахнет смертью.",
        "enemies": [
            {"name": "🕷️ Пещерный паук", "hp": 150, "power": 20, "armor": 10, "reward": 100, "exp": 15, "level": 3},
            {"name": "🦇 Гигантская летучая мышь", "hp": 120, "power": 18, "armor": 8, "reward": 80, "exp": 12, "level": 2},
        ],
        "boss": {"name": "👑 Король пауков", "hp": 500, "power": 45, "armor": 25, "reward": 500, "exp": 60, "level": 5},
        "required_kills": 3,
        "next_floor": 2
    },
    2: {
        "name": "🔥 Огненные чертоги",
        "desc": "Раскалённые залы, где воздух дрожит от жара.",
        "enemies": [
            {"name": "🔥 Огненный элементаль", "hp": 180, "power": 30, "armor": 8, "reward": 200, "exp": 20, "level": 5},
            {"name": "🧟 Пылающий зомби", "hp": 200, "power": 25, "armor": 15, "reward": 150, "exp": 18, "level": 4},
        ],
        "boss": {"name": "👑 Огненный великан", "hp": 800, "power": 70, "armor": 40, "reward": 800, "exp": 100, "level": 10},
        "required_kills": 4,
        "next_floor": 3
    },
    3: {
        "name": "🌑 Теневые земли",
        "desc": "Мрачные пещеры, где тьма сгущается в живые формы.",
        "enemies": [
            {"name": "🌑 Теневой призрак", "hp": 200, "power": 40, "armor": 5, "reward": 300, "exp": 25, "level": 7},
            {"name": "⚔️ Скелет-воин", "hp": 300, "power": 35, "armor": 20, "reward": 250, "exp": 30, "level": 8},
        ],
        "boss": {"name": "👑 Тёмный властелин", "hp": 1500, "power": 120, "armor": 60, "reward": 1500, "exp": 200, "level": 15},
        "required_kills": 5,
        "next_floor": 4
    },
    4: {
        "name": "🐉 Логово драконов",
        "desc": "Огромные залы, где обитают древние ящеры.",
        "enemies": [
            {"name": "🐉 Молодой дракон", "hp": 400, "power": 45, "armor": 25, "reward": 400, "exp": 35, "level": 8},
            {"name": "🦎 Драконий ящер", "hp": 350, "power": 40, "armor": 30, "reward": 350, "exp": 32, "level": 9},
        ],
        "boss": {"name": "👑 Древний дракон", "hp": 3000, "power": 200, "armor": 100, "reward": 3000, "exp": 400, "level": 20},
        "required_kills": 6,
        "next_floor": 5
    },
    5: {
        "name": "👾 Бездна",
        "desc": "Последний этаж. Здесь обитают ужасы из другого измерения.",
        "enemies": [
            {"name": "👾 Ужас из бездны", "hp": 800, "power": 60, "armor": 40, "reward": 800, "exp": 55, "level": 12},
            {"name": "🧙 Безумный маг", "hp": 600, "power": 70, "armor": 20, "reward": 700, "exp": 60, "level": 13},
        ],
        "boss": {"name": "👑 Архидемон", "hp": 8000, "power": 350, "armor": 150, "reward": 8000, "exp": 1000, "level": 30},
        "required_kills": 8,
        "next_floor": None
    }
}

# Активные рейды
active_dungeon_raids = {}


class DungeonManager:
    def __init__(self, uid, player):
        self.uid = uid
        self.player = player
        self.current_floor = player.get('dungeon_floor', 1)
        self.progress = player.get('dungeon_progress', 0)
        self.required_kills = DUNGEON_FLOORS[self.current_floor]["required_kills"]
        self.status = "active"
        self.current_enemy = None
        
        if self.progress > self.required_kills:
            self.progress = self.required_kills
            self.player['dungeon_progress'] = self.progress
            self.player.save()
    
    def get_floor_info(self):
        return DUNGEON_FLOORS[self.current_floor]
    
    def get_progress_bar(self):
        if self.required_kills == 0:
            return "🟩" * 10
        filled = int(self.progress / self.required_kills * 10)
        filled = min(10, max(0, filled))
        return "🟩" * filled + "⬜" * (10 - filled)
    
    def get_status_text(self):
        floor_info = self.get_floor_info()
        progress_bar = self.get_progress_bar()
        percent = int(self.progress / self.required_kills * 100) if self.required_kills > 0 else 0
        
        text = f"🏚️ **{floor_info['name']}**\n"
        text += f"_{floor_info['desc']}_\n\n"
        text += f"📍 Этаж {self.current_floor}/5\n"
        text += f"{progress_bar} {percent}%\n"
        text += f"👾 Побеждено: {self.progress}/{self.required_kills}\n\n"
        
        if self.status == "fighting_boss":
            text += f"⚔️ **СРАЖЕНИЕ С БОССОМ!** ⚔️\n"
        elif self.progress >= self.required_kills:
            text += f"🎯 **БОСС ДОСТУПЕН!** Нажми на кнопку ниже, чтобы призвать его!\n"
        else:
            remaining = self.required_kills - self.progress
            text += f"🎯 Нужно победить ещё {remaining} врагов для вызова босса"
        
        return text
    
    def get_keyboard(self):
        if self.status == "fighting_boss":
            return InlineKeyboardMarkup([
                [InlineKeyboardButton("⚔️ Сражаться с боссом", callback_data="dungeon_fight_boss")],
                [InlineKeyboardButton("🏃 Выйти из подземелья", callback_data="dungeon_exit")]
            ])
        elif self.progress >= self.required_kills:
            return InlineKeyboardMarkup([
                [InlineKeyboardButton("👑 Призвать босса", callback_data="dungeon_summon_boss")],
                [InlineKeyboardButton("🏃 Выйти из подземелья", callback_data="dungeon_exit")]
            ])
        else:
            return InlineKeyboardMarkup([
                [InlineKeyboardButton("👾 Искать врага", callback_data="dungeon_search")],
                [InlineKeyboardButton("🏃 Выйти из подземелья", callback_data="dungeon_exit")]
            ])
    
    async def search_enemy(self, update, context):
        if self.progress >= self.required_kills:
            await update_message(update, context, "👑 Ты уже победил всех врагов на этом этаже! Призови босса!", reply_markup=self.get_keyboard())
            return
        
        await update_message(update, context, "🔍 Обыскиваю подземелье...", reply_markup=None)
        await asyncio.sleep(random.uniform(1, 2))
        
        floor_info = self.get_floor_info()
        enemy_data = random.choice(floor_info["enemies"])
        
        hp_var = int(enemy_data["hp"] * random.uniform(0.95, 1.05))
        power_var = int(enemy_data["power"] * random.uniform(0.95, 1.05))
        
        enemy = Enemy(
            name=enemy_data["name"],
            hp=hp_var,
            power=power_var,
            armor=enemy_data["armor"],
            reward=enemy_data["reward"],
            exp=enemy_data["exp"],
            level=enemy_data["level"]
        )
        
        self.current_enemy = enemy
        self.status = "fighting"
        
        battle = BattleManager(self.uid, self.player, enemy)
        active_battles[self.uid] = battle
        battle.dungeon_mode = True
        battle.dungeon_manager = self
        
        await battle.update_battle_message(update, context)
    
    async def summon_boss(self, update, context):
        floor_info = self.get_floor_info()
        boss_data = floor_info["boss"]
        
        text = (f"⚡ **ТЫ ПРИЗЫВАЕШЬ БОССА!** ⚡\n\n"
                f"**{boss_data['name']}** появляется из тени!\n\n"
                f"❤️ HP: {boss_data['hp']}\n"
                f"⚔️ Сила: {boss_data['power']}\n"
                f"🛡️ Броня: {boss_data['armor']}\n"
                f"💰 Награда: {boss_data['reward']} монет\n"
                f"📚 Опыт: {boss_data['exp']}\n\n"
                f"Готов ли ты сразиться?")
        
        self.status = "boss_summoned"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⚔️ Начать битву!", callback_data="dungeon_fight_boss")],
            [InlineKeyboardButton("🏃 Сбежать", callback_data="dungeon_exit")]
        ])
        
        await update_message(update, context, text, reply_markup=keyboard, parse_mode='Markdown')
    
    async def fight_boss(self, update, context):
        floor_info = self.get_floor_info()
        boss_data = floor_info["boss"]
        
        boss = Enemy(
            name=boss_data["name"],
            hp=boss_data["hp"],
            power=boss_data["power"],
            armor=boss_data["armor"],
            reward=boss_data["reward"],
            exp=boss_data["exp"],
            level=boss_data["level"]
        )
        
        self.current_enemy = boss
        self.status = "fighting_boss_active"
        
        battle = BattleManager(self.uid, self.player, boss)
        active_battles[self.uid] = battle
        battle.dungeon_mode = True
        battle.dungeon_manager = self
        
        await battle.update_battle_message(update, context)
    
    async def on_enemy_defeated(self, update, context):
        self.progress += 1
        if self.progress > self.required_kills:
            self.progress = self.required_kills
        
        self.player['dungeon_progress'] = self.progress
        self.player.save()
        
        if self.progress >= self.required_kills:
            self.status = "active"
            await self.show_floor_status(update, context)
        else:
            await self.show_floor_status(update, context)
    
    async def on_boss_defeated(self, update, context):
        floor_info = self.get_floor_info()
        next_floor = floor_info["next_floor"]
        
        if next_floor is None:
            self.status = "completed"
            self.player['dungeon_floor'] = 1
            self.player['dungeon_progress'] = 0
            self.player['dungeon_completed'] = True
            
            bonus_reward = 5000
            self.player['money'] += bonus_reward
            
            self.player.save()
            
            text = (f"🏆 **ПОДЗЕМЕЛЬЕ ПРОЙДЕНО!** 🏆\n\n"
                    f"Ты победил **{floor_info['boss']['name']}** и очистил Глубинную Бездну!\n"
                    f"💰 Бонус: +{bonus_reward} монет\n\n"
                    f"Твоё имя вписано в Книгу Героев!")
            
            from achievements import AchievementsSystem
            ach = AchievementsSystem()
            ach.check_achievements(self.uid)
            
            await update_message(update, context, text, reply_markup=None, parse_mode='Markdown')
            await asyncio.sleep(2)
            
            if self.uid in active_dungeon_raids:
                del active_dungeon_raids[self.uid]
            
            await show_main_screen(update, context)
        else:
            self.current_floor = next_floor
            self.progress = 0
            self.status = "active"
            self.player['dungeon_floor'] = self.current_floor
            self.player['dungeon_progress'] = 0
            self.player.save()
            
            text = (f"✨ **ЭТАЖ {self.current_floor - 1} ПРОЙДЕН!** ✨\n\n"
                    f"Ты открываешь путь на следующий этаж...\n\n"
                    f"📍 **{DUNGEON_FLOORS[self.current_floor]['name']}**\n"
                    f"_{DUNGEON_FLOORS[self.current_floor]['desc']}_")
            
            await update_message(update, context, text, reply_markup=None, parse_mode='Markdown')
            await asyncio.sleep(2)
            await self.show_floor_status(update, context)
    
    async def show_floor_status(self, update, context):
        text = self.get_status_text()
        await update_message(update, context, text, reply_markup=self.get_keyboard(), parse_mode='Markdown')
    
    async def exit(self, update, context):
        self.player['dungeon_floor'] = self.current_floor
        self.player['dungeon_progress'] = self.progress
        self.player.save()
        
        await update_message(update, context, "🏃 Ты покинул подземелье...")
        await asyncio.sleep(1)
        
        if self.uid in active_dungeon_raids:
            del active_dungeon_raids[self.uid]
        
        await show_main_screen(update, context)


@require_character
async def enter_dungeon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Войти в подземелье"""
    uid = str(update.effective_user.id)
    player = Player(uid)
    
    if not player.get('race'):
        await update_message(update, context, "❌ Сначала создай персонажа через /start")
        return
    
    if player.is_dead():
        remaining = player.get_death_remaining()
        minutes = remaining // 60
        seconds = remaining % 60
        await update_message(update, context, 
            f"💀 Ты ещё не восстановился после смерти!\n"
            f"⏳ Осталось: {minutes}:{seconds:02d}")
        return
    
    if uid in active_dungeon_raids:
        await update_message(update, context, "❌ Ты уже в подземелье!")
        return
    
    manager = DungeonManager(uid, player)
    active_dungeon_raids[uid] = manager
    
    await manager.show_floor_status(update, context)


@require_character
async def dungeon_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопок подземелья"""
    query = update.callback_query
    await query.answer()
    
    uid = str(query.from_user.id)
    action = query.data
    
    if action == "dungeon_search":
        if uid not in active_dungeon_raids:
            await enter_dungeon(update, context)
            return
        manager = active_dungeon_raids[uid]
        await manager.search_enemy(update, context)
    
    elif action == "dungeon_summon_boss":
        if uid not in active_dungeon_raids:
            await enter_dungeon(update, context)
            return
        manager = active_dungeon_raids[uid]
        await manager.summon_boss(update, context)
    
    elif action == "dungeon_fight_boss":
        if uid not in active_dungeon_raids:
            await enter_dungeon(update, context)
            return
        manager = active_dungeon_raids[uid]
        await manager.fight_boss(update, context)
    
    elif action == "dungeon_exit":
        if uid in active_dungeon_raids:
            manager = active_dungeon_raids[uid]
            await manager.exit(update, context)
        else:
            await show_main_screen(update, context)