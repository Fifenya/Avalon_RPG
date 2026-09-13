# ai_ollama.py — полная совместимость с battle.py (эмулирует ai_phone.py)
import requests
import json
import random
import time
from typing import Dict, Any, Optional, List
from enemy_personas import get_persona_for_enemy, get_system_prompt

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "qwen2.5:1.5b"
TIMEOUT = 15

# Маппинг действий на индексы (как в ai_phone.py)
ACTION_MAP = {
    'attack_head': 0,
    'attack_chest': 1,
    'attack_arms': 4,
    'attack_legs': 5,
    'attack_back': 4,  # fallback
    'defend': 2,
    'heal': 3,
    'flee': 6,
    'heavy_attack': 0,  # = attack_head по силе
    'hide': 1,
}

DAMAGE_MULT_MAP = {
    0: 1.5,  # head/heavy
    1: 1.0,  # chest/hide
    2: 0.0,  # defend
    3: 0.0,  # heal
    4: 0.8,  # arms
    5: 0.7,  # legs
    6: 0.0,  # flee
}


class OllamaAI:
    """Эмулирует интерфейс PhoneAI из ai_phone.py"""
    
    def __init__(self, player_id: str = None, enemy_id: str = None):
        self.player_id = player_id
        self.enemy_id = enemy_id
        self.battle_state = {}
        self.defending = False
        self.last_action = None
        self.action_history: List[int] = []
        self.rewards_history: List[float] = []
        self._persona = None
    
    def get_damage_mult(self, action_idx: int) -> float:
        return DAMAGE_MULT_MAP.get(action_idx, 1.0)
    
    def get_heal_amount(self, action_idx: int) -> int:
        return random.randint(15, 30) if action_idx == 3 else 0
    
    def get_flee_chance(self, action_idx: int) -> float:
        return 0.5 if action_idx == 6 else 0.0
    
    def update(self, state, action_idx, reward, next_state, done):
        """Метод для обратной связи (обучение) — просто логируем"""
        self.action_history.append(action_idx)
        self.rewards_history.append(reward)
        self.last_action = action_idx
    
    def record_result(self, player_won: bool):
        """Фиксируем результат боя"""
        print(f"📊 Бой завершён: победа игрока={player_won}, ходов={len(self.action_history)}")


class PhoneBattleState:
    """Заглушка для совместимости с _get_next_state"""
    @staticmethod
    def to_vector(player, enemy, turn, history=None):
        return {
            'player_hp': player.get('hp', 100),
            'player_max_hp': player.get('max_hp', 100),
            'enemy_hp': getattr(enemy, 'hp', 100),
            'enemy_max_hp': getattr(enemy, 'max_hp', 100),
            'turn': turn,
        }


class PhoneAI:
    """Глобальный синглтон — эмулирует phone_ai из ai_phone.py"""
    def record_battle(self, player_won: bool, turns: int):
        pass  # для Ollama не нужно
    
    def remove(self, enemy_name: str, uid: str):
        pass  # для Ollama не нужно


# Глобальный экземпляр (как phone_ai в ai_phone.py)
phone_ai = PhoneAI()

# Кэш агентов и решений
_agents_cache = {}
_action_cache = {}  # cache_key -> (action_tuple, turn)
_cache_turns = 5  # модель думает раз в N ходов


def _build_prompt(player: Dict, enemy, turn: int, persona: dict) -> str:
    """Компактный промпт (~150 токенов)"""
    enemy_hp = getattr(enemy, 'hp', 100)
    enemy_max = getattr(enemy, 'max_hp', 100)
    player_hp = player.get('hp', 100)
    player_max = player.get('max_hp', 100)
    
    if enemy_hp < enemy_max * 0.3:
        strategy = "HP низкое — защищайся, лечись или беги"
    elif player_hp < player_max * 0.3:
        strategy = "Игрок слаб — добей его!"
    else:
        strategy = "Балансируй атаку и защиту"
    
    return f"""Выбери одно действие.

HP: ты {enemy_hp}/{enemy_max}, игрок {player_hp}/{player_max}. Ход {turn}.
Стратегия: {strategy}

Действия: attack_head, attack_chest, attack_arms, attack_legs, defend, heal, flee, heavy_attack, hide.

Ответь ТОЛЬКО JSON: {{"action": "название"}}"""


def _request_ollama(prompt: str, persona: dict) -> str:
    """Запрос к Ollama с системным промптом"""
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "system": persona.get("system", ""),
                "stream": False,
                "options": {"temperature": 0.7, "top_p": 0.9},
            },
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
    except Exception as e:
        print(f"⚠️ Ollama ошибка: {e}")
        return ""


def _parse_action(response_text: str) -> str:
    """Извлекает action из ответа"""
    if not response_text:
        return "attack_chest"
    try:
        s = response_text.find("{")
        e = response_text.rfind("}") + 1
        if s != -1 and e > s:
            data = json.loads(response_text[s:e])
            return data.get("action", "attack_chest")
    except Exception:
        pass
    # Фолбэк по ключевым словам
    low = response_text.lower()
    if "defend" in low or "защит" in low: return "defend"
    if "heal" in low or "леч" in low: return "heal"
    if "flee" in low or "беж" in low: return "flee"
    if "heavy" in low or "тяжёл" in low: return "heavy_attack"
    if "head" in low or "голов" in low: return "attack_head"
    if "hide" in low or "скры" in low: return "hide"
    return "attack_chest"


def _action_to_tuple(action_name: str, enemy_hp_pct: float) -> tuple:
    """Преобразует action в (agent, action_idx, action_info, state)"""
    idx = ACTION_MAP.get(action_name, 1)
    mult = DAMAGE_MULT_MAP.get(idx, 1.0)
    
    desc_map = {
        'attack_head': 'атакует в голову!',
        'attack_chest': 'атакует в грудь!',
        'attack_arms': 'атакует по рукам!',
        'attack_legs': 'атакует по ногам!',
        'attack_back': 'атакует в спину!',
        'defend': 'занимает оборону!',
        'heal': 'лечит свои раны!',
        'flee': 'пытается сбежать!',
        'heavy_attack': 'наносит сокрушительный удар!',
        'hide': 'скрывается в тени!',
    }
    
    action_info = {
        'name': action_name,
        'action': action_name,
        'desc': desc_map.get(action_name, 'атакует'),
        'description': desc_map.get(action_name, 'атакует'),
        'body_part': action_name.replace('attack_', '') if action_name.startswith('attack_') else None,
        'damage_mult': mult,
    }
    return action_name, idx, action_info, {}


def get_phone_ai_action(player: Dict, enemy, turn: int):
    """Главная точка входа — сигнатура как в battle.py"""
    uid = str(player.get('id', player.get('uid', 'unknown')))
    enemy_name = getattr(enemy, 'name', 'enemy').replace(' ', '_')
    cache_key = f"{uid}_{enemy_name}"
    
    # Получаем/создаём агента
    if cache_key not in _agents_cache:
        _agents_cache[cache_key] = OllamaAI(uid, enemy_name)
        _agents_cache[cache_key]._persona = get_persona_for_enemy(
            enemy_name, getattr(enemy, 'level', 1)
        )
    agent = _agents_cache[cache_key]
    persona = agent._persona or get_persona_for_enemy(enemy_name, 1)
    
    enemy_hp = getattr(enemy, 'hp', 100)
    enemy_max = getattr(enemy, 'max_hp', 100)
    enemy_hp_pct = enemy_hp / enemy_max if enemy_max > 0 else 1.0
    
    state = {
        'enemy_hp': enemy_hp,
        'enemy_max_hp': enemy_max,
        'player_hp': player.get('hp', 100),
        'player_max_hp': player.get('max_hp', 100),
        'enemy_level': getattr(enemy, 'level', 1),
        'turn': turn,
    }
    
    # Проверяем кэш
    if cache_key in _action_cache:
        cached_tuple, cached_turn = _action_cache[cache_key]
        if turn - cached_turn < _cache_turns:
            print(f"⚡ Ollama кэш: {cached_tuple[0]} (ход {turn})")
            return agent, cached_tuple[1], cached_tuple[2], state
    
    # Запрашиваем модель
    t0 = time.time()
    print(f"🎭 Персона: {persona['name']}")
    prompt = _build_prompt(player, enemy, turn, persona)
    response_text = _request_ollama(prompt, persona)
    action_name = _parse_action(response_text)
    
    duration = time.time() - t0
    print(f"🧠 Ollama: {action_name} ({duration:.1f}сек)")
    
    # Преобразуем в кортеж
    action_tuple = _action_to_tuple(action_name, enemy_hp_pct)
    _action_cache[cache_key] = (action_tuple, turn)
    
    return agent, action_tuple[1], action_tuple[2], state


# Алиас для совместимости
get_phone_ai_action_compat = get_phone_ai_action
