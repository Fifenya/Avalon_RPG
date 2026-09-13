# ai/enemy_memory.py
import json
import os
from datetime import datetime
from typing import Dict, List

ENEMY_MEMORY_FILE = "data/enemy_memory.json"


class EnemyMemory:
    """Сохранение и загрузка памяти ИИ"""
    
    @staticmethod
    def load() -> Dict:
        """Загружает память о всех боях"""
        if os.path.exists(ENEMY_MEMORY_FILE):
            with open(ENEMY_MEMORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    @staticmethod
    def save(memory: Dict):
        """Сохраняет память"""
        with open(ENEMY_MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def record_battle(enemy_id: str, player_id: str, player_won: bool,
                      player_stats: Dict, battle_log: List):
        """Записывает результат боя"""
        memory = EnemyMemory.load()
        key = f"{enemy_id}_{player_id}"
        
        if key not in memory:
            memory[key] = {
                'total_battles': 0,
                'player_wins': 0,
                'enemy_wins': 0,
                'player_behavior': 'balanced',
                'player_patterns': {},
                'player_stats': {},
                'enemy_adaptations': {},
                'battle_history': []
            }
        
        record = memory[key]
        record['total_battles'] += 1
        if player_won:
            record['player_wins'] += 1
        else:
            record['enemy_wins'] += 1
        
        # Обновляем статистику игрока
        self._update_player_stats(record, player_stats)
        
        # Добавляем в историю
        record['battle_history'].append({
            'timestamp': datetime.now().isoformat(),
            'player_won': player_won,
            'log_summary': battle_log[-10:]  # последние 10 действий
        })
        
        # Ограничиваем историю 50 боями
        if len(record['battle_history']) > 50:
            record['battle_history'] = record['battle_history'][-50:]
        
        EnemyMemory.save(memory)
    
    @staticmethod
    def _update_player_stats(record: Dict, new_stats: Dict):
        """Обновляет агрегированную статистику игрока"""
        stats = record.get('player_stats', {})
        
        for stat, value in new_stats.items():
            if stat in ['min_hp', 'max_hp', 'avg_hp']:
                continue
            
            if stat not in stats:
                stats[stat] = {'min': value, 'max': value, 'sum': value, 'count': 1}
            else:
                stats[stat]['min'] = min(stats[stat]['min'], value)
                stats[stat]['max'] = max(stats[stat]['max'], value)
                stats[stat]['sum'] += value
                stats[stat]['count'] += 1
        
        record['player_stats'] = stats


enemy_memory = EnemyMemory()