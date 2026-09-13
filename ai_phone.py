# ai_phone.py - ПОЛНАЯ ВЕРСИЯ С НЕЙРОННОЙ СЕТЬЮ ДЛЯ БОЕВ

import random
import json
import os
from typing import Dict, List, Optional, Tuple
from collections import deque
import numpy as np

# ===== НАСТРОЙКИ НЕЙРОННОЙ СЕТИ =====
LEARNING_RATE = 0.01
DISCOUNT_FACTOR = 0.95
EXPLORATION_RATE = 0.1
MEMORY_SIZE = 1000
BATCH_SIZE = 32
MIN_EXPERIENCES = 100

# ===== ДЕЙСТВИЯ =====
ACTIONS = [
    "attack_head",
    "attack_chest", 
    "attack_arms",
    "attack_legs",
    "attack_back",
    "defend",
    "heavy_attack",
    "hide",
    "flee"
]

ACTION_NAMES = {
    "attack_head": "⚔️ Удар в голову",
    "attack_chest": "⚔️ Удар в грудь",
    "attack_arms": "⚔️ Удар по рукам",
    "attack_legs": "⚔️ Удар по ногам",
    "attack_back": "⚔️ Удар в спину",
    "defend": "🛡️ Защита",
    "heavy_attack": "💥 Тяжёлый удар",
    "hide": "🌑 Скрыться",
    "flee": "🏃 Сбежать"
}

# ===== НЕЙРОННАЯ СЕТЬ =====
class NeuralNetwork:
    """Простая нейронная сеть для обучения с подкреплением"""
    
    def __init__(self, input_size: int, hidden_size: int, output_size: int):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        
        # Инициализация весов (Xavier)
        self.w1 = np.random.randn(input_size, hidden_size) * np.sqrt(2.0 / input_size)
        self.b1 = np.zeros((1, hidden_size))
        self.w2 = np.random.randn(hidden_size, output_size) * np.sqrt(2.0 / hidden_size)
        self.b2 = np.zeros((1, output_size))
        
        self.lr = LEARNING_RATE
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """Прямой проход"""
        self.z1 = np.dot(x, self.w1) + self.b1
        self.a1 = self._relu(self.z1)
        self.z2 = np.dot(self.a1, self.w2) + self.b2
        self.a2 = self._softmax(self.z2)
        return self.a2
    
    def backward(self, x: np.ndarray, target: np.ndarray):
        """Обратный проход"""
        m = x.shape[0]
        
        # Градиенты для выходного слоя
        dz2 = (self.a2 - target) / m
        dw2 = np.dot(self.a1.T, dz2)
        db2 = np.sum(dz2, axis=0, keepdims=True)
        
        # Градиенты для скрытого слоя
        da1 = np.dot(dz2, self.w2.T)
        dz1 = da1 * self._relu_derivative(self.z1)
        dw1 = np.dot(x.T, dz1)
        db1 = np.sum(dz1, axis=0, keepdims=True)
        
        # Обновление весов
        self.w2 -= self.lr * dw2
        self.b2 -= self.lr * db2
        self.w1 -= self.lr * dw1
        self.b1 -= self.lr * db1
    
    def _relu(self, x: np.ndarray) -> np.ndarray:
        return np.maximum(0, x)
    
    def _relu_derivative(self, x: np.ndarray) -> np.ndarray:
        return (x > 0).astype(float)
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        exp_x = np.exp(x - np.max(x, axis=1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=1, keepdims=True)
    
    def predict(self, state: np.ndarray) -> np.ndarray:
        """Предсказание Q-значений"""
        return self.forward(state)
    
    def train(self, states: np.ndarray, targets: np.ndarray):
        """Обучение на батче"""
        if len(states) == 0:
            return
        self.forward(states)
        self.backward(states, targets)
    
    def save(self, path: str):
        """Сохраняет веса"""
        weights = {
            'w1': self.w1.tolist(),
            'b1': self.b1.tolist(),
            'w2': self.w2.tolist(),
            'b2': self.b2.tolist()
        }
        with open(path, 'w') as f:
            json.dump(weights, f)
    
    def load(self, path: str):
        """Загружает веса"""
        if os.path.exists(path):
            with open(path, 'r') as f:
                weights = json.load(f)
            self.w1 = np.array(weights['w1'])
            self.b1 = np.array(weights['b1'])
            self.w2 = np.array(weights['w2'])
            self.b2 = np.array(weights['b2'])
            return True
        return False


# ===== ОПЫТ =====
class Experience:
    """Опыт для обучения"""
    def __init__(self, state, action, reward, next_state, done):
        self.state = state
        self.action = action
        self.reward = reward
        self.next_state = next_state
        self.done = done


# ===== ПАМЯТЬ =====
class ReplayMemory:
    """Буфер воспроизведения"""
    def __init__(self, capacity: int = MEMORY_SIZE):
        self.capacity = capacity
        self.memory = deque(maxlen=capacity)
    
    def push(self, experience: Experience):
        self.memory.append(experience)
    
    def sample(self, batch_size: int) -> List[Experience]:
        if len(self.memory) < batch_size:
            return list(self.memory)
        return random.sample(self.memory, batch_size)
    
    def __len__(self):
        return len(self.memory)


# ===== УМНЫЙ АГЕНТ =====
class PhoneAI:
    """Нейронная сеть для управления боем"""
    
    def __init__(self, player_id: str = None, enemy_id: str = None):
        self.player_id = player_id or "default"
        self.enemy_id = enemy_id or "default"
        
        # Размеры сети
        self.state_size = 12  # HP%, EnemyHP%, Power, EnemyPower, Armor, EnemyArmor, 
                             # Turn, CritChance, DodgeChance, PlayerLevel, EnemyLevel, LastAction
        
        self.hidden_size = 64
        self.action_size = len(ACTIONS)
        
        # Создаём сеть
        self.model = NeuralNetwork(self.state_size, self.hidden_size, self.action_size)
        
        # Память
        self.memory = ReplayMemory()
        
        # Текущее состояние
        self.last_state = None
        self.last_action = None
        self.last_action_idx = None
        
        # Статистика
        self.total_actions = 0
        self.successful_actions = 0
        self.rewards_history = []
        
        # Загрузка сохранённой модели
        self.load_model()
        
        # Состояние боя
        self.battle_state = {
            'player_hp': 100,
            'player_max_hp': 100,
            'enemy_hp': 100,
            'enemy_max_hp': 100,
            'player_power': 50,
            'enemy_power': 30,
            'player_armor': 0,
            'enemy_armor': 0,
            'turn': 0,
            'crit_chance': 0.1,
            'dodge_chance': 0.05,
            'player_level': 1,
            'enemy_level': 1,
            'last_action': 0  # индекс последнего действия
        }
    
    def get_model_path(self) -> str:
        """Путь к файлу модели"""
        return f"ai_models/ai_{self.player_id}_{self.enemy_id}.json"
    
    def load_model(self):
        """Загружает сохранённую модель"""
        path = self.get_model_path()
        if self.model.load(path):
            print(f"🧠 Загружена модель для {self.player_id} vs {self.enemy_id}")
            return True
        return False
    
    def save_model(self):
        """Сохраняет модель"""
        os.makedirs("ai_models", exist_ok=True)
        path = self.get_model_path()
        self.model.save(path)
    
    def get_state_vector(self) -> np.ndarray:
        """Преобразует состояние боя в вектор"""
        state = self.battle_state
        
        # Нормализуем значения
        hp_pct = state['player_hp'] / max(1, state['player_max_hp'])
        enemy_hp_pct = state['enemy_hp'] / max(1, state['enemy_max_hp'])
        power_norm = state['player_power'] / max(1, state['enemy_power'] + state['player_power'])
        enemy_power_norm = state['enemy_power'] / max(1, state['enemy_power'] + state['player_power'])
        armor_norm = state['player_armor'] / 50.0
        enemy_armor_norm = state['enemy_armor'] / 50.0
        turn_norm = min(1.0, state['turn'] / 20.0)
        
        return np.array([[
            hp_pct,
            enemy_hp_pct,
            power_norm,
            enemy_power_norm,
            armor_norm,
            enemy_armor_norm,
            turn_norm,
            state['crit_chance'],
            state['dodge_chance'],
            state['player_level'] / 50.0,
            state['enemy_level'] / 50.0,
            state['last_action'] / self.action_size
        ]])
    
    def get_action(self, state: Dict = None) -> Dict:
        """Выбирает действие на основе текущего состояния"""
        if state:
            self.battle_state.update(state)
        
        # Увеличиваем счётчик ходов
        self.battle_state['turn'] += 1
        
        # Получаем вектор состояния
        state_vector = self.get_state_vector()
        
        # Exploration vs Exploitation
        if random.random() < EXPLORATION_RATE:
            # Случайное действие
            action_idx = random.randint(0, self.action_size - 1)
        else:
            # Используем нейросеть
            q_values = self.model.predict(state_vector)
            action_idx = np.argmax(q_values[0])
        
        # Сохраняем состояние для обучения
        self.last_state = state_vector
        self.last_action_idx = action_idx
        self.last_action = ACTIONS[action_idx]
        
        # Формируем ответ
        action_name = ACTIONS[action_idx]
        result = self._action_to_result(action_name)
        
        return result
    
    def _action_to_result(self, action_name: str) -> Dict:
        """Преобразует название действия в результат"""
        result = {
            "action": action_name,
            "body_part": None,
            "damage_mult": 1.0,
            "description": ACTION_NAMES.get(action_name, "атакует")
        }
        
        # Парсим действие
        if action_name.startswith("attack_"):
            body_part = action_name.replace("attack_", "")
            result["body_part"] = body_part
            result["damage_mult"] = 1.0
            
            # Бонусы для разных частей тела
            bonuses = {
                "head": {"damage_mult": 1.5, "crit_bonus": 0.2},
                "chest": {"damage_mult": 1.0, "crit_bonus": 0.0},
                "arms": {"damage_mult": 0.8, "crit_bonus": 0.1},
                "legs": {"damage_mult": 0.7, "crit_bonus": 0.1},
                "back": {"damage_mult": 1.3, "crit_bonus": 0.3}
            }
            
            if body_part in bonuses:
                bonus = bonuses[body_part]
                result["damage_mult"] = bonus["damage_mult"]
                result["crit_bonus"] = bonus["crit_bonus"]
            
            result["description"] = f"⚔️ Атакует {body_part}!"
            
        elif action_name == "defend":
            result["damage_mult"] = 0.0
            result["description"] = "🛡️ Занимает оборону!"
            result["defense_bonus"] = 0.5
            
        elif action_name == "heavy_attack":
            result["damage_mult"] = 1.8
            result["description"] = "💥 Наносит сокрушительный удар!"
            result["crit_bonus"] = 0.3
            
        elif action_name == "hide":
            result["damage_mult"] = 0.0
            result["description"] = "🌑 Скрывается в тени!"
            result["hide"] = True
            
        elif action_name == "flee":
            result["damage_mult"] = 0.0
            result["description"] = "🏃 Пытается сбежать!"
            result["flee"] = True
        
        return result
    
    def update(self, reward: float, done: bool, next_state: Dict = None):
        """Обновляет модель на основе полученной награды"""
        if self.last_state is None or self.last_action_idx is None:
            return
        
        self.total_actions += 1
        if reward > 0:
            self.successful_actions += 1
        
        # Сохраняем награду
        self.rewards_history.append(reward)
        if len(self.rewards_history) > 100:
            self.rewards_history = self.rewards_history[-100:]
        
        # Подготавливаем следующее состояние
        if next_state:
            self.battle_state.update(next_state)
        
        next_state_vector = self.get_state_vector() if next_state else self.last_state
        
        # Сохраняем опыт
        experience = Experience(
            self.last_state,
            self.last_action_idx,
            reward,
            next_state_vector,
            done
        )
        self.memory.push(experience)
        
        # Обучаемся
        if len(self.memory) >= MIN_EXPERIENCES:
            self._learn()
        
        # Сохраняем модель если бой закончился
        if done:
            self.save_model()
    
    def _learn(self):
        """Обучение на батче из памяти"""
        batch = self.memory.sample(BATCH_SIZE)
        if len(batch) < BATCH_SIZE:
            return
        
        # Формируем батчи
        states = np.vstack([e.state for e in batch])
        actions = np.array([e.action for e in batch])
        rewards = np.array([e.reward for e in batch])
        next_states = np.vstack([e.next_state for e in batch])
        dones = np.array([e.done for e in batch])
        
        # Предсказываем Q-значения
        current_q = self.model.predict(states)
        next_q = self.model.predict(next_states)
        
        # Вычисляем цели
        targets = current_q.copy()
        for i in range(len(batch)):
            if dones[i]:
                targets[i, actions[i]] = rewards[i]
            else:
                targets[i, actions[i]] = rewards[i] + DISCOUNT_FACTOR * np.max(next_q[i])
        
        # Обучаем
        self.model.train(states, targets)
    
    def get_stats(self) -> Dict:
        """Возвращает статистику работы"""
        success_rate = self.successful_actions / max(1, self.total_actions)
        avg_reward = sum(self.rewards_history) / max(1, len(self.rewards_history))
        memory_size = len(self.memory)
        
        return {
            "total_actions": self.total_actions,
            "successful_actions": self.successful_actions,
            "success_rate": success_rate,
            "avg_reward": avg_reward,
            "memory_size": memory_size,
            "model_saved": os.path.exists(self.get_model_path())
        }


# ===== ГЛОБАЛЬНЫЙ КЭШ АГЕНТОВ =====
_ai_agents_cache = {}


def get_phone_ai_action(state: Dict, player_id: str = None, enemy_id: str = None) -> Dict:
    """
    Основная функция для получения действия от нейронной сети
    
    Args:
        state: словарь с состоянием боя
        player_id: ID игрока
        enemy_id: ID врага
    
    Returns:
        словарь с действием
    """
    # Создаём ключ для кэша
    cache_key = f"{player_id}_{enemy_id}" if player_id and enemy_id else "default"
    
    # Получаем или создаём агента
    if cache_key not in _ai_agents_cache:
        _ai_agents_cache[cache_key] = PhoneAI(player_id, enemy_id)
    
    agent = _ai_agents_cache[cache_key]
    
    # Обновляем состояние
    agent.battle_state.update({
        'player_hp': state.get('player_hp', 100),
        'player_max_hp': state.get('player_max_hp', 100),
        'enemy_hp': state.get('enemy_hp', 100),
        'enemy_max_hp': state.get('enemy_max_hp', 100),
        'player_power': state.get('player_power', 50),
        'enemy_power': state.get('enemy_power', 30),
        'player_armor': state.get('player_armor', 0),
        'enemy_armor': state.get('enemy_armor', 0),
        'turn': state.get('turn', 0),
        'crit_chance': state.get('crit_chance', 0.1),
        'dodge_chance': state.get('dodge_chance', 0.05),
        'player_level': state.get('player_level', 1),
        'enemy_level': state.get('enemy_level', 1),
        'last_action': state.get('last_action', 0)
    })
    
    # Получаем действие
    action = agent.get_action()
    
    return action


def phone_ai_update(reward: float, done: bool, next_state: Dict = None, 
                    player_id: str = None, enemy_id: str = None):
    """
    Обновляет модель после получения награды
    
    Args:
        reward: полученная награда
        done: закончен ли бой
        next_state: следующее состояние
        player_id: ID игрока
        enemy_id: ID врага
    """
    cache_key = f"{player_id}_{enemy_id}" if player_id and enemy_id else "default"
    
    if cache_key in _ai_agents_cache:
        agent = _ai_agents_cache[cache_key]
        agent.update(reward, done, next_state)


def get_ai_stats(player_id: str = None, enemy_id: str = None) -> Dict:
    """Возвращает статистику работы нейронной сети"""
    cache_key = f"{player_id}_{enemy_id}" if player_id and enemy_id else "default"
    
    if cache_key in _ai_agents_cache:
        return _ai_agents_cache[cache_key].get_stats()
    
    return {
        "total_actions": 0,
        "successful_actions": 0,
        "success_rate": 0.0,
        "avg_reward": 0.0,
        "memory_size": 0,
        "model_saved": False
    }


def reset_ai(player_id: str = None, enemy_id: str = None):
    """Сбрасывает обучение для игрока/врага"""
    cache_key = f"{player_id}_{enemy_id}" if player_id and enemy_id else "default"
    
    if cache_key in _ai_agents_cache:
        del _ai_agents_cache[cache_key]
        # Удаляем файл модели
        model_path = f"ai_models/ai_{player_id}_{enemy_id}.json"
        if os.path.exists(model_path):
            os.remove(model_path)
        return True
    
    return False


def plot_learning(enemy_id: str, player_id: str) -> str:
    """
    Создаёт график обучения (для админов)
    """
    try:
        import matplotlib.pyplot as plt
        
        cache_key = f"{player_id}_{enemy_id}"
        if cache_key not in _ai_agents_cache:
            return "Нет данных для этого врага/игрока"
        
        agent = _ai_agents_cache[cache_key]
        rewards = agent.rewards_history
        
        if not rewards:
            return "Нет истории наград"
        
        plt.figure(figsize=(10, 6))
        plt.plot(rewards, label='Reward', alpha=0.7)
        plt.xlabel('Действие')
        plt.ylabel('Награда')
        plt.title(f'Обучение {enemy_id} vs {player_id}')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        os.makedirs("graphs", exist_ok=True)
        path = f"graphs/ai_{enemy_id}_{player_id}.png"
        plt.savefig(path)
        plt.close()
        
        return path
        
    except ImportError:
        return "Для графиков нужен matplotlib: pip install matplotlib"
    except Exception as e:
        return f"Ошибка создания графика: {e}"

# ===== ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР ДЛЯ ОБРАТНОЙ СОВМЕСТИМОСТИ =====
phone_ai = PhoneAI("default", "default")

# ===== ТЕСТОВАЯ ФУНКЦИЯ =====
def test_ai():
    """Тестирование нейронной сети"""
    print("🧠 Тестирование нейронной сети...")
    
    # Создаём тестовое состояние
    state = {
        'player_hp': 80,
        'player_max_hp': 100,
        'enemy_hp': 60,
        'enemy_max_hp': 100,
        'player_power': 50,
        'enemy_power': 40,
        'player_armor': 5,
        'enemy_armor': 3,
        'turn': 5,
        'crit_chance': 0.15,
        'dodge_chance': 0.08,
        'player_level': 3,
        'enemy_level': 2,
        'last_action': 0
    }
    
    # Получаем действие
    action = get_phone_ai_action(state, "test_player", "test_enemy")
    print(f"📊 Действие: {action}")
    
    # Обновляем с наградой
    phone_ai_update(10.0, False, None, "test_player", "test_enemy")
    
    stats = get_ai_stats("test_player", "test_enemy")
    print(f"📊 Статистика: {stats}")
    
    return "✅ Тест пройден"


if __name__ == "__main__":
    print(test_ai())