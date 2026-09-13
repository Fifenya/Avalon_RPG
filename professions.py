# game/professions.py
# Теперь интегрирован с classes.py

from enum import Enum
from typing import Dict, List, Optional
from database import Player

class Profession(Enum):
    BERSERKER = "berserker"
    DEFENDER = "defender"
    # ...

# Данные профессий с привязкой к классам
PROFESSION_DATA = {
    Profession.BERSERKER: {
        "name": "😤 Берсерк",
        "base_class": "warrior",
        "requirements": {"level": 10, "kills": 100},
        "bonuses": {"power": 20, "crit": 0.10},
        "skills": ["Яростный рывок", "Кровавая жатва"],
    },
    # ...
}

class ProfessionSystem:
    def __init__(self):
        self.active_professions = {}
    
    def get_available_professions(self, player: Player) -> List[Dict]:
        """Возвращает доступные профессии для игрока"""
        player_class = player.get('class')
        available = []
        
        for prof_id, prof_data in PROFESSION_DATA.items():
            if prof_data['base_class'] != player_class:
                continue
            
            # Проверка требований
            if self._check_requirements(player, prof_data.get('requirements', {})):
                available.append({
                    'id': prof_id.value,
                    'name': prof_data['name'],
                    'bonuses': prof_data['bonuses'],
                    'skills': prof_data['skills']
                })
        
        return available
    
    def _check_requirements(self, player: Player, requirements: Dict) -> bool:
        for req, value in requirements.items():
            if req == 'level' and player['level'] < value:
                return False
            if req == 'kills' and player.get('kills', 0) < value:
                return False
            if req == 'wins' and player.get('wins', 0) < value:
                return False
        return True
    
    def unlock(self, uid: str, profession_id: str) -> bool:
        """Разблокирует профессию"""
        # ... логика разблокировки
        pass