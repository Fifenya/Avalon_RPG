# database.py - ПОЛНАЯ РАБОЧАЯ ВЕРСИЯ
import json
import os
import time
from config import DATA_FILE, START_MONEY

class Database:
    _instance = None
    _data = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._load()
        return cls._instance
    
    @classmethod
    def _load(cls):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    cls._data = json.load(f)
                print(f"📂 Загружено {len(cls._data)} записей из {DATA_FILE}")
            except Exception as e:
                print(f"❌ Ошибка загрузки: {e}")
                cls._data = {'_clans': {}}
        else:
            cls._data = {'_clans': {}}
            print(f"📂 Создан новый файл {DATA_FILE}")
    
    @classmethod
    def save(cls):
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(cls._data, f, ensure_ascii=False, indent=2)
            print(f"💾 Данные сохранены в {DATA_FILE}")
        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
    
    @classmethod
    def get_all(cls):
        return cls._data
    
    @classmethod
    def get_player(cls, uid):
        return cls._data.get(str(uid))
    
    @classmethod
    def set_player(cls, uid, data):
        cls._data[str(uid)] = data
        cls.save()
    
    @classmethod
    def cleanup_phantoms(cls):
        deleted = 0
        for uid, p in list(cls._data.items()):
            if uid.startswith('_'):
                continue
            if isinstance(p, dict) and not p.get('race'):
                del cls._data[uid]
                deleted += 1
        if deleted:
            cls.save()
            print(f"🗑️ Очистка фантомов: удалено {deleted}")
        return deleted


def default_player_data(name=None):
    """Стандартные данные нового игрока"""
    return {
        'name': name,
        'tg_first_name': None,
        'race': None,
        'class': None,
        'gender': None,
        'money': START_MONEY,
        'power': 50,
        'hp': 100,
        'max_hp': 100,
        'mana': 50,
        'max_mana': 50,
        'mana_regen': 1,
        'level': 1,
        'exp': 0,
        'location': 'city',
        'dungeon_floor': 1,
        'dungeon_progress': 0,
        'last_mana_update': time.time(),
        'tg_username': None,
        'inventory': {'items': [], 'equipped': {}},
        'resources': {},
        'kills': 0,
        'wins': 0,
        'losses': 0,
        'battle_logging_enabled': False,
        'achievements': {},
        'death_time': None,
        'destiny_quest': None,
        'destiny_effect': None,
        'crit_chance': 0.1,
        'dodge_chance': 0.05,
        'block_chance': 0.05,
        'agility': 10,
        'rank': 'G',
        'works_done': 0,
        'crafts_done': 0,
        'class_skills': [],
        'last_login': None,
        'login_streak': 0,
    }


class Player:
    def __init__(self, user_id, name=None):
        self.uid = str(user_id)
        self.db = Database()
        self.data = self.db.get_player(self.uid)
        
        if not self.data and name:
            # Создаём нового игрока
            self.data = {
                'name': name,
                'tg_first_name': None,
                'race': None,
                'class': None,
                'gender': None,
                'money': START_MONEY,
                'power': 50,
                'hp': 100,
                'max_hp': 100,
                'mana': 50,
                'max_mana': 50,
                'mana_regen': 1,
                'level': 1,
                'exp': 0,
                'location': 'city',
                'dungeon_floor': 1,
                'dungeon_progress': 0,
                'last_mana_update': time.time(),
                'tg_username': None,
                'inventory': {'items': [], 'equipped': {}},
                'resources': {},
                'kills': 0,
                'wins': 0,
                'losses': 0,
                'battle_logging_enabled': False,
                'achievements': {},
                'death_time': None,
                'destiny_quest': None,
                'destiny_effect': None,
                'crit_chance': 0.1,
                'dodge_chance': 0.05,
                'block_chance': 0.05,
                'agility': 10,
                'rank': 'G',
                'works_done': 0,
                'crafts_done': 0,
                'class_skills': [],
                'last_login': None,
                'login_streak': 0
            }
            self.save()
            print(f"✅ Создан новый игрок: {name} ({self.uid})")
        elif not self.data:
            self.data = default_player_data()
    
    def save(self):
        if self.data.get('_temp'):
            return
        self.db.set_player(self.uid, self.data)
    
    def __getitem__(self, key):
        return self.data.get(key)
    
    def __setitem__(self, key, value):
        if self.data.get('_temp'):
            return
        self.data[key] = value
    
    def get(self, key, default=None):
        return self.data.get(key, default)
    
    def regenerate_mana(self):
        if self.data.get('_temp'):
            return 50
        current_time = time.time()
        last_update = self.data.get('last_mana_update', current_time)
        time_passed = current_time - last_update
        
        mana_regen = self.data.get('mana_regen', 1)
        mana_gain = int((time_passed / 60) * mana_regen)
        
        if mana_gain > 0:
            current_mana = self.data.get('mana', 50)
            max_mana = self.data.get('max_mana', 50)
            new_mana = min(max_mana, current_mana + mana_gain)
            self.data['mana'] = new_mana
            self.data['last_mana_update'] = current_time
            self.save()
        
        return self.data.get('mana', 50)
    
    def get_mana_info(self):
        if self.data.get('_temp'):
            return 50, 50, 1
        current_mana = self.regenerate_mana()
        return current_mana, self.data.get('max_mana', 50), self.data.get('mana_regen', 1)
    
    def is_dead(self):
        if self.data.get('_temp'):
            return False
        death_time = self.data.get('death_time')
        if not death_time:
            return False
        from config import DEATH_REGEN_DELAY
        if time.time() - death_time >= DEATH_REGEN_DELAY:
            self.data['death_time'] = None
            self.data['hp'] = self.data.get('max_hp', 100)
            self.save()
            return False
        return True
    
    def fix_race(self):
        """Исправляет расу, если она начинается с 'beast_'"""
        race = self.data.get('race', '')
        if race and race.startswith('beast_'):
            self.data['race'] = race.replace('beast_', '')
            self.save()
            return True
        return False
    
    def is_complete(self):
        """Проверяет, полностью ли создан персонаж"""
        missing = []
        if not self.data.get('race'):
            missing.append('race')
        if not self.data.get('gender'):
            missing.append('gender')
        if not self.data.get('class'):
            missing.append('class')
        return (len(missing) == 0, missing)