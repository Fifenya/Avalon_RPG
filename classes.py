# classes.py
from enum import Enum
from typing import Dict, List, Optional
from database import Player

class CharacterClass(Enum):
    WARRIOR = "warrior"
    MAGE = "mage"
    ARCHER = "archer"
    TANK = "tank"
    ROGUE = "rogue"
    PRIEST = "priest"

CLASS_DATA = {
    CharacterClass.WARRIOR: {
        "name": "🗡️ Воин",
        "emoji": "🗡️",
        "description": "Мастер ближнего боя. Сильный и выносливый.",
        "base_stats": {
            "power": 60, "hp": 150, "max_hp": 150, "mana": 30, "max_mana": 30,
            "armor": 5, "crit_chance": 0.08, "dodge_chance": 0.03
        },
        "skills": [
            {"name": "💥 Мощный удар", "ap_cost": 2, "cooldown": 3, "damage_mult": 1.8},
            {"name": "🛡️ Защитная стойка", "ap_cost": 1, "cooldown": 4, "damage_mult": 0, "effect": "defense_up"},
            {"name": "🌀 Круговерть", "ap_cost": 3, "cooldown": 5, "damage_mult": 1.2, "effect": "aoe"}
        ]
    },
    CharacterClass.MAGE: {
        "name": "🔮 Маг",
        "emoji": "🔮",
        "description": "Повелитель стихий. Мощная магия, но хрупкая защита.",
        "base_stats": {
            "power": 40, "hp": 90, "max_hp": 90, "mana": 100, "max_mana": 100,
            "mana_regen": 3, "armor": 0, "crit_chance": 0.05, "dodge_chance": 0.05
        },
        "skills": [
            {"name": "🔥 Огненный шар", "ap_cost": 2, "cooldown": 2, "damage_mult": 1.6},
            {"name": "❄️ Ледяная броня", "ap_cost": 1, "cooldown": 4, "damage_mult": 0, "effect": "armor_up"},
            {"name": "⚡ Цепная молния", "ap_cost": 3, "cooldown": 6, "damage_mult": 1.0, "effect": "chain"}
        ]
    },
    CharacterClass.ARCHER: {
        "name": "🏹 Лучник",
        "emoji": "🏹",
        "description": "Мастер дальнего боя. Точно и критично.",
        "base_stats": {
            "power": 55, "hp": 110, "max_hp": 110, "mana": 50, "max_mana": 50,
            "armor": 2, "crit_chance": 0.15, "dodge_chance": 0.08
        },
        "skills": [
            {"name": "🎯 Точный выстрел", "ap_cost": 2, "cooldown": 2, "damage_mult": 1.5},
            {"name": "💨 Уворост", "ap_cost": 1, "cooldown": 3, "damage_mult": 0, "effect": "dodge_up"},
            {"name": "🏹 Град стрел", "ap_cost": 3, "cooldown": 4, "damage_mult": 0.8, "effect": "multi"}
        ]
    },
    CharacterClass.TANK: {
        "name": "🛡️ Танк",
        "emoji": "🛡️",
        "description": "Живая стена. Почти неубиваемый.",
        "base_stats": {
            "power": 45, "hp": 200, "max_hp": 200, "mana": 40, "max_mana": 40,
            "armor": 15, "crit_chance": 0.03, "dodge_chance": 0.02
        },
        "skills": [
            {"name": "⚔️ Щитовой удар", "ap_cost": 2, "cooldown": 3, "damage_mult": 1.2},
            {"name": "🛡️ Каменная кожа", "ap_cost": 1, "cooldown": 5, "damage_mult": 0, "effect": "super_armor"},
            {"name": "👊 Провокация", "ap_cost": 2, "cooldown": 4, "damage_mult": 0, "effect": "taunt"}
        ]
    },
    CharacterClass.ROGUE: {
        "name": "🗡️ Разбойник",
        "emoji": "🗡️",
        "description": "Скрытный убийца. Критические удары — его конёк.",
        "base_stats": {
            "power": 50, "hp": 100, "max_hp": 100, "mana": 50, "max_mana": 50,
            "armor": 3, "crit_chance": 0.20, "dodge_chance": 0.12
        },
        "skills": [
            {"name": "🔪 Удар в спину", "ap_cost": 2, "cooldown": 3, "damage_mult": 1.4},
            {"name": "🌑 Скрытность", "ap_cost": 2, "cooldown": 5, "damage_mult": 0, "effect": "stealth"},
            {"name": "☠️ Смертельный яд", "ap_cost": 1, "cooldown": 4, "damage_mult": 0.5, "effect": "poison"}
        ]
    },
    CharacterClass.PRIEST: {
        "name": "🙏 Жрец",
        "emoji": "🙏",
        "description": "Целитель и поддержка.",
        "base_stats": {
            "power": 35, "hp": 95, "max_hp": 95, "mana": 80, "max_mana": 80,
            "mana_regen": 2, "armor": 2, "crit_chance": 0.04, "dodge_chance": 0.04
        },
        "skills": [
            {"name": "✨ Святой свет", "ap_cost": 2, "cooldown": 3, "damage_mult": 1.2},
            {"name": "💚 Исцеление", "ap_cost": 2, "cooldown": 4, "damage_mult": 0, "effect": "heal"},
            {"name": "🛡️ Божественный щит", "ap_cost": 2, "cooldown": 6, "damage_mult": 0, "effect": "invincible"}
        ]
    }
}

def get_class_by_emoji(emoji_name: str) -> Optional[CharacterClass]:
    for cls, data in CLASS_DATA.items():
        if data["name"] == emoji_name or data["emoji"] == emoji_name:
            return cls
    return None

def apply_class_stats(player: Player, class_type: CharacterClass):
    """Применяет статы класса к игроку"""
    class_data = CLASS_DATA[class_type]
    stats = class_data["base_stats"]
    
    player["class"] = class_type.value
    player["power"] = stats["power"]
    player["hp"] = stats["hp"]
    player["max_hp"] = stats["max_hp"]
    player["mana"] = stats["mana"]
    player["max_mana"] = stats["max_mana"]
    if "mana_regen" in stats:
        player["mana_regen"] = stats["mana_regen"]
    if "armor" in stats:
        player["armor"] = stats["armor"]
    if "crit_chance" in stats:
        player["crit_chance"] = stats["crit_chance"]
    if "dodge_chance" in stats:
        player["dodge_chance"] = stats["dodge_chance"]
    
    player["class_skills"] = class_data["skills"]
    player.save()
    
    return class_data