# achievements.py
from datetime import datetime
from database import Database
from logger import GameLogger

logger = GameLogger()

def has_full_set(player_data, set_type: str) -> bool:
    """Проверяет, экипирован ли полный сет"""
    equipped = player_data.get('inventory', {}).get('equipped', {})
    required_slots = ['weapon', 'armor', 'helmet', 'boots']
    
    for slot in required_slots:
        if slot not in equipped:
            return False
        item = equipped[slot]
        item_name = item.get('name', '').lower()
        if set_type not in item_name:
            return False
    return True

class AchievementsSystem:
    def __init__(self):
        self.db = Database()
        self.achievements = {
            # Боевые достижения
            'killer_10': {
                'name': '🥉 Новичок',
                'desc': 'Убить 10 монстров',
                'condition': lambda p: p.get('kills', 0) >= 10,
                'reward': 500,
                'emoji': '🥉'
            },
            'killer_100': {
                'name': '🥈 Охотник',
                'desc': 'Убить 100 монстров',
                'condition': lambda p: p.get('kills', 0) >= 100,
                'reward': 2000,
                'emoji': '🥈'
            },
            'killer_1000': {
                'name': '🥇 Легенда',
                'desc': 'Убить 1000 монстров',
                'condition': lambda p: p.get('kills', 0) >= 1000,
                'reward': 10000,
                'emoji': '🥇'
            },
            
            # Экономические достижения
            'rich_10000': {
                'name': '💰 Богач',
                'desc': 'Накопить 10,000 монет',
                'condition': lambda p: p.get('money', 0) >= 10000,
                'reward': 1000,
                'emoji': '💰'
            },
            'rich_100000': {
                'name': '💎 Магнат',
                'desc': 'Накопить 100,000 монет',
                'condition': lambda p: p.get('money', 0) >= 100000,
                'reward': 5000,
                'emoji': '💎'
            },
            'rich_1000000': {
                'name': '👑 Король',
                'desc': 'Накопить 1,000,000 монет',
                'condition': lambda p: p.get('money', 0) >= 1000000,
                'reward': 50000,
                'emoji': '👑'
            },
            
            # Дуэли
            'duelist_10': {
                'name': '⚔️ Дуэлянт',
                'desc': 'Выиграть 10 дуэлей',
                'condition': lambda p: p.get('wins', 0) >= 10,
                'reward': 1000,
                'emoji': '⚔️'
            },
            'duelist_100': {
                'name': '🏆 Чемпион',
                'desc': 'Выиграть 100 дуэлей',
                'condition': lambda p: p.get('wins', 0) >= 100,
                'reward': 10000,
                'emoji': '🏆'
            },
            
            # Работа и крафт
            'worker_100': {
                'name': '🎮 Трудяга',
                'desc': 'Поработать 100 раз',
                'condition': lambda p: p.get('works_done', 0) >= 100,
                'reward': 2000,
                'emoji': '🎮'
            },
            'crafter_100': {
                'name': '🔨 Кузнец',
                'desc': 'Скрафтить 100 предметов',
                'condition': lambda p: p.get('crafts_done', 0) >= 100,
                'reward': 3000,
                'emoji': '🔨'
            },
            'collector_50': {
                'name': '💎 Коллекционер',
                'desc': 'Собрать 50 видов ресурсов',
                'condition': lambda p: len(p.get('resources', {})) >= 50,
                'reward': 5000,
                'emoji': '💎'
            },
            
            # Ранговые достижения
            'rank_D': {
                'name': '🎖️ Воин',
                'desc': 'Достичь ранга D',
                'condition': lambda p: p.get('rank', 'G') in ['D', 'C', 'B', 'A', 'S', 'S+', 'SS', 'SS+', 'SSR', 'SSR+'],
                'reward': 2000,
                'emoji': '🎖️'
            },
            'rank_A': {
                'name': '⭐ Легенда',
                'desc': 'Достичь ранга A',
                'condition': lambda p: p.get('rank', 'G') in ['A', 'S', 'S+', 'SS', 'SS+', 'SSR', 'SSR+'],
                'reward': 10000,
                'emoji': '⭐'
            },
            'rank_SSR': {
                'name': '👑 Бог',
                'desc': 'Достичь ранга SSR',
                'condition': lambda p: p.get('rank', 'G') in ['SSR', 'SSR+'],
                'reward': 50000,
                'emoji': '👑'
            },
            
            # Подземелья
            'dungeon_clear_1': {
                'name': '🏚️ Исследователь',
                'desc': 'Пройди 1-й этаж подземелья',
                'condition': lambda p: p.get('dungeon_best_floor', 0) >= 1,
                'reward': 500,
                'emoji': '🏚️'
            },
            'dungeon_clear_5': {
                'name': '🏆 Покоритель бездны',
                'desc': 'Пройди все 5 этажей подземелья',
                'condition': lambda p: p.get('dungeon_best_floor', 0) >= 5,
                'reward': 10000,
                'emoji': '🏆'
            },  # <-- ИСПРАВЛЕНО: добавлена запятая
            'login_3_days': {
                'name': '📅 Завсегдатай',
                'desc': 'Заходить в игру 3 дня подряд',
                'condition': lambda p: p.get('login_streak', 0) >= 3,
                'reward': 500,
                'emoji': '📅'
            },
            'login_7_days': {
                'name': '📅 Старожил',
                'desc': 'Заходить в игру 7 дней подряд',
                'condition': lambda p: p.get('login_streak', 0) >= 7,
                'reward': 1500,
                'emoji': '📅'
            },
            'login_30_days': {
                'name': '📅 Ветеран',
                'desc': 'Заходить в игру 30 дней подряд',
                'condition': lambda p: p.get('login_streak', 0) >= 30,
                'reward': 10000,
                'emoji': '📅'
            },

            # Достижения за боссов
            'boss_killer_1': {
                'name': '👑 Убийца боссов',
                'desc': 'Убить 1 босса',
                'condition': lambda p: p.get('boss_kills', 0) >= 1,
                'reward': 1000,
                'emoji': '👑'
            },
            'boss_killer_10': {
                'name': '👑 Охотник на боссов',
                'desc': 'Убить 10 боссов',
                'condition': lambda p: p.get('boss_kills', 0) >= 10,
                'reward': 5000,
                'emoji': '👑'
            },
            'boss_killer_50': {
                'name': '👑 Легендарный охотник',
                'desc': 'Убить 50 боссов',
                'condition': lambda p: p.get('boss_kills', 0) >= 50,
                'reward': 25000,
                'emoji': '👑'
            },

            # Достижения за PvP арену
            'arena_win_10': {
                'name': '⚔️ Боец арены',
                'desc': 'Выиграть 10 боёв на арене',
                'condition': lambda p: p.get('arena_wins', 0) >= 10,
                'reward': 1000,
                'emoji': '⚔️'
            },
            'arena_win_100': {
                'name': '⚔️ Ветеран арены',
                'desc': 'Выиграть 100 боёв на арене',
                'condition': lambda p: p.get('arena_wins', 0) >= 100,
                'reward': 10000,
                'emoji': '⚔️'
            },

            # Достижения за экипировку
            'full_set_iron': {
                'name': '⚙️ Железный воин',
                'desc': 'Надеть полный железный сет',
                'condition': lambda p: has_full_set(p, 'iron'),
                'reward': 2000,
                'emoji': '⚙️'
            },
            'full_set_steel': {
                'name': '⚙️ Стальной рыцарь',
                'desc': 'Надеть полный стальной сет',
                'condition': lambda p: has_full_set(p, 'steel'),
                'reward': 5000,
                'emoji': '⚙️'
            }
        }
    
    def check_achievements(self, uid):
        """Проверяет, не получил ли игрок новые достижения"""
        player_data = self.db.get_player(uid)
        if not player_data:
            return []
        
        if 'achievements' not in player_data:
            player_data['achievements'] = {}
        
        new_achievements = []
        
        for ach_id, ach_data in self.achievements.items():
            if ach_id not in player_data['achievements']:
                if ach_data['condition'](player_data):
                    player_data['achievements'][ach_id] = {
                        'got': datetime.now().isoformat(),
                        'name': ach_data['name']
                    }
                    
                    # Выдаём награду
                    player_data['money'] = player_data.get('money', 0) + ach_data['reward']
                    
                    new_achievements.append({
                        'id': ach_id,
                        'name': ach_data['name'],
                        'desc': ach_data['desc'],
                        'reward': ach_data['reward'],
                        'emoji': ach_data['emoji']
                    })
        
        if new_achievements:
            self.db.set_player(uid, player_data)
        
        return new_achievements
    
    def get_achievements_list(self, uid):
        """Возвращает список всех достижений игрока"""
        player_data = self.db.get_player(uid)
        if not player_data or 'achievements' not in player_data:
            return {}
        
        return player_data['achievements']
    
    def format_achievements(self, uid):
        """Форматирует достижения для вывода"""
        player_data = self.db.get_player(uid)
        if not player_data:
            return "❌ Игрок не найден"
        
        achievements = player_data.get('achievements', {})
        
        if not achievements:
            return "🏆 **ДОСТИЖЕНИЯ** 🏆\n\nПока нет достижений...\n\n💡 Убивай монстров, зарабатывай монеты и прокачивай ранг!"
        
        text = "🏆 **ДОСТИЖЕНИЯ** 🏆\n\n"
        
        # Сортируем достижения по дате получения (новые сверху)
        sorted_achs = sorted(achievements.items(), key=lambda x: x[1].get('got', ''), reverse=True)
        
        for ach_id, ach_data in sorted_achs:
            ach_info = self.achievements.get(ach_id, {})
            emoji = ach_info.get('emoji', '🏆')
            name = ach_data.get('name', ach_id)
            date_str = ach_data.get('got', '')
            try:
                date = datetime.fromisoformat(date_str).strftime('%d.%m.%Y')
            except:
                date = "недавно"
            text += f"{emoji} **{name}**\n└ Получено: {date}\n\n"
        
        return text