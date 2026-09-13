# battle.py — ПОЛНАЯ ВЕРСИЯ С НЕЙРОНКОЙ

import random
import asyncio
import time
from enum import Enum
from typing import Dict, Tuple
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Player
from game_data import get_random_enemy, get_drop
from rank_system import RankSystem
from keyboards import get_battle_after_keyboard, get_hidden_mode_keyboard, get_hide_potion_keyboard, get_hide_spell_keyboard, get_hide_armor_buff_keyboard, get_hide_equip_keyboard, get_hide_belt_keyboard
from utils import update_message, save_battle_log, require_character
from main_screen import show_main_screen
from logger import GameLogger
from config import DEATH_REGEN_DELAY

# ===== ИМПОРТ НЕЙРОНКИ =====
try:
    from config import AI_ENGINE
    if AI_ENGINE == "ollama":
        from ai_ollama import get_phone_ai_action_compat as get_phone_ai_action
        print("🧠 AI: Ollama (локальная модель)")
    else:
        from ai_phone import get_phone_ai_action
        print("📱 AI: Phone AI (облачная)")
except ImportError:
    from ai_phone import get_phone_ai_action, phone_ai
    print("⚠️ AI: Phone AI (fallback)")

logger = GameLogger()
active_battles = {}


class BodyPart(Enum):
    HEAD = "голова"
    CHEST = "грудь"
    ARMS = "руки"
    LEGS = "ноги"
    BACK = "спина"


BODY_PARTS = {
    "humanoid": {
        BodyPart.HEAD: {"name": "👤 Голова", "multiplier": 1.5, "hit_chance": 0.6, "critical_mult": 2.0},
        BodyPart.CHEST: {"name": "🩻 Грудь", "multiplier": 1.0, "hit_chance": 0.8, "critical_mult": 1.5},
        BodyPart.ARMS: {"name": "💪 Руки", "multiplier": 0.8, "hit_chance": 0.7, "critical_mult": 1.3},
        BodyPart.LEGS: {"name": "🦵 Ноги", "multiplier": 0.7, "hit_chance": 0.75, "critical_mult": 1.2},
        BodyPart.BACK: {"name": "🎒 Спина", "multiplier": 1.2, "hit_chance": 0.65, "critical_mult": 1.6},
    },
    "beast": {
        BodyPart.HEAD: {"name": "🐺 Голова", "multiplier": 1.3, "hit_chance": 0.65, "critical_mult": 1.8},
        BodyPart.CHEST: {"name": "🩻 Корпус", "multiplier": 1.0, "hit_chance": 0.75, "critical_mult": 1.4},
        BodyPart.ARMS: {"name": "🐾 Лапы", "multiplier": 0.9, "hit_chance": 0.7, "critical_mult": 1.3},
        BodyPart.LEGS: {"name": "🦵 Ноги", "multiplier": 0.8, "hit_chance": 0.7, "critical_mult": 1.2},
        BodyPart.BACK: {"name": "🎒 Хребет", "multiplier": 1.1, "hit_chance": 0.7, "critical_mult": 1.5},
    },
    "undead": {
        BodyPart.HEAD: {"name": "💀 Череп", "multiplier": 1.4, "hit_chance": 0.55, "critical_mult": 1.9},
        BodyPart.CHEST: {"name": "🦴 Грудная клетка", "multiplier": 0.9, "hit_chance": 0.8, "critical_mult": 1.3},
        BodyPart.ARMS: {"name": "🦴 Костяные руки", "multiplier": 0.7, "hit_chance": 0.7, "critical_mult": 1.2},
        BodyPart.LEGS: {"name": "🦴 Костяные ноги", "multiplier": 0.6, "hit_chance": 0.7, "critical_mult": 1.1},
        BodyPart.BACK: {"name": "🎒 Позвоночник", "multiplier": 1.0, "hit_chance": 0.65, "critical_mult": 1.4},
    },
    "dragon": {
        BodyPart.HEAD: {"name": "🐉 Голова", "multiplier": 1.6, "hit_chance": 0.5, "critical_mult": 2.2},
        BodyPart.CHEST: {"name": "🩻 Грудная пластина", "multiplier": 0.8, "hit_chance": 0.7, "critical_mult": 1.3},
        BodyPart.ARMS: {"name": "🐉 Крылья", "multiplier": 0.9, "hit_chance": 0.65, "critical_mult": 1.4},
        BodyPart.LEGS: {"name": "🐉 Лапы", "multiplier": 1.0, "hit_chance": 0.7, "critical_mult": 1.5},
        BodyPart.BACK: {"name": "🎒 Хвост", "multiplier": 1.2, "hit_chance": 0.6, "critical_mult": 1.7},
    },
    "magical": {
        BodyPart.HEAD: {"name": "🔮 Голова", "multiplier": 1.5, "hit_chance": 0.6, "critical_mult": 2.0},
        BodyPart.CHEST: {"name": "✨ Магическое ядро", "multiplier": 1.3, "hit_chance": 0.65, "critical_mult": 1.8},
        BodyPart.ARMS: {"name": "🌀 Энергетические руки", "multiplier": 0.8, "hit_chance": 0.7, "critical_mult": 1.3},
        BodyPart.LEGS: {"name": "🌊 Энергетические ноги", "multiplier": 0.7, "hit_chance": 0.7, "critical_mult": 1.2},
        BodyPart.BACK: {"name": "⭐ Энергетический столб", "multiplier": 1.1, "hit_chance": 0.65, "critical_mult": 1.6},
    },
}

ENEMY_TYPES = {
    "humanoid": ["Зомби", "Вампир", "Оборотень", "Рыцарь", "Маг", "Демон"],
    "beast": ["Крыса", "Волк", "Паук", "Медведь", "Кабан"],
    "undead": ["Скелет", "Лич", "Умертвие", "Призрак"],
    "dragon": ["Дракон", "Виверн", "Ящер"],
    "magical": ["Элементаль", "Дух", "Голем"]
}


def get_enemy_type(enemy_name: str) -> str:
    for enemy_type, keywords in ENEMY_TYPES.items():
        for keyword in keywords:
            if keyword.lower() in enemy_name.lower():
                return enemy_type
    return "humanoid"


def get_body_parts_keyboard(enemy_type: str):
    parts = BODY_PARTS.get(enemy_type, BODY_PARTS["humanoid"])
    keyboard = []
    row = []
    
    emojis = {
        BodyPart.HEAD: "👤",
        BodyPart.CHEST: "🩻", 
        BodyPart.ARMS: "💪",
        BodyPart.LEGS: "🦵", 
        BodyPart.BACK: "🎒"
    }
    
    descriptions = {
        BodyPart.HEAD: "Голова",
        BodyPart.CHEST: "Грудь",
        BodyPart.ARMS: "Руки",
        BodyPart.LEGS: "Ноги",
        BodyPart.BACK: "Спина"
    }
    
    for part in parts.keys():
        row.append(InlineKeyboardButton(
            f"{emojis.get(part, '🎯')} {descriptions.get(part, part.value)}",
            callback_data=f"battle_attack_{part.value}"
        ))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🛡️ Защита", callback_data="battle_defend")])
    keyboard.append([InlineKeyboardButton("🌑 Скрыться", callback_data="battle_hide")])
    keyboard.append([InlineKeyboardButton("🏃 Сбежать", callback_data="battle_run")])
    
    return InlineKeyboardMarkup(keyboard)


class BattleManager:
    def __init__(self, uid, player, enemy):
        self.uid = uid
        self.player = player
        self.enemy = enemy
        self.player_hp = player['hp']
        self.enemy_hp = enemy.hp
        self.turn = 0
        self.defending = False
        self.log = []
        self.finished = False
        self.enemy_type = get_enemy_type(enemy.name)
        self.dungeon_mode = False
        self.dungeon_manager = None
        self.hidden = False
        self.hidden_turns = 0
        self.start_time = time.time()
        self.battle_log = []
        self.player_actions_log = []
        
        # ===== НЕЙРОНКА =====
        self.ai = None
        self.action_idx = 0
        self.action_info = None
        self.state = None
        self.last_reward = 0
    
    def add_log(self, message):
        self.log.append(message)
    
    def get_hp_bar(self, current, maximum):
        percent = current / maximum if maximum > 0 else 0
        filled = int(percent * 10)
        return "🟥" * filled + "⬜" * (10 - filled)
    
    def get_battle_text(self):
        player_hp_bar = self.get_hp_bar(self.player_hp, self.player['max_hp'])
        enemy_hp_bar = self.get_hp_bar(self.enemy_hp, self.enemy.max_hp)
        enemy_rank = self.enemy.get_rank_display()
        
        text = f"⚔️ **БИТВА** ⚔️\n\n"
        text += f"👤 **{self.player['name']}**\n"
        text += f"{player_hp_bar} {self.player_hp}/{self.player['max_hp']} ❤️\n"
        text += f"💙 {self.player.get('mana', 50)}/{self.player.get('max_mana', 50)}\n\n"
        text += f"👾 **{enemy_rank} {self.enemy.name}**\n"
        text += f"{enemy_hp_bar} {self.enemy_hp}/{self.enemy.max_hp} ❤️\n"
        text += f"⚔️ Сила: {self.enemy.power} | 🛡️ Броня: {self.enemy.armor}\n\n"
        
        if self.log:
            text += f"📋 **Ход {self.turn}:**\n"
            for msg in self.log[-3:]:
                text += f"• {msg}\n"
        
        return text
    
    def get_player_power(self) -> int:
        base_power = self.player['power']
        inventory = self.player.get('inventory', {})
        equipped = inventory.get('equipped', {})
        equipment_bonus = 0
        for slot, item in equipped.items():
            if 'stats' in item:
                equipment_bonus += item['stats'].get('power', 0)
        return base_power + equipment_bonus
    
    async def update_battle_message(self, update, context):
        text = self.get_battle_text()
        await update_message(update, context, text, 
                            reply_markup=get_body_parts_keyboard(self.enemy_type),
                            parse_mode='Markdown')
    
    # ===== АТАКА ИГРОКА =====
    
    async def player_attack(self, update, context, body_part_name: str):
        parts = BODY_PARTS.get(self.enemy_type, BODY_PARTS["humanoid"])
        
        selected_part = None
        part_data = None
        for part, data in parts.items():
            if part.value == body_part_name:
                selected_part = part
                part_data = data
                break
        
        if not selected_part:
            selected_part = BodyPart.CHEST
            part_data = parts[BodyPart.CHEST]
        
        base_damage = random.randint(8, 15)
        damage = base_damage + self.get_player_power()
        damage = int(damage * part_data["multiplier"])
        
        hit_chance = part_data["hit_chance"]
        is_hit = random.random() < hit_chance
        
        if not is_hit:
            self.add_log(f"❌ Ты промахнулся по {selected_part.value}!")
            self.player_actions_log.append({
                "action_type": "attack_miss",
                "body_part": body_part_name,
                "player_hp": self.player_hp,
                "player_power": self.get_player_power()
            })
            self.battle_log.append({
                "turn": self.turn,
                "actor": "player",
                "action_type": "attack_miss",
                "body_part": body_part_name,
                "player_hp": self.player_hp,
                "player_power": self.get_player_power()
            })
            
            self.last_reward = 2
            await self.enemy_attack(update, context)
            return
        
        crit_chance = self.player.get('crit_chance', 0.1)
        is_crit = random.random() < crit_chance
        if is_crit:
            crit_mult = part_data.get("critical_mult", 1.5)
            damage = int(damage * crit_mult)
            self.add_log(f"💥 КРИТ! {damage} урона по {selected_part.value}!")
            logger.crit(self.player['name'], damage)
        else:
            self.add_log(f"⚔️ Ты бьёшь по {selected_part.value} и наносишь {damage} урона")
        
        if self.get_player_power() > self.enemy.armor:
            damage = max(1, damage - self.enemy.armor // 2)
        else:
            damage = max(1, damage - self.enemy.armor)
        
        self.enemy_hp -= damage
        self.enemy.hp = self.enemy_hp
        
        self.player_actions_log.append({
            "action_type": "attack",
            "body_part": body_part_name,
            "is_crit": is_crit,
            "damage": damage,
            "player_hp": self.player_hp,
            "player_power": self.get_player_power(),
            "player_armor": self.player.get('armor', 0)
        })
        
        self.battle_log.append({
            "turn": self.turn,
            "actor": "player",
            "action_type": "attack",
            "body_part": body_part_name,
            "damage": damage,
            "is_crit": is_crit,
            "player_hp": self.player_hp,
            "player_power": self.get_player_power(),
            "player_armor": self.player.get('armor', 0)
        })
        
        self.last_reward = damage / 10
        
        if self.enemy_hp <= 0:
            await self.victory(update, context)
            return
        
        await self.enemy_attack(update, context)
    
    # ===== АТАКА ВРАГА (С НЕЙРОНКОЙ) =====
    
    async def enemy_attack(self, update, context):
        # Получаем действие от нейросети
        self.ai, self.action_idx, self.action_info, self.state = get_phone_ai_action(
            self.player, self.enemy, self.turn
        )
        
        action = self.action_info
        action_idx = self.action_idx
        
        self.ai.defending = False
        
        # Логируем действие врага
        self.battle_log.append({
            "turn": self.turn,
            "actor": "enemy",
            "action_type": action['name'],
            "description": action['desc']
        })
        
        # ===== ЛЕЧЕНИЕ =====
        if action_idx == 3:
            heal = self.ai.get_heal_amount(action_idx)
            old_hp = self.enemy_hp
            self.enemy_hp = min(self.enemy.max_hp, self.enemy_hp + heal)
            self.enemy.hp = self.enemy_hp
            self.add_log(f"👾 {self.enemy.name} {action['desc']} +{self.enemy_hp - old_hp} HP!")
            
            next_state = self._get_next_state()
            self.ai.update(self.state, action_idx, 3, next_state, False)
            
            self.turn += 1
            await self.update_battle_message(update, context)
            return
        
        # ===== ПОБЕГ =====
        if action_idx == 6:
            chance = self.ai.get_flee_chance(action_idx)
            if random.random() < chance:
                self.add_log(f"👾 {self.enemy.name} сбежал!")
                await self.run(update, context)
                return
            self.add_log(f"👾 {self.enemy.name} пытался сбежать, но не смог!")
            
            next_state = self._get_next_state()
            self.ai.update(self.state, action_idx, -2, next_state, False)
            
            self.turn += 1
            await self.update_battle_message(update, context)
            return
        
        # ===== ЗАЩИТА =====
        if action_idx == 2:
            self.ai.defending = True
            self.defending = True
            self.add_log(f"👾 {self.enemy.name} {action['desc']}")
            
            next_state = self._get_next_state()
            self.ai.update(self.state, action_idx, 1, next_state, False)
            
            self.turn += 1
            await self.update_battle_message(update, context)
            return
        
        # ===== АТАКА =====
        damage_mult = self.ai.get_damage_mult(action_idx)
        
        # Уворот игрока
        dodge_chance = self.player.get('dodge_chance', 0.05)
        if random.random() < dodge_chance:
            self.add_log(f"💨 Ты увернулся от атаки врага!")
            logger.dodge(self.player['name'])
            
            self.battle_log.append({
                "turn": self.turn,
                "actor": "enemy",
                "action_type": "miss",
                "description": "промахнулся"
            })
            
            next_state = self._get_next_state()
            self.ai.update(self.state, action_idx, -3, next_state, False)
            
            self.turn += 1
            await self.update_battle_message(update, context)
            return
        
        # Расчёт урона
        damage = self.enemy.power + random.randint(-5, 5)
        damage = max(1, int(damage * damage_mult))
        
        # Защита игрока
        if self.defending:
            damage = damage // 2
            self.add_log(f"🛡️ Защита уменьшила урон вдвое!")
        
        # Блок игрока
        block_chance = self.player.get('block_chance', 0.05)
        if random.random() < block_chance:
            block = random.randint(5, 15)
            damage = max(1, damage - block)
            self.add_log(f"🛡️ Ты заблокировал {block} урона!")
            logger.block(self.player['name'], block)
        
        self.player_hp -= damage
        self.add_log(f"👾 {self.enemy.name} {action['desc']} и наносит {damage} урона")
        
        reward = 5 if damage > 15 else 1 if damage > 5 else -1
        if self.player_hp < self.player['max_hp'] * 0.2:
            reward += 3
        self.last_reward = reward
        
        next_state = self._get_next_state()
        self.ai.update(self.state, action_idx, reward, next_state, False)
        
        self.defending = False
        self.turn += 1
        
        self.player['hp'] = self.player_hp
        self.player.save()
        
        if self.player_hp <= 0:
            await self.defeat(update, context)
            return
        
        await self.update_battle_message(update, context)
    
    def _get_next_state(self):
        from ai_phone import PhoneBattleState
        return PhoneBattleState.to_vector(
            self.player, self.enemy, self.turn + 1, 
            list(self.ai.action_history) if self.ai else None
        )
    
    # ===== ЗАЩИТА =====
    
    async def defend(self, update, context):
        self.player_actions_log.append({"action_type": "defend", "turn": self.turn})
        self.battle_log.append({"turn": self.turn, "actor": "player", "action_type": "defend"})
        
        self.defending = True
        self.add_log(f"🛡️ Ты встал в защитную стойку!")
        self.turn += 1
        await self.enemy_attack(update, context)
    
    # ===== ПОБЕГ =====
    
    async def run(self, update, context):
        self.player_actions_log.append({"action_type": "flee", "turn": self.turn})
        self.battle_log.append({"turn": self.turn, "actor": "player", "action_type": "flee"})
        
        success = random.random() < 0.5
        if success:
            self.add_log(f"🏃 Ты успешно сбежал!")
            await self.update_battle_message(update, context)
            self.finished = True
            if self.uid in active_battles:
                del active_battles[self.uid]
            logger.flee(self.player['name'], True)
            
            if self.ai:
                self.ai.record_result(player_won=True)
                phone_ai.record_battle(player_won=True, turns=self.turn)
                phone_ai.remove(self.enemy.name.replace(' ', '_').replace('️', ''), self.uid)
            
            await asyncio.sleep(1.5)
            await show_main_screen(update, context)
        else:
            self.add_log(f"❌ Не удалось сбежать!")
            await self.update_battle_message(update, context)
            await self.enemy_attack(update, context)
            logger.flee(self.player['name'], False)
    
    # ===== ПОБЕДА =====
    
    async def victory(self, update, context):
        self.finished = True
        if self.uid in active_battles:
            del active_battles[self.uid]
        
        final_reward = RankSystem.calculate_reward_with_rank(
            self.enemy.reward, self.player['power'], self.enemy.level
        )
        final_exp = RankSystem.calculate_reward_with_rank(
            self.enemy.exp, self.player['power'], self.enemy.level
        )
        
        old_rank, _ = RankSystem.get_player_rank(self.player['power'])
        
        self.player['money'] += final_reward
        self.player['exp'] += final_exp
        self.player['kills'] = self.player.get('kills', 0) + 1
        
        level_up_text = ""
        exp_needed = self.player['level'] * 100
        while self.player['exp'] >= exp_needed:
            self.player['level'] += 1
            self.player['power'] += 5
            self.player['max_hp'] += 20
            self.player['hp'] = self.player['max_hp']
            self.player['exp'] -= exp_needed
            exp_needed = self.player['level'] * 100
            level_up_text += f"\n\n🎉 **УРОВЕНЬ ПОВЫШЕН!** Теперь уровень {self.player['level']}! 🎉"
            logger.level_up(self.player['name'], self.player['level'], 5, 20)
        
        new_rank, _ = RankSystem.get_player_rank(self.player['power'])
        rank_up_text = ""
        if new_rank != old_rank:
            rank_up_text = f"\n\n✨ **РАНГ ПОВЫШЕН!** ✨\n{old_rank} → {new_rank}"
            self.player['rank'] = str(new_rank)
        
        drops = get_drop(self.enemy.name, self.player['level'], self.player['name'])
        drop_text = ""
        if drops:
            if 'inventory' not in self.player.data:
                self.player['inventory'] = {'items': [], 'equipped': {}}
            
            from inventory import can_add_item
            for item in drops:
                if can_add_item(self.player, item):
                    if isinstance(item, dict):
                        item.setdefault('rank', 'G')
                    elif not hasattr(item, 'rank'):
                        item.rank = "G"
                    self.player['inventory']['items'].append(item)
                    item_name = item.get('name') if isinstance(item, dict) else item.name
                    drop_text += f"\n• {item_name}"
                else:
                    item_name = item.get('name', 'Предмет') if isinstance(item, dict) else getattr(item, 'name', 'Предмет')
                    drop_text += f"\n• {item_name} (не влезло в инвентарь!)"
            logger.drop_received(self.player['name'], len(drops), self.enemy.name)
        
        self.player.save()
        
        if self.dungeon_mode and self.dungeon_manager:
            await self.dungeon_manager.on_enemy_defeated(update, context)
            return
        
        from achievements import AchievementsSystem
        ach = AchievementsSystem()
        new_achs = ach.check_achievements(self.uid)
        ach_text = ""
        if new_achs:
            ach_text = "\n\n🏆 **НОВЫЕ ДОСТИЖЕНИЯ!** 🏆\n"
            for a in new_achs:
                ach_text += f"{a['emoji']} {a['name']} +{a['reward']}💰\n"
        
        result_text = (f"🎉 **ПОБЕДА!** 🎉\n\n"
                      f"Ты победил **{self.enemy.name}**!\n"
                      f"💰 +{final_reward} монет\n"
                      f"📚 +{final_exp} опыта"
                      f"{level_up_text}{rank_up_text}{drop_text}{ach_text}")
        
        logger.hunt_win(self.player['name'], self.enemy.name, final_reward, final_exp, drops)
        
        if self.ai:
            self.ai.record_result(player_won=True)
            phone_ai.record_battle(player_won=True, turns=self.turn)
            phone_ai.remove(self.enemy.name.replace(' ', '_').replace('️', ''), self.uid)
        
        await update_message(update, context, result_text, 
                            reply_markup=get_battle_after_keyboard(), 
                            parse_mode='Markdown')
    
    # ===== ПОРАЖЕНИЕ =====
    
    async def defeat(self, update, context):
        self.finished = True
        if self.uid in active_battles:
            del active_battles[self.uid]
        
        lost = self.enemy.reward // 2
        self.player['money'] = max(0, self.player['money'] - lost)
        
        from hospital import hospital
        money_loss, exp_loss = self.player.on_killed()
        hospital.admit(self.uid, self.player)
        
        result_text = (
            f"💀 **ТЫ ПОГИБ В БОЮ!** 💀\n\n"
            f"Ты проиграл **{self.enemy.name}**.\n\n"
            f"💰 Потеряно в бою: {lost} монет\n"
            f"💀 Штраф за смерть: {money_loss} монет, {exp_loss} опыта\n\n"
            f"🏥 **Ты доставлен в Госпиталь Святого Клинка!**\n"
            f"_Восстанавливайся, герой..._"
        )
        
        logger.hunt_lose(self.player['name'], self.enemy.name, lost)
        
        battle_logging_enabled = self.player.get('battle_logging_enabled', False)
        if battle_logging_enabled:
            battle_data = {
                "result": "defeat",
                "enemy": self.enemy.name,
                "lost": lost,
                "log": self.log,
                "turns": self.turn
            }
            save_battle_log(self.uid, battle_data)
        
        if self.ai:
            self.ai.record_result(player_won=False)
            phone_ai.record_battle(player_won=False, turns=self.turn)
            phone_ai.remove(self.enemy.name.replace(' ', '_').replace('️', ''), self.uid)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(result_text, parse_mode='Markdown')
        else:
            await update_message(update, context, result_text, parse_mode='Markdown')
        
        await asyncio.sleep(3)
        await show_main_screen(update, context)
    
    # ========== МЕТОДЫ СКРЫТНОСТИ ==========
    
    async def try_hide(self, update, context):
        chance = 0.60
        player_class = self.player.get('class')
        if player_class == 'rogue':
            chance += 0.25
        elif player_class == 'archer':
            chance += 0.15
        
        race = self.player.get('race', '')
        if 'Кошколюд' in race:
            chance += 0.20
        elif 'Эльф' in race:
            chance += 0.10
        
        chance += self.player.get('dodge_chance', 0)
        chance -= self.player.get('drunk_level', 0) * 0.05
        
        success = random.random() < chance
        
        if success:
            self.hidden = True
            self.hidden_turns = random.randint(2, 4)
            
            self.battle_log.append({
                "turn": self.turn,
                "actor": "player",
                "action_type": "hide_success",
                "hidden_turns": self.hidden_turns
            })
            
            await update_message(update, context,
                f"🌑 **ТЫ СКРЫЛСЯ В ТЕНИ!**\n\n"
                f"Враг потерял тебя из виду на {self.hidden_turns} хода.\n\n"
                f"✨ Ты можешь использовать заклинания, зелья и баффы брони\n"
                f"⚔️ А также менять экипировку.\n\n"
                f"_Враг оглядывается по сторонам..._",
                reply_markup=get_hidden_mode_keyboard(),
                parse_mode='Markdown')
        else:
            damage = self.enemy.power * 2 + random.randint(5, 15)
            self.player_hp -= damage
            
            self.battle_log.append({
                "turn": self.turn,
                "actor": "player",
                "action_type": "hide_fail",
                "damage_taken": damage
            })
            
            self.player['hp'] = self.player_hp
            self.player.save()
            
            await update_message(update, context,
                f"❌ **НЕ УДАЛОСЬ СКРЫТЬСЯ!**\n\n"
                f"👾 {self.enemy.name} замечает твоё движение и наносит удар!\n"
                f"⚔️ Урон: {damage} ❤️\n"
                f"❤️ Твоё HP: {self.player_hp}/{self.player['max_hp']}",
                parse_mode='Markdown')
            
            if self.player_hp <= 0:
                await self.defeat(update, context)
            else:
                self.turn += 1
                await self.enemy_attack(update, context)
    
    async def hide_use_potion(self, update, context):
        if not self.hidden:
            await update_message(update, context, "❌ Ты не в тени!")
            return
        
        inventory = self.player.get('inventory', {}).get('items', [])
        potions = [item for item in inventory 
                   if item.get('type') == 'potion' and 'hp' in item.get('stats', {})]
        
        if not potions:
            await update_message(update, context,
                "❌ У тебя нет зелий здоровья!\n\n"
                "_Используй алхимию или купи в магазине_",
                reply_markup=get_hidden_mode_keyboard())
            return
        
        context.user_data['hide_potions'] = potions
        
        await update_message(update, context,
            "💊 **ВЫБЕРИ ЗЕЛЬЕ**\n\n"
            f"🌑 Осталось скрытых ходов: {self.hidden_turns}",
            reply_markup=get_hide_potion_keyboard(potions),
            parse_mode='Markdown')
    
    async def hide_use_potion_confirm(self, update, context, potion_index: int):
        if not self.hidden:
            return
        
        potions = context.user_data.get('hide_potions', [])
        if potion_index >= len(potions):
            await update_message(update, context, "❌ Зелье не найдено!")
            return
        
        potion = potions[potion_index]
        heal = potion.get('stats', {}).get('hp', 0)
        heal = int(heal * 1.5)
        
        old_hp = self.player_hp
        self.player_hp = min(self.player['max_hp'], self.player_hp + heal)
        self.player['hp'] = self.player_hp
        
        inventory = self.player['inventory']['items']
        inventory.remove(potion)
        self.player.save()
        
        self.battle_log.append({
            "turn": self.turn,
            "actor": "player",
            "action_type": "hide_potion",
            "potion": potion.get('name'),
            "heal": heal
        })
        
        self.hidden_turns -= 1
        
        await update_message(update, context,
            f"💊 **{potion['name']}** (скрыто)\n\n"
            f"Ты выпил зелье из тени!\n"
            f"✨ Бонус скрытности: +50% к лечению\n"
            f"❤️ +{heal} HP (теперь {self.player_hp}/{self.player['max_hp']})\n\n"
            f"🌑 Осталось скрытых ходов: {self.hidden_turns}",
            parse_mode='Markdown')
        
        if self.hidden_turns <= 0:
            await self.exit_hide(update, context)
        else:
            await update_message(update, context,
                "🌑 **Что дальше?**",
                reply_markup=get_hidden_mode_keyboard())
    
    async def hide_use_spell(self, update, context):
        if not self.hidden:
            await update_message(update, context, "❌ Ты не в тени!")
            return
        
        spells = self.player.get('class_skills', [])
        
        if not spells:
            await update_message(update, context,
                "❌ У тебя нет заклинаний!\n\n"
                "_Выбери класс с магией_",
                reply_markup=get_hidden_mode_keyboard())
            return
        
        context.user_data['hide_spells'] = spells
        
        await update_message(update, context,
            "✨ **ВЫБЕРИ ЗАКЛИНАНИЕ**\n\n"
            f"🌑 Осталось скрытых ходов: {self.hidden_turns}",
            reply_markup=get_hide_spell_keyboard(spells),
            parse_mode='Markdown')
    
    async def hide_use_spell_confirm(self, update, context, spell_index: int):
        if not self.hidden:
            return
        
        spells = context.user_data.get('hide_spells', [])
        if spell_index >= len(spells):
            await update_message(update, context, "❌ Заклинание не найдено!")
            return
        
        spell = spells[spell_index]
        mana_cost = spell.get('ap_cost', spell.get('mana_cost', 0))
        
        current_mana, max_mana, _ = self.player.get_mana_info()
        if current_mana < mana_cost:
            await update_message(update, context,
                f"❌ Не хватает маны! Нужно {mana_cost} MP, у тебя {current_mana}",
                reply_markup=get_hidden_mode_keyboard())
            return
        
        self.player['mana'] = current_mana - mana_cost
        
        base_damage = spell.get('damage_mult', 1.0) * 50
        damage = int(base_damage * 1.5)
        
        self.enemy_hp -= damage
        self.enemy.hp = self.enemy_hp
        self.player.save()
        
        self.battle_log.append({
            "turn": self.turn,
            "actor": "player",
            "action_type": "hide_spell",
            "spell": spell.get('name'),
            "damage": damage
        })
        
        self.hidden_turns -= 1
        
        await update_message(update, context,
            f"✨ **{spell['name']} (скрыто)**\n\n"
            f"Ты выпускаешь заклинание из тени!\n"
            f"✨ Бонус скрытности: x1.5 к урону\n"
            f"⚔️ Урон: {damage} ❤️\n"
            f"👾 У врага осталось HP: {max(0, self.enemy_hp)}/{self.enemy.max_hp}\n\n"
            f"🌑 Осталось скрытых ходов: {self.hidden_turns}",
            parse_mode='Markdown')
        
        if self.enemy_hp <= 0:
            await self.victory(update, context)
            return
        
        if self.hidden_turns <= 0:
            await self.exit_hide(update, context)
        else:
            await update_message(update, context,
                "🌑 **Что дальше?**",
                reply_markup=get_hidden_mode_keyboard())
    
    async def hide_use_armor(self, update, context):
        if not self.hidden:
            await update_message(update, context, "❌ Ты не в тени!")
            return
        
        equipped = self.player.get('inventory', {}).get('equipped', {})
        armor = equipped.get('armor') or equipped.get('shield')
        
        if not armor:
            await update_message(update, context,
                "❌ У тебя нет брони с активными способностями!\n\n"
                "_Купи или скрафти броню_",
                reply_markup=get_hidden_mode_keyboard())
            return
        
        buffs = armor.get('buffs', [])
        if not buffs:
            await update_message(update, context,
                f"❌ {armor.get('name')} не имеет активных способностей!",
                reply_markup=get_hidden_mode_keyboard())
            return
        
        context.user_data['hide_armor'] = armor
        context.user_data['hide_armor_buffs'] = buffs
        
        await update_message(update, context,
            f"🛡️ **{armor.get('name')} — АКТИВНЫЕ БАФФЫ**\n\n"
            f"🌑 Осталось скрытых ходов: {self.hidden_turns}",
            reply_markup=get_hide_armor_buff_keyboard(armor),
            parse_mode='Markdown')
    
    async def hide_use_armor_confirm(self, update, context, buff_index: int):
        if not self.hidden:
            return
        
        buffs = context.user_data.get('hide_armor_buffs', [])
        if buff_index >= len(buffs):
            await update_message(update, context, "❌ Бафф не найден!")
            return
        
        buff = buffs[buff_index]
        effect = buff.get('effect', {})
        duration = buff.get('duration', 3) * 2
        
        from utils import apply_temp_buff
        for stat, value in effect.items():
            apply_temp_buff(self.player, stat, value, duration)
        
        self.player.save()
        
        self.battle_log.append({
            "turn": self.turn,
            "actor": "player",
            "action_type": "hide_armor_buff",
            "buff": buff.get('name')
        })
        
        self.hidden_turns -= 1
        
        await update_message(update, context,
            f"🛡️ **{buff['name']} (скрыто)**\n\n"
            f"Ты активируешь способность брони из тени!\n"
            f"✨ Бонус скрытности: длительность x2\n"
            f"📊 Эффект: {buff.get('description', '')}\n"
            f"⏱️ Длительность: {duration} хода\n\n"
            f"🌑 Осталось скрытых ходов: {self.hidden_turns}",
            parse_mode='Markdown')
        
        if self.hidden_turns <= 0:
            await self.exit_hide(update, context)
        else:
            await update_message(update, context,
                "🌑 **Что дальше?**",
                reply_markup=get_hidden_mode_keyboard())
    
    async def hide_change_item(self, update, context, item_type: str):
        if not self.hidden:
            return
        
        inventory = self.player.get('inventory', {}).get('items', [])
        
        type_map = {
            'weapon': ['weapon'],
            'armor': ['armor', 'shield'],
            'other': ['helmet', 'boots'],
            'accessory': ['accessory']
        }
        
        allowed = type_map.get(item_type, [])
        items = [item for item in inventory if item.get('type') in allowed]
        
        if not items:
            await update_message(update, context,
                f"❌ Нет предметов для смены!",
                reply_markup=get_hidden_mode_keyboard())
            return
        
        context.user_data['hide_equip_type'] = item_type
        context.user_data['hide_equip_items'] = items
        
        type_names = {
            'weapon': 'оружия',
            'armor': 'брони/щита',
            'other': 'обуви/шлема',
            'accessory': 'аксессуара'
        }
        
        await update_message(update, context,
            f"⚔️ **СМЕНИТЬ {type_names.get(item_type, 'предмет').upper()}**\n\n"
            f"🌑 Осталось скрытых ходов: {self.hidden_turns}",
            reply_markup=get_hide_equip_keyboard(items, item_type),
            parse_mode='Markdown')
    
    async def hide_change_item_confirm(self, update, context, item_type: str, item_index: int):
        if not self.hidden:
            return
        
        items = context.user_data.get('hide_equip_items', [])
        if item_index >= len(items):
            await update_message(update, context, "❌ Предмет не найден!")
            return
        
        item = items[item_index]
        
        slot_map = {
            'weapon': 'weapon',
            'armor': 'armor',
            'shield': 'shield',
            'helmet': 'helmet',
            'boots': 'boots',
            'accessory': 'accessory'
        }
        slot = slot_map.get(item.get('type', 'weapon'), 'weapon')
        
        if slot in self.player['inventory']['equipped']:
            old_item = self.player['inventory']['equipped'][slot]
            self.player['inventory']['items'].append(old_item)
        
        self.player['inventory']['equipped'][slot] = item
        self.player['inventory']['items'].remove(item)
        
        from equipment import update_player_stats_from_equipment
        update_player_stats_from_equipment(self.player)
        self.player.save()
        
        await update_message(update, context,
            f"✅ **{item['name']} экипирован!**\n\n"
            f"🌑 Осталось скрытых ходов: {self.hidden_turns}",
            parse_mode='Markdown')
        
        await update_message(update, context,
            "🌑 **Что дальше?**",
            reply_markup=get_hidden_mode_keyboard())
    
    async def hide_equip_spells(self, update, context):
        if not self.hidden:
            await update_message(update, context, "❌ Ты не в тени!")
            return
        
        await update_message(update, context,
            "📖 **ЭКИПИРОВКА ЗАКЛИНАНИЙ**\n\n"
            "_Эта функция в разработке_\n\n"
            "💡 Чтобы экипировать заклинания, используй команду вне боя\n\n"
            f"🌑 Осталось скрытых ходов: {self.hidden_turns}",
            parse_mode='Markdown',
            reply_markup=get_hidden_mode_keyboard())
    
    async def hide_belt(self, update, context):
        if not self.hidden:
            await update_message(update, context, "❌ Ты не в тени!")
            return
        
        inventory = self.player.get('inventory', {}).get('items', [])
        potions = [item for item in inventory 
                   if item.get('type') == 'potion' and 'hp' in item.get('stats', {})]
        
        if not potions:
            await update_message(update, context,
                "❌ У тебя нет зелий!",
                reply_markup=get_hidden_mode_keyboard())
            return
        
        context.user_data['hide_belt_potions'] = potions
        
        await update_message(update, context,
            "🧪 **ПОЛОЖИТЬ ЗЕЛЬЕ В ПОЯС**\n\n"
            "Зелье в поясе можно использовать мгновенно в бою\n"
            "(не тратя ход на отбег).\n\n"
            f"🌑 Осталось скрытых ходов: {self.hidden_turns}",
            reply_markup=get_hide_belt_keyboard(potions),
            parse_mode='Markdown')
    
    async def hide_belt_confirm(self, update, context, potion_index: int):
        if not self.hidden:
            return
        
        potions = context.user_data.get('hide_belt_potions', [])
        if potion_index >= len(potions):
            await update_message(update, context, "❌ Зелье не найдено!")
            return
        
        potion = potions[potion_index]
        
        if 'belt' in self.player['inventory']['equipped']:
            old_potion = self.player['inventory']['equipped']['belt']
            self.player['inventory']['items'].append(old_potion)
        
        self.player['inventory']['equipped']['belt'] = potion
        self.player['inventory']['items'].remove(potion)
        self.player.save()
        
        self.battle_log.append({
            "turn": self.turn,
            "actor": "player",
            "action_type": "hide_belt",
            "potion": potion.get('name')
        })
        
        await update_message(update, context,
            f"✅ **{potion['name']} положено в пояс!**\n\n"
            f"Теперь ты можешь использовать это зелье мгновенно в бою.\n"
            f"🌑 Осталось скрытых ходов: {self.hidden_turns}",
            parse_mode='Markdown')
        
        await update_message(update, context,
            "🌑 **Что дальше?**",
            reply_markup=get_hidden_mode_keyboard())
    
    async def hide_cancel(self, update, context):
        if not self.hidden:
            return
        
        await update_message(update, context,
            f"🌑 Осталось скрытых ходов: {self.hidden_turns}",
            reply_markup=get_hidden_mode_keyboard())
    
    async def exit_hide(self, update, context):
        self.hidden = False
        
        self.battle_log.append({
            "turn": self.turn,
            "actor": "player",
            "action_type": "hide_exit"
        })
        
        await update_message(update, context,
            "🌑 **Ты выходишь из тени...**\n\n"
            f"👾 {self.enemy.name} замечает тебя!\n"
            f"_Враг выглядит растерянным..._",
            parse_mode='Markdown')
        
        self.turn += 1
        await self.update_battle_message(update, context)


# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================

async def start_battle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    player = Player(uid)
    
    if not player.get('race'):
        await update_message(update, context, "❌ Сначала создай персонажа через /start")
        return
    
    from hospital import hospital
    if hospital.is_in_hospital(uid):
        await update_message(update, context, "🏥 Ты в больнице! Сначала вылечись.")
        return
    
    if player.is_dead():
        remaining = player.get_death_remaining()
        minutes = remaining // 60
        seconds = remaining % 60
        await update_message(update, context, 
            f"💀 Ты ещё не восстановился после смерти!\n"
            f"⏳ Осталось: {minutes}:{seconds:02d}")
        return
    
    if uid in active_battles:
        await update_message(update, context, "⚔️ Ты уже в бою! Сначала закончи текущее сражение.")
        return
    
    await update_message(update, context, "🏃 Отправляюсь на охоту... 🔍")
    await asyncio.sleep(random.uniform(1.5, 2.5))
    
    enemy = get_random_enemy(player['level'])
    battle = BattleManager(uid, player, enemy)
    active_battles[uid] = battle
    
    logger.hunt_start(player['name'], enemy.name)
    await battle.update_battle_message(update, context)


@require_character
async def battle_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    uid = str(query.from_user.id)
    action = query.data
    
    if uid not in active_battles:
        await update_message(update, context, "❌ Битва уже закончена!")
        return
    
    battle = active_battles[uid]
    
    if battle.finished:
        await update_message(update, context, "❌ Битва уже закончена!")
        return
    
    if action == "battle_hide":
        await battle.try_hide(update, context)
        return
    
    if battle.hidden:
        if action == "hide_use_potion":
            await battle.hide_use_potion(update, context)
        elif action.startswith("hide_potion_"):
            idx = int(action.replace("hide_potion_", ""))
            await battle.hide_use_potion_confirm(update, context, idx)
        elif action == "hide_use_spell":
            await battle.hide_use_spell(update, context)
        elif action.startswith("hide_spell_"):
            idx = int(action.replace("hide_spell_", ""))
            await battle.hide_use_spell_confirm(update, context, idx)
        elif action == "hide_use_armor":
            await battle.hide_use_armor(update, context)
        elif action.startswith("hide_armor_buff_"):
            idx = int(action.replace("hide_armor_buff_", ""))
            await battle.hide_use_armor_confirm(update, context, idx)
        elif action.startswith("hide_change_"):
            item_type = action.replace("hide_change_", "")
            await battle.hide_change_item(update, context, item_type)
        elif action.startswith("hide_equip_"):
            parts = action.split("_")
            if len(parts) >= 4:
                item_type = parts[2]
                idx = int(parts[3])
                await battle.hide_change_item_confirm(update, context, item_type, idx)
        elif action == "hide_equip_spells":
            await battle.hide_equip_spells(update, context)
        elif action == "hide_belt":
            await battle.hide_belt(update, context)
        elif action.startswith("hide_belt_"):
            idx = int(action.replace("hide_belt_", ""))
            await battle.hide_belt_confirm(update, context, idx)
        elif action == "hide_cancel":
            await battle.hide_cancel(update, context)
        elif action == "hide_exit":
            await battle.exit_hide(update, context)
        return
    
    if action.startswith("battle_attack_"):
        body_part = action.replace("battle_attack_", "")
        await battle.player_attack(update, context, body_part)
    elif action == "battle_defend":
        await battle.defend(update, context)
    elif action == "battle_run":
        await battle.run(update, context)


@require_character
async def battle_save_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data in ["battle_save_yes", "battle_save_no"]:
        await show_main_screen(update, context)
    elif data == "battle_logging_disable":
        uid = str(query.from_user.id)
        player = Player(uid)
        player['battle_logging_enabled'] = False
        player.save()
        await show_main_screen(update, context)
