# rank_system.py
from enum import Enum
from typing import Dict, Tuple, Optional

class Rank(Enum):
    G = "G"
    F = "F"
    E = "E"
    D = "D"
    C = "C"
    B = "B"
    A = "A"
    S = "S"
    S_PLUS = "S+"
    SS = "SS"
    SS_PLUS = "SS+"
    SSR = "SSR"
    SSR_PLUS = "SSR+"
    
    def __str__(self):
        return self.value


# Данные рангов для игроков
RANK_DATA = {
    Rank.G: {
        "name": "Мусор",
        "emoji": "💩",
        "color": "⚪",
        "power_min": 0,
        "power_max": 49,
        "reward_mult": 0.5,
        "exp_mult": 0.5,
        "drop_mult": 0.5,
        "title": "Отброс"
    },
    Rank.F: {
        "name": "Новичок",
        "emoji": "🌱",
        "color": "🟢",
        "power_min": 50,
        "power_max": 99,
        "reward_mult": 0.7,
        "exp_mult": 0.7,
        "drop_mult": 0.7,
        "title": "Зелёный новичок"
    },
    Rank.E: {
        "name": "Ученик",
        "emoji": "📘",
        "color": "🔵",
        "power_min": 100,
        "power_max": 199,
        "reward_mult": 0.9,
        "exp_mult": 0.9,
        "drop_mult": 0.9,
        "title": "Ученик"
    },
    Rank.D: {
        "name": "Воин",
        "emoji": "💜",
        "color": "🟣",
        "power_min": 200,
        "power_max": 349,
        "reward_mult": 1.0,
        "exp_mult": 1.0,
        "drop_mult": 1.0,
        "title": "Опытный воин"
    },
    Rank.C: {
        "name": "Ветеран",
        "emoji": "🔶",
        "color": "🟠",
        "power_min": 350,
        "power_max": 549,
        "reward_mult": 1.2,
        "exp_mult": 1.2,
        "drop_mult": 1.1,
        "title": "Ветеран"
    },
    Rank.B: {
        "name": "Герой",
        "emoji": "🔴",
        "color": "🔴",
        "power_min": 550,
        "power_max": 799,
        "reward_mult": 1.5,
        "exp_mult": 1.5,
        "drop_mult": 1.3,
        "title": "Народный герой"
    },
    Rank.A: {
        "name": "Легенда",
        "emoji": "⭐",
        "color": "🟡",
        "power_min": 800,
        "power_max": 1099,
        "reward_mult": 2.0,
        "exp_mult": 2.0,
        "drop_mult": 1.6,
        "title": "Живая легенда"
    },
    Rank.S: {
        "name": "Мифический",
        "emoji": "💎",
        "color": "✨",
        "power_min": 1100,
        "power_max": 1499,
        "reward_mult": 3.0,
        "exp_mult": 3.0,
        "drop_mult": 2.0,
        "title": "Мифический герой"
    },
    Rank.S_PLUS: {
        "name": "Сияющий",
        "emoji": "👑",
        "color": "🌟",
        "power_min": 1500,
        "power_max": 1999,
        "reward_mult": 4.0,
        "exp_mult": 4.0,
        "drop_mult": 2.5,
        "title": "Сияющий властелин"
    },
    Rank.SS: {
        "name": "Мифический+",
        "emoji": "🏆",
        "color": "💫",
        "power_min": 2000,
        "power_max": 2999,
        "reward_mult": 5.0,
        "exp_mult": 5.0,
        "drop_mult": 3.0,
        "title": "Мифический император"
    },
    Rank.SS_PLUS: {
        "name": "Легендарный",
        "emoji": "🔥",
        "color": "🔥",
        "power_min": 3000,
        "power_max": 4499,
        "reward_mult": 7.0,
        "exp_mult": 7.0,
        "drop_mult": 4.0,
        "title": "Легендарный владыка"
    },
    Rank.SSR: {
        "name": "Божественный",
        "emoji": "⚡",
        "color": "⚡",
        "power_min": 4500,
        "power_max": 6999,
        "reward_mult": 10.0,
        "exp_mult": 10.0,
        "drop_mult": 5.0,
        "title": "Божественный аватар"
    },
    Rank.SSR_PLUS: {
        "name": "Абсолют",
        "emoji": "🌌",
        "color": "🌌",
        "power_min": 7000,
        "power_max": 999999,
        "reward_mult": 15.0,
        "exp_mult": 15.0,
        "drop_mult": 7.0,
        "title": "Абсолютный бог"
    }
}


# Данные рангов для предметов
ITEM_RANKS = {
    "G": {"name": "Мусор", "emoji": "💩", "color": "⚪", "multiplier": 0.5, "upgrade_chance": 0.9},
    "F": {"name": "Обычный", "emoji": "🌱", "color": "🟢", "multiplier": 0.7, "upgrade_chance": 0.8},
    "E": {"name": "Необычный", "emoji": "📘", "color": "🔵", "multiplier": 0.9, "upgrade_chance": 0.7},
    "D": {"name": "Редкий", "emoji": "💜", "color": "🟣", "multiplier": 1.0, "upgrade_chance": 0.6},
    "C": {"name": "Эпический", "emoji": "🔶", "color": "🟠", "multiplier": 1.2, "upgrade_chance": 0.5},
    "B": {"name": "Уникальный", "emoji": "🔴", "color": "🔴", "multiplier": 1.5, "upgrade_chance": 0.4},
    "A": {"name": "Легендарный", "emoji": "⭐", "color": "🟡", "multiplier": 2.0, "upgrade_chance": 0.3},
    "S": {"name": "Мифический", "emoji": "💎", "color": "✨", "multiplier": 3.0, "upgrade_chance": 0.2},
    "S+": {"name": "Сияющий", "emoji": "👑", "color": "🌟", "multiplier": 4.0, "upgrade_chance": 0.15},
    "SS": {"name": "Мифический+", "emoji": "🏆", "color": "💫", "multiplier": 5.0, "upgrade_chance": 0.1},
    "SS+": {"name": "Легендарный+", "emoji": "🔥", "color": "🔥", "multiplier": 7.0, "upgrade_chance": 0.08},
    "SSR": {"name": "Божественный", "emoji": "⚡", "color": "⚡", "multiplier": 10.0, "upgrade_chance": 0.05},
    "SSR+": {"name": "Абсолют", "emoji": "🌌", "color": "🌌", "multiplier": 15.0, "upgrade_chance": 0.02}
}


# Данные рангов для монстров
MONSTER_RANKS = {
    "G": {"min_level": 1, "max_level": 5, "emoji": "💩", "color": "⚪", "reward_mult": 0.5},
    "F": {"min_level": 6, "max_level": 10, "emoji": "🌱", "color": "🟢", "reward_mult": 0.7},
    "E": {"min_level": 11, "max_level": 15, "emoji": "📘", "color": "🔵", "reward_mult": 0.9},
    "D": {"min_level": 16, "max_level": 20, "emoji": "💜", "color": "🟣", "reward_mult": 1.0},
    "C": {"min_level": 21, "max_level": 25, "emoji": "🔶", "color": "🟠", "reward_mult": 1.2},
    "B": {"min_level": 26, "max_level": 30, "emoji": "🔴", "color": "🔴", "reward_mult": 1.5},
    "A": {"min_level": 31, "max_level": 35, "emoji": "⭐", "color": "🟡", "reward_mult": 2.0},
    "S": {"min_level": 36, "max_level": 40, "emoji": "💎", "color": "✨", "reward_mult": 3.0},
    "S+": {"min_level": 41, "max_level": 45, "emoji": "👑", "color": "🌟", "reward_mult": 4.0},
    "SS": {"min_level": 46, "max_level": 50, "emoji": "🏆", "color": "💫", "reward_mult": 5.0},
    "SS+": {"min_level": 51, "max_level": 55, "emoji": "🔥", "color": "🔥", "reward_mult": 7.0},
    "SSR": {"min_level": 56, "max_level": 60, "emoji": "⚡", "color": "⚡", "reward_mult": 10.0},
    "SSR+": {"min_level": 61, "max_level": 999, "emoji": "🌌", "color": "🌌", "reward_mult": 15.0}
}


class RankSystem:
    @staticmethod
    def get_player_rank(power: int) -> Tuple[Rank, Dict]:
        """Получить ранг игрока по силе"""
        for rank, data in RANK_DATA.items():
            if data["power_min"] <= power <= data["power_max"]:
                return rank, data
        return Rank.G, RANK_DATA[Rank.G]
    
    @staticmethod
    def get_item_rank(rank_key: str) -> Dict:
        """Получить данные ранга предмета"""
        return ITEM_RANKS.get(rank_key, ITEM_RANKS["G"])
    
    @staticmethod
    def get_monster_rank(level: int) -> Tuple[str, Dict]:
        """Получить ранг монстра по уровню"""
        for rank_key, data in MONSTER_RANKS.items():
            if data["min_level"] <= level <= data["max_level"]:
                return rank_key, data
        return "G", MONSTER_RANKS["G"]
    
    @staticmethod
    def calculate_reward_with_rank(base_reward: int, player_power: int, monster_level: int) -> int:
        """Рассчитать награду с учётом рангов"""
        player_rank, player_data = RankSystem.get_player_rank(player_power)
        monster_rank, monster_data = RankSystem.get_monster_rank(monster_level)
        
        multiplier = player_data["reward_mult"]
        
        rank_order = list(RANK_DATA.keys())
        player_idx = rank_order.index(player_rank)
        monster_idx = rank_order.index(Rank(monster_rank))
        
        rank_diff = player_idx - monster_idx
        if rank_diff > 0:
            multiplier *= (1 + rank_diff * 0.1)
        elif rank_diff < 0:
            multiplier *= max(0.3, 1 + rank_diff * 0.05)
        
        return int(base_reward * multiplier)
    
    @staticmethod
    def format_player_rank(power: int) -> str:
        """Форматирует ранг игрока: ⚪ Ранг: G"""
        rank, data = RankSystem.get_player_rank(power)
        return f"{data['color']} Ранг: {rank}"
    
    @staticmethod
    def format_item_rank(rank_key: str) -> str:
        """Форматирует ранг предмета: F 🌱"""
        data = ITEM_RANKS.get(rank_key, ITEM_RANKS["G"])
        return f"{rank_key} {data['emoji']}"
    
    @staticmethod
    def format_monster_rank(level: int) -> str:
        """Форматирует ранг монстра: G 💩"""
        rank_key, data = RankSystem.get_monster_rank(level)
        return f"{rank_key} {data['emoji']}"
    
    @staticmethod
    def upgrade_item_rank(current_rank: str) -> Tuple[bool, str, int]:
        """Попытка улучшить ранг предмета"""
        rank_order = ["G", "F", "E", "D", "C", "B", "A", "S", "S+", "SS", "SS+", "SSR", "SSR+"]
        
        if current_rank not in rank_order:
            return False, current_rank, 0
        
        current_idx = rank_order.index(current_rank)
        if current_idx + 1 >= len(rank_order):
            return False, current_rank, 0
        
        next_rank = rank_order[current_idx + 1]
        chance = ITEM_RANKS[current_rank]["upgrade_chance"]
        
        import random
        if random.random() < chance:
            return True, next_rank, int(chance * 100)
        return False, current_rank, int(chance * 100)
    
    @staticmethod
    def get_next_rank_info(power: int) -> Optional[Dict]:
        """Получить информацию о следующем ранге"""
        current_rank, _ = RankSystem.get_player_rank(power)
        rank_order = list(RANK_DATA.keys())
        current_idx = rank_order.index(current_rank)
        
        if current_idx + 1 < len(rank_order):
            next_rank = rank_order[current_idx + 1]
            next_data = RANK_DATA[next_rank]
            return {
                "rank": next_rank,
                "power_needed": next_data["power_min"] - power,
                "power_min": next_data["power_min"],
                "title": next_data["title"],
                "emoji": next_data["emoji"],
                "color": next_data["color"]
            }
        return None