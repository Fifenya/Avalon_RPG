# smart_ai.py - УМНЫЙ ИИ ДЛЯ ВРАГОВ
# Вся техническая информация доступна только админам

import random
from enum import Enum
from typing import Dict, List
from collections import deque


class ActionType(Enum):
    """Типы действий врага"""
    ATTACK = "attack"
    HEAVY_ATTACK = "heavy_attack"
    DEFEND = "defend"
    HEAL = "heal"
    FLEE = "flee"
    BOSS_SKILL = "boss_skill"
    COUNTER = "counter"
    AIM_WEAK_POINT = "aim_weak_point"


class SmartEnemyAI:
    """Умный ИИ для врагов (адаптируется к стилю игрока)"""
    
    def __init__(self, enemy_id: str, player_id: str, enemy_name: str, 
                 base_power: int, base_hp: int, level: int):
        # Основные данные
        self.enemy_id = enemy_id
        self.player_id = player_id
        self.enemy_name = enemy_name
        self.base_power = base_power
        self.base_hp = base_hp
        self.level = level
        self.current_hp = base_hp
        self.turn_count = 0
        
        # Память о действиях игрока
        self.player_actions_history = deque(maxlen=10)
        self.consecutive_attacks = 0
        self.consecutive_defends = 0
        
        # Адаптивные параметры (для админов)
        self.aggression = 0.5
        self.counter_chance = 0.2
        
        # Q-learning для выбора действий
        self.q_values = {
            "attack": 1.0,
            "heavy_attack": 0.5,
            "defend": 0.5,
            "heal": 0.3
        }
        self.lr = 0.1
        self.gamma = 0.9
    
    def analyze_player(self, player_power: int, player_hp: int, player_max_hp: int,
                       player_armor: int, player_actions: List[Dict]) -> Dict:
        """Анализирует игрока и выбирает действие (игрок видит только описание)"""
        
        player_hp_pct = player_hp / player_max_hp if player_max_hp > 0 else 0.5
        enemy_hp_pct = self.current_hp / self.base_hp if self.base_hp > 0 else 0.5
        
        # Сохраняем последнее действие игрока
        if player_actions:
            last_action = player_actions[-1].get('action_type', '')
            if hasattr(last_action, 'value'):
                last_action = last_action.value
            
            self.player_actions_history.append(last_action)
            
            if last_action in ['attack', 'heavy_attack']:
                self.consecutive_attacks += 1
                self.consecutive_defends = 0
            elif last_action == 'defend':
                self.consecutive_defends += 1
                self.consecutive_attacks = 0
            else:
                self.consecutive_attacks = 0
                self.consecutive_defends = 0
        
        # Выбираем действие
        action = self._choose_action(player_hp_pct, enemy_hp_pct)
        
        self.turn_count += 1
        return action
    
    def _choose_action(self, player_hp_pct: float, enemy_hp_pct: float) -> Dict:
        """Выбирает действие на основе ситуации"""
        
        # Враг почти мёртв -> яростная атака
        if enemy_hp_pct < 0.2:
            return {
                "type": ActionType.HEAVY_ATTACK,
                "damage_mult": 1.8,
                "description": "яростно атакует!"
            }
        
        # Игрок часто защищается -> тяжёлая атака
        if self.consecutive_defends >= 2:
            return {
                "type": ActionType.HEAVY_ATTACK,
                "damage_mult": 1.5,
                "description": "наносит сокрушительный удар!"
            }
        
        # Игрок часто атакует -> контратака или защита
        if self.consecutive_attacks >= 2:
            if random.random() < self.counter_chance:
                return {
                    "type": ActionType.COUNTER,
                    "damage_mult": 1.3,
                    "description": "контратакует!"
                }
            else:
                return {
                    "type": ActionType.DEFEND,
                    "damage_mult": 0,
                    "description": "занимает оборону"
                }
        
        # У игрока мало здоровья -> агрессия
        if player_hp_pct < 0.25:
            return {
                "type": ActionType.HEAVY_ATTACK,
                "damage_mult": 1.5,
                "description": "пытается добить!"
            }
        
        # Лечение для боссов
        if self.level >= 10 and enemy_hp_pct < 0.35 and random.random() < 0.4:
            return {
                "type": ActionType.HEAL,
                "heal_amount": int(self.base_hp * 0.25),
                "description": "лечится!"
            }
        
        # Стандартная атака
        best_action = max(self.q_values, key=self.q_values.get)
        
        if best_action == "heavy_attack":
            return {
                "type": ActionType.HEAVY_ATTACK,
                "damage_mult": 1.5,
                "description": "наносит мощный удар!"
            }
        elif best_action == "defend":
            return {
                "type": ActionType.DEFEND,
                "damage_mult": 0,
                "description": "защищается"
            }
        elif best_action == "heal" and self.level >= 10:
            return {
                "type": ActionType.HEAL,
                "heal_amount": int(self.base_hp * 0.25),
                "description": "восстанавливает силы!"
            }
        else:
            return {
                "type": ActionType.ATTACK,
                "damage_mult": 1.0,
                "description": "атакует"
            }
    
    def update_after_action(self, action: Dict, damage_dealt: int, damage_taken: int,
                            player_action: Dict, success: bool):
        """Обновляет Q-значения (внутренняя механика)"""
        
        reward = 0
        action_type = action.get('type', ActionType.ATTACK)
        
        if success and damage_dealt > 0:
            reward += 10
            self.aggression = min(0.9, self.aggression + 0.03)
        elif damage_dealt == 0:
            reward -= 5
        
        if damage_taken > self.base_power:
            reward -= 8
            self.aggression = max(0.3, self.aggression - 0.05)
        
        # Обновляем Q-значение
        action_key = None
        if action_type == ActionType.ATTACK:
            action_key = "attack"
        elif action_type == ActionType.HEAVY_ATTACK:
            action_key = "heavy_attack"
        elif action_type == ActionType.DEFEND:
            action_key = "defend"
        elif action_type == ActionType.HEAL:
            action_key = "heal"
        
        if action_key and action_key in self.q_values:
            self.q_values[action_key] += self.lr * reward
        
        # Нормализуем Q-значения
        min_q = min(self.q_values.values())
        max_q = max(self.q_values.values())
        if max_q > min_q:
            for k in self.q_values:
                self.q_values[k] = (self.q_values[k] - min_q) / (max_q - min_q)
        
        # Адаптируем шанс контратаки
        if success and action_type == ActionType.COUNTER:
            self.counter_chance = min(0.5, self.counter_chance + 0.02)
    
    def record_battle_result(self, player_won: bool, battle_log: List[Dict]):
        """Записывает результат боя (для будущего обучения)"""
        pass
    
    def get_admin_report(self) -> str:
        """Возвращает технический отчёт ТОЛЬКО ДЛЯ АДМИНОВ"""
        return f"""
🤖 **SmartEnemyAI — {self.enemy_name}**
🎭 Текущая эмоция: {self._get_emotion_text()}
📊 Агрессивность: {self.aggression:.0%}
💥 Шанс контратаки: {self.counter_chance:.0%}
📈 Q-значения:
   • Обычная атака: {self.q_values.get('attack', 0):.2f}
   • Тяжёлая атака: {self.q_values.get('heavy_attack', 0):.2f}
   • Защита: {self.q_values.get('defend', 0):.2f}
   • Лечение: {self.q_values.get('heal', 0):.2f}
🎯 Здоровье: {self.current_hp}/{self.base_hp}
🎮 Раундов в бою: {self.turn_count}
📜 История действий игрока: {list(self.player_actions_history)[-5:]}
        """
    
    def _get_emotion_text(self) -> str:
        """Возвращает текст эмоции для админа"""
        if self.current_hp < self.base_hp * 0.2:
            return "Отчаян 😫"
        elif self.current_hp < self.base_hp * 0.4 and self.aggression < 0.4:
            return "Напуган 😨"
        elif self.aggression > 0.7:
            return "Разъярён 😤"
        elif self.aggression > 0.6:
            return "Агрессивен 😠"
        elif self.aggression < 0.4:
            return "Осторожен 🧐"
        else:
            return "Спокоен 😌"


class SmartEnemyManager:
    """Менеджер умных врагов"""
    
    def __init__(self):
        self.active_ais = {}
    
    def get_ai(self, enemy_id: str, player_id: str, enemy_name: str,
               base_power: int, base_hp: int, level: int) -> SmartEnemyAI:
        """Получает или создаёт ИИ для врага"""
        key = (enemy_id, player_id)
        if key not in self.active_ais:
            self.active_ais[key] = SmartEnemyAI(
                enemy_id, player_id, enemy_name, base_power, base_hp, level
            )
        return self.active_ais[key]
    
    def remove_ai(self, enemy_id: str, player_id: str):
        """Удаляет ИИ после боя"""
        key = (enemy_id, player_id)
        if key in self.active_ais:
            del self.active_ais[key]
    
    def get_all_admins_report(self) -> str:
        """Возвращает общий отчёт по всем ИИ (только для админов)"""
        if not self.active_ais:
            return "📊 Нет активных боевых ИИ в данный момент"
        
        report = "📊 **ГЛОБАЛЬНАЯ АНАЛИТИКА ИИ** (Только для админов)\n\n"
        for (eid, pid), ai in self.active_ais.items():
            report += f"👾 Противник: {ai.enemy_name}\n"
            report += f"🎮 Игрок: {pid}\n"
            report += ai.get_admin_report()
            report += "\n" + "=" * 40 + "\n"
        return report
    
    def get_player_ai_report(self, player_id: str) -> str:
        """Возвращает отчёт по ИИ для конкретного игрока (только для админов)"""
        result = f"📊 **Аналитика ИИ для игрока**\n\n"
        found = False
        for (eid, pid), ai in self.active_ais.items():
            if pid == player_id:
                result += f"👾 Противник: {ai.enemy_name}\n"
                result += ai.get_admin_report()
                result += "\n" + "=" * 40 + "\n"
                found = True
        
        if not found:
            return "📭 Нет активных боевых ИИ для этого игрока"
        return result


# Глобальный экземпляр
smart_enemy_manager = SmartEnemyManager()