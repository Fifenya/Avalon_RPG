# enemy_personas.py — типы врагов с уникальным поведением
import random

# Системные промпты для разных типов врагов
ENEMY_PERSONAS = {
    "aggressive": {
        "name": "Агрессивный",
        "system": """Ты агрессивный воин. Ты любишь атаковать и наносить максимальный урон.
- Предпочитай heavy_attack и attack_head
- Защищайся ТОЛЬКО если HP < 20%
- Никогда не беги и не скрывайся
- Цель: убить врага как можно быстрее""",
        "modifiers": {"aggression": 0.9, "defense": 0.1},
    },
    
    "cautious": {
        "name": "Осторожный",
        "system": """Ты осторожный тактик. Ты ценишь свою жизнь и атакуешь обдуманно.
- Защищайся если HP < 50%
- Атакуй только когда уверен в успехе
- Избегай risky moves (heavy_attack при высоком HP врага)
- Можешь flee если HP < 15%""",
        "modifiers": {"aggression": 0.4, "defense": 0.6},
    },
    
    "cunning": {
        "name": "Хитрый",
        "system": """Ты хитрый боец. Ты используешь слабости врага и критические удары.
- Предпочитай attack_back и attack_arms (больше крита)
- Используй hide когда HP < 40%
- Тяжёлые удары только когда враг не защищается
- Можешь flee если ситуация безнадёжна""",
        "modifiers": {"aggression": 0.6, "defense": 0.3, "crit_focus": 0.8},
    },
    
    "berserker": {
        "name": "Берсерк",
        "system": """Ты берсерк. Чем ближе к смерти, тем яростнее атакуешь.
- При HP > 60%: обычные атаки
- При HP 30-60%: heavy_attack чаще
- При HP < 30%: ТОЛЬКО heavy_attack и attack_head
- Никогда не защищайся и не беги""",
        "modifiers": {"aggression": 0.7, "berserk": 1.0},
    },
    
    "default": {
        "name": "Обычный",
        "system": """Ты обычный боец. Ты балансируешь между атакой и защитой.
- Атакуй когда у тебя преимущество
- Защищайся когда HP низкое или враг силён
- Используй все доступные действия разумно""",
        "modifiers": {"aggression": 0.5, "defense": 0.5},
    },
}

def get_persona_for_enemy(enemy_id: str, enemy_level: int = 1) -> dict:
    """Возвращает персону для врага (случайно или по ID)"""
    
    # Специальные враги с фиксированной персоной
    special_enemies = {
        "wolf": "aggressive",
        "bear": "berserker",
        "assassin": "cunning",
        "guard": "cautious",
        "boss_dragon": "berserker",
        "boss_lich": "cunning",
    }
    
    enemy_key = enemy_id.lower() if enemy_id else ""
    for key, persona in special_enemies.items():
        if key in enemy_key:
            return ENEMY_PERSONAS[persona]
    
    # Случайная персона для обычных врагов
    # Чем выше уровень, тем чаще встречаются хитрые/берсерки
    if enemy_level >= 10:
        weights = [0.2, 0.2, 0.3, 0.3]  # aggressive, cautious, cunning, berserker
    elif enemy_level >= 5:
        weights = [0.3, 0.3, 0.2, 0.2]
    else:
        weights = [0.4, 0.4, 0.1, 0.1]
    
    persona_keys = ["aggressive", "cautious", "cunning", "berserker"]
    chosen = random.choices(persona_keys, weights=weights, k=1)[0]
    return ENEMY_PERSONAS[chosen]

def get_system_prompt(persona: dict, state: dict) -> str:
    """Формирует полный системный промпт с учётом состояния боя"""
    base_prompt = persona.get("system", ENEMY_PERSONAS["default"]["system"])
    
    # Добавляем контекст если нужно
    enemy_hp = state.get("enemy_hp", 100)
    enemy_max_hp = state.get("enemy_max_hp", 100)
    hp_percent = (enemy_hp / enemy_max_hp) * 100 if enemy_max_hp > 0 else 100
    
    context = f"\nТекущее состояние: HP {hp_percent:.0f}%"
    
    # Специальные указания для берсерка
    if "berserk" in persona.get("modifiers", {}):
        if hp_percent < 30:
            context += " [БЕРСЕРК РЕЖИМ: только яростные атаки!]"
    
    return base_prompt + context
